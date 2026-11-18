"""Automatico theme: dark from sunset to sunrise at the home site (board v82, SceltaTema).
Reads the Moon calendar rows the round writes; compares, never computes the Sun."""

import datetime as dt
import sqlite3
from dataclasses import dataclass
from typing import Literal

from ..clock import night_date, parse_iso
from ..site_of import Site

Shown = Literal["scuro", "chiaro"]


@dataclass(frozen=True, slots=True)
class ThemeNow:
    mode: Shown
    until: str | None  # the next change, in the site's zone; None when it never comes (polar)


def _edges(
    conn: sqlite3.Connection, site_id: int, night: str
) -> tuple[dt.datetime | None, dt.datetime | None] | None:
    row = conn.execute(
        "SELECT sun_down_from, sun_down_until FROM moon_nights"
        " WHERE site_id = ? AND night_date = ?",
        (site_id, night),
    ).fetchone()
    return None if row is None else (parse_iso(row[0]), parse_iso(row[1]))


def shown(conn: sqlite3.Connection, site: Site | None, now: dt.datetime) -> ThemeNow | None:
    """None when the night is not written yet (no site, no zone, round still to come)."""
    if site is None or not site.timezone:
        return None
    tonight = night_date(now.isoformat(), site.timezone)
    edges = _edges(conn, site.id, tonight) if tonight else None
    if tonight is None or edges is None:
        return None
    sunset, sunrise = edges
    if sunset is not None and sunrise is not None and sunset <= now < sunrise:
        return ThemeNow("scuro", sunrise.isoformat())
    return ThemeNow("chiaro", _next_sunset(conn, site.id, tonight, now))


def _next_sunset(
    conn: sqlite3.Connection, site_id: int, tonight: str, now: dt.datetime
) -> str | None:
    """First sunset written after now, tonight or later: a midnight sun skips its nights."""
    rows = conn.execute(
        "SELECT sun_down_from FROM moon_nights WHERE site_id = ? AND night_date >= ?"
        " AND sun_down_from IS NOT NULL ORDER BY night_date",
        (site_id, tonight),
    )
    return next((r[0] for r in rows if (s := parse_iso(r[0])) is not None and s > now), None)
