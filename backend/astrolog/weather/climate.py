"""Il vento in quota tipico del sito: un anno di notti, il vento a 700 hPa di ognuna sulle ore su
cui la si giudica, e la loro distribuzione scritta per chi deve dire dove cade una notte
(`position.py`).

Vincoli non ovvi:

* **Una volta l'anno per sito**, una chiamata all'archivio delle previsioni: l'archivio della
  rianalisi a 700 hPa non risponde, quello delle previsioni si' (verificato il 26/9/2026). Un giro
  andato male aspetta prima di riprovare, scritto in `weather_fetches`.
* **Le notti, non le ore**: ogni notte vale la media delle ore su cui la previsione giudica la sua
  (`verdict.window`: il buio, o dove non arriva il Sole sotto l'orizzonte). Il giorno non descrive
  le notti in cui si riprende.
* **Il solito e' di un posto**: si scrive con le coordinate che l'hanno misurato, e un sito che si
  sposta lo richiede subito invece di aspettare l'anno.
* **Sotto un terzo dell'anno non si scrive niente**: e' una scelta, non una convenzione. Meno notti
  sarebbero il solito di una stagione sola, e meglio nessun confronto che uno sbagliato. Un anno
  corto tornera' corto anche fra un quarto d'ora: dopo una risposta che non basta si aspetta un
  giorno, non l'attesa di un servizio muto.
"""

import json
import urllib.parse
from datetime import UTC, datetime, timedelta

from .. import net
from ..clock import iso_z
from . import fetches, forecast, nights, openmeteo, verdict

URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
SOURCE = "open-meteo/climate"
VARIABLE = "wind_speed_700hPa"
YEAR_DAYS = 365
MIN_NIGHTS = 120
BAD_ANSWER_WAIT = timedelta(days=1)

# La chiamata vera: un nome di questo modulo, cosi' le prove la sostituiscono qui.
_fetch = net.fetch


def _url(site, dal, al):
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


def _spostato(conn, site):
    riga = conn.execute(
        "SELECT latitude, longitude FROM weather_climate WHERE site_id = ?", (site["id"],)
    ).fetchone()
    return riga is not None and (riga[0], riga[1]) != (site["latitude"], site["longitude"])


def _tocca(conn, site, adesso):
    ultimo = fetches.last(conn, site["id"], SOURCE)
    if ultimo is None:
        return True
    eta = fetches.age(ultimo, adesso)
    if ultimo["status"] == forecast.BAD_ANSWER:
        return eta >= BAD_ANSWER_WAIT
    if ultimo["status"] != forecast.OK:
        return eta >= timedelta(seconds=forecast.RETRY_S)
    return _spostato(conn, site) or eta >= timedelta(days=YEAR_DAYS)


def _percentili(valori):
    """I 101 percentili dei valori, per interpolazione fra i due vicini."""
    xs = sorted(valori)
    out = []
    for p in range(101):
        pos = (len(xs) - 1) * p / 100
        basso = int(pos)
        alto = min(basso + 1, len(xs) - 1)
        out.append(round(xs[basso] + (xs[alto] - xs[basso]) * (pos - basso), 2))
    return out


def _medie_notturne(site, tempi, serie):
    """Il vento medio di ogni notte intera che la serie copre, sulle ore della sua finestra."""
    notti = nights.covered(site["timezone"], tempi, tempi[0].date().isoformat(), whole=True)
    cielo = nights.sky(site["latitude"], site["longitude"], notti)
    medie = []
    for _, coppie in notti:
        ore, _ = verdict.window([{"sky": cielo[t], "v": serie[i]} for i, t in coppie])
        valori = [o["v"] for o in ore if o["v"] is not None]
        if valori:
            medie.append(sum(valori) / len(valori))
    return medie


def step(conn, site, *, fetch=None, now=None):
    """Un passo della climatologia del sito: una chiamata se tocca, l'esito; `None` se non tocca."""
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


def _scrivi(conn, site, risposta, adesso):
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
