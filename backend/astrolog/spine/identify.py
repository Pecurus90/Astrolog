"""The `identify` stage: cross-checks the header's name against the measured sky, and links.
A learned rule names only where the sky is silent; a user's correction applies even where it speaks.
"""

import logging
import sqlite3
from collections.abc import Iterator
from functools import partial
from typing import Any

from ..catalog import lookup
from ..clock import now_iso
from ..db.transaction import transaction
from ..vocab.header_value import normalize_header_value
from ..vocab.object_label import clean_object_name
from . import declarations as decl
from . import gear_usage, object_candidates, unnamed
from . import identify_decide as rule
from . import identify_geometry as geometry
from . import identify_link as link
from . import identify_score as score
from . import identify_store as store
from . import object_answer as risposta
from .stage_run import Event, frame_safely, receipt, watched
from .stages import ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("linked", "new_objects", "review", "waiting", "name_taken", "swept", "errors")
CANDIDATES_LIMIT = 6


def candidates(
    conn: sqlite3.Connection, wcs: dict[str, Any], limit: int | None = CANDIDATES_LIMIT
) -> list[dict[str, Any]]:
    """Catalog entries competing for this frame, best first, each with `score` and `in_frame`."""
    if wcs.get("ra_deg") is None or wcs.get("dec_deg") is None:
        return []

    fov = geometry.frame_radius_deg(wcs)
    found = lookup.in_cone(conn, wcs["ra_deg"], wcs["dec_deg"], geometry.search_radius_deg(fov))

    running = []
    for entry in found:
        size = entry.get("size_major_arcmin")
        if not geometry.overlaps_frame(entry["sep_deg"], size, fov):
            continue
        running.append(
            {
                **entry,
                "score": score.score_candidate(entry, fov),
                "in_frame": geometry.in_frame(wcs, entry["ra_deg"], entry["dec_deg"], size),
            }
        )
    running.sort(key=lambda c: c["score"], reverse=True)
    return running[:limit]


def identify_frames(conn: sqlite3.Connection) -> Iterator[Event]:
    """Links every frame waiting on this stage: one event per frame, then the receipt."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    errors, seen, frame_ids = [], 0, []

    def at_end() -> None:
        if frame_ids:  # detach and sweep already ran, even before the first frame
            _at_round_end(conn)

    with watched("identify", counts, at_end):
        frame_ids = ready(conn, "identify")
        store.detach(conn, frame_ids)
        counts["swept"] = _sweep(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            # Removing a folder mid-run can send a listed frame back to waiting.
            if ready(conn, "identify", frame_id=frame_id):
                work = partial(_one_frame, conn, frame_id, counts)
                frame_safely(conn, "identify", frame_id, work, counts, errors)
            seen += 1
            yield {"current": seen, "total": total, **counts}
    yield receipt("ok", None, counts, errors, total=seen)


def _at_round_end(conn: sqlite3.Connection) -> None:
    """Rewrites what a name move affects."""
    gear_usage.write(conn)
    object_candidates.write(conn)


def _sweep(conn: sqlite3.Connection) -> int:
    """After the detach and at the start, not the end: the names it frees go to this same pass."""
    tolti = store.drop_empty_objects(conn)
    if tolti:
        log.info("identify: oggetti rimasti senza pose, tolti", extra={"quanti": tolti})
    return tolti


def _one_frame(conn: sqlite3.Connection, frame_id: int, counts: dict[str, int]) -> None:
    """The frame's outcome in one transaction: what is done stays done even on a later failure."""
    frame = store.frame(conn, frame_id)
    raw = clean_object_name(frame["object_raw"])
    sky = store.wcs(conn, frame_id)
    # The whole list, not the page's cap: the header's designation may rank below it.
    cands = candidates(conn, sky, limit=None)
    fov = geometry.frame_radius_deg(sky) if sky else None
    # `raw` stays the header's spelling; the name that DECIDES is the ruled one.
    named, hit, da_regola = _named_by_rule(conn, raw, con_cielo=bool(cands))
    # No name and no candidates: fall back to the frame's group.
    detto = None if raw or cands else unnamed.named_by_group(conn, unnamed.assign(conn, frame_id))
    if detto and detto != unnamed.NONE:
        (named, hit), da_regola = detto, True
    decision = rule.decide(raw_name=named, hit=hit, cands=cands, fov_radius_deg=fov)
    if da_regola:
        # A rule is the user's word where the sky cannot contradict it: locked.
        decision = {**decision, "method": "user", "confidence": "user", "review": False}
    decision = _as_the_user_said(conn, decision)

    now = now_iso()
    with transaction(conn):
        store.set_empty_cone(conn, frame_id, int(not cands) if sky else None)
        if decision["branch"] == "nothing":
            # Not a fault: `skipped`, not `pending`, or the backlog never reaches zero.
            motivo = rule.NOT_AN_OBJECT if detto == unnamed.NONE else rule.NO_NAME_NO_SKY
            set_status(conn, frame_id, "identify", "skipped", reason=motivo, now=now)
            counts["waiting"] += motivo == rule.NO_NAME_NO_SKY
        else:
            entry = link.entry_for(conn, decision["slug"], hit, cands)
            object_id, lucchettato = link.hang(conn, decision, raw, entry, now, counts)
            store.set_frame_object(conn, frame_id, object_id)
            set_status(conn, frame_id, "identify", "done", now=now)
            counts["linked"] += 1
            # Only counted if the page will actually ask: a locked object's doubt does not reach it.
            if decision["review"] and not lucchettato:
                counts["review"] += 1


def _named_by_rule(
    conn: sqlite3.Connection, raw: str | None, *, con_cielo: bool
) -> tuple[str | None, dict[str, Any] | None, bool]:
    """`(name, entry, ruled)` after the learned rules."""
    if not raw:
        return raw, None, False
    target = None if con_cielo else decl.alias_target(conn, "object", normalize_header_value(raw))
    if target:
        named, entry = risposta.catalog_target(conn, target) or (target, None)
        return named, entry, True
    return raw, lookup.by_designation(conn, raw), False


def _as_the_user_said(conn: sqlite3.Connection, decision: dict[str, Any]) -> dict[str, Any]:
    """The decision after the user's corrections, followed as a chain: a later one overrides."""
    found = decision["slug"] or decision["name"]
    visti = set()
    while found:
        visti.add(found)
        target = risposta.correction_of(conn, found)
        # Checked BEFORE applying: after, it would land right back where it started.
        if target is None or target[1] in visti:
            break
        # Joins `visti` even on failure, or a missing target would retry forever.
        visti.add(target[1])
        decision = _towards(conn, decision, target[1], kind=target[0])
        found = decision["slug"] or decision["name"]
    return decision


def _towards(
    conn: sqlite3.Connection, decision: dict[str, Any], value: str, kind: str
) -> dict[str, Any]:
    """The decision moved onto `value`, a catalog slug or a free-text name."""
    entry = lookup.by_slug(conn, value)
    if kind == "catalog" and entry is None:
        log.warning(
            "identify: la parola dell'utente punta a uno slug che non c'e'", extra={"a": value}
        )
        return decision
    # Born from the user's own word: `user`/`user`, which also locks it.
    detto = {"method": "user", "confidence": "user", "review": False}
    if entry is not None:
        return {**decision, **detto, "slug": value, "name": None}
    return {**decision, **detto, "slug": None, "name": value}
