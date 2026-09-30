"""Il catalogo nel database: cercarlo per nome e per pezzo di cielo.

Sono le due domande su cui `identify` sara' costruito. Qui si provano su un catalogo finto,
piccolo e scritto a mano: quello vero e' un dato di 22.080 voci, e un test che dipendesse da
lui si romperebbe alla prossima ricostruzione senza che nessuno abbia sbagliato niente. Le
prove che DEVONO vedere il catalogo vero -- che il file impacchettato sia leggibile, e che
ogni designazione si sappia leggere -- stanno in fondo e in `test_designation.py`.
"""

import json
import math
import sqlite3

import pytest

from astrolog.catalog import bundle, load, lookup

# Catturato all'import, PRIMA del recinto della suite: le ultime due prove hanno bisogno del
# file impacchettato vero.
real_bundle = bundle.path

# Cinque voci vere, scelte perche' ognuna prova qualcosa: M 31 ha due sigle, M 110 le sta
# accanto (39' piu' in la'), NGC 2237 e' la Rosetta con quattro sigle, e le ultime due stanno
# dall'altra parte del cielo -- una proprio a cavallo dello zero dell'ascensione retta.
VOCI = [
    {"slug": "m-31", "name": "M 31", "common_name": "Andromeda Galaxy",
     "ra": 10.6847, "dec": 41.269, "constellation": "And", "type_code": "GALAXY",
     "kind": "galaxy", "size_major_arcmin": 199.5, "magnitude": 3.44, "magnitude_band": "V",
     "n": [["M", "31"], ["NGC", "224"]], "src": {"_": "openngc"}},
    {"slug": "m-110", "name": "M 110", "ra": 10.0919, "dec": 41.685, "constellation": "And",
     "type_code": "GALAXY", "kind": "galaxy", "size_major_arcmin": 21.9, "magnitude": 8.07,
     "magnitude_band": "V", "n": [["M", "110"], ["NGC", "205"]]},
    {"slug": "ngc-2237", "name": "NGC 2237", "common_name": "Rosette Nebula",
     "ra": 97.9704, "dec": 4.9503, "constellation": "Mon", "type_code": "NEBULA",
     "kind": "nebula", "k": ["emission"], "size_major_arcmin": 80.0,
     "n": [["NGC", "2237"], ["NGC", "2238"], ["C", "49"]]},
    {"slug": "ldn-1", "name": "LDN 1", "ra": 0.5, "dec": 60.0, "constellation": "Cas",
     "type_code": "DARK_NEBULA", "kind": "nebula", "n": [["LDN", "1"]]},
    {"slug": "ldn-2", "name": "LDN 2", "ra": 359.5, "dec": 60.0, "constellation": "Cas",
     "type_code": "DARK_NEBULA", "kind": "nebula", "n": [["LDN", "2"]]},
]  # fmt: skip


def scrivi(percorso, versione, voci):
    percorso.write_text(json.dumps({"version": versione, "objects": voci}), encoding="utf-8")
    return percorso


@pytest.fixture
def catalogo(conn, tmp_path):
    """Un catalogo finto, caricato nel database di prova."""
    load.load_catalog(conn, scrivi(tmp_path / "catalogo-prova-1.json", "prova-1", VOCI))
    return conn


# --- che oggetto e' questa sigla? -----------------------------------------------------------


def test_a_designation_finds_its_object(catalogo):
    voce = lookup.by_designation(catalogo, "M 31")
    assert voce["slug"] == "m-31" and voce["common_name"] == "Andromeda Galaxy"


def test_different_designations_of_one_object_land_on_the_same_entry(catalogo):
    """E' il motivo per cui le ore non si sparpagliano: qualunque cosa scriva il software di
    ripresa -- `NGC 2237`, `NGC 2238`, `C 49` -- e' la stessa Rosetta."""
    slug = {lookup.by_designation(catalogo, s)["slug"] for s in ("NGC 2237", "NGC 2238", "C 49")}
    assert slug == {"ngc-2237"}
    m31 = lookup.by_designation(catalogo, "M 31")
    assert m31["slug"] == lookup.by_designation(catalogo, "NGC 224")["slug"]


def test_the_spelling_of_a_designation_does_not_matter(catalogo):
    """Negli header un oggetto e' scritto in mille modi. Sono tutti lo stesso oggetto, e
    nessuno di questi e' piu' giusto degli altri. Il giro completo sulle ventiquattromila
    designazioni vere sta in `test_designation.py`."""
    for scritto in ("M 31", "M31", "m31", "M  31", " M 31 ", "m 31", "M 031", "Messier 31"):
        assert lookup.by_designation(catalogo, scritto)["slug"] == "m-31", scritto


