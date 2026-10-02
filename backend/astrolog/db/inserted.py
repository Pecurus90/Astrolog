import sqlite3


def inserted_id(cursor: sqlite3.Cursor) -> int:
    """The id of the row an INSERT just wrote; sqlite3 types `lastrowid` as optional."""
    row_id = cursor.lastrowid
    assert row_id is not None  # always set after an INSERT into a rowid table
    return row_id
