"""Da confermare legge l'archivio con un numero fisso di query, quanti che siano gli elementi in
pagina (passo 6.20): una lettura per elemento faceva 64 query con 2 elementi per sezione e 103
con 5.

L'archivio ha `k` elementi per sezione: filtri dalla banda ignota, schede dell'attrezzatura,
oggetti, gruppi senza nome, cartelle senza data e senza tipo, coordinate senza sito; e ogni
domanda che ha una risposta la porta, perche' anche leggere la risposta costa.
"""

from astrolog.api import review as review_api
from astrolog.db.connect import connect, create_database
from astrolog.spine import coordinates, declarations, signature, signature_page, undated, unnamed
from astrolog.spine.group import GroupReason, group_frames
from conftest import populate, write_fits
from group_bench import ROMA, luogo

NOW = "2026-01-01T00:00:00Z"


def _posa(path, i, **card):
    header = {
        "IMAGETYP": "LIGHT",
        "INSTRUME": f"Camera {i}",
        "TELESCOP": f"Scope {i}",
        "FOCALLEN": 400.0 + 100 * i,
        "XPIXSZ": 3.76,
        "EXPTIME": 300.0,
        "FILTER": f"Q{i}",
        "OBJECT": f"Oggetto {i}",
        "DATE-OBS": f"2024-0{i + 1}-10T21:00:00",
        "SITELAT": 40.0 + i,
        "SITELONG": 5.0 + i,
        **card,
    }
    write_fits(path, {k: v for k, v in header.items() if v is not None})


def _archivio(db_path, root, k):
    for i in range(k):
        _posa(root / f"gear{i}" / "a.fits", i, INSTRUME=None)
        _posa(root / f"gear{i}" / "b.fits", i, TELESCOP=None)
        _posa(root / f"unnamed{i}" / "a.fits", i, OBJECT=None)
        _posa(root / f"nodate{i}" / "a.fits", i, **{"DATE-OBS": None})
        _posa(root / f"typeless{i}" / "a.fits", i, IMAGETYP=None)
    populate(db_path, root)
    conn = connect(db_path)
    try:
        luogo(conn, ROMA)
        list(group_frames(conn))
        _rispondi(conn)
        conn.commit()
    finally:
        conn.close()


def _rispondi(conn):
    """Ogni domanda con una risposta: la pagina legge anche quella."""
    for card in signature_page.by_signature(conn):
        signature.declare(conn, card["key"], signature.Answer(camera="Camera X"), NOW)
    for g in unnamed.by_group(conn):
        unnamed.declare(conn, g.key, name="Qualcosa", now=NOW)
    for g in undated.by_folder(conn):
        undated.declare(conn, g["key"], "2024-01-10", NOW)
    for spot in coordinates.unclear_coordinates(conn, GroupReason.SITE_UNCLEAR):
        declarations.declare_coordinates(conn, spot["key"], ROMA[0], NOW)


def _pagina(tmp_path, k):
    """La pagina e quante query l'hanno letta."""
    db_path = tmp_path / f"k{k}.db"
    create_database(db_path)
    _archivio(db_path, tmp_path / f"lib{k}", k)
    conn = connect(db_path)
    lette = []
    try:
        conn.set_trace_callback(lette.append)
        page = review_api.review(conn)
    finally:
        conn.set_trace_callback(None)
        conn.close()
    sezioni = (page.filters, page.gear, page.objects, page.unclear, page.undated, page.typeless)
    return len(lette), [len(s) for s in sezioni]


def test_the_page_reads_the_same_number_of_queries_whatever_it_holds(tmp_path):
    poche, sezioni_poche = _pagina(tmp_path, 2)
    tante, sezioni_tante = _pagina(tmp_path, 5)
    # ogni sezione cresce davvero, o il conto uguale non direbbe niente
    assert all(t > p > 0 for p, t in zip(sezioni_poche, sezioni_tante, strict=True))
    assert tante == poche
