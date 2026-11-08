"""A night's measures for its window (`docs/domini/misure.md`, ADR 0045)."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..spine.night_measures_read import night_measures
from .deps import get_db
from .models_night_measures import NightMeasures

router = APIRouter(prefix="/api/v1", tags=["nights"])


@router.get("/nights/{night_id}/measures", response_model=NightMeasures)
def measures_of_night(night_id: int, conn: sqlite3.Connection = Depends(get_db)) -> NightMeasures:
    """The night's frames measured, as the Nights page counts them: per set (the night, each
    object, each filter, each object in a filter) every measure's median and quartiles over the
    frames that have it, and the frames one by one in shooting order with their values.

    Written after each scan (`night_measures.py`): before, `sets` is empty and every frame is
    still to be measured. Not paged: the frames of one night do not grow with the archive
    (ADR 0011). 404 `night_not_found`: no such night."""
    found = night_measures(conn, night_id)
    if found is None:
        raise HTTPException(status_code=404, detail="night_not_found")
    return NightMeasures.model_validate(found)
