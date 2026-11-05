"""An explicit BEGIN, because in autocommit `with conn` opens nothing. COMMIT sits inside the guard:
a constraint checked at the end makes it fail, and SQLite leaves the transaction open."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def transaction(
    conn: sqlite3.Connection, *, immediate: bool = True
) -> Iterator[sqlite3.Connection]:
    """Writer takes lock at start, so busy_timeout waits. Deferred, a read then a write fails at
    once if another writer committed between (WAL, stale snapshot): Behind writes beside the app."""
    conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
