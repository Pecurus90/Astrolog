"""The sign that the Archive's derived tables are fresh (ADR 0048): their writer leaves it, a
trigger on any of their inputs removes it (schema.sql). Without it, readers count the frames."""

import sqlite3

# One sign for the options and the rows: one writer, the same inputs (schema.sql, derived_fresh).
ARCHIVE = "archive_options"


def is_fresh(conn: sqlite3.Connection) -> bool:
    found = conn.execute("SELECT 1 FROM derived_fresh WHERE name = ?", (ARCHIVE,)).fetchone()
    return found is not None


def mark_fresh(conn: sqlite3.Connection) -> None:
    """Inside the writer's BEGIN IMMEDIATE, after the tables: no write can fall in between."""
    conn.execute("INSERT OR IGNORE INTO derived_fresh(name) VALUES (?)", (ARCHIVE,))
