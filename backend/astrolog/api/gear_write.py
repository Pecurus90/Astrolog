"""The same functions as *Da confermare*, never a second way: one answer valid on one page and not
the other would be two truths about one piece. Nothing is written while the worker runs."""

import sqlite3
from collections.abc import Collection

from fastapi import APIRouter, Depends, Request

from ..clock import now_iso
from ..spine import gear, gear_create, gear_usage
from ..spine import rigs as corredi
from ..spine.run import STAGE_NORMALIZE
from . import instrument_answer as strumento
from . import review_write as write
from . import work
from .deps import get_db
from .models_gear import (
    FilterNew,
    GearWritten,
    InstrumentCorrection,
    InstrumentNew,
    RigMount,
    RigNaming,
    RigNew,
)
from .models_review_apply import FilterCorrection

router = APIRouter(prefix="/api/v1", tags=["attrezzatura"])


@router.post("/gear/instruments", response_model=GearWritten, status_code=201)
def add_instrument(
    body: InstrumentNew, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A piece your files do not name: a guide scope, a reducer, a mount.

    It is born **declared**. A name you already own in that kind does not make a second piece: it
    is a refusal, and what you write by hand is exactly what the scan will recognise.

    409 `worker_busy`; 409 `name_taken`; 422 `field_not_of_kind` with the `fields` that kind's card
    does not ask for."""
    work.busy(request.app.state)
    now = now_iso()
    with write.scrivendo(conn):
        new_id = gear_create.instrument(conn, body.kind, body.name, now, detected=False)
        scheda = strumento.of_the_kind(body.kind, body.model_dump(exclude_none=True))
        # without kind and name: resending them would be a rename onto itself, which would set
        # `detected` by hand and hide that a piece you write is born declared
        gear.declare_instrument(
            conn, new_id, {c: v for c, v in scheda.items() if c not in ("kind", "name")}, now
        )
        # the page shows the usage at once (zero, or unknown for a kind no frame names)
        gear_usage.add_piece(conn, new_id, body.kind)
    # a piece just born has no frames: a run would change no row
    return GearWritten(id=new_id, requeued=0, run_started=False)


@router.patch("/gear/instruments/{instrument_id}", response_model=GearWritten)
def edit_instrument(
    instrument_id: int,
    body: InstrumentCorrection,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> GearWritten:
    """A piece's card, corrected from the page where it is read.

    Renaming learns the old spelling -- otherwise the next scan recreates the piece as it was --
    and changing a camera's colour requeues the frames that do not name their filter: it is the
    same answer as *Da confermare*, written by the same hand.

    409 `worker_busy`; 404 `not_found`; 409 `name_taken` if the new name is already another piece
    of that kind; 422 `field_not_of_kind` with the `fields` that kind's card does not ask for; 422
    `merge_refused`."""
    work.busy(request.app.state)
    now = now_iso()
    with write.scrivendo(conn):
        requeued = strumento.answer(conn, instrument_id, body, now)
    return _scritto(request, instrument_id, requeued)


@router.patch("/gear/rigs/{rig_id}", response_model=GearWritten)
def name_rig(
    rig_id: int, body: RigNaming, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A rig's name. It is kept among the declarations, not in the row: it comes back when the
    spine rebuilds the same rig.

    409 `worker_busy`; 404 `not_found`."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        corredi.declare_rig(conn, rig_id, body.name, now_iso())
    return GearWritten(id=rig_id, requeued=0, run_started=False)


@router.post("/gear/filters", response_model=GearWritten, status_code=201)
def add_filter(
    body: FilterNew, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A filter you have not used yet, or that your files call in a way the app does not
    understand. A name you already own is a refusal, not a second filter.

    409 `worker_busy`; 409 `name_taken`, or `spelling_taken` if the name is already a spelling of
    another filter of yours."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        bande = [b.model_dump() for b in body.bands]
        nuovo = gear_create.filter_declared(
            conn, body.name, bande, now_iso(), brand=body.brand, model=body.model
        )
        gear_usage.add_new(conn, "filter", nuovo)
    return GearWritten(id=nuovo, requeued=0, run_started=False)


@router.post("/gear/rigs", response_model=GearWritten, status_code=201)
def add_rig(
    body: RigNew, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A rig that has not imaged yet: its fingerprint, hence what the scan will find. One you
    already have, focal length within 5 %, is a refusal.

    409 `worker_busy`; 409 `rig_exists`; 422 `wrong_kind` if the optics or the camera is not a
    piece of that kind."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        nuovo = corredi.create_declared(
            conn, body.optics_id, body.camera_id, body.focal_mm, now_iso()
        )
        gear_usage.add_new(conn, "rig", nuovo)
    return GearWritten(id=nuovo, requeued=0, run_started=False)


@router.put("/gear/rigs/{rig_id}/mount", response_model=GearWritten)
def mount_rig(
    rig_id: int, body: RigMount, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A rig's mount, from its card. It is kept among the declarations like the name, and the
    rig's frames go back to `normalize`, which writes it on each.

    409 `worker_busy`; 404 `not_found`; 422 `not_a_mount`."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        requeued = corredi.declare_mount(conn, rig_id, body.mount_id, now_iso())
    return _scritto(request, rig_id, requeued)


@router.patch("/gear/filters/{filter_id}", response_model=GearWritten)
def edit_filter(
    filter_id: int,
    body: FilterCorrection,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> GearWritten:
    """The same functions as *Da confermare*.

    409 `worker_busy`; 404 `not_found`; 409 `name_taken` if the new name is already another
    filter's; 422 `merge_refused`."""
    work.busy(request.app.state)
    now = now_iso()
    with write.scrivendo(conn):
        requeued, _ = write.answer_filter(conn, filter_id, body, now)
    return _scritto(request, filter_id, requeued)


def _scritto(request: Request, row_id: int, requeued: Collection[int]) -> GearWritten:
    """The work restarts only if some frame has to be redone."""
    started = bool(requeued) and work.after(request.app.state, {STAGE_NORMALIZE})
    return GearWritten(id=row_id, requeued=len(requeued), run_started=started)
