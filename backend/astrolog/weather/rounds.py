"""A weather round, for the background loop and the button: the models' forecast, then the sky
aloft. Without a site or its timezone the sky sources are not even asked."""

import sqlite3
from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

from . import Fetch, forecast, sky


def refresh(
    conn: sqlite3.Connection,
    site: Mapping[str, Any] | None,
    *,
    fetch: Fetch | None = None,
    now: datetime | None = None,
) -> forecast.Outcome:
    """Only the forecast's outcome comes back; the sky sources' outcomes are dropped."""
    esito = forecast.refresh(conn, site, fetch=fetch, now=now)
    if esito not in (forecast.NO_SITE, forecast.NO_TIMEZONE):
        # past those two outcomes there is a site
        sky.refresh(conn, cast("Mapping[str, Any]", site), fetch=fetch, now=now)
    return esito
