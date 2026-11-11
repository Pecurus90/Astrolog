"""The year so far, for the Dashboard: nights, hours, one square per day (board v37), a bar per
month beside the year before and the share of each filter (board v79)."""

import calendar
import datetime as dt
import sqlite3
from dataclasses import dataclass
from enum import StrEnum

from . import counts, filters_used

# The board's legend: 0 h, under 2, 2-4, 4-6, over 6. [T] Design board
_EDGES_H = ((2, "under2"), (4, "2to4"), (6, "4to6"))

# Same frames as the Nights page: inside a night, copies left out. Two sites on one date make one
# square, so the calendar counts dates, not night rows.
_PER_DATE = f"""
SELECT n.night_date AS night_date, COALESCE(SUM(f.exposure_s), 0) AS integration_s
FROM frames f JOIN nights n ON {counts.of(counts.Subject.NIGHT)}
WHERE f.copy_of IS NULL AND n.night_date BETWEEN ? AND ?
GROUP BY n.night_date
"""  # noqa: S608 - our columns

# The year's time per filter, the frames naming none in their own row (`filter_id` NULL).
_PER_FILTER = f"""
SELECT x.name AS name, x.passband AS passband, COALESCE(SUM(f.exposure_s), 0) AS integration_s
FROM frames f JOIN nights n ON {counts.of(counts.Subject.NIGHT)}
LEFT JOIN filters x ON x.id = f.filter_id
WHERE f.copy_of IS NULL AND n.night_date BETWEEN ? AND ?
GROUP BY f.filter_id
ORDER BY integration_s DESC, {filters_used.order_by("x")}
"""  # noqa: S608 - our columns


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
class Month:
    month: int
    integration_s: int
    previous_s: int
    bar: float
    previous_bar: float
    current: bool
    future: bool


@dataclass(frozen=True, slots=True)
class FilterShare:
    name: str
    passband: str
    integration_s: int
    share_pct: int


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
    months: list[Month]
    previous_same_period_s: int
    filters: list[FilterShare]
    no_filter_s: int
    no_filter_pct: int


def _level(seconds: float) -> Level:
    if seconds <= 0:
        return Level.NONE
    hours = seconds / 3600
    for edge, name in _EDGES_H:
        if hours < edge:
            return Level(name)
    return Level.OVER6


def _per_date(conn: sqlite3.Connection, first: dt.date, last: dt.date) -> dict[str, float]:
    rows = conn.execute(_PER_DATE, (first.isoformat(), last.isoformat()))
    return {r["night_date"]: r["integration_s"] for r in rows}


def _by_month(shot: dict[str, float]) -> list[int]:
    hours = [0.0] * 12
    for date, seconds in shot.items():
        hours[int(date[5:7]) - 1] += seconds
    return [round(s) for s in hours]


def _same_day_before(today: dt.date) -> dt.date:
    """The same day a year before; February 29 falls on the 28th."""
    day = min(today.day, calendar.monthrange(today.year - 1, today.month)[1])
    return dt.date(today.year - 1, today.month, day)


def _months(conn: sqlite3.Connection, today: dt.date, shot: dict[str, float]) -> list[Month]:
    """The bars on the fullest month of both years: the comparison reads at a glance."""
    before = _per_date(conn, dt.date(today.year - 1, 1, 1), dt.date(today.year - 1, 12, 31))
    now, then = _by_month(shot), _by_month(before)
    top = max([*now, *then, 1])
    return [
        Month(
            month=i + 1,
            integration_s=now[i],
            previous_s=then[i],
            bar=round(now[i] / top, 3),
            previous_bar=round(then[i] / top, 3),
            current=i + 1 == today.month,
            future=i + 1 > today.month,
        )
        for i in range(12)
    ]


def _filters(
    conn: sqlite3.Connection, today: dt.date, total: int
) -> tuple[list[FilterShare], int, int]:
    """Each filter's time and share of the year, the most shot first, then the time and share of
    the frames naming no filter."""
    rows = conn.execute(_PER_FILTER, (dt.date(today.year, 1, 1).isoformat(), today.isoformat()))
    named, none_s = [], 0
    for r in rows:
        seconds = round(r["integration_s"])
        if r["name"] is None:
            none_s = seconds
        elif seconds > 0:
            named.append((r["name"], r["passband"], seconds))
    *pcts, none_pct = _shares([s for _, _, s in named] + [none_s], total)
    shares = [FilterShare(n, b, s, p) for (n, b, s), p in zip(named, pcts, strict=True)]
    return shares, none_s, none_pct


def _shares(parts: list[int], total: int) -> list[int]:
    """Whole percents that add up to 100: the leftover points go to the largest remainders
    (Hamilton's method), so the list and the ring never say 99 or 101."""
    if not total:
        return [0] * len(parts)
    exact = [p * 100 / total for p in parts]
    whole = [int(e) for e in exact]
    by_remainder = sorted(range(len(parts)), key=lambda i: exact[i] - whole[i], reverse=True)
    for i in by_remainder[: 100 - sum(whole)]:
        whole[i] += 1
    return whole


def of(conn: sqlite3.Connection, today: dt.date) -> Year:
    """From January 1 to `today`, the night date of now at home. A night with frames but no timed
    frame is a night all the same, of level `none`."""
    first = dt.date(today.year, 1, 1)
    shot = _per_date(conn, first, today)
    total = round(sum(shot.values()))
    period_before = _per_date(conn, dt.date(today.year - 1, 1, 1), _same_day_before(today))
    filters, no_filter_s, no_filter_pct = _filters(conn, today, total)
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
        months=_months(conn, today, shot),
        previous_same_period_s=round(sum(period_before.values())),
        filters=filters,
        no_filter_s=no_filter_s,
        no_filter_pct=no_filter_pct,
    )
