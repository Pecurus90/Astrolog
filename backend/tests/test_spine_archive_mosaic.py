"""L'Archivio raggruppa: un mosaico confermato e' **una riga**, e le ore restano quelle vere.

Un mosaico e' un insieme di POSE (`frames.mosaic_key`, scritto da `spine/mosaic.py`): le
sue pose stanno solo nella sua riga, quelle che un oggetto ha ripreso da solo restano sue. Il banco
riproduce il caso vero di IC 405, i cui quattro pannelli sono identificati come oggetti diversi di
quattro cataloghi diversi.
"""

import re

from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db import idlist
from astrolog.spine import archive, filters_used, objects
from astrolog.spine import declarations as decl
from group_bench import filtro as nasce_filtro
from test_spine_archive import oggetto, posa


def test_archive_panels_find_their_objects_through_the_mosaic_index(conn):
    """Gli oggetti dei pannelli di una pagina dell'Archivio si cercano dalle pose dei suoi mosaici,
    con l'indice sulla chiave del mosaico: senza, la pagina scorrerebbe tutte le pose
    dell'archivio. L'elenco vero, non una costante: con una costante SQLite sceglie un altro
    piano, e quello che si guarderebbe non sarebbe quello che gira."""
    with idlist.holding(conn, ["mosaico"]) as elencate:
        query = archive._OGGETTI_DEI_PANNELLI.format(listed=elencate)
        piano = [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query)]
    pose = [p for p in piano if re.match(r"(SCAN|SEARCH) f\b", p)]
    assert pose and all(re.search(r"INDEX frames_mosaic\b", p) for p in pose), piano


CHIAVE = "impronta-della-prima-posa"  # la chiave di un mosaico: l'impronta di una sua posa


def nomi(righe):
    return [objects.display_name(r) for r in righe]


def mosaico(conn, pose, bersaglio="catalog:ic-405"):
    """Il mosaico confermato su quelle pose, come lo lascia chi risponde: la dichiarazione e la
    chiave scritta sulle pose. Chi la scrive ha le sue prove; qui si guarda chi la legge."""
    decl.write_declaration(conn, decl.MOSAIC, CHIAVE, decl.MOSAIC_FIELD, bersaglio)
    mosaico_id = conn.execute(
        "INSERT INTO mosaics(key, ra_deg, dec_deg, proposed) VALUES(?, 80, 34, 'IC 405')", (CHIAVE,)
    ).lastrowid
    # qui ogni posa e' un pannello suo, con un centro suo e diverso da quello del mosaico: chi
    # legge il centro del mosaico, o scambia due pannelli, cade
    for i, p in enumerate(pose, start=1):
        pannello = conn.execute(
            "INSERT INTO panels(rig_id, ra_deg, dec_deg, radius_deg, mosaic_id)"
            " VALUES(NULL, ?, ?, 0.5, ?)",
            (80 + i, 34 - i, mosaico_id),
        ).lastrowid
        conn.execute(
            "UPDATE frames SET mosaic_key = ?, panel_id = ? WHERE id = ?", (CHIAVE, pannello, p)
        )


def banco(conn):
    """I quattro pannelli di IC 405 -- `ic-405`, `lbn-796`, `ldn-1516`, `sh2-230` -- e IC 405
    ripreso anche **da solo** un'altra sera, piu' M 31 che col mosaico non c'entra."""
    ha, oiii = nasce_filtro(conn, "Ha", "ha"), nasce_filtro(conn, "OIII", "oiii")
    pannelli = {n: oggetto(conn, n, n.lower().replace(" ", "-")) for n in
                ("IC 405", "LBN 796", "LDN 1516", "Sh2 230")}  # fmt: skip
    # IC 405 dentro il mosaico in Ha e da solo in OIII: se la sua riga guardasse l'oggetto intero,
    # prenderebbe anche l'Ha dei pannelli, e le prove dei filtri non distinguerebbero le due regole
    dentro = [
        posa(conn, pannelli["IC 405"], filtro=ha),
        posa(conn, pannelli["LBN 796"], filtro=oiii),
    ]
    dentro += [posa(conn, pannelli[n], filtro=ha) for n in ("LDN 1516", "Sh2 230")]
    da_solo = posa(conn, pannelli["IC 405"], filtro=oiii, secondi=600.0)
    m31 = posa(conn, oggetto(conn, "M 31", "m-31"))
    mosaico(conn, dentro)
    return dentro, da_solo, m31


