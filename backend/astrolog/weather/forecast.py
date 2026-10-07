"""Writes the forecast: asks the service, splits the hours into nights and writes each night per
model as it came. The page reads `view`, rebuilt by the round once the sky sources are in too."""

import logging
import sqlite3
import zoneinfo
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import astuple, dataclass, fields
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeGuard, cast

from .. import net
from ..clock import iso_z, night_date
from ..db.replace_table import replace_rows
from . import nights, openmeteo

log = logging.getLogger(__name__)

# Global models run every six hours; every three catches each run within a few hours of release.
REFRESH_EVERY_S = 3 * 3600
# Sooner after a failed round, but not every minute: a NAS without network would hammer the
# service for nothing.
RETRY_S = 15 * 60


class Outcome(StrEnum):
    OK = "ok"
    NO_SITE = "no_site"
    NO_TIMEZONE = "no_timezone"
    BAD_ANSWER = "bad_answer"


# How a weather call went, as `weather_fetches.status` holds it.
type Status = Outcome | net.Failure

KIND = "forecast"

# The real call, named in this module so the route tests replace it here.
_fetch = net.fetch


@dataclass(frozen=True, slots=True)
class NightRow:
    """A `weather_nights` row: the fields are the table's columns, in order."""

    site_id: int
    night_date: str
    kind: str
    source: str
    fetched_at: str
    hourly_json: str
    summary_json: str | None


COLUMNS = tuple(f.name for f in fields(NightRow))


def source_of(model: str) -> str:
    return f"open-meteo/{model}"


def write_rows(
    conn: sqlite3.Connection, site_id: int, sources: Sequence[str], rows: Iterable[NightRow]
) -> None:
    """All or nothing for these sources of the site: other sources, other sites and the observed
    weather stay."""
    marks = ", ".join("?" * len(sources))  # segnaposto-ok: the sources, the caller's constants
    replace_rows(
        conn,
        "weather_nights",
        COLUMNS,
        [astuple(r) for r in rows],
        where=f"site_id = ? AND kind = ? AND source IN ({marks})",
        args=(site_id, KIND, *sources),
    )


def _rows(
    site: Mapping[str, Any],
    models: Mapping[str, Mapping[str, list[Any]]],
    covered: Sequence[nights.Night],
    fetched_at: str,
) -> list[NightRow]:
    """Each model's nights that carry a value, with each hour's sky band; the judgement is
    `view`'s, which joins the sky sources first."""
    sky = nights.sky(site["latitude"], site["longitude"], covered)
    tz = zoneinfo.ZoneInfo(site["timezone"])
    rows = []
    for model, series in models.items():
        for night, pairs in covered:
            hours = nights.hours(series, pairs, tz, sky=sky)
            if not nights.empty(hours):
                rows.append(
                    NightRow(
                        site["id"],
                        night,
                        KIND,
                        source_of(model),
                        fetched_at,
                        nights.hours_json(hours),
                        None,
                    )
                )
    return rows


def refresh(
    conn: sqlite3.Connection,
    site: Mapping[str, Any] | None,
    *,
    fetch: net.Fetch | None = None,
    now: datetime | None = None,
) -> Status:
    """Asks the forecast for the site and writes it; a code says how it went. A silent or nightless
    answer deletes nothing: the previous forecast stays with its time."""
    if site is None:
        return Outcome.NO_SITE
    if not site["timezone"]:
        return Outcome.NO_TIMEZONE
    answer = net.ask(fetch or _fetch, openmeteo.forecast_url(site["latitude"], site["longitude"]))
    if answer is None:
        return net.Failure.UNREACHABLE  # `net` already logged the silence
    try:
        times, models = openmeteo.parse(answer)
    except openmeteo.BadAnswerError:
        log.info("meteo: il servizio non ha risposto una previsione")
        return Outcome.BAD_ANSWER
    moment = now or datetime.now(UTC)
    current = cast("str", night_date(iso_z(moment), site["timezone"]))  # a valid instant and zone
    # Whole nights only: beyond the model's horizon, better no night than half a night.
    covered = nights.covered(site["timezone"], times, current, whole=True)
    if not covered:
        log.info("meteo: la risposta non porta nessuna notte intera")
        return Outcome.BAD_ANSWER
    rows = _rows(site, models, covered, iso_z(moment))
    if not rows:
        log.info("meteo: la risposta porta solo ore vuote")
        return Outcome.BAD_ANSWER
    write_rows(conn, site["id"], [source_of(m) for m in openmeteo.MODELS], rows)
    return Outcome.OK


class Cadence:
    """When the background round is due: at once for a new or changed home site, then every
    `every_s`, sooner after a failure. A site without timezone is not hurried like a failure."""

    def __init__(self, every_s: float) -> None:
        self.every_s = every_s
        self._done_for: tuple[Any, ...] | None = None
        self._next = 0.0

    def due(self, site: Mapping[str, Any] | None, now: float) -> TypeGuard[Mapping[str, Any]]:
        if site is None:
            return False
        return self._key(site) != self._done_for or now >= self._next

    def done(self, site: Mapping[str, Any], outcome: Status, now: float) -> None:
        self._done_for = self._key(site)
        wait = (
            self.every_s
            if outcome in (Outcome.OK, Outcome.NO_TIMEZONE)
            else min(self.every_s, RETRY_S)
        )
        self._next = now + wait

    @staticmethod
    def _key(site: Mapping[str, Any]) -> tuple[Any, ...]:
        return (site["id"], site["latitude"], site["longitude"], site["timezone"])
