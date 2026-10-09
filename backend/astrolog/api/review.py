"""Apply writes only the answers: seeing a question does not close it (ADR 0014, S4)."""

import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from ..clock import now_iso
from ..spine import mosaic_proposals as mosaic_reader
from ..spine import signature_page as gear_reader
from ..spine import typeless as typeless_reader
from ..spine.stages import StageName
from ..vocab.filters import Passband
from . import lookalike, work
from . import review_page as page
from . import review_write as write
from .deps import get_db
from .models_page import page_of
from .models_review import BandOut, FilterOut, ReviewOut, SettledObjects
from .models_review_apply import ReviewApplied, ReviewApply
from .models_review_groups import GearSignature, MosaicCandidate, TypelessFolder

router = APIRouter(prefix="/api/v1", tags=["review"])


def unanswered(rows: Iterable[Mapping[str, Any]]) -> int:
    """An answered group stays on the page, so one can change one's mind, but it is no longer
    something to confirm."""
    return sum(1 for r in rows if r["answer"] is None)


# Only filters with an unknown band: counting the others' frames would grow with the archive. A
# copy is not another frame; `copy_of IS NULL` is spelled out: composed SQL is one less safety hold.
_FILTERS = """
SELECT fi.*, (SELECT COUNT(*) FROM frames f
              WHERE f.copy_of IS NULL AND f.filter_id = fi.id) AS frames
FROM filters fi WHERE fi.passband = ?
"""


@router.get("/review", response_model=ReviewOut)
def review(conn: sqlite3.Connection = Depends(get_db)) -> ReviewOut:
    """The open questions about what the scan found, and the objects."""
    bands: dict[int, list[BandOut]] = {}
    for r in conn.execute("SELECT filter_id, band, width_nm FROM filter_bands ORDER BY band"):
        bands.setdefault(r["filter_id"], []).append(BandOut(band=r["band"], width_nm=r["width_nm"]))
    # the most used first
    rows = conn.execute(_FILTERS, (Passband.UNKNOWN,)).fetchall()
    rows.sort(key=lambda r: (-r["frames"], r["name"]))
    filters = [
        FilterOut(
            id=r["id"],
            name=r["name"],
            brand=r["brand"],
            model=r["model"],
            catalog_id=r["catalog_id"],
            passband=r["passband"],
            is_none=bool(r["is_none"]),
            bands=bands.get(r["id"], []),
            frames=r["frames"],
        )
        for r in rows
    ]

    objects, settled = page.objects(conn)
    unclear = page.unclear_coordinates(conn)
    gear_rows = gear_reader.by_signature(conn)
    typeless_rows = typeless_reader.by_folder(conn)
    mosaic_rows = mosaic_reader.candidates(conn)
    mosaics = [MosaicCandidate(**asdict(m)) for m in mosaic_rows]
    pairs = lookalike.lookalikes(conn)
    # Seeing a question is not answering it: each one counts until answered, or the count would
    # drop to zero while the frames still wait.
    to_confirm = (
        sum(1 for o in objects if page.asks(o))
        + len(filters)
        + len(pairs)
        + sum(1 for p in unclear if p.site is None)
        # a card counts until every part it asks is answered
        + sum(1 for g in gear_rows if not g["complete"])
        # a mosaic's no closes it too, or a wrong proposal could only be silenced by accepting it
        + sum(1 for m in mosaic_rows if m.answer is None)
        + unanswered(typeless_rows)
    )
    return ReviewOut(
        lookalikes=pairs,
        filters=filters,
        filter_choices=page.filter_choices(conn),
        rig_choices=page.rig_choices(conn),
        objects=objects,
        settled_objects=len(settled),
        unclear=unclear,
        gear=[GearSignature(**g) for g in gear_rows],
        optics_choices=page.optics_choices(conn),
        typeless=[TypelessFolder(**g) for g in typeless_rows],
        mosaics=mosaics,
        empty=conn.execute("SELECT NOT EXISTS (SELECT 1 FROM frames)").fetchone()[0] == 1,
        to_confirm=to_confirm,
    )


@router.get("/review/objects/settled", response_model=SettledObjects)
def settled_objects(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> SettledObjects:
    """The objects the app knows, with nothing to choose, in pages, in the page's order."""
    _, settled = page.objects(conn)
    return SettledObjects(**page_of(settled, limit, offset))


@router.post("/review/apply", response_model=ReviewApplied)
def apply(
    body: ReviewApply, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> ReviewApplied:
    """The answers become rules, and the work restarts on the frames they concern. All of them are
    written together or none is.

    409 `worker_busy`; 404 `not_found` if what an answer points to no longer exists or is no
    longer asked (an old page); 422 `unknown_target` for a catalog slug that does not exist or a
    rig the page does not offer; 422 `merge_refused`; 409 `name_taken` or `none_filter_exists` if
    a filter answer collides with another filter."""
    state = request.app.state
    work.busy(state)
    now = now_iso()
    with write.writing(conn):
        changed, requeued = write.apply_answers(conn, body, now)
    # without frames to redo the worker is not taken for nothing
    started = bool(requeued) and work.after(state, _stages_touched(body))
    return ReviewApplied(changed=changed, requeued=len(requeued), run_started=started)


def _stages_touched(body: ReviewApply) -> set[StageName]:
    """An answer on objects alone changes nothing upstream, but a MIXED answer needs both stages,
    in this order, or the object answer would wait for someone to click Start."""
    wanted: set[StageName] = set()
    if body.lookalikes or body.filters:
        wanted.add(StageName.NORMALIZE)
    if body.gear:
        wanted.add(StageName.NORMALIZE)  # they change the filter or the rig of their frames
    if body.typeless:
        # the SKY of those frames is requeued: name and night follow from the stage graph
        wanted.add(StageName.SOLVE)
    if body.objects:
        wanted.add(StageName.IDENTIFY)
    elif body.unclear:
        # a place answer changes only where those frames sit: the last stage is enough
        wanted.add(StageName.GROUP)
    return wanted
