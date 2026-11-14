"""The camera's bias for the sky brightness, one per offset (ADR 0021, ADR 0022): the sheet's
field the camera card shows, keyed by the camera as the files write it."""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ..clock import now_iso
from ..pipeline.sqm_measure import biases, declare_bias
from ..spine import inventory
from . import work
from .deps import get_db
from .models_gear import CameraBiasIn, CameraBiasOut, OffsetBias, OffsetBiasIn

router = APIRouter(prefix="/api/v1", tags=["gear"])

_SEEN = (
    "SELECT 1 FROM pipeline_cards WHERE camera = ? AND offset IS ? AND frame_type = 'light' LIMIT 1"
)


def declare_restored(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    """A backup's biases rewrite their shots' sky brightness, as declaring them does: the spine
    restores the row, it cannot reach the new pipeline (ADR 0030)."""
    now = now_iso()
    for b in data.get("camera_biases", []):
        declare_bias(conn, b["camera"], b["offset"], b["bias_adu"], now)


@router.get("/gear/camera-biases", response_model=list[CameraBiasOut])
def camera_biases(conn: sqlite3.Connection = Depends(get_db)) -> list[CameraBiasOut]:
    """Every camera and offset the light frames write, with its declared bias or null, and every
    declared bias even without frames (back from a backup). Not paged: one row per camera and
    offset, they do not grow with the archive."""
    return [CameraBiasOut(**dict(r)) for r in biases(conn)]


@router.put("/gear/camera-biases", response_model=CameraBiasOut)
def declare_camera_bias(
    body: CameraBiasIn, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> CameraBiasOut:
    """Declares the bias of a camera at an offset; its shots' sky brightness is written again.

    404 `camera_not_found`: no light frame writes that camera with that offset. 409 `worker_busy`
    while the worker runs."""
    work.busy(request.app.state)
    if conn.execute(_SEEN, (body.camera, body.offset)).fetchone() is None:
        raise HTTPException(status_code=404, detail={"code": "camera_not_found"})
    declare_bias(conn, body.camera, body.offset, body.bias_adu, now_iso())
    row = next(r for r in biases(conn) if (r["camera"], r["offset"]) == (body.camera, body.offset))
    return CameraBiasOut(**dict(row))


@router.put("/gear/instruments/{camera_id}/biases", response_model=OffsetBias)
def declare_offset_bias(
    camera_id: int, body: OffsetBiasIn, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> OffsetBias:
    """The bias of a camera of the page at one offset: it goes to every way its files write that
    camera, and their shots' sky brightness is written again.

    404 `offset_not_found`: none of its light frames writes that offset. 409 `worker_busy` while
    the worker runs."""
    work.busy(request.app.state)
    spellings = [c for c, o in inventory.camera_spellings(conn, camera_id) if o == body.offset]
    if not spellings:
        raise HTTPException(status_code=404, detail={"code": "offset_not_found"})
    for camera in spellings:
        declare_bias(conn, camera, body.offset, body.bias_adu, now_iso())
    row = next(b for b in inventory.camera_biases(conn, camera_id) if b["offset"] == body.offset)
    return OffsetBias(**row)
