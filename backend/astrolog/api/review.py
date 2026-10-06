"""Apply writes only the answers: seeing a question does not close it (ADR 0014, S4)."""

import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from ..clock import now_iso
from ..spine import mosaic_proposals as mosaic_reader
from ..spine import signature_page as gear_reader
from ..spine import typeless as typeless_reader
from ..spine.run import STAGE_GROUP, STAGE_IDENTIFY, STAGE_NORMALIZE, STAGE_SOLVE
from ..vocab.filters import UNKNOWN
from . import lookalike, work
from . import review_page as page
from . import review_write as write
from .deps import get_db
from .models_page import page_of
from .models_review import BandOut, FilterOut, ReviewOut, SettledObjects
from .models_review_apply import ReviewApplied, ReviewApply
from .models_review_groups import GearSignature, MosaicCandidate, TypelessFolder

router = APIRouter(prefix="/api/v1", tags=["da confermare"])


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
    # a filter the vocabulary recognises is not a question; the most used first
    rows = conn.execute(_FILTERS, (UNKNOWN,)).fetchall()
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

    objects, certi = page.objects(conn)
    incerte = page.unclear_coordinates(conn)
    righe_attrezzatura = gear_reader.by_signature(conn)
    righe_senza_tipo = typeless_reader.by_folder(conn)
    righe_mosaici = mosaic_reader.candidates(conn)
    mosaici = [MosaicCandidate(**m) for m in righe_mosaici]
    coppie = lookalike.lookalikes(conn)
    # Seeing a question is not answering it: each one counts until answered, or the count would
    # drop to zero while the frames still wait.
    to_confirm = (
        sum(1 for o in objects if page.asks(o))
        + len(filters)
        + len(coppie)
        + sum(1 for p in incerte if p.site is None)
        # a card counts until every part it asks is answered
        + sum(1 for g in righe_attrezzatura if not g["complete"])
        # a mosaic's no closes it too, or a wrong proposal could only be silenced by accepting it
        + unanswered(righe_mosaici)
        + unanswered(righe_senza_tipo)
    )
    return ReviewOut(
        lookalikes=coppie,
        filters=filters,
        filter_choices=page.filter_choices(conn),
        rig_choices=page.rig_choices(conn),
        objects=objects,
        settled_objects=len(certi),
        unclear=incerte,
        gear=[GearSignature(**g) for g in righe_attrezzatura],
        optics_choices=page.optics_choices(conn),
        typeless=[TypelessFolder(**g) for g in righe_senza_tipo],
        mosaics=mosaici,
        to_confirm=to_confirm,
    )


@router.get("/review/objects/settled", response_model=SettledObjects)
def settled_objects(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> SettledObjects:
    """The objects the app knows, with nothing to choose, in pages, in the page's order."""
    _, certi = page.objects(conn)
    return SettledObjects(**page_of(certi, limit, offset))


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
    with write.scrivendo(conn):
        changed, requeued = write.apply_answers(conn, body, now)
    # without frames to redo the worker is not taken for nothing
    started = bool(requeued) and work.after(state, _stadi_toccati(body))
    return ReviewApplied(changed=changed, requeued=len(requeued), run_started=started)


def _stadi_toccati(body: ReviewApply) -> set[str]:
    """An answer on objects alone changes nothing upstream, but a MIXED answer needs both stages,
    in this order, or the object answer would wait for someone to click Start."""
    voluti: set[str] = set()
    if body.lookalikes or body.filters:
        voluti.add(STAGE_NORMALIZE)
    if body.gear:
        voluti.add(STAGE_NORMALIZE)  # they change the filter or the rig of their frames
    if body.typeless:
        # the SKY of those frames is requeued: name and night follow from the stage graph
        voluti.add(STAGE_SOLVE)
    if body.objects:
        voluti.add(STAGE_IDENTIFY)
    elif body.unclear:
        # a place answer changes only where those frames sit: the last stage is enough
        voluti.add(STAGE_GROUP)
    return voluti