def test_a_confirmed_mosaic_is_one_row_with_the_hours_of_all_its_panels(archivio):
    """**L'obiettivo della fetta.** Il mosaico si chiama come l'hai detto, IC 405, e porta i frame
    e le ore di tutti e quattro i pannelli. I pannelli che vivono solo li' dentro non hanno una
    riga loro: le loro ore stanno nel mosaico, non in due posti."""
    banco(archivio)

    righe, quanti = archive.page(archivio, limit=50, offset=0)

    assert nomi(righe) == ["IC 405", "IC 405", "M 31"]
    riga = next(r for r in righe if r["mosaic_key"])
    assert (riga["frames"], riga["integration_s"]) == (4, 4 * 300.0)
    assert quanti == 3


def test_an_object_shot_inside_and_outside_a_mosaic_keeps_its_own_poses(archivio):
    """IC 405 ripreso da solo resta una riga sua, con le **sole** pose fuori dal mosaico. Nessuna
    posa contata due volte, nessuna persa: la somma delle righe e' la somma dell'archivio."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0)

    da_solo = next(r for r in righe if r["id"] and r["catalog_slug"] == "ic-405")
    assert (da_solo["frames"], da_solo["integration_s"]) == (1, 600.0)
    totale = archivio.execute("SELECT COUNT(*), SUM(exposure_s) FROM frames").fetchone()
    assert (sum(r["frames"] for r in righe), sum(r["integration_s"] for r in righe)) == tuple(
        totale
    )


def test_a_filter_of_the_bar_lets_the_mosaic_through_if_one_of_its_poses_passes(archivio):
    """I quattro pannelli portano quattro cataloghi: stringendo a `LBN` il mosaico deve restare, e
    **intero** -- con un filtro sulle pose ne resterebbe un quarto, e la riga direbbe un quarto
    delle ore. Lo stesso per chi cerca `LDN 1516`: chi cerca un pannello lo trova."""
    banco(archivio)

    per_catalogo, _ = archive.page(archivio, limit=50, offset=0, catalog="LBN")
    cercando, _ = archive.page(archivio, limit=50, offset=0, q="ldn1516")

    for righe in (per_catalogo, cercando):
        assert [(r["mosaic_key"], r["frames"]) for r in righe] == [(CHIAVE, 4)]


def test_the_filter_used_is_asked_of_the_poses_of_the_row(archivio):
    """ "Cosa ho ripreso in Ha": il mosaico si', perche' tre pannelli lo sono; IC 405 da solo no,
    anche se l'oggetto IC 405 ha pose nel mosaico: quelle non stanno nella sua riga."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0, filter_name="Ha")

    assert [r["mosaic_key"] for r in righe] == [CHIAVE]


def test_the_pills_of_a_row_are_the_filters_of_its_own_poses(archivio):
    """Le pastiglie dicono con che filtri hai ripreso **quella riga**: il mosaico ha Ha e OIII, IC
    405 da solo solo OIII."""
    banco(archivio)
    righe, _ = archive.page(archivio, limit=50, offset=0)
    da_solo = next(r["id"] for r in righe if r["id"] and r["catalog_slug"] == "ic-405")

    suoi = filters_used.of(archivio, "object", [da_solo], alone=True)
    del_mosaico = filters_used.of(archivio, "mosaic", [CHIAVE])

    assert [f["name"] for f in suoi[da_solo]] == ["OIII"]
    assert sorted(f["name"] for f in del_mosaico[CHIAVE]) == ["Ha", "OIII"]


def _dalla_rotta(archivio, db_path_col_catalogo):
    """Le righe come le manda la rotta, per nome: la rotta e' dove le pastiglie si attaccano."""
    archivio.commit()
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        righe = c.get("/api/v1/archive").json()["items"]
    return {(r["name"], r["key"] == CHIAVE): r for r in righe}


def test_the_route_gives_every_row_the_pills_of_its_own_poses(archivio, db_path_col_catalogo):
    """Dalla rotta: il mosaico porta Ha e OIII, IC 405 ripreso da solo solo OIII. Le pastiglie di
    un oggetto chieste sull'oggetto intero gli darebbero anche l'Ha, che e' dei pannelli."""
    banco(archivio)

    righe = _dalla_rotta(archivio, db_path_col_catalogo)

    assert sorted(f["name"] for f in righe[("IC 405", True)]["filters"]) == ["Ha", "OIII"]
    assert [f["name"] for f in righe[("IC 405", False)]["filters"]] == ["OIII"]


