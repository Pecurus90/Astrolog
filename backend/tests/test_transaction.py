"""Una scrittura rotta a meta' non lascia niente, e non lascia la connessione dentro una
transazione aperta: la regola sta in `db/transaction.py`, e vale per l'API, la spina e gli stadi."""

import sqlite3

import pytest

from astrolog.db.transaction import transaction
from astrolog.pipeline.changes import open_receipt
from astrolog.spine import scan_store
from conftest import add_folder

_A_FRAME = (
    "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
    " VALUES('h', 'light', '[]', 'now')"
)


def _frames(conn):
    return conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]


def test_a_block_that_breaks_leaves_nothing(conn):
    with pytest.raises(RuntimeError), transaction(conn):
        conn.execute(_A_FRAME)
        raise RuntimeError("guasto finto")
    assert _frames(conn) == 0
    assert not conn.in_transaction


def test_a_stop_in_the_middle_leaves_nothing(conn):
    """Una corsa fermata e' un `GeneratorExit`, che non e' un `Exception`: annulla lo stesso."""
    with pytest.raises(GeneratorExit), transaction(conn):
        conn.execute(_A_FRAME)
        raise GeneratorExit
    assert _frames(conn) == 0
    assert not conn.in_transaction


def test_a_commit_that_is_refused_leaves_nothing(conn):
    """Un vincolo controllato alla fine fa fallire il COMMIT stesso: SQLite lascia la transazione
    aperta, e la scrittura dopo ci finirebbe dentro."""
    with pytest.raises(sqlite3.IntegrityError), transaction(conn):
        conn.execute("PRAGMA defer_foreign_keys = ON")
        conn.execute(_A_FRAME)
        conn.execute(
            "INSERT INTO frame_stages(frame_id, stage, status, updated_at)"
            " VALUES(999, 'solve', 'pending', 'now')"
        )
    assert _frames(conn) == 0
    assert not conn.in_transaction


def test_a_scan_receipt_that_breaks_leaves_nothing_open(conn):
    """La ricevuta di una scansione che si rompe a meta' scrittura non resta aperta: la scrittura
    successiva della spina finirebbe nella stessa transazione."""
    run_id = open_receipt(conn, add_folder(conn, "x"), "now")
    with pytest.raises(sqlite3.IntegrityError):  # found < 0: lo schema la ferma a meta'
        scan_store.finish_run(conn, run_id, run_id, "ok", None, {"found": -1}, {}, [], "now")
    assert not conn.in_transaction
    assert scan_store.run_outcomes(conn, run_id)[0]["ended_at"] is None
