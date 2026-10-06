"""Static SQL for the `identify` stage."""

import sqlite3
from typing import Any

from ..db import idlist
from ..db.inserted import inserted_id


def frame(conn: sqlite3.Connection, frame_id: int) -> sqlite3.Row:
    """The header's own object name, and the fingerprint the user's word on the frame hangs on."""
    return conn.execute(
        "SELECT id, object_raw, frame_hash, found_key FROM frames WHERE id = ?", (frame_id,)
    ).fetchone()


def wcs(conn: sqlite3.Connection, frame_id: int) -> dict[str, Any]:
    """The measured sky, or `{}` if unsolved; a dict, not a Row, because the geometry reads it
    with `.get()`."""
    row = conn.execute(
        "SELECT ra_deg, dec_deg, scale_arcsec_px, rotation_deg, width_deg, height_deg"
        " FROM frame_wcs WHERE frame_id = ?",
        (frame_id,),
    ).fetchone()
    return dict(row) if row else {}


def object_by_slug(conn: sqlite3.Connection, slug: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM objects WHERE catalog_slug = ?", (slug,)).fetchone()
    return dict(row) if row else None


# A name is unique across objects (schema), so the owner is one row or none.
_OWNER = "SELECT object_id FROM object_names WHERE name = ?"


def object_by_name(conn: sqlite3.Connection, name: str | None) -> dict[str, Any] | None:
    row = conn.execute(
        f"SELECT * FROM objects WHERE id = ({_OWNER})",  # noqa: S608 - a constant
        (name,),
    ).fetchone()
    return dict(row) if row else None


def name_owner(conn: sqlite3.Connection, name: str) -> int | None:
    """Which object already owns this name, if any: one name, one object."""
    row = conn.execute(_OWNER, (name,)).fetchone()
    return row[0] if row else None


def create_object(
    conn: sqlite3.Connection,
    *,
    slug: str | None,
    method: str | None,
    confidence: str | None,
    now: str,
) -> int:
    return inserted_id(
        conn.execute(
            "INSERT INTO objects(catalog_slug, identity_method, identity_confidence,"
            " identified_at, created_at) VALUES(?, ?, ?, ?, ?)",
            (slug, method, confidence, now, now),
        )
    )


def set_identity(
    conn: sqlite3.Connection,
    object_id: int,
    *,
    method: str | None,
    confidence: str | None,
    now: str,
) -> None:
    conn.execute(
        "UPDATE objects SET identity_method = ?, identity_confidence = ?, identified_at = ?"
        " WHERE id = ?",
        (method, confidence, now, object_id),
    )


def add_name(
    conn: sqlite3.Connection, object_id: int, name: str, *, origin: str, is_primary: int = 0
) -> bool:
    """True if the object ends up with the name; False only when another object owns it.
    Kept here so the caller does not repeat the ownership query."""
    owner = name_owner(conn, name)
    if owner is not None:
        return owner == object_id
    conn.execute(
        "INSERT INTO object_names(object_id, name, origin, is_primary) VALUES(?, ?, ?, ?)",
        (object_id, name, origin, is_primary),
    )
    return True


def set_frame_object(conn: sqlite3.Connection, frame_id: int, object_id: int) -> None:
    conn.execute("UPDATE frames SET object_id = ? WHERE id = ?", (object_id, frame_id))


def set_empty_cone(conn: sqlite3.Connection, frame_id: int, empty: int | None) -> None:
    conn.execute("UPDATE frames SET empty_cone = ? WHERE id = ?", (empty, frame_id))


def set_found_key(conn: sqlite3.Connection, frame_id: int, key: str | None) -> None:
    conn.execute("UPDATE frames SET found_key = ? WHERE id = ?", (key, frame_id))


def detach(conn: sqlite3.Connection, frame_ids: list[int]) -> None:
    """Unlinks the object from these frames: a derived value, and the caller has said the
    old one no longer holds."""
    if not frame_ids:
        return
    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(f"UPDATE frames SET object_id = NULL WHERE id IN {listed}")  # noqa: S608


def drop_empty_objects(conn: sqlite3.Connection) -> int:
    """Drops objects with no frames (names and sessions follow by CASCADE), `user` ones
    too: the user's word lives in `declarations`, not in the object."""
    return conn.execute(
        "DELETE FROM objects"
        " WHERE id NOT IN (SELECT object_id FROM frames WHERE object_id IS NOT NULL)"
    ).rowcount