def test_a_mosaic_pose_without_a_time_is_counted_apart(archivio, db_path_col_catalogo):
    """Una posa del mosaico che non dice quanto e' durata non vale zero ore: si conta a parte,
    come in ogni altra riga."""
    dentro = [posa(archivio, oggetto(archivio, "IC 405", "ic-405"), secondi=None)]
    dentro.append(posa(archivio, oggetto(archivio, "LBN 796", "lbn-796")))
    mosaico(archivio, dentro)

    riga = _dalla_rotta(archivio, db_path_col_catalogo)[("IC 405", True)]

    assert (riga["frames"], riga["integration_s"], riga["untimed"]) == (2, 300.0, 1)


def test_a_mosaic_row_says_how_many_panels_it_has(archivio):
    """La riga del mosaico porta quanti pannelli ha, contati da cio' che e' scritto sulle pose; la
    riga di un oggetto non ne ha."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0)

    assert {(r["mosaic_key"] is not None, r["panels"]) for r in righe} == {(True, 4), (False, None)}


def _nel_pannello_di(conn, compagna, **kw):
    """Una posa in piu' nello stesso pannello di `compagna`, con l'oggetto che le si da'."""
    nuova = posa(conn, kw.pop("oggetto_id", None), **kw)
    conn.execute(
        "UPDATE frames SET (mosaic_key, panel_id) = (SELECT mosaic_key, panel_id FROM frames"
        " WHERE id = ?) WHERE id = ?",
        (compagna, nuova),
    )
    return nuova


def test_every_panel_of_a_mosaic_says_its_object_its_frames_and_its_hours(archivio):
    """**L'obiettivo della fetta 2.** La carta del mosaico elenca i suoi pannelli, ognuno col suo
    oggetto, le sue pose e le sue ore, dal pannello a cui e' andato piu' tempo. IC 405 ripreso da
    solo un'altra sera non entra nel suo pannello: quella posa non e' del mosaico."""
    dentro, _, _ = banco(archivio)
    sh2 = archivio.execute("SELECT object_id FROM frames WHERE id = ?", (dentro[3],)).fetchone()[0]
    _nel_pannello_di(archivio, dentro[3], oggetto_id=sh2, secondi=600.0)

    pannelli = archive.panels(archivio, [CHIAVE])[CHIAVE]

    campi = ("object", "frames", "integration_s", "ra_deg", "dec_deg")
    assert [tuple(p[c] for c in campi) for p in pannelli] == [
        ("Sh2 230", 2, 900.0, 84.0, 30.0),
        ("IC 405", 1, 300.0, 81.0, 33.0),
        ("LBN 796", 1, 300.0, 82.0, 32.0),
        ("LDN 1516", 1, 300.0, 83.0, 31.0),
    ]


def test_a_panel_counts_like_every_row_copies_out_and_untimed_apart(archivio):
    """Il pannello conta come il resto dell'Archivio: la copia riscritta non raddoppia le ore, e una
    posa che non dice quanto e' durata si conta a parte invece di valere zero. E la copia non
    presta il suo oggetto al nome del pannello."""
    dentro, _, _ = banco(archivio)
    ic405 = archivio.execute("SELECT object_id FROM frames WHERE id = ?", (dentro[0],)).fetchone()
    _nel_pannello_di(archivio, dentro[0], oggetto_id=ic405[0], secondi=None)
    m31 = archivio.execute("SELECT id FROM objects WHERE catalog_slug = 'm-31'").fetchone()[0]
    copia = _nel_pannello_di(archivio, dentro[0], oggetto_id=m31)
    archivio.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (dentro[0], copia))

    primo = archive.panels(archivio, [CHIAVE])[CHIAVE][0]

    assert (primo["object"], primo["frames"], primo["integration_s"], primo["untimed"]) == (
        "IC 405",
        2,
        300.0,
        1,
    )


def test_a_panel_whose_poses_found_no_object_says_so_with_nothing(archivio):
    """Un pannello le cui pose non sono legate a un oggetto non ha un nome da dire: nullo, non una
    stringa vuota che a schermo sarebbe una riga senza nome. Due oggetti nello stesso pannello si
    dicono tutti e due, e un oggetto fuori catalogo col suo nome."""
    dentro, _, _ = banco(archivio)
    archivio.execute("UPDATE frames SET object_id = NULL WHERE id = ?", (dentro[1],))
    m31 = archivio.execute("SELECT id FROM objects WHERE catalog_slug = 'm-31'").fetchone()[0]
    _nel_pannello_di(archivio, dentro[2], oggetto_id=m31)
    libero = oggetto(archivio, "La mia nebulosa")
    archivio.execute("UPDATE frames SET object_id = ? WHERE id = ?", (libero, dentro[3]))

    detti = {p["ra_deg"]: p["object"] for p in archive.panels(archivio, [CHIAVE])[CHIAVE]}

    assert detti == {81.0: "IC 405", 82.0: None, 83.0: "LDN 1516, M 31", 84.0: "La mia nebulosa"}