def test_a_designation_that_does_not_exist_is_not_an_error(catalogo):
    """Un nome che il catalogo non conosce e' la norma, non un guasto: l'utente fotografa
    anche cose che non hanno una voce."""
    for niente in ("NGC 99999", "", None, "roba a caso"):
        assert lookup.by_designation(catalogo, niente) is None, niente


def test_the_search_by_designation_uses_the_index(catalogo):
    """La chiave normalizzata sta in colonna proprio per questo: `identify` fara' questa
    ricerca una volta per posa, e su ventiquattromila sigle una scansione intera e' il
    doppio del lavoro di tutto il resto messo insieme."""
    piano = "\n".join(
        r[3]
        for r in catalogo.execute(
            "EXPLAIN QUERY PLAN SELECT e.slug FROM catalog_entries e"
            " JOIN catalog_names n ON n.slug = e.slug WHERE n.key = ?",
            ("M|31",),
        )
    )
    assert "catalog_names_key" in piano, piano


# --- cosa c'e' in questo pezzo di cielo? ----------------------------------------------------


def test_the_cone_finds_what_is_inside_and_leaves_out_the_rest(catalogo):
    """E' la domanda su cui `identify` e' costruito: dato il cielo misurato di una posa, cosa
    c'e' li'. M 110 sta a 39 primi da M 31: dentro un grado, fuori da mezzo."""
    dentro = {v["slug"] for v in lookup.in_cone(catalogo, 10.6847, 41.269, 1.0)}
    assert dentro == {"m-31", "m-110"}

    stretto = {v["slug"] for v in lookup.in_cone(catalogo, 10.6847, 41.269, 0.5)}
    assert stretto == {"m-31"}

    assert lookup.in_cone(catalogo, 97.97, 4.95, 0.5)[0]["slug"] == "ngc-2237"


def test_the_cone_says_how_far_each_one_is(catalogo):
    """Chi sceglie il soggetto ha bisogno dello scarto, non solo dell'elenco: e' meta' del
    criterio (l'altra meta' e' quanto e' esteso)."""
    trovati = {v["slug"]: v for v in lookup.in_cone(catalogo, 10.6847, 41.269, 1.0)}
    assert trovati["m-31"]["sep_deg"] == pytest.approx(0.0, abs=0.001)
    assert trovati["m-110"]["sep_deg"] == pytest.approx(0.65, abs=0.05)


def test_the_cone_is_sorted_by_nearest_first(catalogo):
    trovati = lookup.in_cone(catalogo, 10.6847, 41.269, 2.0)
    assert [v["sep_deg"] for v in trovati] == sorted(v["sep_deg"] for v in trovati)


def test_the_cone_survives_the_zero_of_right_ascension(catalogo):
    """A 0 gradi l'ascensione retta torna a 360: due oggetti a mezzo grado l'uno dall'altro
    hanno coordinate 0,5 e 359,5. Un filtro sulle coordinate sferiche li perderebbe; il
    versore no, ed e' il motivo per cui esiste."""
    trovati = {v["slug"] for v in lookup.in_cone(catalogo, 0.0, 60.0, 1.0)}
    assert trovati == {"ldn-1", "ldn-2"}


def test_a_wide_cone_still_catches_what_sits_on_its_edge(catalogo):
    """Il riquadro che sgrossa e' largo **la corda**, `2 sin(r/2)`, non il seno dell'angolo:
    su un cono largo il seno e' piu' corto della corda e taglierebbe via proprio il bordo,
    che e' dove stanno gli oggetti piu' interessanti di una ricerca larga."""
    lontani = {v["slug"] for v in lookup.in_cone(catalogo, 10.6847, 41.269, 100.0)}
    assert {"ldn-1", "ldn-2"} <= lontani  # a 40 gradi da M 31: dentro un cono di 100

    tutto = lookup.in_cone(catalogo, 10.6847, 41.269, 180.0)
    assert len(tutto) == len(VOCI)  # mezzo cielo per lato: c'e' dentro tutto


