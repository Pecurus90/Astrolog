"""Il tetto dei segnaposto di SQLite, e le sei query della spina che ci sbattevano.

Non e' "va piu' lento": oltre il tetto, in una `WHERE id IN (?, ?, ...)` SQLite rifiuta la query
con `too many SQL variables`, e l'archivio si ferma.

**Il tetto il test lo impone, non lo trova.** Dipende da come SQLite e' stato compilato: 32.766 su
Windows, 250.000 sulla build di Ubuntu. Con un tetto trovato, su Linux quarantamila id starebbero
sotto e le sei prove sarebbero verdi per costruzione: la guardia cieca proprio li'. Abbassato a
un valore noto con `setlimit`, la prova morde uguale su ogni sistema, e costa meno.

Le prove costano niente perche' il guasto scatta quando la query si **prepara**, non sui dati:
servono gli id, non le righe.
"""

import re
import sqlite3
from pathlib import Path

import pytest

from astrolog.clock import night_date
from astrolog.db import idlist
from astrolog.spine import gear, group_store, identify_store, normalize_store, solve_store

# Il tetto imposto, e abbastanza id da passarlo due volte.
TETTO = 999
TANTI = list(range(1, TETTO * 2 + 2))


@pytest.fixture
def conn(conn):
    """La connessione della suite, col tetto dei segnaposto abbassato a `TETTO` su ogni sistema."""
    conn.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, TETTO)
    return conn


# Le grafie con cui si costruisce un segnaposto per riga. Sono quattro perche' nel repo ce
# n'erano **tre** diverse, e la prima versione di questa guardia ne cercava una sola: ha
# dichiarato sano `normalize_store`, che era rotto, e il difetto e' arrivato fino al revisore.
COSTRUISCE_SEGNAPOSTO = re.compile(
    r"""["']\?["']\s*\*|join\(\s*["']\?["']\s*for|\[\s*["']\?["']\s*\]\s*\*|["']\?,["']\s*\*"""
)


def test_past_the_ceiling_sqlite_refuses_the_query(conn):
    """Il guasto da cui parte tutto, rifatto qui invece che creduto: un segnaposto oltre il tetto
    e la query non si prepara nemmeno."""
    limite = conn.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
    assert limite == TETTO
    with pytest.raises(sqlite3.OperationalError, match="too many SQL variables"):
        conn.execute(
            f"SELECT 1 FROM frames WHERE id IN ({','.join('?' * (limite + 1))})",  # noqa: S608
            list(range(limite + 1)),
        )


@pytest.mark.parametrize(
    "chiamata",
    [
        pytest.param(lambda c: identify_store.detach(c, TANTI), id="identify.detach"),
        pytest.param(lambda c: group_store.detach(c, TANTI), id="group.detach"),
        pytest.param(lambda c: solve_store.first_per_order_key(c, TANTI), id="solve.primo"),
        pytest.param(lambda c: solve_store.newest_first(c, TANTI), id="solve.piu_recenti"),
        pytest.param(lambda c: normalize_store.pending_focals(c, TANTI), id="normalize.focali"),
        pytest.param(lambda c: gear._detach_rigs(c, TANTI), id="gear.corredi"),
    ],
)
def test_ids_past_the_ceiling_do_not_break_the_query(conn, chiamata):
    """Le sei query che portavano un segnaposto per riga. Col doppio del tetto devono passare:
    con un segnaposto per id, tutte e sei direbbero `too many SQL variables`."""
    chiamata(conn)


def test_the_list_keeps_group_by_and_order_by_honest(conn):
    """Perche' una tabella temporanea e non lotti da trentamila.

    Coi lotti queste due query **cambierebbero senso**: il `GROUP BY` tornerebbe il primo di
    ogni gruppo *per lotto* invece che sul totale, e l'`ORDER BY` ordinerebbe dentro il lotto."""
    for i, data in enumerate(("2024-05-03T21:00:00", "2024-05-03T22:00:00", None), start=1):
        conn.execute(
            "INSERT INTO frames(id, frame_hash, image_type, object_raw, date_obs, local_night,"
            " header_json, created_at) VALUES(?, ?, 'light', 'M 31', ?, ?, '[]', 'now')",
            (i, f"h{i}", data, night_date(data)),
        )
    assert solve_store.newest_first(conn, [1, 2, 3]) == [2, 1, 3]
    assert solve_store.first_per_order_key(conn, [1, 2, 3]) == [1, 3]


