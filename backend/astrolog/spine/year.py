"""The year so far, for the Dashboard: nights, hours and one square per day (board v37)."""

import calendar
import datetime as dt
import sqlite3
from dataclasses import dataclass
from enum import StrEnum

# The board's legend: 0 h, under 2, 2-4, 4-6, over 6.
_EDGES_H = ((2, "under2"), (4, "2to4"), (6, "4to6"))

# Same frames as the Nights page: inside a night, copies left out. Two sites on one date make one
# square, so the calendar counts dates, not night rows.
_PER_DATE = """
SELECT n.night_date AS night_date, COALESCE(SUM(f.exposure_s), 0) AS integration_s
FROM frames f JOIN nights n ON n.id = f.night_id
WHERE f.copy_of IS NULL AND n.night_date BETWEEN ? AND ?
GROUP BY n.night_date
"""


class Level(StrEnum):
    FUTURE = "future"
    NONE = "none"
    UNDER2 = "under2"
    BETWEEN2_4 = "2to4"
    BETWEEN4_6 = "4to6"
    OVER6 = "over6"


@dataclass(frozen=True, slots=True)
class Day:
    date: str
    level: Level
    integration_s: int


@dataclass(frozen=True, slots=True)
class Year:
    year: int
    until: str
    nights: int
    integration_s: int
    per_night_s: int | None
    per_month: float
    lead_blank: int
    days: list[Day]


def _level(seconds: float) -> Level:
    if seconds <= 0:
        return Level.NONE
    hours = seconds / 3600
    for edge, name in _EDGES_H:
        if hours < edge:
            return Level(name)
    return Level.OVER6


def of(conn: sqlite3.Connection, today: dt.date) -> Year:
    """From January 1 to `today`, the night date of now at home. A night with frames but no timed
    frame is a night all the same, of level `none`."""
    first = dt.date(today.year, 1, 1)
    shot = {
        r["night_date"]: r["integration_s"]
        for r in conn.execute(_PER_DATE, (first.isoformat(), today.isoformat()))
    }
    total = round(sum(shot.values()))
    days = []
    for i in range(366 if calendar.isleap(today.year) else 365):
        day = first + dt.timedelta(days=i)
        key = day.isoformat()
        seconds = round(shot.get(key, 0))
        days.append(Day(key, Level.FUTURE if day > today else _level(seconds), seconds))
    # At least a whole month: one night on the first of January is one a month, not thirty-one.
    months = max(1.0, today.month - 1 + today.day / calendar.monthrange(today.year, today.month)[1])
    return Year(
        year=today.year,
        until=today.isoformat(),
        nights=len(shot),
        integration_s=total,
        per_night_s=round(total / len(shot)) if shot else None,
        per_month=round(len(shot) / months, 1),
        lead_blank=first.weekday(),
        days=days,
    )