def test_a_radius_bigger_than_the_sky_is_the_whole_sky(catalogo):
    """Oltre i 180 gradi il coseno ricomincia a salire, e un cono di 500 gradi tornerebbe
    **vuoto** invece che tutto: il limite si mette una volta in cima, prima che il raggio
    entri sia nella corda sia nel coseno. Chi chiama arriva da una posa e puo' avere un
    numero qualunque."""
    for esagerato in (181.0, 500.0, 3600.0):
        assert len(lookup.in_cone(catalogo, 10.6847, 41.269, esagerato)) == len(VOCI), esagerato
    # e un raggio negativo vale zero: resta solo cio' che sta esattamente li'
    assert lookup.in_cone(catalogo, 10.6847, 41.269, -1.0) == lookup.in_cone(
        catalogo, 10.6847, 41.269, 0.0
    )
    assert lookup.in_cone(catalogo, 200.0, -30.0, -1.0) == []


def test_the_cone_uses_the_index_on_the_unit_vector(catalogo):
    """Il versore esiste **per questo**: senza l'indice sui tre assi la ricerca legge tutte e
    22.080 le voci, e `identify` la fara' una volta per posa. La misura non basta a
    accorgersene -- sul catalogo vero una scansione intera e' 1,8 ms, ben sotto il tetto del
    test `lento` -- quindi la guardia va messa sul piano della query, non sul cronometro."""
    piano = "\n".join(
        r[3]
        for r in catalogo.execute(
            "EXPLAIN QUERY PLAN SELECT slug FROM catalog_entries"
            " WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?",
            (0.0, 0.1, 0.0, 0.1, 0.0, 0.1),
        )
    )
    assert "catalog_entries_x" in piano, piano


def test_a_cone_with_nothing_in_it_is_an_empty_list(catalogo):
    assert lookup.in_cone(catalogo, 180.0, -70.0, 1.0) == []


# --- il caricamento --------------------------------------------------------------------------


def test_the_loaded_catalogue_says_its_version(catalogo):
    assert load.loaded_version(catalogo) == "prova-1"


def test_reloading_the_same_version_does_nothing(conn, tmp_path):
    """Il caricamento e' derivato e si rifa', ma non a ogni avvio: 22.080 voci sono un lavoro
    che non ha senso ripetere se il file non e' cambiato."""
    percorso = scrivi(tmp_path / "catalogo-prova-1.json", "prova-1", VOCI)
    assert load.load_catalog(conn, percorso) == len(VOCI)
    assert load.load_catalog(conn, percorso) == 0  # gia' caricato: non si tocca niente
    assert conn.execute("SELECT COUNT(*) FROM catalog_entries").fetchone()[0] == len(VOCI)


def test_a_new_version_rebuilds_the_catalogue_from_scratch(conn, tmp_path):
    """Un aggiornamento dell'app porta un catalogo nuovo: le voci vecchie se ne vanno, non si
    sommano. Le voci sono un dato derivato, non una cronologia."""
    load.load_catalog(conn, scrivi(tmp_path / "catalogo-prova-1.json", "prova-1", VOCI))

    secondo = scrivi(tmp_path / "catalogo-prova-2.json", "prova-2", VOCI[:2])
    assert load.load_catalog(conn, secondo) == 2
    assert conn.execute("SELECT COUNT(*) FROM catalog_entries").fetchone()[0] == 2
    assert lookup.by_designation(conn, "NGC 2237") is None
    assert load.loaded_version(conn) == "prova-2"


def test_a_load_that_fails_halfway_leaves_the_old_catalogue_whole(conn, tmp_path):
    """Il caricamento cancella prima di scrivere: senza transazione, un file nuovo rotto a
    meta' lascerebbe l'archivio **senza catalogo**, e l'utente lo scoprirebbe solo quando
    `identify` smette di riconoscere. O entra tutto, o non entra niente."""
    load.load_catalog(conn, scrivi(tmp_path / "catalogo-prova-1.json", "prova-1", VOCI))

    doppio = [dict(VOCI[0]), dict(VOCI[0])]  # due voci con lo stesso slug: la chiave si oppone
    rotto = scrivi(tmp_path / "catalogo-prova-2.json", "prova-2", doppio)
    with pytest.raises(sqlite3.Error):
        load.load_catalog(conn, rotto)

    assert conn.execute("SELECT COUNT(*) FROM catalog_entries").fetchone()[0] == len(VOCI)
    assert load.loaded_version(conn) == "prova-1"
    assert lookup.by_designation(conn, "NGC 2237")["slug"] == "ngc-2237"