def test_the_list_behaves_like_the_placeholders_it_replaces(conn):
    """Deve comportarsi come la lista di segnaposto che sostituisce, o e' una regressione.

    Con una chiave primaria non era cosi': un id ripetuto sollevava (e prima non succedeva), e
    un `None` si prendeva un rowid -- cioe' `detach` avrebbe staccato l'oggetto della posa 1."""
    conn.execute(
        "INSERT INTO frames(id, frame_hash, image_type, header_json, created_at)"
        " VALUES(1, 'h1', 'light', '[]', 'now')"
    )
    conn.execute("UPDATE frames SET object_id = NULL WHERE id = 1")

    identify_store.detach(conn, [7, 7, 9])  # il doppio non solleva
    with idlist.holding(conn, [None]) as listed:
        assert conn.execute(f"SELECT id FROM frames WHERE id IN {listed}").fetchall() == []  # noqa: S608


def test_a_cursor_still_open_after_the_block_does_not_lose_rows(conn):
    """La tabella si svuota all'INGRESSO, non all'uscita: svuotandola all'uscita un cursore
    ancora aperto perdeva righe **in silenzio**, che e' il guasto peggiore che ci sia."""
    for i in (1, 2, 3):
        conn.execute(
            "INSERT INTO frames(id, frame_hash, image_type, header_json, created_at)"
            " VALUES(?, ?, 'light', '[]', 'now')",
            (i, f"h{i}"),
        )
    with idlist.holding(conn, [1, 2, 3]) as listed:
        cursore = conn.execute(f"SELECT id FROM frames WHERE id IN {listed}")  # noqa: S608
        assert cursore.fetchone()[0] == 1
    assert [r[0] for r in cursore] == [2, 3]


def test_a_failed_insert_does_not_look_like_an_open_list(conn):
    """Un errore a meta' inserimento lasciava righe che il giro dopo scambiava per un elenco
    aperto, e da li' in poi quella connessione diceva una bugia a ogni chiamata."""
    with pytest.raises(sqlite3.ProgrammingError), idlist.holding(conn, [1, object(), 3]):
        pass
    identify_store.detach(conn, [1])  # il giro dopo non trova un finto elenco aperto


def test_two_open_lists_on_one_connection_are_refused(conn):
    """Due elenchi aperti insieme si calpesterebbero, e la seconda query lavorerebbe sugli id
    della prima -- un risultato plausibile e sbagliato."""
    with idlist.holding(conn, [1, 2]):
        secondo = idlist.holding(conn, [3, 4])
        with pytest.raises(RuntimeError, match="gia' aperto"):
            secondo.__enter__()


def test_no_query_builds_one_placeholder_per_row(conn):
    """La regola con la sua macchina: nel prodotto non deve restare **nessuna** query che
    costruisce un segnaposto per riga, in nessuna delle grafie con cui la si scrive.

    La prima versione di questa guardia ne cercava una sola, e ha dichiarato sano un modulo che
    era rotto. Chi ne ha bisogno per un elenco davvero corto lo dichiara sulla riga con
    `segnaposto-ok` e la sua ragione, come `software-ok`."""
    radice = Path(__file__).resolve().parents[1] / "astrolog"
    colpevoli = [
        f"{f.relative_to(radice)}:{n}"
        for f in radice.rglob("*.py")
        for n, riga in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
        if COSTRUISCE_SEGNAPOSTO.search(riga) and "segnaposto-ok" not in riga
    ]
    assert colpevoli == [], "usare `db.idlist.holding`, o dichiarare perche' l'elenco e' corto"


@pytest.mark.parametrize(
    "grafia",
    [
        'marks = ",".join("?" * len(ids))',
        'marks = ", ".join("?" for _ in ids)',
        'marks = ",".join(["?"] * len(ids))',
        'marks = "?," * len(ids)',
    ],
)
def test_the_rule_catches_every_spelling(grafia):
    """La guardia qui sopra vale quanto l'elenco delle grafie che riconosce: qui si vede rossa
    su ognuna, compresa quella che le e' sfuggita la prima volta."""
    assert COSTRUISCE_SEGNAPOSTO.search(grafia), grafia
