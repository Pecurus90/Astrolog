"""La connessione di una richiesta: regge il cambio di thread (`api/deps.py`) e non e' mai l'ultima
a chiudersi (`api/app.py`).

FastAPI esegue la dipendenza e il corpo della rotta su **due thread diversi** del threadpool:
finche' il pool e' scarico i due coincidono e il difetto non si vede: appena due richieste
partono insieme, no. Il test non aspetta quella coincidenza -- userebbe la fortuna come banco --
ma apre la connessione qui e la interroga da un altro thread, che e' la stessa cosa in forma
deterministica.
"""

import threading
from types import SimpleNamespace

from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.api.deps import get_db


def _query_from_another_thread(conn):
    """Interroga `conn` da un thread che non l'ha aperta. Torna `(ok, errore)`."""
    esito = {}

    def corri():
        try:
            conn.execute("SELECT 1").fetchone()
            esito["ok"] = True
        except Exception as err:  # noqa: BLE001 - si riporta al thread del test invece di ingoiarla
            esito["ok"], esito["err"] = False, err

    t = threading.Thread(target=corri)
    t.start()
    t.join()
    return esito.get("ok", False), esito.get("err")


def _request(db_path):
    """Cio' che `get_db` guarda di una richiesta, e nient'altro."""
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db_path=str(db_path))))


def test_the_request_connection_survives_a_thread_change(db_path):
    """**La regola.** La connessione che la dipendenza apre viene usata dal corpo della rotta, e
    i due girano su thread diversi del pool: se non regge il passaggio, ogni pagina che fa due
    chiamate insieme prende un 500. Col valore di fabbrica (`check_same_thread=True`) SQLite
    solleva `ProgrammingError`, ed e' il difetto che questo test tiene chiuso."""
    gen = get_db(_request(db_path))
    conn = next(gen)
    try:
        ok, err = _query_from_another_thread(conn)
        assert ok, f"la connessione della richiesta non regge il cambio di thread: {err!r}"
    finally:
        gen.close()


def test_closing_a_request_is_never_the_last_close(db_path):
    """L'app tiene il database aperto finche' vive: chiudere una richiesta non e' mai l'ultima
    chiusura, e l'app spenta lo lascia andare."""
    wal = db_path.with_name(db_path.name + "-wal")
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        assert client.get("/api/v1/nights").status_code == 200
        assert wal.exists(), "la richiesta ha chiuso l'ultima connessione e cancellato il WAL"
    assert not wal.exists(), "l'app chiusa tiene ancora aperto il database"
