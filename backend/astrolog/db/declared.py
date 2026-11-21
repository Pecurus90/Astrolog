"""One answer of the user, read: the spine and `site_of` both read it, and site_of sits below the
spine (ADR 0030)."""

import sqlite3
from typing import Any


def declared(conn: sqlite3.Connection, entity_type: str, entity_key: str | None, field: str) -> Any:
    """The row's presence wins over what was detected."""
    if entity_key is None:
        return None
    row = conn.execute(
        "SELECT value FROM declarations WHERE entity_type = ? AND entity_key = ? AND field = ?",
        (entity_type, entity_key, field),
    ).fetchone()
    return None if row is None else row["value"]


def declared_by_key(conn: sqlite3.Connection, entity_type: str, field: str) -> dict[str, Any]:
    """`declared` of every key at once: a page with many questions reads its answers in one go."""
    return {
        r["entity_key"]: r["value"]
        for r in conn.execute(
            "SELECT entity_key, value FROM declarations WHERE entity_type = ? AND field = ?",
            (entity_type, field),
        )
    }
