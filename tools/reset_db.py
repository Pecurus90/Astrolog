"""Ricrea il database da `backend/astrolog/schema.sql` e da nient'altro.

Uso: python tools/reset_db.py [percorso.db] [--anche-se-pieno]   senza percorso usa il DB dell'app
Conserva nulla: e' il reset di sviluppo. Il reset dell'utente, che tiene cartelle, siti e
impostazioni, e' una rotta dell'app e nasce con la pagina Impostazioni.

Vincolo non ovvio: un DB con qualcosa dentro fuori dal catalogo -- che e' derivato e si ricarica --
si rifiuta, e si butta solo dicendolo (`--anche-se-pieno`), lasciandone una copia accanto:
guardare prima di cancellare e' una regola, e senza questa macchina dipendeva dall'attenzione di
chi lancia il comando.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from astrolog.catalog.load import load_catalog  # noqa: E402
from astrolog.db.connect import connect, create_database  # noqa: E402
from astrolog.db.paths import db_path  # noqa: E402

ANCHE_SE_PIENO = "--anche-se-pieno"
COPIA = "{}.prima-del-reset-{}"  # il DB, e un numero: un reset dopo l'altro non si sovrascrivono


def _copia(sorgente, destinazione):
    """La copia di SQLite, non quella del file: il DB lavora col registro accanto (`-wal`), e le
    scritture recenti stanno li' finche' SQLite non le riversa nel file."""
    da = sqlite3.connect(sorgente)
    a = sqlite3.connect(destinazione)
    try:
        da.backup(a)
    finally:
        a.close()
        da.close()


def _copia_libera(target):
    """Il primo nome di copia che non c'e' ancora."""
    n = 1
    while Path(COPIA.format(target, n)).exists():
        n += 1
    return Path(COPIA.format(target, n))


def _pieno(target):
    """Le tabelle che hanno righe, fuori dal catalogo. Un file che non e' un DB e' pieno di suo."""
    if not target.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
        try:
            tabelle = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                    " AND name NOT LIKE 'catalog\\_%' ESCAPE '\\'"
                    " AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\'"
                )
            ]
            return [t for t in tabelle if conn.execute(f'SELECT 1 FROM "{t}" LIMIT 1').fetchone()]  # noqa: S608 - nomi letti da sqlite_master
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        return ["(non e' un database)"]


def main(argv):
    opzioni = [a for a in argv if a.startswith("-")]
    percorsi = [a for a in argv if not a.startswith("-")]
    if set(opzioni) - {ANCHE_SE_PIENO} or len(percorsi) > 1:
        sys.stderr.write(__doc__ or "")
        return 2
    target = Path(percorsi[0]) if percorsi else db_path()
    pieno = _pieno(target)
    if pieno and ANCHE_SE_PIENO not in opzioni:
        sys.stderr.write(
            f"{target} non e' vuoto ({', '.join(pieno)}): non lo ricreo."
            f" Per buttarlo davvero: {ANCHE_SE_PIENO}\n"
        )
        return 1
    if pieno:  # buttato solo dicendolo, e comunque lasciandone una copia accanto
        copia = _copia_libera(target)
        _copia(target, copia)
        sys.stdout.write(f"copia di prima: {copia}\n")
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(target) + suffix)
        if p.exists():
            p.unlink()
    create_database(target)
    # Il catalogo e' derivato al 100%: un DB ricreato senza non e' un DB pulito, e' un DB a
    # meta' -- e chi azzera per provare `identify` se ne accorgerebbe solo li'.
    conn = connect(target)
    try:
        quante = load_catalog(conn)
    finally:
        conn.close()
    sys.stdout.write(f"database ricreato da schema.sql: {target}\n")
    sys.stdout.write(f"catalogo: {quante} voci\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
