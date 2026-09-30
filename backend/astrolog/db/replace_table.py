"""Rewrites a derived table, or the part being redone, all or nothing. A savepoint, not BEGIN: in a
caller's transaction it nests, and the commit stays with whoever opened it."""

import sqlite3
from collections.abc import Iterable, Sequence
from typing import Any


def replace_rows(  # noqa: PLR0913
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
    where: str = "1",
    args: Sequence[Any] = (),
) -> None:
    """Table, columns and condition are the caller's constants, never user values: those travel in
    `args`. `rows` are tuples in `columns` order."""
    elenco = ", ".join(columns)
    segnaposto = ", ".join("?" * len(columns))  # segnaposto-ok: the columns, not the rows
    conn.execute("SAVEPOINT replace_rows")
    try:
        conn.execute(f"DELETE FROM {table} WHERE {where}", args)  # noqa: S608 - caller's constants
        conn.executemany(
            f"INSERT INTO {table}({elenco}) VALUES({segnaposto})",  # noqa: S608 - constants
            rows,
        )
    except Exception:
        conn.execute("ROLLBACK TO replace_rows")
        conn.execute("RELEASE replace_rows")
        raise
    conn.execute("RELEASE replace_rows")
