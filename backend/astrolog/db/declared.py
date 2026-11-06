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
