"""A frame's measures as the pipeline wrote them (`docs/domini/misure.md`)."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..measure_read import frame_measures
from .deps import get_db
from .models_measures import FrameMeasuresOut, MeasureOut

router = APIRouter(prefix="/api/v1", tags=["measures"])


@router.get("/pipeline/frames/{frame_id}/measures", response_model=FrameMeasuresOut)
def measures(frame_id: int, conn: sqlite3.Connection = Depends(get_db)) -> FrameMeasuresOut:
    """Every measure of one frame (`measure_list.py`), in its order, each with its
    value or the code of why it has none; the stages' outcomes and the written words beside.

    Not paged: one frame's list is fixed by the catalogue, it does not grow with the archive
    (ADR 0011). Reads only what the stages wrote. 404 `frame_not_found`: no such frame."""
    found = frame_measures(conn, frame_id)
    if found is None:
        raise HTTPException(status_code=404, detail="frame_not_found")
    words = {k: v for k, v in vars(found).items() if k != "values"}
    return FrameMeasuresOut.model_validate(words | {"measures": [
        MeasureOut(key=v.entry.key, unit=v.entry.unit, group=v.entry.group, value=v.value,
                   silent=v.silent)
        for v in found.values
    ]})  # fmt: skip