def test_all_the_panels_of_a_page_come_in_two_questions(archivio):
    """Tutti i pannelli della pagina in **due domande**, quanti che siano i mosaici; e nessuna per
    la pagina di chi non ne ha. Le altre istruzioni sono l'elenco delle chiavi, non domande."""
    banco(archivio)
    domande = []
    archivio.set_trace_callback(lambda s: s.lstrip().startswith("SELECT") and domande.append(s))

    archive.panels(archivio, [])
    nessuna = len(domande)
    archive.panels(archivio, [CHIAVE, "un-altro", "un-terzo"])

    assert (nessuna, len(domande)) == (0, 2)


def test_the_route_gives_a_mosaic_its_panels_and_an_object_none(archivio, db_path_col_catalogo):
    """Dalla rotta: il mosaico porta i suoi quattro pannelli, la riga di un oggetto nessuno."""
    banco(archivio)

    righe = _dalla_rotta(archivio, db_path_col_catalogo)

    assert sorted(p["object"] for p in righe[("IC 405", True)]["panel_list"]) == [
        "IC 405",
        "LBN 796",
        "LDN 1516",
        "Sh2 230",
    ]
    assert righe[("IC 405", False)]["panel_list"] == []


def test_you_can_narrow_down_to_the_mosaics(archivio):
    """ "Solo i mosaici" tiene le righe dei mosaici, e si somma agli altri filtri."""
    banco(archivio)

    solo, quanti = archive.page(archivio, limit=50, offset=0, mosaic=True)
    nessuno, _ = archive.page(archivio, limit=50, offset=0, mosaic=True, catalog="M")

    assert ([r["mosaic_key"] for r in solo], quanti) == ([CHIAVE], 1)
    assert nessuno == []


def test_the_count_says_how_many_objects_and_how_many_mosaics(archivio):
    """La conta non chiama "oggetto" un mosaico: IC 405 da solo e M 31 sono due oggetti, il
    mosaico e' un mosaico. Con un filtro acceso conta cio' che passa."""
    banco(archivio)

    assert archive.found(archivio) == {"objects": 2, "mosaics": 1}
    assert archive.found(archivio, catalog="M") == {"objects": 1, "mosaics": 0}


def test_the_mosaic_choice_is_offered_only_to_who_has_a_mosaic(archivio):
    """La tendina dei mosaici c'e' solo se l'archivio ne ha uno confermato: a chi non ne ha
    prometterebbe qualcosa che non puo' fare."""
    posa(archivio, oggetto(archivio, "M 42", "m-42"))
    assert archive.choices(archivio)["mosaics"] is False
    banco(archivio)
    assert archive.choices(archivio)["mosaics"] is True


def test_the_pages_count_rows_not_objects(archivio):
    """Si impaginano **righe**: cinque oggetti in tre righe sono tre righe, e la seconda pagina
    comincia dalla seconda riga, non dal secondo oggetto."""
    banco(archivio)

    prima, quanti = archive.page(archivio, limit=1, offset=0)
    resto, _ = archive.page(archivio, limit=10, offset=1)

    assert quanti == 3
    assert len(prima) + len(resto) == 3


def test_a_mosaic_named_with_a_free_name_is_found_by_that_name(archivio):
    """Il nome l'hai detto tu, anche fuori catalogo: il mosaico si chiama cosi', si trova cosi', e
    va in fondo come ogni cosa senza catalogo."""
    dentro = [posa(archivio, oggetto(archivio, "IC 405", "ic-405"))]
    mosaico(archivio, dentro, bersaglio="name:La regione dell'Auriga")
    posa(archivio, oggetto(archivio, "M 31", "m-31"))

    tutte, _ = archive.page(archivio, limit=50, offset=0)
    trovate, _ = archive.page(archivio, limit=50, offset=0, q="auriga")

    assert nomi(tutte) == ["M 31", "La regione dell'Auriga"]
    assert nomi(trovate) == ["La regione dell'Auriga"]


def test_without_a_confirmed_mosaic_nothing_changes(archivio):
    """Un mosaico proposto e non confermato non rimescola niente (Marco, 22/9/2026): ogni pannello
    resta la riga del suo oggetto."""
    for n in ("IC 405", "LBN 796"):
        posa(archivio, oggetto(archivio, n, n.lower().replace(" ", "-")))

    righe, _ = archive.page(archivio, limit=50, offset=0)

    assert nomi(righe) == ["IC 405", "LBN 796"]
