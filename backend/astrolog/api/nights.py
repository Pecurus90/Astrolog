"""The rows and their order come from SQL (`spine/nights.py`): two screens ordering on their own
would agree by chance."""

import sqlite3

from fastapi import APIRouter, Depends, Query

from ..spine import nights
from ..weather import history
from .deps import get_db
from .models_nights import NightList

router = APIRouter(prefix="/api/v1", tags=["nights"])


@router.get("/nights", response_model=NightList)
def night_list(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> NightList:
    """The archive's nights, newest first. Beside them travel the two things that explain a short
    list: how many frames wait for an answer (`waiting`) and how many the spine has still to read
    (`still_reading`).

    The factory cap is the same as the Archive's (100): there are many more rows -- one per night,
    not one per object -- but they are looked at the same way, scrolling back in time, and asking
    for twenty at a time would be five rounds to see a year."""
    # The spine already sends the page's shape: copying it field by field would be two name lists
    # to keep in step, and validating still rejects a missing or mistyped field here.
    return NightList.model_validate(
        {
            "items": nights.page(conn, limit=limit, offset=offset, observed=history.KIND),
            "total": nights.how_many(conn),
            "limit": limit,
            "offset": offset,
            "totals": nights.archive_totals(conn),
            "waiting": nights.waiting(conn),
            "still_reading": nights.still_reading(conn),
        }
    )
