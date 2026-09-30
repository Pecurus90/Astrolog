"""Autocommit (`isolation_level=None`) with explicit BEGIN/COMMIT, so the PRAGMAs stay outside any
transaction. The database never goes on a network share: WAL over SMB can corrupt it."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


def schema_sql() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def create_database(path: str | Path) -> None:
    """Raises if the file exists and is not empty: recreating is an explicit act
    (`tools/reset_db.py`), never a side effect."""
    p = Path(path)
    if p.exists() and p.stat().st_size > 0:
        raise FileExistsError(f"il database esiste gia': {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        conn.executescript(schema_sql())
    finally:
        conn.close()


def connect(path: str | Path, *, check_same_thread: bool = True) -> sqlite3.Connection:
    """`check_same_thread=False` is for a connection used, one at a time, from a thread other than
    the one that opened it: the worker and each API request."""
    conn = sqlite3.connect(str(path), check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    # The app keeps one connection open, so the WAL is never deleted:
    # truncate it whenever a checkpoint rewinds it.
    conn.execute("PRAGMA journal_size_limit = 0")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def ensure_database(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        create_database(p)
    return p
