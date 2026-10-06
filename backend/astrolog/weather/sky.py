"""Writes the sky aloft per source; the upper wind arrives with the models, in the forecast. Each
source is on its own: a silent or broken one keeps its old rows and stops none of the others."""

import logging
import sqlite3
import zoneinfo
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from .. import net
from ..clock import iso_z, night_of
from ..db import config
from . import cams, meteoblue, nights, seventimer
from .fetches import Source
from .forecast import KIND, NightRow, Outcome, Status, write_rows
from .openmeteo import BadAnswerError, Series

log = logging.getLogger(__name__)

type Parse = Callable[[Any], Series]

# The keyless sources -> the module that asks and reads each.
SOURCES = {Source.SEVENTIMER: seventimer, Source.CAMS: cams}
# Every sky source; the reader takes a night's seeing from Meteoblue when it is there, else 7Timer.
ALL_SOURCES = (*SOURCES, Source.METEOBLUE)

# The real call, named in this module so the route tests replace it here.
_fetch = net.fetch


def _parsed(source: Source, parse: Parse, answer: Any) -> Series | None:
    try:
        return parse(answer)
    except BadAnswerError:
        log.info(
            "meteo: una fonte del cielo non ha risposto una previsione", extra={"source": source}
        )
        return None


def _write(
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    source: Source,
    series: Series | None,
    now: datetime,
) -> Outcome:
    if series is None:
        return Outcome.BAD_ANSWER
    times, values = series
    tz = zoneinfo.ZoneInfo(site["timezone"])
    current = night_of(now.astimezone(tz))
    rows = []
    for night, pairs in nights.covered(site["timezone"], times, current, whole=False):
        hours = nights.hours(values, pairs, tz)
        if not nights.empty(hours):
            rows.append(
                NightRow(
                    site["id"], night, KIND, source, iso_z(now), nights.hours_json(hours), None
                )
            )
    if not rows:
        log.info("meteo: una fonte del cielo non porta nessuna notte", extra={"source": source})
        return Outcome.BAD_ANSWER
    write_rows(conn, site["id"], [source], rows)
    return Outcome.OK


def _one(
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    source: Source,
    fetch: net.Fetch,
    now: datetime,
) -> Status:
    module = SOURCES[source]
    answer = net.ask(fetch, module.url(site["latitude"], site["longitude"]))
    if answer is None:
        return net.Failure.UNREACHABLE
    return _write(conn, site, source, _parsed(source, module.parse, answer), now)


def _meteoblue(
    conn: sqlite3.Connection, site: Mapping[str, Any], fetch: net.Fetch, now: datetime
) -> Status | None:
    """The outcome, recorded with its attempt; `None` without a key or before it is due."""
    key = config.read(conn).meteoblue_key
    if not key or not meteoblue.due(conn, site["id"], now):
        return None
    answer, failure = net.ask_why(fetch, meteoblue.url(site["latitude"], site["longitude"], key))
    outcome = failure or _write(
        conn, site, Source.METEOBLUE, _parsed(Source.METEOBLUE, meteoblue.parse, answer), now
    )
    # only a refusal speaks of the key; a silence keeps the seeing it gave last time
    if outcome == net.Failure.REFUSED:
        meteoblue.drop_seeing(conn)
    meteoblue.record(conn, site["id"], outcome, now)
    return outcome


def refresh(
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    *,
    fetch: net.Fetch | None = None,
    now: datetime | None = None,
) -> dict[Source, Status]:
    """`{source: outcome}`; Meteoblue is there only when it was asked."""
    moment = now or datetime.now(UTC)
    outcomes: dict[Source, Status] = {
        source: _one(conn, site, source, fetch or _fetch, moment) for source in SOURCES
    }
    outcome = _meteoblue(conn, site, fetch or _fetch, moment)
    if outcome is not None:
        outcomes[Source.METEOBLUE] = outcome
    return outcomes
