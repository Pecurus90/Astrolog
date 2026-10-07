"""Tens of thousands of ids go to a query through a temp table: the placeholder ceiling depends on
how SQLite was built, and batches would change what GROUP BY and ORDER BY mean."""

import sqlite3
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

TABLE = "id_list"
IN_LIST = f"(SELECT id FROM {TABLE})"  # noqa: S608 - TABLE is a constant of this file

# Guarded on who is using the table, not on its content: two lists open on one connection
# would trample each other and give a plausible, wrong result.
_in_use: set[sqlite3.Connection] = set()


@contextmanager
def holding(conn: sqlite3.Connection, ids: Iterable[int | str | None]) -> Iterator[str]:
    """Yields the SQL for "among these ids": `WHERE id IN {listed}`."""
    if conn in _in_use:
        raise RuntimeError("un elenco e' gia' aperto su questa connessione")
    _in_use.add(conn)
    try:
        # A plain INTEGER, not a primary key: like the placeholders it replaces, a repeated id is
        # harmless and a None matches nothing.
        conn.execute(  # ddl-ok: one scratch table per connection, outside the schema
            f"CREATE TEMP TABLE IF NOT EXISTS {TABLE} (id INTEGER)"
        )
        # Emptied on entry, not on exit: on exit a cursor still open would lose rows silently.
        conn.execute(f"DELETE FROM {TABLE}")  # noqa: S608 - TABLE is a constant of this file
        conn.executemany(f"INSERT INTO {TABLE}(id) VALUES(?)", [(i,) for i in ids])  # noqa: S608
        yield IN_LIST
    finally:
        _in_use.discard(conn)


def grouped(
    conn: sqlite3.Connection,
    sql: str | tuple[str, Sequence[Any]],
    ids: Collection[int | str | None],
    key: str,
    row: Callable[[sqlite3.Row], Any],
) -> dict[Any, list[Any]]:
    """One query for many ids, split by `key`; `sql` carries `{listed}`, plus its values when it
    has other placeholders. No ids, no query."""
    if not ids:
        return {}
    text, values = (sql, ()) if isinstance(sql, str) else sql
    out: dict[Any, list[Any]] = {}
    with holding(conn, ids) as listed:
        for r in conn.execute(text.format(listed=listed), values):
            out.setdefault(r[key], []).append(row(r))
    return out
