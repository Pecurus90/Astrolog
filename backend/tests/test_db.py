"""Il DB nasce da schema.sql e da nient'altro; la connessione porta i suoi PRAGMA."""

import sqlite3

import pytest

from astrolog.db.connect import (
    StaleSchemaError,
    _shape,
    connect,
    create_database,
    ensure_database,
    schema_sql,
)
from conftest import add_folder


def test_database_is_created_from_the_single_schema(tmp_path):
    p = tmp_path / "a.db"
    create_database(p)
    c = connect(p)
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"frames", "positions", "folders", "frame_stages", "scan_runs", "sites"} <= tables
    c.close()


def test_the_created_file_has_every_table_index_view_and_trigger_of_the_schema_in_wal(tmp_path):
    """La forma intera, non qualche tabella: e' la prova di chi cambia come lo schema si scrive."""
    p = tmp_path / "a.db"
    create_database(p)
    fresh = sqlite3.connect(":memory:")
    fresh.executescript(schema_sql())
    made = sqlite3.connect(str(p))
    try:
        assert _shape(made) == _shape(fresh)
        assert made.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    finally:
        fresh.close()
        made.close()


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


@pytest.mark.parametrize(
    "change",
    [
        "ALTER TABLE scan_runs ADD COLUMN gone_since INTEGER",
        "DROP VIEW position_folders",
        "CREATE TABLE left_over (x INTEGER)",
    ],
)
def test_a_database_of_an_older_schema_is_refused_at_start(tmp_path, change):
    """Un DB nato da uno schema.sql di prima non si apre: senza, l'app parte e cade dopo con
    `no such column` a meta' scansione, o un 500 su /tonight. Si ricrea (tools/reset_db.py)."""
    p = tmp_path / "a.db"
    ensure_database(p)
    c = connect(p)
    c.execute(change)
    c.close()
    with pytest.raises(StaleSchemaError, match="reset_db"):
        ensure_database(p)


def test_on_a_nas_an_older_database_is_set_aside_and_the_app_starts(tmp_path):
    """Sul NAS non c'e' terminale per tools/reset_db.py: il container ripartiva in loop (#97). Il
    DB vecchio si rinomina accanto, mai cancellato, e l'app parte su uno nuovo."""
    from astrolog.api.app import create_app

    p = tmp_path / "astrolog.db"
    ensure_database(p)
    c = connect(p)
    add_folder(c, "x")
    c.execute("CREATE TABLE left_over (x INTEGER)")
    c.close()

    create_app(p, data_root=str(tmp_path))

    aside = list(tmp_path.glob("astrolog.db.schema-vecchio-*"))
    assert len(aside) == 1
    old = connect(aside[0])
    assert old.execute("SELECT COUNT(*) FROM folders").fetchone()[0] == 1
    old.close()
    c = connect(p)
    assert c.execute("SELECT COUNT(*) FROM folders").fetchone()[0] == 0
    c.close()


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
    """Una risposta di Da confermare porta il NUMERO DI RIGA dello strumento, e l'Applica dice "ho
    visto fin qui" col numero (`api/review_write.py`); queste quattro tabelle perdono righe:
    un'unione cancella uno strumento o un filtro, la spazzata di identify un oggetto, group i setup
    rimasti senza frame. Senza `AUTOINCREMENT` SQLite ridarebbe il numero piu' alto appena liberato
    alla prima riga nuova, che nascerebbe gia' "vista", o riceverebbe la risposta scritta per quella
    che c'era prima.

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


def test_the_wal_shrinks_back_while_a_connection_stays_open(db_path):
    """L'app tiene una connessione aperta, quindi il WAL non si cancella mai: dopo una scrittura
    grossa deve tornare piccolo, o resta grande quanto lei finche' l'app gira."""
    wal = db_path.with_name(db_path.name + "-wal")
    keepalive = connect(db_path)
    try:
        grossa = connect(db_path)
        grossa.execute("CREATE TABLE ingombro(b)")
        grossa.execute("BEGIN")
        grossa.executemany("INSERT INTO ingombro VALUES(randomblob(1000))", [()] * 8000)
        grossa.execute("COMMIT")
        grossa.close()
        dopo_la_grossa = wal.stat().st_size
        for _ in range(3):
            piccola = connect(db_path)
            piccola.execute("INSERT INTO ingombro VALUES(1)")
            piccola.close()
        assert wal.stat().st_size < dopo_la_grossa / 10, "il WAL resta grande come la scrittura"
    finally:
        keepalive.close()
