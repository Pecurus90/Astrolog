"""The queries of the `group` stage, all static. Nights and sessions are derived: found before
created, detached when redone, swept when empty. The user's word lives in `declarations`."""

import sqlite3
from collections.abc import Collection

from ..db import idlist
from ..db.inserted import inserted_id


def frame(conn: sqlite3.Connection, frame_id: int) -> sqlite3.Row:
    return conn.execute(
        "SELECT id, date_obs, object_id, rig_id, site_lat, site_lon, header_json"
        " FROM frames WHERE id = ?",
        (frame_id,),
    ).fetchone()


_SITE = "SELECT id, name, latitude, longitude, timezone, sky_sqm FROM sites"


def home_site(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(_SITE + " WHERE is_default = 1").fetchone()


def sites(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(_SITE).fetchall()


def night(conn: sqlite3.Connection, site_id: int, night_date: str | None) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id FROM nights WHERE site_id = ? AND night_date = ?", (site_id, night_date)
    ).fetchone()


def site_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """By NAME: the user's answer travels on it, because ids are reused."""
    return conn.execute(_SITE + " WHERE name = ?", (name,)).fetchone()


def create_night(
    conn: sqlite3.Connection,
    site_id: int,
    night_date: str | None,
    now: str,
    *,
    declared: bool = False,
) -> int:
    return inserted_id(
        conn.execute(
            "INSERT INTO nights(site_id, night_date, site_source, created_at) VALUES(?, ?, ?, ?)",
            (site_id, night_date, "declared" if declared else "detected", now),
        )
    )


def session(
    conn: sqlite3.Connection, night_id: int, object_id: int, rig_id: int | None
) -> sqlite3.Row | None:
    """A missing rig compares as the schema's key does, or two rigless frames would not meet in
    the same session."""
    return conn.execute(
        "SELECT id FROM sessions WHERE night_id = ? AND object_id = ?"
        " AND COALESCE(rig_id, -1) = COALESCE(?, -1)",
        (night_id, object_id, rig_id),
    ).fetchone()


def create_session(
    conn: sqlite3.Connection, night_id: int, object_id: int, rig_id: int | None
) -> int:
    return inserted_id(
        conn.execute(
            "INSERT INTO sessions(night_id, object_id, rig_id) VALUES(?, ?, ?)",
            (night_id, object_id, rig_id),
        )
    )


def set_frame_group(
    conn: sqlite3.Connection, frame_id: int, night_id: int, session_id: int
) -> None:
    conn.execute(
        "UPDATE frames SET night_id = ?, session_id = ? WHERE id = ?",
        (night_id, session_id, frame_id),
    )


def detach(conn: sqlite3.Connection, frame_ids: Collection[int]) -> None:
    """Whoever requeued these frames said the old night and session no longer hold."""
    if not frame_ids:
        return
    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(
            f"UPDATE frames SET night_id = NULL, session_id = NULL"  # noqa: S608
            f" WHERE id IN {listed}"
        )


def drop_empty_sessions(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "DELETE FROM sessions"
        " WHERE id NOT IN (SELECT session_id FROM frames WHERE session_id IS NOT NULL)"
    ).rowcount


def drop_empty_nights(conn: sqlite3.Connection) -> int:
    """Never a night the user declared: it may stay empty while its frames wait for another stage,
    and removing it would silently delete an answer."""
    return conn.execute(
        "DELETE FROM nights"
        " WHERE site_source != 'declared'"
        " AND id NOT IN (SELECT night_id FROM sessions)"
        " AND id NOT IN (SELECT night_id FROM frames WHERE night_id IS NOT NULL)"
    ).rowcount
