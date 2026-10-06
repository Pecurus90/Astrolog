"""Meteoblue seeing, hourly, for seven nights. The user's key rides only in the request: the log
names the service without its query, and a service error by its code, never its text."""

import math
import sqlite3
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from .. import net
from . import fetches
from .fetches import Source
from .forecast import Outcome, Status
from .openmeteo import BadAnswerError, Series

URL = "https://my.meteoblue.com/packages/seeing-1h"
USAGE_URL = "https://my.meteoblue.com/account/usage"

# The free key's yearly cap (https://business.meteoblue.com/products/weather-apis/free-weather-api);
# the cost of one call of this package, as the account's usage page reports it.
FREE_YEAR_CREDITS = 10_000_000
CREDITS_PER_CALL = 8_000
CALLS_PER_YEAR = FREE_YEAR_CREDITS // CREDITS_PER_CALL
# Twice a day at most, since one answer already brings seven nights; never more than the cap.
MIN_GAP_H = max(12, math.ceil(24 * 365 / CALLS_PER_YEAR))

type KeyOutcome = Literal[Outcome.OK, Outcome.BAD_ANSWER] | net.Failure

# The real call, named in this module so the route tests replace it here.
_fetch = net.fetch

__all__ = ["BadAnswerError", "check_key", "due", "last_attempt", "parse", "record", "url"]


def url(latitude: float, longitude: float, key: str) -> str:
    query = urllib.parse.urlencode(
        {"lat": latitude, "lon": longitude, "apikey": key, "forecastDays": 7, "tz": "UTC"}
    )
    return f"{URL}?{query}"


def parse(payload: Any) -> Series:
    """Seeing is one value, so the range has equal ends. The declared `utc_timeoffset` is removed
    even though UTC is asked: if the parameter were ever ignored, nothing slips."""
    data = payload.get("data_1h") if isinstance(payload, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get("time"), list):
        raise BadAnswerError("manca la serie oraria del seeing")
    offset = timedelta(hours=float((payload.get("metadata") or {}).get("utc_timeoffset") or 0))
    try:
        instants = [
            datetime.fromisoformat(str(t).replace(" ", "T")).replace(tzinfo=UTC) - offset
            for t in data["time"]
        ]
    except ValueError as err:
        raise BadAnswerError("orari illeggibili") from err
    values = data.get("seeing_arcsec")
    if not isinstance(values, list) or len(values) != len(instants):
        raise BadAnswerError("manca il seeing")
    return instants, {"seeing_from": list(values), "seeing_to": list(values)}


def check_key(key: str, *, fetch: net.Fetch | None = None) -> KeyOutcome:
    """Asks the account's usage, which costs no credits."""
    answer, failure = net.ask_why(
        fetch or _fetch, f"{USAGE_URL}?{urllib.parse.urlencode({'apikey': key})}"
    )
    if failure:
        return failure
    if not isinstance(answer, dict) or not isinstance(answer.get("items"), list):
        return Outcome.BAD_ANSWER
    return Outcome.OK


def last_attempt(conn: sqlite3.Connection, site_id: int) -> sqlite3.Row | None:
    return fetches.last(conn, site_id, Source.METEOBLUE)


def due(conn: sqlite3.Connection, site_id: int, now: datetime) -> bool:
    """A failed attempt counts too: retrying at once would spend credits."""
    attempt = last_attempt(conn, site_id)
    return attempt is None or fetches.age(attempt, now) >= timedelta(hours=MIN_GAP_H)


def record(conn: sqlite3.Connection, site_id: int, status: Status, now: datetime) -> None:
    fetches.record(conn, site_id, Source.METEOBLUE, status, now)


def forget(conn: sqlite3.Connection) -> None:
    """Key removed or changed: the previous seeing and the last attempt no longer hold."""
    conn.execute("DELETE FROM weather_fetches WHERE source = ?", (Source.METEOBLUE,))
    drop_seeing(conn)


def drop_seeing(conn: sqlite3.Connection) -> None:
    """The seeing of a key that no longer holds must not pose as the current one; the night falls
    back to 7Timer."""
    conn.execute("DELETE FROM weather_nights WHERE source = ?", (Source.METEOBLUE,))
