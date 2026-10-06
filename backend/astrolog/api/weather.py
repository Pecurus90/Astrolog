"""The read does not compute: verdict, factors, usable hours and agreement are written per model
with the forecast, and the upper air is merged per hour from its sources' rows."""

import json
import sqlite3
from typing import Any, cast

from fastapi import APIRouter, Depends

from ..clock import night_date, now_iso
from ..db import config
from ..spine.group_store import home_site
from ..weather import forecast, meteoblue, openmeteo, rounds, sky
from ..weather.fetches import Source
from .deps import get_db
from .models_weather import (
    RefreshStatus,
    WeatherAloftOut,
    WeatherBriefOut,
    WeatherNightOut,
    WeatherOut,
    WeatherRefreshOut,
    WeatherSeeingOut,
    WeatherSourceOut,
)

router = APIRouter(prefix="/api/v1", tags=["meteo"])

_NOTTI = (
    "SELECT night_date, fetched_at, hourly_json, summary_json FROM weather_nights"
    " WHERE site_id = ? AND kind = ? AND source = ? AND night_date >= ? ORDER BY night_date"
)
_ARRIVATA = (
    "SELECT MAX(fetched_at) FROM weather_nights WHERE site_id = ? AND kind = ? AND source LIKE ?"
)
_FONTI_DEL_CIELO = ", ".join("?" * len(sky.ALL_SOURCES))  # segnaposto-ok: the sources, constants
# S608: the placeholders are constants.
_CIELO = (
    "SELECT night_date, source, fetched_at, hourly_json FROM weather_nights"  # noqa: S608
    f" WHERE site_id = ? AND kind = ? AND source IN ({_FONTI_DEL_CIELO}) AND night_date >= ?"
)

_SEEING = ("seeing_from", "seeing_to")

# A product choice, not a threshold: no source found says from which day an hourly forecast stops
# being worth reading.
FULL_NIGHTS = 3
# the current night and the six after: the service sometimes brings one more, which is not shown
MAX_NIGHTS = 7
_VENTO = ("wind_700hpa_kmh", "wind_250hpa_kmh", "wind_200hpa_kmh")
_CAMPI_DEL_CIELO = (
    "seeing_from", "seeing_to", "transparency_from", "transparency_to",
    "aerosol_optical_depth", "dust_ugm3",
)  # fmt: skip


def _in_quota(
    ore: list[dict[str, Any]], del_cielo: dict[str, dict[str, Any]]
) -> list[WeatherAloftOut]:
    """The wind from the model, the rest from the sky sources at the hour they have; an hour a
    source does not give stays empty."""
    return [
        WeatherAloftOut(
            at=o["at"],
            **{k: o.get(k) for k in _VENTO},
            **{k: del_cielo.get(o["at"], {}).get(k) for k in _CAMPI_DEL_CIELO},
        )
        for o in ore
    ]


def _notte(
    riga: sqlite3.Row, posto: int, del_cielo: dict[str, dict[str, dict[str, Any]]]
) -> WeatherNightOut:
    riassunto = json.loads(riga["summary_json"])
    if posto >= FULL_NIGHTS:
        # the trend carries nothing read from the hours
        riassunto.update(
            factors=[], usable_hours=None, wind_700hpa_kmh=None, wind_700hpa_tenths=None
        )
        return WeatherNightOut(
            night=riga["night_date"], trend=True, hours=[], aloft=[], **riassunto
        )
    ore = json.loads(riga["hourly_json"])
    return WeatherNightOut(
        night=riga["night_date"],
        trend=False,
        hours=ore,
        aloft=_in_quota(ore, del_cielo.get(riga["night_date"], {})),
        **riassunto,
    )


def _seeing(conn: sqlite3.Connection, site_id: int, arrivate: dict[str, str]) -> WeatherSeeingOut:
    """Meteoblue's last attempt only with a key: it is what lets the page say why seeing comes from
    7Timer."""
    fonte = "meteoblue" if "meteoblue" in arrivate else "7timer" if "7timer" in arrivate else None
    ultimo = meteoblue.last_attempt(conn, site_id) if config.read(conn).meteoblue_key else None
    return WeatherSeeingOut(source=fonte, meteoblue=ultimo["status"] if ultimo else None)


