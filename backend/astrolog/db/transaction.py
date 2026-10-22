"""An explicit BEGIN, because in autocommit `with conn` opens nothing. COMMIT sits inside the guard:
a constraint checked at the end makes it fail, and SQLite leaves the transaction open."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def transaction(
    conn: sqlite3.Connection, *, immediate: bool = False
) -> Iterator[sqlite3.Connection]:
    """`immediate`: writer takes lock at start, so busy_timeout waits instead of failing."""
    conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