def test_a_catalogue_that_does_not_load_does_not_stop_the_app(conn, tmp_path):
    """A mani vuote l'app funziona lo stesso: cataloga, cerca, mostra le ore. Un catalogo che
    manca o e' rotto e' un guasto da dire, non un avvio che fallisce."""
    for rotto in (tmp_path / "non-esiste.json", tmp_path / "vuoto.json"):
        if rotto.name == "vuoto.json":
            rotto.write_text("{ questo non e' json", encoding="utf-8")
        assert load.load_catalog(conn, rotto) == 0
    assert load.loaded_version(conn) is None
    assert lookup.by_designation(conn, "M 31") is None  # e cercare non esplode


def test_a_catalogue_code_nobody_can_read_is_said_out_loud(conn, tmp_path, caplog):
    """Una sigla con un codice che il lettore non conosce entra nel database ma non si potra'
    mai cercare: e' il guasto delle 313 Sharpless, e senza avviso il prossimo catalogo lo
    rifarebbe in silenzio. La voce resta -- vale anche senza quella sigla -- ma si sa."""
    strano = dict(VOCI[0], slug="cr-399", n=[["Cr", "399"]])
    with caplog.at_level("WARNING"):
        load.load_catalog(conn, scrivi(tmp_path / "catalogo-x.json", "x", [strano]))
    assert "Cr" in caplog.text and "non si sanno leggere" in caplog.text
    assert conn.execute("SELECT COUNT(*) FROM catalog_entries").fetchone()[0] == 1
    assert lookup.by_designation(conn, "Cr 399") is None


def test_a_designation_claimed_twice_does_not_leave_an_entry_nameless(conn, tmp_path, caplog):
    """Due voci sulla stessa sigla sono un difetto del file, non dell'app: la prima vince e si
    dice. Ma la **principale** si sceglie dopo lo scarto: se la si scegliesse prima, la voce
    che perde la sua prima sigla resterebbe senza principale, cioe' senza niente da mostrare
    quando non ha un nome comune -- e nessun vincolo del database se ne accorgerebbe."""
    primo = dict(VOCI[0], slug="uno", n=[["NGC", "1"]])
    secondo = dict(VOCI[1], slug="due", n=[["NGC", "1"], ["M", "9"]])
    with caplog.at_level("WARNING"):
        load.load_catalog(conn, scrivi(tmp_path / "catalogo-x.json", "x", [primo, secondo]))
    assert "rivendicate da piu' voci" in caplog.text

    assert lookup.by_designation(conn, "NGC 1")["slug"] == "uno"
    assert lookup.by_designation(conn, "M 9")["slug"] == "due"
    senza_principale = [
        slug
        for (slug,) in conn.execute(
            "SELECT e.slug FROM catalog_entries e WHERE NOT EXISTS (SELECT 1 FROM catalog_names n"
            " WHERE n.slug = e.slug AND n.is_primary = 1)"
        )
    ]
    assert senza_principale == []


def test_an_entry_has_exactly_one_primary_designation(catalogo):
    """La prima sigla e' quella che si mostra quando l'oggetto non ha un nome comune."""
    righe = [
        tuple(r)
        for r in catalogo.execute(
            "SELECT catalog, designation FROM catalog_names"
            " WHERE slug = 'ngc-2237' AND is_primary = 1"
        )
    ]
    assert righe == [("NGC", "2237")]


def test_the_kinds_of_an_entry_come_from_both_fields(catalogo):
    """Le famiglie d'uso stanno in DUE campi del file: `kind` ce l'hanno tutte le voci, `k`
    solo cinquecento. Leggere solo `k` lasciava la colonna vuota per il 97,7% del catalogo,
    e i filtri per famiglia sarebbero nati ciechi."""
    famiglie = dict(catalogo.execute("SELECT slug, kinds_json FROM catalog_entries"))
    assert json.loads(famiglie["m-31"]) == ["galaxy"]
    assert json.loads(famiglie["ngc-2237"]) == ["nebula", "emission"]
    assert all(v for v in famiglie.values()), famiglie


def test_the_unit_vector_agrees_with_the_coordinates(catalogo):
    """Se il versore e le coordinate raccontassero due cieli diversi, la ricerca per cono
    troverebbe oggetti che non sono li'."""
    for slug, ra, dec, x, y, z in catalogo.execute(
        "SELECT slug, ra_deg, dec_deg, x, y, z FROM catalog_entries"
    ):
        r, d = math.radians(ra), math.radians(dec)
        assert x == pytest.approx(math.cos(d) * math.cos(r), abs=1e-9), slug
        assert y == pytest.approx(math.cos(d) * math.sin(r), abs=1e-9), slug
        assert z == pytest.approx(math.sin(d), abs=1e-9), slug


