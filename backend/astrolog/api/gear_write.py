"""The same functions as *Da confermare*, never a second way: one answer valid on one page and not
the other would be two truths about one piece. Nothing is written while the worker runs."""

import sqlite3
from collections.abc import Collection

from fastapi import APIRouter, Depends, HTTPException, Request

from ..clock import now_iso
from ..spine import gear, gear_create, gear_usage, rigs
from ..spine.stages import StageName
from . import instrument_answer, work
from . import review_write as write
from .deps import get_db
from .models_gear import (
    ChosenKind,
    FilterNew,
    GearWritten,
    InstrumentCorrection,
    InstrumentNew,
    RigNaming,
    RigNew,
    RigPartChoice,
)
from .models_review_apply import FilterCorrection

router = APIRouter(prefix="/api/v1", tags=["gear"])


# [C RFC 9110 15.3.2: 201 Created]
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
    with write.writing(conn):
        new_id = gear_create.instrument(conn, body.kind, body.name, now, detected=False)
        card = instrument_answer.of_the_kind(body.kind, body.model_dump(exclude_none=True))
        # without kind and name: resending them would be a rename onto itself, which would set
        # `detected` by hand and hide that a piece you write is born declared
        gear.declare_instrument(
            conn, new_id, {c: v for c, v in card.items() if c not in ("kind", "name")}, now
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
    with write.writing(conn):
        requeued = instrument_answer.answer(conn, instrument_id, body, now)
    return _written(request, instrument_id, requeued)


@router.patch("/gear/rigs/{rig_id}", response_model=GearWritten)
def name_rig(
    rig_id: int, body: RigNaming, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A rig's name. It is kept among the declarations, not in the row: it comes back when the
    spine rebuilds the same rig.

    409 `worker_busy`; 404 `not_found`; 409 `name_taken` if another rig has it, in any case."""
    work.busy(request.app.state)
    try:
        with write.writing(conn):
            rigs.declare_rig(conn, rig_id, body.name, now_iso())
    except rigs.RigNameTakenError as err:
        raise HTTPException(status_code=409, detail={"code": "name_taken"}) from err
    return GearWritten(id=rig_id, requeued=0, run_started=False)


# [C RFC 9110 15.3.2: 201 Created]
@router.post("/gear/filters", response_model=GearWritten, status_code=201)
def add_filter(
    body: FilterNew, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A filter you have not used yet, or that your files call in a way the app does not
    understand. A name you already own is a refusal, not a second filter.

    409 `worker_busy`; 409 `name_taken`, or `spelling_taken` if the name is already a spelling of
    another filter of yours."""
    work.busy(request.app.state)
    with write.writing(conn):
        bands = [b.model_dump() for b in body.bands]
        new_id = gear_create.filter_declared(
            conn, body.name, bands, now_iso(), brand=body.brand, model=body.model
        )
        gear_usage.add_new(conn, gear_usage.UsageSubject.FILTER, new_id)
    return GearWritten(id=new_id, requeued=0, run_started=False)


# [C RFC 9110 15.3.2: 201 Created]
@router.post("/gear/rigs", response_model=GearWritten, status_code=201)
def add_rig(
    body: RigNew, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> GearWritten:
    """A rig that has not imaged yet: its fingerprint, hence what the scan will find. One you
    already have, focal length within 5 %, is a refusal.

    409 `worker_busy`; 409 `rig_exists`; 422 `wrong_kind` if the optics or the camera is not a
    piece of that kind."""
    work.busy(request.app.state)
    with write.writing(conn):
        new_id = rigs.create_declared(
            conn, body.optics_id, body.camera_id, body.focal_mm, now_iso()
        )
        gear_usage.add_new(conn, gear_usage.UsageSubject.RIG, new_id)
    return GearWritten(id=new_id, requeued=0, run_started=False)


@router.put("/gear/rigs/{rig_id}/parts/{kind}", response_model=GearWritten)
def choose_rig_part(
    rig_id: int,
    kind: ChosenKind,
    body: RigPartChoice,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> GearWritten:
    """A part of a rig, chosen from its card. It is kept among the declarations like the name, and
    the rig's frames go back to `normalize`, which writes it on each: the mount on all of them,
    any other kind where the file names none.

    409 `worker_busy`; 404 `not_found`; 422 `not_of_kind`."""
    work.busy(request.app.state)
    with write.writing(conn):
        requeued = rigs.declare_part(conn, rig_id, kind, body.piece_id, now_iso())
        # the page shows the choice at once, before `normalize` has put it on the frames
        gear_usage.write_parts(conn)
    return _written(request, rig_id, requeued)


@router.patch("/gear/filters/{filter_id}", response_model=GearWritten)
def edit_filter(
    filter_id: int,
    body: FilterCorrection,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> GearWritten:
    """The same functions as *Da confermare*.

    409 `worker_busy`; 404 `not_found`; 409 `name_taken` if the new name is already another
    filter's; 422 `merge_refused`; 422 `model_contradicts_bands` for a model with bands not
    its own."""
    work.busy(request.app.state)
    now = now_iso()
    with write.writing(conn):
        requeued, _ = write.answer_filter(conn, filter_id, body, now)
    return _written(request, filter_id, requeued)


def _written(request: Request, row_id: int, requeued: Collection[int]) -> GearWritten:
    """The work restarts only if some frame has to be redone."""
    started = bool(requeued) and work.after(request.app.state, {StageName.NORMALIZE})
    return GearWritten(id=row_id, requeued=len(requeued), run_started=started)