@router.get("/weather", response_model=WeatherOut)
def weather(conn: sqlite3.Connection = Depends(get_db)) -> WeatherOut:
    """The coming nights of the home site, from the model chosen in the preferences, as the
    forecast wrote them: changing model is reading another row.

    Without a home site `site` is `null` and there are no nights; with a site whose time zone is
    missing or unknown, `missing` is `no_timezone`.

    **Three full nights, then a trend**: from the fourth (`trend`) only the verdict, the clouds,
    the dark hours and the agreement, without usable hours, factors, hours, upper sky or upper
    wind. A night that has Meteoblue's seeing takes all of it from there: the hours Meteoblue does
    not cover stay empty instead of taking 7Timer's bands, or the page would say "from Meteoblue"
    over a night of two sources."""
    scelto = config.read(conn).weather_model
    vuoto = WeatherOut(
        site=None,
        missing=None,
        model=scelto,
        models=list(openmeteo.MODELS),
        fetched_at=None,
        full_nights=FULL_NIGHTS,
        seeing=WeatherSeeingOut(source=None, meteoblue=None),
        sources=[],
        nights=[],
    )
    sito = home_site(conn)
    if sito is None:
        return vuoto
    in_corso = night_date(now_iso(), sito["timezone"]) if sito["timezone"] else None
    if in_corso is None:
        return vuoto.model_copy(
            update={"site": sito["name"], "missing": forecast.Outcome.NO_TIMEZONE}
        )
    righe = conn.execute(
        _NOTTI, (sito["id"], forecast.KIND, forecast.source_of(scelto), in_corso)
    ).fetchall()
    del_cielo: dict[str, dict[str, dict[str, Any]]] = {}  # night -> hour -> sky source fields
    arrivate: dict[str, str] = {}  # source -> when it arrived
    del_sito = conn.execute(
        _CIELO, (sito["id"], forecast.KIND, *sky.ALL_SOURCES, in_corso)
    ).fetchall()
    con_meteoblue = {r["night_date"] for r in del_sito if r["source"] == Source.METEOBLUE}
    for r in del_sito:
        arrivate[r["source"]] = max(arrivate.get(r["source"], ""), r["fetched_at"])
        per_ora = del_cielo.setdefault(r["night_date"], {})
        via = _SEEING if r["source"] == "7timer" and r["night_date"] in con_meteoblue else ()
        for o in json.loads(r["hourly_json"]):
            per_ora.setdefault(o["at"], {}).update(
                {k: v for k, v in o.items() if v is not None and k not in via}
            )
    return vuoto.model_copy(
        update={
            "site": sito["name"],
            "fetched_at": conn.execute(
                _ARRIVATA, (sito["id"], forecast.KIND, forecast.source_of("%"))
            ).fetchone()[0],
            "nights": [_notte(r, i, del_cielo) for i, r in enumerate(righe[:MAX_NIGHTS])],
            "seeing": _seeing(conn, sito["id"], arrivate),
            "sources": [
                WeatherSourceOut(source=f, fetched_at=q) for f, q in sorted(arrivate.items())
            ],
        }
    )


@router.post("/weather/refresh", response_model=WeatherRefreshOut)
def refresh(conn: sqlite3.Connection = Depends(get_db)) -> WeatherRefreshOut:
    """Asks for the forecast now. If the service is silent the previous one stays, and the reply
    says why."""
    sito = home_site(conn)
    status = rounds.refresh(conn, dict(sito) if sito else None)
    return WeatherRefreshOut(status=cast(RefreshStatus, status))


def brief_of(conn: sqlite3.Connection, site_id: int, night: str) -> WeatherBriefOut | None:
    """One night's summary from the chosen model, as written; Tonight reads it."""
    scelto = config.read(conn).weather_model
    riga = conn.execute(
        _NOTTI + " LIMIT 1", (site_id, forecast.KIND, forecast.source_of(scelto), night)
    ).fetchone()
    if riga is None or riga["night_date"] != night:
        return None
    return WeatherBriefOut(**json.loads(riga["summary_json"]))
