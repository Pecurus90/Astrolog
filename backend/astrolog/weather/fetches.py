"""The last attempt of a weather source for a site and how it went, written rather than kept in
memory so a restart neither spends Meteoblue credits nor hammers an archive that refused."""

import sqlite3
from datetime import datetime, timedelta
from enum import StrEnum
from typing import cast

from ..clock import iso_z, parse_iso
from .forecast import RETRY_S, Outcome, Status


class Source(StrEnum):
    """A source's name as written in its rows; the forecast's go by model (`forecast.source_of`)."""

    CAMS = "cams"
    METEOBLUE = "meteoblue"
    ARCHIVE = "open-meteo/archive"
    CLIMATE = "open-meteo/climate"


def last(conn: sqlite3.Connection, site_id: int, source: Source) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT attempted_at, status FROM weather_fetches WHERE site_id = ? AND source = ?",
        (site_id, source),
    ).fetchone()


def record(
    conn: sqlite3.Connection, site_id: int, source: Source, status: Status, now: datetime
) -> None:
    conn.execute(
        "INSERT INTO weather_fetches(site_id, source, attempted_at, status) VALUES(?, ?, ?, ?)"
        " ON CONFLICT(site_id, source) DO UPDATE SET attempted_at = excluded.attempted_at,"
        " status = excluded.status",
        (site_id, source, iso_z(now), status),
    )


def age(attempt: sqlite3.Row, now: datetime) -> timedelta:
    # `record` writes the instant, so it always parses.
    return now - cast("datetime", parse_iso(attempt["attempted_at"]))


def failed_recently(attempt: sqlite3.Row | None, now: datetime) -> bool:
    """A failed round not long ago: wait before asking the same site again."""
    return (
        attempt is not None
        and attempt["status"] != Outcome.OK
        and age(attempt, now) < timedelta(seconds=RETRY_S)
    )
