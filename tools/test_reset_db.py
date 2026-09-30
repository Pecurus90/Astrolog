"""Il reset del database di sviluppo non butta via cio' che c'e' dentro senza che glielo si dica,
e non scambia un'opzione per il nome di un file.
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import reset_db  # noqa: E402


def test_an_empty_database_is_recreated(tmp_path):
    db = tmp_path / "vuoto.db"
    assert reset_db.main([str(db)]) == 0
    assert reset_db.main([str(db)]) == 0, "un DB appena ricreato non porta niente di tuo"


def test_a_database_with_something_in_it_is_refused(tmp_path):
    """Un sito, una cartella, un frame: dentro c'e' lavoro, e senza dirlo non si butta."""
    db = tmp_path / "pieno.db"
    reset_db.main([str(db)])
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO folders(root_path, created_at) VALUES('D:/Astro', '2026-09-23T00:00:00Z')"
    )
    conn.commit()
    conn.close()

    assert reset_db.main([str(db)]) == 1
    assert _cartelle(db) == 1
    assert reset_db.main([str(db), reset_db.ANCHE_SE_PIENO]) == 0
    assert _cartelle(db) == 0
    assert _cartelle(reset_db.COPIA.format(db, 1)) == 1, "cio' che c'era resta accanto"


def test_a_second_reset_does_not_overwrite_the_first_copy(tmp_path):
    """Due reset di fila lasciano due copie: la seconda sovrascrivendo la prima butterebbe via
    proprio cio' che la prima aveva salvato."""
    db = tmp_path / "pieno.db"
    for volta in (1, 2):
        reset_db.main([str(db), reset_db.ANCHE_SE_PIENO])
        conn = sqlite3.connect(db)
        conn.execute(
            "INSERT INTO folders(root_path, created_at) VALUES(?, 'x')", (f"D:/Astro{volta}",)
        )
        conn.commit()
        conn.close()
    reset_db.main([str(db), reset_db.ANCHE_SE_PIENO])
    assert [_cartelle(reset_db.COPIA.format(db, n)) for n in (1, 2)] == [1, 1]


def test_the_copy_keeps_what_is_still_in_the_write_ahead_log(tmp_path):
    """Il database lavora col registro accanto (`-wal`): le scritture recenti stanno li' finche'
    SQLite non le riversa. Una copia del solo file le perderebbe; la copia di SQLite no."""
    db = tmp_path / "pieno.db"
    reset_db.main([str(db)])
    tiene = sqlite3.connect(db)  # tiene aperto il registro: le scritture restano nel -wal
    tiene.execute("PRAGMA journal_mode=WAL")
    tiene.execute("PRAGMA wal_autocheckpoint=0")
    tiene.execute("INSERT INTO folders(root_path, created_at) VALUES('D:/Astro', 'x')")
    tiene.commit()
    copia = tmp_path / "copia.db"
    reset_db._copia(db, copia)
    tiene.close()
    assert _cartelle(copia) == 1


def _cartelle(db):
    """Quante cartelle ha quel DB, chiudendo la connessione: su Windows un file aperto non si
    cancella, e il reset fallirebbe per colpa della prova."""
    conn = sqlite3.connect(db)
    try:
        return conn.execute("SELECT COUNT(*) FROM folders").fetchone()[0]
    finally:
        conn.close()


def test_an_option_it_does_not_know_is_not_a_path(tmp_path, monkeypatch):
    """`--help` non e' il nome di un database, e non ne diventa uno."""
    monkeypatch.chdir(tmp_path)
    assert reset_db.main(["--help"]) == 2
    assert not (tmp_path / "--help").exists()
