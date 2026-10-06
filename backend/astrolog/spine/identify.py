"""The `identify` stage: cross-checks the header's name against the measured sky, and links.
A learned rule names only where the sky is silent; a user's correction applies even where it speaks.
"""

import logging
import sqlite3
from collections.abc import Iterator
from dataclasses import asdict, replace
from functools import partial
from typing import Any

from ..catalog import NamedEntry, lookup
from ..clock import now_iso
from ..db.transaction import transaction
from ..vocab.header_value import normalize_header_value
from ..vocab.object_label import clean_object_name
from . import declarations as decl
from . import gear_usage, object_answer, object_candidates, unnamed
from . import identify_decide as rule
from . import identify_geometry as geometry
from . import identify_link as link
from . import identify_score as score
from . import identify_store as store
from .identify_decide import Branch, Decision, IdentifyReason, IdentityConfidence, IdentityMethod
from .identify_score import Candidate
from .stage_run import Event, frame_safely, receipt, watched
from .stages import StageName, StageStatus, ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("linked", "new_objects", "review", "waiting", "name_taken", "swept", "errors")
CANDIDATES_LIMIT = 6


def candidates(
    conn: sqlite3.Connection, wcs: dict[str, Any], limit: int | None = CANDIDATES_LIMIT
) -> list[Candidate]:
    """Catalog entries competing for this frame, best first, each with `score` and `in_frame`."""
    if wcs.get("ra_deg") is None or wcs.get("dec_deg") is None:
        return []

    fov = geometry.frame_radius_deg(wcs)
    found = lookup.in_cone(conn, wcs["ra_deg"], wcs["dec_deg"], geometry.search_radius_deg(fov))

    running = []
    for entry in found:
        size = entry.size_major_arcmin
        if not geometry.overlaps_frame(entry.sep_deg, size, fov):
            continue
        running.append(
            Candidate(
                **asdict(entry),
                score=score.score_candidate(entry, fov),
                in_frame=geometry.in_frame(wcs, entry.ra_deg, entry.dec_deg, size),
            )
        )
    running.sort(key=lambda c: c.score, reverse=True)
    return running[:limit]


