"""A weather round, for the loop and the button: the forecast, written with how it went, the sky
aloft, then the nights the page reads (`view`). Without a site or its timezone nothing is asked."""

import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast

from ..net import Fetch
from . import fetches, forecast, sky, view
from .forecast import Outcome


def refresh(
    conn: sqlite3.Connection,
    site: Mapping[str, Any] | None,
    *,
    fetch: Fetch | None = None,
    now: datetime | None = None,
) -> forecast.Status:
    """Only the forecast's outcome comes back; the sky sources' outcomes are dropped."""
    outcome = forecast.refresh(conn, site, fetch=fetch, now=now)
    if outcome not in (Outcome.NO_SITE, Outcome.NO_TIMEZONE):
        # past those two outcomes there is a site
        known = cast("Mapping[str, Any]", site)
        # so the page can say "no answer since": a restart or another reader knows it too
        fetches.record(
            conn, known["id"], fetches.Source.FORECAST, outcome, now or datetime.now(UTC)
        )
        sky.refresh(conn, known, fetch=fetch, now=now)
        view.rebuild(conn, known)
    return outcome
