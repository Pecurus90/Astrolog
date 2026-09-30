"""Apre una connessione SQLite coi PRAGMA dell'app, e crea un DB nuovo da `schema.sql`.

Vincolo non ovvio: autocommit (`isolation_level=None`) con BEGIN/COMMIT espliciti, cosi' i
PRAGMA stanno fuori da ogni transazione e il commit per frame e' davvero per frame. Il DB
non va mai su una condivisione di rete (WAL + SMB = corruzione possibile).
"""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


def schema_sql():
    """Il testo di `schema.sql`, l'unica verita' del DB."""
    return SCHEMA_PATH.read_text(encoding="utf-8")


def create_database(path):
    """Crea il file del DB da `schema.sql`. Solleva se il file esiste gia' e non e' vuoto:
    ricreare e' un gesto esplicito (`tools/reset_db.py`), mai un effetto collaterale."""
    p = Path(path)
    if p.exists() and p.stat().st_size > 0:
        raise FileExistsError(f"il database esiste gia': {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        conn.executescript(schema_sql())
    finally:
        conn.close()


def connect(path, *, check_same_thread=True):
    """Una connessione pronta: foreign keys, WAL, `busy_timeout`, righe per nome.

    `check_same_thread=False` serve a chi usa la connessione da un thread diverso da quello che
    l'ha aperta, uno alla volta: il worker, e ogni richiesta dell'API (`api/deps.py`)."""
    conn = sqlite3.connect(str(path), check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def ensure_database(path):
    """Crea il DB se non c'e'; se c'e' lo lascia com'e'. E' cio' che l'app fa all'avvio."""
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        create_database(p)
    return p
