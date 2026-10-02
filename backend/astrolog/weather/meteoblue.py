"""Meteoblue seeing, hourly, for seven nights. The user's key rides only in the request: the log
names the service without its query, and a service error by its code, never its text."""

import math
import sqlite3
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Literal

from .. import net
from . import fetches, forecast
from .openmeteo import BadAnswerError

URL = "https://my.meteoblue.com/packages/seeing-1h"
USAGE_URL = "https://my.meteoblue.com/account/usage"
SOURCE = "meteoblue"

# The free key's yearly cap (https://business.meteoblue.com/products/weather-apis/free-weather-api);
# the cost of one call of this package, as the account's usage page reports it.
FREE_YEAR_CREDITS = 10_000_000
CREDITS_PER_CALL = 8_000
CALLS_PER_YEAR = FREE_YEAR_CREDITS // CREDITS_PER_CALL
# Twice a day at most, since one answer already brings seven nights; never more than the cap.
MIN_GAP_H = max(12, math.ceil(24 * 365 / CALLS_PER_YEAR))

type KeyOutcome = Literal["ok", "bad_answer"] | net.Failure
OK: Final = forecast.OK
REFUSED: Final = net.REFUSED
UNREACHABLE: Final = net.UNREACHABLE
BAD_ANSWER: Final = forecast.BAD_ANSWER

# The real call, named in this module so the route tests replace it here.
_fetch = net.fetch

__all__ = ["SOURCE", "BadAnswerError", "check_key", "due", "last_attempt", "parse", "record", "url"]


def url(latitude: float, longitude: float, key: str) -> str:
    query = urllib.parse.urlencode(
        {"lat": latitude, "lon": longitude, "apikey": key, "forecastDays": 7, "tz": "UTC"}
    )
    return f"{URL}?{query}"


def parse(payload: Any) -> tuple[list[datetime], dict[str, list[Any]]]:
    """Seeing is one value, so the range has equal ends. The declared `utc_timeoffset` is removed
    even though UTC is asked: if the parameter were ever ignored, nothing slips."""
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


def check_key(key: str, *, fetch: net.Fetch | None = None) -> KeyOutcome:
    """Asks the account's usage, which costs no credits."""
    risposta, perche = net.ask_why(
        fetch or _fetch, f"{USAGE_URL}?{urllib.parse.urlencode({'apikey': key})}"
    )
    if perche:
        return perche
    if not isinstance(risposta, dict) or not isinstance(risposta.get("items"), list):
        return BAD_ANSWER
    return OK


def last_attempt(conn: sqlite3.Connection, site_id: int) -> sqlite3.Row | None:
    return fetches.last(conn, site_id, SOURCE)


def due(conn: sqlite3.Connection, site_id: int, adesso: datetime) -> bool:
    """A failed attempt counts too: retrying at once would spend credits."""
    ultimo = last_attempt(conn, site_id)
    return ultimo is None or fetches.age(ultimo, adesso) >= timedelta(hours=MIN_GAP_H)


def record(conn: sqlite3.Connection, site_id: int, status: str, adesso: datetime) -> None:
    fetches.record(conn, site_id, SOURCE, status, adesso)


def forget(conn: sqlite3.Connection) -> None:
    """Key removed or changed: the previous seeing and the last attempt no longer hold."""
    conn.execute("DELETE FROM weather_fetches WHERE source = ?", (SOURCE,))
    drop_seeing(conn)


def drop_seeing(conn: sqlite3.Connection) -> None:
    """The seeing of a key that no longer holds must not pose as the current one; the night falls
    back to 7Timer."""
    conn.execute("DELETE FROM weather_nights WHERE source = ?", (SOURCE,))