# --- il file impacchettato -------------------------------------------------------------------


def test_no_bundled_file_is_not_an_error(tmp_path, monkeypatch):
    """Al primo avvio di chi costruisce dai sorgenti il file puo' non esserci ancora."""
    monkeypatch.setattr(bundle, "DATA", tmp_path)
    assert bundle.path() is None
    assert bundle.read() == (None, [])


def test_two_bundled_files_are_a_fault_and_not_a_choice(tmp_path, monkeypatch):
    """Si caricherebbe il primo in ordine alfabetico, che e' un modo silenzioso di usare un
    catalogo vecchio dopo un aggiornamento andato a meta'."""
    monkeypatch.setattr(bundle, "DATA", tmp_path)
    scrivi(tmp_path / "catalogo-20260101-aaa.json", "vecchio", VOCI)
    scrivi(tmp_path / "catalogo-20260825-bbb.json", "nuovo", VOCI)
    assert bundle.path() is None


def test_the_bundled_catalogue_loads_and_answers(conn):
    """Il file vero, quello che viene spedito: se si rompesse in una ricostruzione, tutto il
    resto della suite resterebbe verde -- gira sul catalogo finto -- e l'app uscirebbe senza
    catalogo. `Sh2 155` c'e' perche' e' la Cave, ed e' la sigla che si scriveva male."""
    file = real_bundle()
    assert file, "il catalogo impacchettato non c'e'"
    quante = load.load_catalog(conn, file)
    assert quante > 20000, f"il catalogo ha solo {quante} voci"

    assert lookup.by_designation(conn, "Sh2 155")["slug"]
    assert lookup.by_designation(conn, "M 31")["common_name"]
    senza_famiglia = conn.execute(
        "SELECT COUNT(*) FROM catalog_entries WHERE kinds_json IS NULL"
    ).fetchone()[0]
    assert senza_famiglia == 0, f"{senza_famiglia} voci senza famiglia d'uso"


# --- all'avvio dell'app ----------------------------------------------------------------------


def test_the_app_loads_the_catalogue_when_it_starts(db_path, tmp_path, monkeypatch):
    """Il catalogo si carica da solo: nessuno deve premere un pulsante perche' l'archivio sappia
    riconoscere gli oggetti."""
    from astrolog.api.app import create_app
    from astrolog.db.connect import connect

    percorso = scrivi(tmp_path / "catalogo-prova-1.json", "prova-1", VOCI)
    monkeypatch.setattr(bundle, "path", lambda: percorso)

    create_app(db_path)
    conn = connect(db_path)
    assert load.loaded_version(conn) == "prova-1"
    assert lookup.by_designation(conn, "M 31")["slug"] == "m-31"
    conn.close()


def test_a_broken_catalogue_does_not_stop_the_app(db_path, tmp_path, monkeypatch):
    """A mani vuote l'app funziona: cataloga, cerca, conta le ore. Un catalogo che manca o e'
    rotto e' un guasto da dire, non un avvio che fallisce -- e al primo avvio di chiunque il
    catalogo potrebbe non esserci ancora."""
    from astrolog.api.app import create_app

    rotto = tmp_path / "catalogo-rotto.json"
    rotto.write_text("{ non e' json", encoding="utf-8")
    monkeypatch.setattr(bundle, "path", lambda: rotto)

    app = create_app(db_path)  # non deve sollevare
    assert app is not None


def test_health_says_whether_the_catalogue_is_there(db_path, tmp_path, monkeypatch):
    """Senza catalogo l'app funziona, ma non sa dire cosa hai fotografato: si vede da qui,
    invece di scoprirlo quando `identify` non riconosce niente."""
    from fastapi.testclient import TestClient

    from astrolog.api.app import create_app

    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        salute = c.get("/api/health").json()
    assert salute["catalog_entries"] == 0 and salute["catalog_version"] is None

    monkeypatch.setattr(
        bundle, "path", lambda: scrivi(tmp_path / "catalogo-prova-1.json", "prova-1", VOCI)
    )
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        salute = c.get("/api/health").json()
    assert salute["catalog_entries"] == len(VOCI) and salute["catalog_version"] == "prova-1"
