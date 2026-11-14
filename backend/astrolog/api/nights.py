"""The rows and their order come from the spine (`spine/nights.py`, `spine/night_criteria.py`):
two screens ordering on their own would agree by chance."""

import datetime as dt
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db.config import moon_rule
from ..db.config import read as read_settings
from ..site_of import home_tonight
from ..spine import night_calendar, nights
from ..spine import night_detail as night_detail_read
from ..spine.night_criteria import Chosen, Key, select
from ..weather import history
from .deps import get_db
from .models_night_detail import NightDetail
from .models_nights import NightList, NightMonth

router = APIRouter(prefix="/api/v1", tags=["nights"])

# [T] a criterion's value: a year, an id, a filter's name, a constellation, a verdict
_Values = Annotated[list[str] | None, Query(max_length=120)]


@router.get("/nights", response_model=NightList)
def night_list(  # noqa: PLR0913 - one parameter per criterion of the sheet
    limit: int = Query(20, ge=1, le=500),  # [P docs/domini/notti.md] 20 at a time
    offset: int = Query(0, ge=0),
    night: int | None = Query(None, ge=1),
    q: str | None = Query(None, max_length=200),  # [T]
    year: _Values = None,
    site: _Values = None,
    setup: _Values = None,
    filter_name: Annotated[list[str] | None, Query(alias="filter", max_length=120)] = None,
    constellation: _Values = None,
    sky: _Values = None,
    conn: sqlite3.Connection = Depends(get_db),
) -> NightList:
    """The archive's nights that pass the criteria, newest first, `limit` at a time. Beside them
    the criteria with their counts, the months of the whole list, the archive's totals and the
    two things that explain a short list: frames waiting for an answer (`waiting`) and frames the
    spine has still to read (`still_reading`).

    Within a criterion one value is enough, across criteria all hold; each value says how many
    nights it would give with the other choices applied.

    `night` asks a single night by id, wherever it falls and whatever the criteria: the search
    opens it there. An id that is not there gives no rows, not an error -- an old address."""
    by = {
        Key.YEAR: year,
        Key.SITE: site,
        Key.SETUP: setup,
        Key.FILTER: filter_name,
        Key.CONSTELLATION: constellation,
        Key.SKY: sky,
    }
    chosen = select(conn, Chosen(q, {k: v for k, v in by.items() if v}), history.KIND)
    listed = (
        chosen.ids if night is None else [i for i in chosen.ids if i == night] or _one(conn, night)
    )
    left = nights.still_reading(conn)
    waiting = nights.waiting(conn)
    return NightList.model_validate(
        {
            "items": nights.page(
                conn,
                ids=listed[offset : offset + limit],
                weather=nights.Observed(history.KIND, history.arrives_on),
                rule=moon_rule(read_settings(conn)),
            ),
            "total": len(listed),
            "limit": limit,
            "offset": offset,
            "criteria": chosen.criteria,
            "months": nights.months(conn, listed),
            "totals": nights.archive_totals(conn) if offset == 0 else None,
            "waiting": waiting,
            "waiting_frames": sum(
                w["frames"] for w in waiting if w["answer_at"] != nights.AnswerAt.REVIEW
            ),
            "empty": nights.empty(conn, waiting, left),
            "still_reading": left,
            "reading_done_pct": nights.reading_done_pct(conn, left),
        }
    )


def _one(conn: sqlite3.Connection, night: int) -> list[int]:
    """The asked night even outside the criteria."""
    row = conn.execute("SELECT id FROM nights WHERE id = ?", (night,)).fetchone()
    return [row[0]] if row else []


@router.get("/nights/calendar", response_model=NightMonth)
def night_month(
    # [T] years 1000-9899: the dates around stay inside Python's calendar
    month: str = Query(pattern=r"^(1\d|[2-8]\d|9[0-8])\d\d-(0[1-9]|1[0-2])$"),
    conn: sqlite3.Connection = Depends(get_db),
) -> NightMonth:
    """A month of nights for the calendar: one sign per night with its verdict, the month's nights,
    good ones and hours; and the months it moves between, from the first with nights to tonight's
    at home. A month without nights is an empty month."""
    first_day = dt.date.fromisoformat(f"{month}-01")
    return NightMonth.model_validate(
        night_calendar.month(conn, first_day, history.KIND, home_tonight(conn))
    )


# After `/nights/calendar`: the first route that matches wins.
@router.get("/nights/{night_id}", response_model=NightDetail)
def night_detail(night_id: int, conn: sqlite3.Connection = Depends(get_db)) -> NightDetail:
    """One night for its window: the Nights page's row, when it was shot from the first start to
    the last end in the site's zone, the setups that took it with that night's frames, and what
    the catalog says of each object (type, constellation, distance, true size).

    404 `night_not_found`: no such night."""
    found = night_detail_read.detail(conn, night_id)
    if found is None:
        raise HTTPException(status_code=404, detail="night_not_found")
    row = nights.page(
        conn,
        ids=[night_id],
        weather=nights.Observed(history.KIND, history.arrives_on),
        rule=moon_rule(read_settings(conn)),
    )
    return NightDetail.model_validate({"night": row[0], **found})
