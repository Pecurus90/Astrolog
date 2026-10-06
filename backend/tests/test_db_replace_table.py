"""La riscrittura intera di una tabella derivata: tutto o niente (`db.replace_table.replace_rows`).

La usano chi scrive l'uso dell'attrezzatura e chi scrive i candidati degli oggetti in dubbio: chi
legge a meta' deve vedere la tabella di prima, mai vuota, e una riscrittura che cade la lascia.
"""

import sqlite3

import pytest

from astrolog.db.replace_table import replace_rows

_COLONNE = ("object_key", "rank", "slug", "name")
# The card's stable key: the table carries it, not the object's row.
_OGGETTO = "m-45"


def _righe(conn):
    return conn.execute("SELECT slug FROM object_candidates ORDER BY rank").fetchall()


def test_the_table_is_replaced_whole(conn):
    replace_rows(conn, "object_candidates", _COLONNE, [(_OGGETTO, 0, "m-1", "M 1")])
    replace_rows(conn, "object_candidates", _COLONNE, [(_OGGETTO, 0, "m-2", "M 2")])
    assert [r[0] for r in _righe(conn)] == ["m-2"]


def test_a_rewrite_that_breaks_leaves_the_table_as_it_was(conn):
    replace_rows(conn, "object_candidates", _COLONNE, [(_OGGETTO, 0, "m-1", "M 1")])
    doppia = [(_OGGETTO, 0, "m-2", "M 2"), (_OGGETTO, 0, "m-3", "M 3")]
    with pytest.raises(sqlite3.IntegrityError):
        replace_rows(conn, "object_candidates", _COLONNE, doppia)
    assert [r[0] for r in _righe(conn)] == ["m-1"]


def test_it_nests_inside_a_transaction_that_is_already_open(conn):
    """Chi risponde "sono file di calibrazione" in Da confermare e' gia' dentro la transazione
    dell'Applica: la riscrittura ci sta dentro, e la conferma resta di chi l'ha aperta."""
    conn.execute("BEGIN")
    replace_rows(conn, "object_candidates", _COLONNE, [(_OGGETTO, 0, "m-1", "M 1")])
    conn.execute("ROLLBACK")
    assert _righe(conn) == []
