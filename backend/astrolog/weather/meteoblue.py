"""Il seeing di Meteoblue, con la chiave dell'utente: ora per ora, in arcosecondi, per sette notti.

Vincoli non ovvi:

* **La chiave non esce mai**: sta nell'indirizzo della richiesta, e il log scrive solo il servizio
  (`net`); un errore del servizio si dice col suo codice, mai col suo testo.
* **Due volte al giorno al massimo**: una risposta porta gia' sette notti, e il tetto dei crediti
  della chiave gratuita ne reggerebbe di piu' (la prova lo tiene). L'ultimo tentativo si scrive
  (`weather_fetches`), cosi' un riavvio non rispende crediti.
* **Un rifiuto toglie il seeing di quella chiave**, che non vale piu', e il seeing torna a 7Timer;
  un silenzio no -- non dice niente della chiave, e resta il seeing di prima.
"""

import math
import urllib.parse
from datetime import UTC, datetime, timedelta

from .. import net
from . import fetches, forecast
from .openmeteo import BadAnswerError

URL = "https://my.meteoblue.com/packages/seeing-1h"
USAGE_URL = "https://my.meteoblue.com/account/usage"
SOURCE = "meteoblue"

# Il tetto della chiave gratuita e il costo di una chiamata del pacchetto, misurati sul conto il
# 26/9/2026 (https://business.meteoblue.com/products/weather-apis/free-weather-api).
FREE_YEAR_CREDITS = 10_000_000
CREDITS_PER_CALL = 8_000
CALLS_PER_YEAR = FREE_YEAR_CREDITS // CREDITS_PER_CALL
# Due volte al giorno al massimo; e mai piu' di quanto il tetto regge in un anno.
MIN_GAP_H = max(12, math.ceil(24 * 365 / CALLS_PER_YEAR))

OK = forecast.OK
REFUSED = net.REFUSED
UNREACHABLE = net.UNREACHABLE
BAD_ANSWER = forecast.BAD_ANSWER

# La chiamata vera: un nome di questo modulo, cosi' le prove delle rotte la sostituiscono qui.
_fetch = net.fetch

__all__ = ["SOURCE", "BadAnswerError", "check_key", "due", "last_attempt", "parse", "record", "url"]


def url(latitude, longitude, key):
    query = urllib.parse.urlencode(
        {"lat": latitude, "lon": longitude, "apikey": key, "forecastDays": 7, "tz": "UTC"}
    )
    return f"{URL}?{query}"


def parse(payload):
    """`(istanti UTC, {seeing_from, seeing_to})`: il seeing e' un valore solo, e l'intervallo ha i
    due estremi uguali. L'ora arriva nel fuso che il servizio dichiara (`utc_timeoffset`), che si
    toglie anche se chiesto in UTC: se un giorno il parametro fosse ignorato, niente slitta."""
    dati = payload.get("data_1h") if isinstance(payload, dict) else None
    if not isinstance(dati, dict) or not isinstance(dati.get("time"), list):
        raise BadAnswerError("manca la serie oraria del seeing")
    scarto = timedelta(hours=float((payload.get("metadata") or {}).get("utc_timeoffset") or 0))
    try:
        istanti = [
            datetime.fromisoformat(str(t).replace(" ", "T")).replace(tzinfo=UTC) - scarto
            for t in dati["time"]
        ]
    except ValueError as err:
        raise BadAnswerError("orari illeggibili") from err
    valori = dati.get("seeing_arcsec")
    if not isinstance(valori, list) or len(valori) != len(istanti):
        raise BadAnswerError("manca il seeing")
    return istanti, {"seeing_from": list(valori), "seeing_to": list(valori)}


def check_key(key, *, fetch=None):
    """La chiave vale? Si chiede il consumo del conto, che non costa crediti: `ok`, `refused` (il
    servizio la rifiuta), `unreachable`, o `bad_answer`."""
    risposta, perche = net.ask_why(
        fetch or _fetch, f"{USAGE_URL}?{urllib.parse.urlencode({'apikey': key})}"
    )
    if perche:
        return perche
    if not isinstance(risposta, dict) or not isinstance(risposta.get("items"), list):
        return BAD_ANSWER
    return OK


def last_attempt(conn, site_id):
    return fetches.last(conn, site_id, SOURCE)


def due(conn, site_id, adesso):
    """Tocca chiedere? Si' se non si e' mai chiesto, o se l'ultimo tentativo ha l'eta' della
    cadenza. Anche un tentativo andato male conta: riprovare subito spenderebbe crediti."""
    ultimo = last_attempt(conn, site_id)
    return ultimo is None or fetches.age(ultimo, adesso) >= timedelta(hours=MIN_GAP_H)


def record(conn, site_id, status, adesso):
    fetches.record(conn, site_id, SOURCE, status, adesso)


def forget(conn):
    """Chiave tolta o cambiata: il seeing di prima e l'ultimo tentativo non valgono piu'."""
    conn.execute("DELETE FROM weather_fetches WHERE source = ?", (SOURCE,))
    drop_seeing(conn)


def drop_seeing(conn):
    """Il seeing di una chiave che non vale piu': non resta a fingere di essere quello di adesso."""
    conn.execute("DELETE FROM weather_nights WHERE source = ?", (SOURCE,))
