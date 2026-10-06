"""The site's usual upper wind: a year of nights, each the mean 700 hPa wind over the hours its
verdict judges, written as percentiles for `position`. Asked once a year per site."""

import json
import sqlite3
import zoneinfo
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from .. import net
from ..clock import iso_z
from . import fetches, nights, openmeteo, verdict
from .fetches import Source
from .forecast import Outcome, Status

# The reanalysis archive does not answer at 700 hPa; the historical forecast archive does.
URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
VARIABLE = "wind_speed_700hPa"
YEAR_DAYS = 365
# A third of a year, a product choice, not a convention: fewer nights would be one season's usual,
# and better no comparison than a wrong one.
MIN_NIGHTS = 120
# A year too short is still short at the next `forecast.RETRY_S` retry: wait a day instead.
BAD_ANSWER_WAIT = timedelta(days=1)

# The real call, named in this module so tests replace it here.
_fetch = net.fetch


def _moved(conn: sqlite3.Connection, site: Mapping[str, Any]) -> bool:
    """The usual belongs to a place: a site that moved asks again now, not in a year."""
    row = conn.execute(
        "SELECT latitude, longitude FROM weather_climate WHERE site_id = ?", (site["id"],)
    ).fetchone()
    return row is not None and (row[0], row[1]) != (site["latitude"], site["longitude"])


def _due(conn: sqlite3.Connection, site: Mapping[str, Any], now: datetime) -> bool:
    attempt = fetches.last(conn, site["id"], Source.CLIMATE)
    if attempt is None:
        return True
    if attempt["status"] == Outcome.BAD_ANSWER:
        return fetches.age(attempt, now) >= BAD_ANSWER_WAIT
    if attempt["status"] != Outcome.OK:
        return not fetches.failed_recently(attempt, now)
    return _moved(conn, site) or fetches.age(attempt, now) >= timedelta(days=YEAR_DAYS)


def _percentiles(values: Sequence[float]) -> list[float]:
    """The 101 percentiles, interpolated between the two neighbours."""
    xs = sorted(values)
    out = []
    for p in range(101):
        pos = (len(xs) - 1) * p / 100
        low = int(pos)
        high = min(low + 1, len(xs) - 1)
        out.append(round(xs[low] + (xs[high] - xs[low]) * (pos - low), 2))
    return out


def _night_means(
    site: Mapping[str, Any], times: Sequence[datetime], wind: Sequence[float | None]
) -> list[float]:
    """Mean wind of each whole night, over its verdict window: the day says nothing of the nights
    one shoots."""
    covered = nights.covered(site["timezone"], times, times[0].date().isoformat(), whole=True)
    sky = nights.sky(site["latitude"], site["longitude"], covered)
    tz = zoneinfo.ZoneInfo(site["timezone"])
    means = []
    for _, pairs in covered:
        judged, _ = verdict.window(nights.hours({"v": wind}, pairs, tz, sky=sky))
        values = [h.values["v"] for h in judged if h.values["v"] is not None]
        if values:
            means.append(sum(values) / len(values))
    return means


def step(
    conn: sqlite3.Connection,
    site: Mapping[str, Any] | None,
    *,
    fetch: net.Fetch | None = None,
    now: datetime | None = None,
) -> Status | None:
    """One call if due, and its outcome; `None` when not due."""
    if site is None or not site["timezone"]:
        return None
    moment = now or datetime.now(UTC)
    if not _due(conn, site, moment):
        return None
    end = moment.date() - timedelta(days=1)
    query = openmeteo.url(
        URL,
        site["latitude"],
        site["longitude"],
        (VARIABLE,),
        start_date=(end - timedelta(days=YEAR_DAYS)).isoformat(),
        end_date=end.isoformat(),
    )
    answer, failure = net.ask_why(fetch or _fetch, query)
    outcome = failure or _write(conn, site, answer, moment)
    fetches.record(conn, site["id"], Source.CLIMATE, outcome, moment)
    return outcome


def _write(
    conn: sqlite3.Connection, site: Mapping[str, Any], answer: Any, now: datetime
) -> Outcome:
    try:
        times, series = openmeteo.parse_single(answer, {VARIABLE: "wind_700hpa_kmh"})
    except openmeteo.BadAnswerError:
        return Outcome.BAD_ANSWER
    means = _night_means(site, times, series["wind_700hpa_kmh"]) if times else []
    if len(means) < MIN_NIGHTS:
        return Outcome.BAD_ANSWER
    conn.execute(
        "INSERT INTO weather_climate(site_id, latitude, longitude, computed_at, nights,"
        " percentiles_json) VALUES(?, ?, ?, ?, ?, ?) ON CONFLICT(site_id) DO UPDATE SET"
        " latitude = excluded.latitude, longitude = excluded.longitude,"
        " computed_at = excluded.computed_at, nights = excluded.nights,"
        " percentiles_json = excluded.percentiles_json",
        (
            site["id"],
            site["latitude"],
            site["longitude"],
            iso_z(now),
            len(means),
            json.dumps(_percentiles(means)),
        ),
    )
    return Outcome.OK
