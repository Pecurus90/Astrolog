"""Il meteo delle prossime notti: legge cio' che la previsione ha scritto, e la chiede a richiesta.

Vincoli non ovvi:

* **La lettura non calcola**. Verdetto, fattori, ore utili e accordo sono scritti con la previsione
  per ogni modello, e cambiare modello e' leggere un'altra riga. Il cielo in quota si **unisce** per
  ora dalle righe delle sue fonti: e' una lettura, non un conto.
* **Tre notti piene, poi tendenza** (Marco, 26/9/2026): dalla quarta il verdetto, le
  nuvole, le ore di buio e l'accordo, senza ore utili, fattori, ore, cielo e vento in quota.
  E' una scelta di prodotto, non una soglia: nessuna fonte trovata dice da che giorno la previsione
  ora per ora smette di valere.
"""

import json
import sqlite3

from fastapi import APIRouter, Depends

from ..clock import night_date, now_iso
from ..db import config
from ..spine.group_store import home_site
from ..weather import forecast, meteoblue, openmeteo, rounds, sky
from .deps import get_db
from .models_weather import (
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
_FONTI_DEL_CIELO = ", ".join("?" * len(sky.ALL_SOURCES))  # segnaposto-ok: le fonti, costanti
_CIELO = (
    "SELECT night_date, source, fetched_at, hourly_json FROM weather_nights"  # noqa: S608 - segnaposto costanti
    f" WHERE site_id = ? AND kind = ? AND source IN ({_FONTI_DEL_CIELO}) AND night_date >= ?"
)  # fmt: skip

_SEEING = ("seeing_from", "seeing_to")

FULL_NIGHTS = 3
# la notte in corso e le sei dopo: il servizio a volte ne porta una in piu', e non si mostra
MAX_NIGHTS = 7
_VENTO = ("wind_700hpa_kmh", "wind_250hpa_kmh", "wind_200hpa_kmh")
_CAMPI_DEL_CIELO = (
    "seeing_from", "seeing_to", "transparency_from", "transparency_to",
    "aerosol_optical_depth", "dust_ugm3",
)  # fmt: skip


def _in_quota(ore, del_cielo):
    """Le ore del cielo in quota, sulle ore della notte: il vento dal modello, il resto dalle fonti
    del cielo all'ora che hanno. Un'ora che una fonte non da' resta vuota."""
    return [
        WeatherAloftOut(
            at=o["at"],
            **{k: o.get(k) for k in _VENTO},
            **{k: del_cielo.get(o["at"], {}).get(k) for k in _CAMPI_DEL_CIELO},
        )
        for o in ore
    ]


def _notte(riga, posto, del_cielo):
    riassunto = json.loads(riga["summary_json"])
    if posto >= FULL_NIGHTS:
        # la tendenza non porta cio' che si legge dalle ore: ne' i fattori, ne' le ore utili, ne'
        # il vento in quota
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


def _seeing(conn, site_id, arrivate):
    """Da dove viene il seeing, e com'e' andato l'ultimo tentativo di Meteoblue quando c'e' la
    chiave: e' cio' che fa dire alla pagina perche' il seeing viene da 7Timer."""
    fonte = "meteoblue" if "meteoblue" in arrivate else "7timer" if "7timer" in arrivate else None
    ultimo = meteoblue.last_attempt(conn, site_id) if config.read(conn)["meteoblue_key"] else None
    return WeatherSeeingOut(source=fonte, meteoblue=ultimo["status"] if ultimo else None)


@router.get("/weather", response_model=WeatherOut)
def weather(conn: sqlite3.Connection = Depends(get_db)):
    """Le prossime notti del sito di casa, dal modello scelto nelle preferenze."""
    scelto = config.read(conn)["weather_model"]
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
        return vuoto.model_copy(update={"site": sito["name"], "missing": forecast.NO_TIMEZONE})
    righe = conn.execute(
        _NOTTI, (sito["id"], forecast.KIND, forecast.source_of(scelto), in_corso)
    ).fetchall()
    del_cielo = {}  # notte -> ora -> campi delle fonti del cielo
    arrivate = {}  # fonte -> quando e' arrivata
    del_sito = conn.execute(
        _CIELO, (sito["id"], forecast.KIND, *sky.ALL_SOURCES, in_corso)
    ).fetchall()
    # Una notte che ha il seeing di Meteoblue lo prende tutto da li': le ore che Meteoblue non copre
    # restano vuote invece di prendere le fasce di 7Timer, o la pagina direbbe "viene da Meteoblue"
    # sopra una notte a due fonti.
    con_meteoblue = {r["night_date"] for r in del_sito if r["source"] == meteoblue.SOURCE}
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
def refresh(conn: sqlite3.Connection = Depends(get_db)):
    """Chiede la previsione adesso. Se il servizio tace resta quella di prima, e si dice perche'."""
    sito = home_site(conn)
    return WeatherRefreshOut(status=rounds.refresh(conn, dict(sito) if sito else None))


def brief_of(conn, site_id, night):
    """Il riassunto di una notte della previsione, dal modello scelto, come scritto: `None` se non
    c'e'. Lo legge Stanotte."""
    scelto = config.read(conn)["weather_model"]
    riga = conn.execute(
        _NOTTI + " LIMIT 1", (site_id, forecast.KIND, forecast.source_of(scelto), night)
    ).fetchone()
    if riga is None or riga["night_date"] != night:
        return None
    return WeatherBriefOut(**json.loads(riga["summary_json"]))
