"""The last attempt of a weather source for a site and how it went, written rather than kept in
memory so a restart neither spends Meteoblue credits nor hammers an archive that refused."""

import sqlite3
from datetime import datetime, timedelta
from typing import cast

from ..clock import iso_z, parse_iso


def last(conn: sqlite3.Connection, site_id: int, source: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT attempted_at, status FROM weather_fetches WHERE site_id = ? AND source = ?",
        (site_id, source),
    ).fetchone()


def record(
    conn: sqlite3.Connection, site_id: int, source: str, status: str, adesso: datetime
) -> None:
    conn.execute(
        "INSERT INTO weather_fetches(site_id, source, attempted_at, status) VALUES(?, ?, ?, ?)"
        " ON CONFLICT(site_id, source) DO UPDATE SET attempted_at = excluded.attempted_at,"
        " status = excluded.status",
        (site_id, source, iso_z(adesso), status),
    )


def age(ultimo: sqlite3.Row, adesso: datetime) -> timedelta:
    # `record` writes the instant, so it always parses.
    return adesso - cast("datetime", parse_iso(ultimo["attempted_at"]))
