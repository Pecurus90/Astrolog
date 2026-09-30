"""Le scritture di dentro passano tutte o nessuna: la transazione dell'API, della spina e degli
stadi, scritta una volta.

Vincolo non ovvio: serve un BEGIN esplicito, perche' la connessione dell'app e' in autocommit
(`db/connect.py`) e li' `with conn` non aprirebbe niente. E il COMMIT sta dentro la guardia: un
vincolo controllato alla fine lo fa fallire, e SQLite lascia la transazione aperta.
`catalog/load.py` la scrive a mano: gli strati (`backend/pyproject.toml`) non gli lasciano
importare `db`.
"""

from contextlib import contextmanager


@contextmanager
def transaction(conn):
    conn.execute("BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
