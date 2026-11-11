"""The year so far, for the Dashboard (board v79): nights, hours, a bar per month beside the year
before and the share of each filter, with its piece of the ring."""

import calendar
import datetime as dt
import sqlite3
from dataclasses import dataclass

from ..vocab.filters import Passband
from . import counts, filters_used
from .night_criteria import NO_FILTER

# Same frames as the Nights page: inside a night, copies left out. Two sites on one date make one
# night, so the year counts dates, not night rows.
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
    ring_from: float
    ring_to: float


@dataclass(frozen=True, slots=True)
class Year:
    year: int
    until: str
    nights: int
    integration_s: int
    per_night_s: int | None
    per_month: float
    months: list[Month]
    previous_same_period_s: int
    previous_known: bool
    vs_previous_s: int
    filters: list[FilterShare]


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


def _months(now: list[int], then: list[int], today: dt.date) -> list[Month]:
    """The bars on the fullest month of both years: the comparison reads at a glance."""
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


def _filters(conn: sqlite3.Connection, today: dt.date) -> list[FilterShare]:
    """Each filter's time and share, the most shot first, no filter last (as the night's
    measures). On exact seconds: rounded one by one, two of 300.6 s make 602 of 601."""
    rows = conn.execute(_PER_FILTER, (dt.date(today.year, 1, 1).isoformat(), today.isoformat()))
    named: list[tuple[str, str, float]] = []
    none_s = 0.0
    for r in rows:
        if r["name"] is None:
            none_s = r["integration_s"]
        elif r["integration_s"] > 0:
            named.append((r["name"], r["passband"], r["integration_s"]))
    if none_s > 0:
        named.append((NO_FILTER, Passband.UNKNOWN.value, none_s))
    total = sum(s for _, _, s in named)
    pcts = _shares([s for _, _, s in named], total)
    shares, done = [], 0.0
    last = len(named) - 1
    for i, ((name, band, seconds), pct) in enumerate(zip(named, pcts, strict=True)):
        start = done * 100 / total
        done += seconds
        end = 100.0 if i == last else done * 100 / total
        shares.append(FilterShare(name, band, round(seconds), pct, round(start, 3), round(end, 3)))
    return shares


def _shares(parts: list[float], total: float) -> list[int]:
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
    frame is a night all the same."""
    shot = _per_date(conn, dt.date(today.year, 1, 1), today)
    total = round(sum(shot.values()))
    before = _per_date(conn, dt.date(today.year - 1, 1, 1), dt.date(today.year - 1, 12, 31))
    period_before = round(
        sum(s for d, s in before.items() if d <= _same_day_before(today).isoformat())
    )
    # At least a whole month: one night on the first of January is one a month, not thirty-one.
    months = max(1.0, today.month - 1 + today.day / calendar.monthrange(today.year, today.month)[1])
    return Year(
        year=today.year,
        until=today.isoformat(),
        nights=len(shot),
        integration_s=total,
        per_night_s=round(total / len(shot)) if shot else None,
        per_month=round(len(shot) / months, 1),
        months=_months(_by_month(shot), _by_month(before), today),
        previous_same_period_s=period_before,
        previous_known=bool(before),
        vs_previous_s=total - period_before,
        filters=_filters(conn, today),
    )
