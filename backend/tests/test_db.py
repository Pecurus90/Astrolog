"""Il DB nasce da schema.sql e da nient'altro; la connessione porta i suoi PRAGMA."""

import pytest

from astrolog.db.connect import connect, create_database, ensure_database
from conftest import add_folder


def test_database_is_created_from_the_single_schema(tmp_path):
    p = tmp_path / "a.db"
    create_database(p)
    c = connect(p)
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"frames", "positions", "folders", "frame_stages", "scan_runs", "sites"} <= tables
    c.close()


def test_create_refuses_to_overwrite_and_ensure_is_idempotent(tmp_path):
    p = tmp_path / "a.db"
    ensure_database(p)
    c = connect(p)
    add_folder(c, "x")
    c.close()
    ensure_database(p)  # non ricrea: la riga resta
    c = connect(p)
    assert c.execute("SELECT COUNT(*) FROM folders").fetchone()[0] == 1
    c.close()
    with pytest.raises(FileExistsError):
        create_database(p)


def test_connection_pragmas(tmp_path):
    c = connect(tmp_path / "a.db")
    assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert c.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert c.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    c.close()


def test_foreign_keys_are_enforced(conn):
    with pytest.raises(Exception):  # noqa: B017 - qualunque violazione di FK
        conn.execute(
            "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
            " VALUES(999, 999, 'x', 1, 1.0, 'now')"
        )


def test_the_row_numbers_of_the_confirmed_tables_are_never_reused(conn):
    """Una risposta di Da confermare porta il NUMERO DI RIGA del pezzo, e l'Applica dice "ho visto
    fin qui" col numero (`api/review_write.py`); queste quattro tabelle perdono righe: un'unione
    cancella uno strumento o un filtro, la spazzata di identify un oggetto, group i corredi rimasti
    senza pose. Senza `AUTOINCREMENT` SQLite ridarebbe il numero piu' alto appena liberato alla
    prima riga nuova, che nascerebbe gia' "vista", o riceverebbe la risposta scritta per quella che
    c'era prima.

    E' la meta' scomoda della scelta dei numeri di riga, e senza questa riga nessuno la vede:
    e' un caso raro, che cade dalla parte che non si rivede."""
    casi = [
        ("instruments", "INSERT INTO instruments(kind, name, created_at) VALUES('mount', ?, 'x')"),
        ("filters", "INSERT INTO filters(name, passband, created_at) VALUES(?, 'unknown', 'x')"),
        ("rigs", "INSERT INTO rigs(focal_mm, created_at) VALUES(?, 'x')"),
        ("objects", "INSERT INTO objects(catalog_slug, created_at) VALUES(?, 'x')"),
    ]
    con_autoincrement = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND sql LIKE '%AUTOINCREMENT%'"
        )
    }
    assert con_autoincrement == {t for t, _ in casi}, (
        "AUTOINCREMENT costa una scrittura in piu' per riga e serve solo dove Da confermare"
        " risponde col numero: una quinta tabella o e' una svista, o e' una decisione da scrivere"
    )

    for tabella, insert in casi:
        primo, secondo = (1.0, 2.0) if tabella == "rigs" else ("a", "b")
        vecchio = conn.execute(insert, (primo,)).lastrowid
        conn.execute(f"DELETE FROM {tabella} WHERE id = ?", (vecchio,))  # noqa: S608 - nome nostro
        nuovo = conn.execute(insert, (secondo,)).lastrowid
        assert nuovo > vecchio, f"{tabella}: il numero di una riga cancellata e' tornato"
