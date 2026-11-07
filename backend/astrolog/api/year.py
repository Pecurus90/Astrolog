"""The year so far, on the Dashboard. The totals are SQL sums, like the Nights page's."""

import sqlite3
from dataclasses import asdict

from fastapi import APIRouter, Depends

from ..site_of import home_tonight
from ..spine import year
from .deps import get_db
from .models_year import YearOut

router = APIRouter(prefix="/api/v1", tags=["year"])


@router.get("/year", response_model=YearOut)
def this_year(conn: sqlite3.Connection = Depends(get_db)) -> YearOut:
    """The current year up to tonight at home (`site_of.home_tonight`)."""
    return YearOut.model_validate(asdict(year.of(conn, home_tonight(conn))))