def identify_frames(conn: sqlite3.Connection) -> Iterator[Event]:
    """Links every frame waiting on this stage: one event per frame, then the receipt."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    errors, seen, frame_ids = [], 0, []

    def at_end() -> None:
        if frame_ids:  # detach and sweep already ran, even before the first frame
            _at_round_end(conn)

    with watched(StageName.IDENTIFY, counts, at_end):
        frame_ids = ready(conn, StageName.IDENTIFY)
        store.detach(conn, frame_ids)
        counts["swept"] = _sweep(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            # Removing a folder mid-run can send a listed frame back to waiting.
            if ready(conn, StageName.IDENTIFY, frame_id=frame_id):
                work = partial(_one_frame, conn, frame_id, counts)
                frame_safely(conn, StageName.IDENTIFY, frame_id, work, counts, errors)
            seen += 1
            yield {"current": seen, "total": total, **counts}
    yield receipt("ok", None, counts, errors, total=seen)


def _at_round_end(conn: sqlite3.Connection) -> None:
    """Rewrites what a name move affects."""
    gear_usage.write(conn)
    object_candidates.write(conn)


def _sweep(conn: sqlite3.Connection) -> int:
    """After the detach and at the start, not the end: the names it frees go to this same pass."""
    dropped = store.drop_empty_objects(conn)
    if dropped:
        log.info("identify: oggetti rimasti senza pose, tolti", extra={"quanti": dropped})
    return dropped


def _one_frame(conn: sqlite3.Connection, frame_id: int, counts: dict[str, int]) -> None:
    """The frame's outcome in one transaction: what is done stays done even on a later failure."""
    frame = store.frame(conn, frame_id)
    raw = clean_object_name(frame["object_raw"])
    sky = store.wcs(conn, frame_id)
    # The whole list, not the page's cap: the header's designation may rank below it.
    cands = candidates(conn, sky, limit=None)
    fov = geometry.frame_radius_deg(sky) if sky else None
    # `raw` stays the header's spelling; the name that DECIDES is the ruled one.
    named, hit, ruled = _named_by_rule(conn, raw, with_sky=bool(cands))
    # No name and no candidates: fall back to the frame's group.
    group_said = (
        None if raw or cands else unnamed.named_by_group(conn, unnamed.assign(conn, frame_id))
    )
    if group_said and group_said != unnamed.NONE:
        (named, hit), ruled = group_said, True
    decision = rule.decide(raw_name=named, hit=hit, cands=cands, fov_radius_deg=fov)
    if ruled:
        # A rule is the user's word where the sky cannot contradict it: locked.
        decision = _users(decision)
    decision = _as_the_user_said(conn, decision)
    # The user's "not an object" beats name and sky, a group's (no `found_key`) only without
    # candidates. What was found is the card's key; a frame finding nothing keeps the card's.
    put_out = object_answer.said_not_an_object(conn, frame["frame_hash"]) and bool(
        frame["found_key"] or not cands
    )
    found_key = (decision.slug or decision.name or frame["found_key"]) if put_out else None

    now = now_iso()
    with transaction(conn):
        store.set_empty_cone(conn, frame_id, int(not cands) if sky else None)
        store.set_found_key(conn, frame_id, found_key)
        if put_out or decision.branch == Branch.NOTHING:
            # Not a fault: `skipped`, not `pending`, or the backlog never reaches zero.
            skip_reason = (
                IdentifyReason.NOT_AN_OBJECT
                if put_out or group_said == unnamed.NONE
                else IdentifyReason.NO_NAME_NO_SKY
            )
            set_status(
                conn, frame_id, StageName.IDENTIFY, StageStatus.SKIPPED, reason=skip_reason, now=now
            )
            counts["waiting"] += skip_reason == IdentifyReason.NO_NAME_NO_SKY
        else:
            entry = link.entry_for(conn, decision.slug, hit, cands)
            object_id, locked = link.hang(conn, decision, raw, entry, now, counts)
            store.set_frame_object(conn, frame_id, object_id)
            set_status(conn, frame_id, StageName.IDENTIFY, StageStatus.DONE, now=now)
            counts["linked"] += 1
            # Only counted if the page will actually ask: a locked object's doubt does not reach it.
            if decision.review and not locked:
                counts["review"] += 1


def _named_by_rule(
    conn: sqlite3.Connection, raw: str | None, *, with_sky: bool
) -> tuple[str | None, NamedEntry | None, bool]:
    """`(name, entry, ruled)` after the learned rules."""
    if not raw:
        return raw, None, False
    target = None if with_sky else decl.alias_target(conn, "object", normalize_header_value(raw))
    if target:
        named, entry = object_answer.catalog_target(conn, target) or (target, None)
        return named, entry, True
    return raw, lookup.by_designation(conn, raw), False


def _as_the_user_said(conn: sqlite3.Connection, decision: Decision) -> Decision:
    """The decision after the user's corrections, followed as a chain: a later one overrides."""
    found = decision.slug or decision.name
    visited: set[str] = set()
    while found:
        target = object_answer.correction_of(conn, found)
        # Checked BEFORE applying: after, it would land right back where it started. A target
        # equal to `found` still applies once: "it is right" makes it the user's.
        if target is None or target[1] in visited:
            break
        # Joins `visited` even on failure, or a missing target would retry forever.
        visited.update((found, target[1]))
        decision = _towards(conn, decision, target[1], kind=target[0])
        found = decision.slug or decision.name
    return decision


def _towards(conn: sqlite3.Connection, decision: Decision, value: str, kind: str) -> Decision:
    """The decision moved onto `value`, a catalog slug or a free-text name."""
    entry = lookup.by_slug(conn, value)
    if kind == "catalog" and entry is None:
        log.warning(
            "identify: la parola dell'utente punta a uno slug che non c'e'", extra={"a": value}
        )
        return decision
    if entry is not None:
        return replace(_users(decision), slug=value, name=None)
    return replace(_users(decision), slug=None, name=value)


def _users(decision: Decision) -> Decision:
    """Born from the user's own word: `user`/`user`, which also locks it."""
    return replace(
        decision,
        method=IdentityMethod.USER,
        confidence=IdentityConfidence.USER,
        review=False,
    )
