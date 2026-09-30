"""Quanto costa una pagina dell'Archivio, contato in **passi** del motore di SQLite.

I passi non dipendono dalla macchina, e dicono la forma del costo: la pagina deve crescere con le
righe che mostra, non con le pose che le righe contengono, e un filtro non deve scorrere il
catalogo intero per ogni riga.
"""

from astrolog.db.connect import connect, create_database
from astrolog.spine import archive
from astrolog.spine import declarations as decl

ORA = "2026-09-23T12:00:00Z"


def _banco(conn, oggetti, pose_a_testa):
    """Oggetti senza catalogo, ognuno con le sue pose, nessun mosaico: il caso di quasi tutti."""
    conn.executemany(
        "INSERT INTO objects(id, identity_confidence, created_at) VALUES(?, 'high', ?)",
        [(i, ORA) for i in range(1, oggetti + 1)],
    )
    conn.executemany(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at, object_id,"
        " exposure_s) VALUES(?, 'light', '[]', ?, ?, 300.0)",
        [(f"h{i}-{j}", ORA, i) for i in range(1, oggetti + 1) for j in range(pose_a_testa)],
    )


def _mosaici(conn, quanti):
    """`quanti` mosaici confermati da due pannelli, ognuno di due oggetti NGC veri del catalogo e
    con la sua risposta: il costo dei mosaici si vede solo dove ce ne sono."""
    slug = [
        r[0]
        for r in conn.execute(
            "SELECT slug FROM catalog_names WHERE catalog = 'NGC' AND is_primary = 1"
            " ORDER BY slug LIMIT ?",
            (2 * quanti,),
        )
    ]
    for m in range(quanti):
        chiave = f"{quanti}-{m}"
        decl.write_declaration(
            conn, decl.MOSAIC, chiave, decl.MOSAIC_FIELD, f"catalog:{slug[2 * m]}"
        )
        mosaico_id = conn.execute(
            "INSERT INTO mosaics(key, ra_deg, dec_deg, proposed) VALUES(?, 10, 20, '')", (chiave,)
        ).lastrowid
        for pannello in (1, 2):
            pannello_id = conn.execute(
                "INSERT INTO panels(ra_deg, dec_deg, radius_deg, mosaic_id) VALUES(10, 20, 0.5, ?)",
                (mosaico_id,),
            ).lastrowid
            oggetto = conn.execute(
                "INSERT INTO objects(catalog_slug, identity_confidence, created_at)"
                " VALUES(?, 'high', ?)",
                (slug[2 * m + pannello - 1], ORA),
            ).lastrowid
            conn.execute(
                "INSERT INTO frames(frame_hash, image_type, header_json, created_at, object_id,"
                " exposure_s, mosaic_key, panel_id)"
                " VALUES(?, 'light', '[]', ?, ?, 300.0, ?, ?)",
                (f"{chiave}-{pannello}", ORA, oggetto, chiave, pannello_id),
            )


def _passi(conn, **chiesta):
    """I passi del motore per una pagina da una riga, cioe' quasi tutto il costo e' la conta."""
    contati = [0]

    def conta():
        contati[0] += 1
        return 0

    conn.set_progress_handler(conta, 100)
    try:
        archive.page(conn, limit=1, offset=0, **chiesta)
    finally:
        conn.set_progress_handler(None, 0)
    return contati[0]


def test_the_page_does_not_grow_with_the_poses_inside_its_rows(tmp_path):
    """Quattro volte le pose negli stessi oggetti: la pagina da una riga non deve costare quattro
    volte tanto. Se le ore si contassero per ogni riga -- anche per la sola conta -- si'. I due
    banchi nascono uguali, e differiscono solo nelle pose."""
    passi = {}
    for pose in (5, 20):
        create_database(tmp_path / f"{pose}.db")
        c = connect(tmp_path / f"{pose}.db")
        try:
            _banco(c, 200, pose)
            passi[pose] = _passi(c)
        finally:
            c.close()

    poche, tante = passi[5], passi[20]

    assert tante < 1.5 * poche, (poche, tante)


def test_a_catalogue_filter_does_not_walk_the_catalogue_for_every_row(archivio):
    """Stringere a un catalogo che l'archivio non ha costa quanto non stringere: la riga di un
    oggetto sa gia' il suo catalogo, e cercarlo fra i pannelli -- che una riga oggetto non ha --
    vorrebbe dire scorrere le voci di quel catalogo per ogni riga."""
    _banco(archivio, 200, 5)

    senza, stretto = _passi(archivio), _passi(archivio, catalog="NGC")

    assert stretto < 3 * senza, (senza, stretto)


def test_a_catalogue_filter_does_not_walk_the_catalogue_for_every_mosaic(archivio):
    """Lo stesso, con dei mosaici confermati: i pannelli di un mosaico si guardano partendo dalle
    sue pose, non dalle migliaia di voci del catalogo scelto. Il catalogo e' uno che i mosaici non
    hanno, e grande: con quello del mosaico la riga passa gia' dal suo bersaglio."""
    _banco(archivio, 200, 5)
    _mosaici(archivio, 30)

    senza, stretto = _passi(archivio), _passi(archivio, catalog="Abell")

    assert stretto < 3 * senza, (senza, stretto)


def test_the_mosaic_rows_grow_with_the_mosaics_not_with_their_square(archivio):
    """Quattro volte i mosaici: la pagina cresce con loro, non col loro quadrato -- che e' cio'
    che costa agganciare le risposte a ogni posa invece che a ogni mosaico."""
    _mosaici(archivio, 20)
    pochi = _passi(archivio)
    archivio.execute("DELETE FROM frames")
    archivio.execute("DELETE FROM declarations")
    archivio.execute("DELETE FROM objects")
    _mosaici(archivio, 80)

    tanti = _passi(archivio)

    assert tanti < 6 * pochi, (pochi, tanti)
