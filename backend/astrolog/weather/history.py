"""Observed weather of the nights you shot, from the Open-Meteo archive. One call per round, one
site and at most a year, so a long archive fills without hammering the service."""

import json
import logging
import sqlite3
import urllib.parse
import zoneinfo
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .. import net
from ..clock import iso_z, night_date
from . import Fetch, fetches, forecast, nights, openmeteo, verdict

log = logging.getLogger(__name__)

URL = "https://archive-api.open-meteo.com/v1/archive"
SOURCE = "open-meteo/archive"
KIND = "observed"
# The archive joins ECMWF at once with the ERA5 reanalysis five days later, and is final only then
# (https://open-meteo.com/en/docs/historical-weather-api).
DELAY_DAYS = 5
MAX_DAYS = 366

# The forecast's quantities without the upper wind: the archive does not carry it.
VARIABLES = {k: v for k, v in openmeteo.VARIABLES.items() if "hPa" not in k}

# The real call, named in this module so tests replace it here.
_fetch = net.fetch

_MANCANTI = """
SELECT n.site_id, n.night_date, s.latitude, s.longitude, s.timezone
FROM nights n JOIN sites s ON s.id = n.site_id
WHERE s.timezone IS NOT NULL AND NOT EXISTS (
  SELECT 1 FROM weather_nights w
  WHERE w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
)
ORDER BY n.site_id, n.night_date
"""


def _url(site: Mapping[str, Any], dal: date, al: date) -> str:
    query = urllib.parse.urlencode(
        {
            "latitude": site["latitude"],
            "longitude": site["longitude"],
            "start_date": dal.isoformat(),
            "end_date": al.isoformat(),
            "hourly": ",".join(VARIABLES),
            "timezone": "UTC",
        }
    )
    return f"{URL}?{query}"


def parse(payload: Any) -> tuple[list[datetime], dict[str, list[Any]]]:
    return openmeteo.parse_single(payload, VARIABLES)


def _in_attesa(conn: sqlite3.Connection, site_id: int, adesso: datetime) -> bool:
    """A failed round not long ago: wait before asking the same site again."""
    ultimo = fetches.last(conn, site_id, SOURCE)
    if ultimo is None or ultimo["status"] == forecast.OK:
        return False
    return fetches.age(ultimo, adesso) < timedelta(seconds=forecast.RETRY_S)


def _da_chiedere(
    conn: sqlite3.Connection, adesso: datetime
) -> tuple[dict[str, Any] | None, list[str]]:
    """The first site with nights old enough for the reanalysis and no weather, and those nights."""
    per_sito: dict[int, tuple[dict[str, Any], list[str]]] = {}
    for r in conn.execute(_MANCANTI, (KIND,)):
        oggi = night_date(iso_z(adesso), r["timezone"])
        # a night ends the morning after: that morning is what must be five days old
        if (
            oggi is None
            or r["night_date"]
            >= (date.fromisoformat(oggi) - timedelta(days=DELAY_DAYS)).isoformat()
        ):
            continue
        per_sito.setdefault(r["site_id"], (dict(r), []))[1].append(r["night_date"])
    for site_id, (sito, date_) in per_sito.items():
        if not _in_attesa(conn, site_id, adesso):
            return sito, date_
    return None, []


def step(
    conn: sqlite3.Connection, *, fetch: Fetch | None = None, now: datetime | None = None
) -> str | None:
    """One call at most: the outcome, or `None` when there was nothing to ask or a failed round is
    still waiting."""
    adesso = now or datetime.now(UTC)
    sito, date_ = _da_chiedere(conn, adesso)
    if sito is None:
        return None
    dal = date.fromisoformat(date_[0])
    # up to the last night needed, never beyond a year: the archive refuses future days
    fino = min(dal + timedelta(days=MAX_DAYS - 1), date.fromisoformat(date_[-1]))
    volute = {d for d in date_ if date.fromisoformat(d) <= fino}
    # a day before and two after in UTC: the night runs noon to noon in the site's timezone
    risposta, perche = net.ask_why(
        fetch or _fetch, _url(sito, dal - timedelta(days=1), fino + timedelta(days=2))
    )
    esito = perche or _scrivi(conn, sito, volute, risposta, adesso)
    fetches.record(conn, sito["site_id"], SOURCE, esito, adesso)
    return esito


def _scrivi(
    conn: sqlite3.Connection,
    sito: Mapping[str, Any],
    volute: set[str],
    risposta: Any,
    adesso: datetime,
) -> str:
    try:
        tempi, serie = parse(risposta)
    except openmeteo.BadAnswerError:
        log.info("meteo: l'archivio non ha risposto una serie", extra={"site_id": sito["site_id"]})
        return forecast.BAD_ANSWER
    notti = [
        n
        for n in nights.covered(sito["timezone"], tempi, min(volute), whole=True)
        if n[0] in volute
    ]
    if not notti:
        log.info("meteo: l'archivio non copre le notti chieste", extra={"site_id": sito["site_id"]})
        return forecast.BAD_ANSWER
    cielo = nights.sky(sito["latitude"], sito["longitude"], notti)
    fuso = zoneinfo.ZoneInfo(sito["timezone"])
    scritto = iso_z(adesso)
    righe = []
    for data, coppie in notti:
        ore = nights.hours(serie, coppie, fuso, sky=cielo)
        righe.append(
            (
                sito["site_id"],
                data,
                KIND,
                SOURCE,
                scritto,
                json.dumps(ore),
                json.dumps(verdict.assess(ore)),
            )
        )
    # The history is final: a night already written is never touched.
    conn.executemany(
        "INSERT INTO weather_nights(site_id, night_date, kind, source, fetched_at, hourly_json,"
        " summary_json) VALUES(?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
        righe,
    )
    return forecast.OK
