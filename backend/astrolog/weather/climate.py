"""The site's usual upper wind: a year of nights, each the mean 700 hPa wind over the hours its
verdict judges, written as percentiles for `position`. Asked once a year per site."""

import json
import sqlite3
import urllib.parse
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .. import net
from ..clock import iso_z
from . import Fetch, fetches, forecast, nights, openmeteo, verdict

# The reanalysis archive does not answer at 700 hPa; the historical forecast archive does.
URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
SOURCE = "open-meteo/climate"
VARIABLE = "wind_speed_700hPa"
YEAR_DAYS = 365
# A third of a year, a product choice, not a convention: fewer nights would be one season's usual,
# and better no comparison than a wrong one.
MIN_NIGHTS = 120
# A year too short is still short at the next `forecast.RETRY_S` retry: wait a day instead.
BAD_ANSWER_WAIT = timedelta(days=1)

# The real call, named in this module so tests replace it here.
_fetch = net.fetch


# Twin of `history._url`; the markers go when the Open-Meteo recipes merge (docs/coda.md).
# jscpd:ignore-start
def _url(site: Mapping[str, Any], dal: date, al: date) -> str:
    query = urllib.parse.urlencode(
        {
            "latitude": site["latitude"],
            "longitude": site["longitude"],
            "start_date": dal.isoformat(),
            "end_date": al.isoformat(),
            "hourly": VARIABLE,
            "timezone": "UTC",
        }
    )
    return f"{URL}?{query}"


# jscpd:ignore-end


def _spostato(conn: sqlite3.Connection, site: Mapping[str, Any]) -> bool:
    """The usual belongs to a place: a site that moved asks again now, not in a year."""
    riga = conn.execute(
        "SELECT latitude, longitude FROM weather_climate WHERE site_id = ?", (site["id"],)
    ).fetchone()
    return riga is not None and (riga[0], riga[1]) != (site["latitude"], site["longitude"])


def _tocca(conn: sqlite3.Connection, site: Mapping[str, Any], adesso: datetime) -> bool:
    ultimo = fetches.last(conn, site["id"], SOURCE)
    if ultimo is None:
        return True
    eta = fetches.age(ultimo, adesso)
    if ultimo["status"] == forecast.BAD_ANSWER:
        return eta >= BAD_ANSWER_WAIT
    if ultimo["status"] != forecast.OK:
        return eta >= timedelta(seconds=forecast.RETRY_S)
    return _spostato(conn, site) or eta >= timedelta(days=YEAR_DAYS)


def _percentili(valori: Sequence[float]) -> list[float]:
    """The 101 percentiles, interpolated between the two neighbours."""
    xs = sorted(valori)
    out = []
    for p in range(101):
        pos = (len(xs) - 1) * p / 100
        basso = int(pos)
        alto = min(basso + 1, len(xs) - 1)
        out.append(round(xs[basso] + (xs[alto] - xs[basso]) * (pos - basso), 2))
    return out


def _medie_notturne(
    site: Mapping[str, Any], tempi: Sequence[datetime], serie: Sequence[float | None]
) -> list[float]:
    """Mean wind of each whole night, over its verdict window: the day says nothing of the nights
    one shoots."""
    notti = nights.covered(site["timezone"], tempi, tempi[0].date().isoformat(), whole=True)
    cielo = nights.sky(site["latitude"], site["longitude"], notti)
    medie = []
    for _, coppie in notti:
        ore, _ = verdict.window([{"sky": cielo[t], "v": serie[i]} for i, t in coppie])
        valori = [o["v"] for o in ore if o["v"] is not None]
        if valori:
            medie.append(sum(valori) / len(valori))
    return medie


def step(
    conn: sqlite3.Connection,
    site: Mapping[str, Any] | None,
    *,
    fetch: Fetch | None = None,
    now: datetime | None = None,
) -> str | None:
    """One call if due, and its outcome; `None` when not due."""
    if site is None or not site["timezone"]:
        return None
    adesso = now or datetime.now(UTC)
    if not _tocca(conn, site, adesso):
        return None
    al = adesso.date() - timedelta(days=1)
    risposta, perche = net.ask_why(fetch or _fetch, _url(site, al - timedelta(days=YEAR_DAYS), al))
    esito = perche or _scrivi(conn, site, risposta, adesso)
    fetches.record(conn, site["id"], SOURCE, esito, adesso)
    return esito


def _scrivi(
    conn: sqlite3.Connection, site: Mapping[str, Any], risposta: Any, adesso: datetime
) -> str:
    try:
        tempi, serie = openmeteo.parse_single(risposta, {VARIABLE: "wind_700hpa_kmh"})
    except openmeteo.BadAnswerError:
        return forecast.BAD_ANSWER
    medie = _medie_notturne(site, tempi, serie["wind_700hpa_kmh"]) if tempi else []
    if len(medie) < MIN_NIGHTS:
        return forecast.BAD_ANSWER
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
            iso_z(adesso),
            len(medie),
            json.dumps(_percentili(medie)),
        ),
    )
    return forecast.OK
