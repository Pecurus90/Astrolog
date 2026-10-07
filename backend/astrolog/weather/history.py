"""Observed weather of the nights you shot, from the Open-Meteo archive. One call per round, one
site and at most a year, so a long archive fills without hammering the service."""

import json
import logging
import sqlite3
import zoneinfo
from collections.abc import Mapping
from dataclasses import asdict, astuple
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .. import net
from ..clock import iso_z, night_date
from . import fetches, nights, openmeteo, verdict
from .fetches import Source
from .forecast import COLUMNS, NightRow, Outcome, Status

log = logging.getLogger(__name__)

URL = "https://archive-api.open-meteo.com/v1/archive"
KIND = "observed"
# The archive joins ECMWF at once with the ERA5 reanalysis five days later, and is final only then
# (https://open-meteo.com/en/docs/historical-weather-api).
DELAY_DAYS = 5
MAX_DAYS = 366

# The forecast's quantities without the upper wind: the archive does not carry it.
VARIABLES = {k: v for k, v in openmeteo.VARIABLES.items() if "hPa" not in k}

# The real call, named in this module so tests replace it here.
_fetch = net.fetch

_MISSING = """
SELECT n.site_id, n.night_date, s.latitude, s.longitude, s.timezone
FROM nights n JOIN sites s ON s.id = n.site_id
WHERE s.timezone IS NOT NULL AND NOT EXISTS (
  SELECT 1 FROM weather_nights w
  WHERE w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
)
ORDER BY n.site_id, n.night_date
"""

# The history is final: a night already written is never touched.
_INSERT = (
    f"INSERT INTO weather_nights({', '.join(COLUMNS)})"  # noqa: S608 - the columns are constants
    f" VALUES({', '.join('?' * len(COLUMNS))}) ON CONFLICT DO NOTHING"  # segnaposto-ok: columns
)


def parse(payload: Any) -> openmeteo.Series:
    return openmeteo.parse_single(payload, VARIABLES)


def asked_from(night: str) -> str:
    """The first night date (noon to noon, site zone) on which the archive is asked for `night`:
    a night ends the morning after, and that morning must be five days old."""
    return (date.fromisoformat(night) + timedelta(days=DELAY_DAYS + 1)).isoformat()


def arrives_on(night: str, timezone: str, now: datetime | None = None) -> str | None:
    """The day a young night's weather is asked; `None` once it is due, when only the service's
    answer is missing and a date would be a promise already broken."""
    today = night_date(iso_z(now or datetime.now(UTC)), timezone)
    first = asked_from(night)
    return first if today is not None and today < first else None


def _due_site(conn: sqlite3.Connection, now: datetime) -> tuple[dict[str, Any] | None, list[str]]:
    """The first site with nights old enough for the reanalysis and no weather, and those nights."""
    per_site: dict[int, tuple[dict[str, Any], list[str]]] = {}
    for r in conn.execute(_MISSING, (KIND,)):
        today = night_date(iso_z(now), r["timezone"])
        if today is None or today < asked_from(r["night_date"]):
            continue
        per_site.setdefault(r["site_id"], (dict(r), []))[1].append(r["night_date"])
    for site_id, (site, dates) in per_site.items():
        if not fetches.failed_recently(fetches.last(conn, site_id, Source.ARCHIVE), now):
            return site, dates
    return None, []


def step(
    conn: sqlite3.Connection, *, fetch: net.Fetch | None = None, now: datetime | None = None
) -> Status | None:
    """One call at most: the outcome, or `None` when there was nothing to ask or a failed round is
    still waiting."""
    moment = now or datetime.now(UTC)
    site, dates = _due_site(conn, moment)
    if site is None:
        return None
    start = date.fromisoformat(dates[0])
    # up to the last night needed, never beyond a year: the archive refuses future days
    until = min(start + timedelta(days=MAX_DAYS - 1), date.fromisoformat(dates[-1]))
    wanted = {d for d in dates if date.fromisoformat(d) <= until}
    # a day before and two after in UTC: the night runs noon to noon in the site's timezone
    query = openmeteo.url(
        URL,
        site["latitude"],
        site["longitude"],
        VARIABLES,
        start_date=(start - timedelta(days=1)).isoformat(),
        end_date=(until + timedelta(days=2)).isoformat(),
    )
    answer, failure = net.ask_why(fetch or _fetch, query)
    outcome = failure or _write(conn, site, wanted, answer, moment)
    fetches.record(conn, site["site_id"], Source.ARCHIVE, outcome, moment)
    return outcome


def _write(
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    wanted: set[str],
    answer: Any,
    now: datetime,
) -> Outcome:
    try:
        times, series = parse(answer)
    except openmeteo.BadAnswerError:
        log.info("meteo: l'archivio non ha risposto una serie", extra={"site_id": site["site_id"]})
        return Outcome.BAD_ANSWER
    covered = [
        n
        for n in nights.covered(site["timezone"], times, min(wanted), whole=True)
        if n[0] in wanted
    ]
    if not covered:
        log.info("meteo: l'archivio non copre le notti chieste", extra={"site_id": site["site_id"]})
        return Outcome.BAD_ANSWER
    sky = nights.sky(site["latitude"], site["longitude"], covered)
    tz = zoneinfo.ZoneInfo(site["timezone"])
    fetched_at = iso_z(now)
    rows = []
    for night, pairs in covered:
        hours = nights.hours(series, pairs, tz, sky=sky)
        rows.append(
            NightRow(
                site["site_id"],
                night,
                KIND,
                Source.ARCHIVE,
                fetched_at,
                nights.hours_json(hours),
                json.dumps(asdict(verdict.assess(hours))),
            )
        )
    conn.executemany(_INSERT, [astuple(r) for r in rows])
    return Outcome.OK
