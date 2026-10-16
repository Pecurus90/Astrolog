"""The year so far, on the Dashboard. The totals are SQL sums, like the Nights page's."""

import datetime as dt
import sqlite3
from dataclasses import asdict

from fastapi import APIRouter, Depends

from ..clock import night_date, now_iso
from ..spine import year
from ..spine.group_store import home_site
from .deps import get_db
from .models_year import YearOut

router = APIRouter(prefix="/api/v1", tags=["year"])


@router.get("/year", response_model=YearOut)
def this_year(conn: sqlite3.Connection = Depends(get_db)) -> YearOut:
    """The current year up to tonight: the night date at home, noon to noon, so whoever looks at
    two in the morning still counts last night. Without a home site, or with a zone that does not
    resolve, today in UTC: the archive does not depend on the site."""
    home = home_site(conn)
    tonight = night_date(now_iso(), home["timezone"]) if home else None
    today = dt.date.fromisoformat(tonight) if tonight else dt.datetime.now(dt.UTC).date()
    return YearOut.model_validate(asdict(year.of(conn, today)))
