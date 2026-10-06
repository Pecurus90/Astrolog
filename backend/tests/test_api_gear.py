"""La pagina **Attrezzatura**: *"con cosa ho ripreso, e quanto"*.

I pezzi li scrive la spina leggendo gli header; qui si leggono, raccolti per genere. Ogni numero
viene dai file o da una risposta dell'utente: dove non c'e', la pagina dice **perche'** invece di
scrivere uno zero (`docs/domini/attrezzatura.md`).
"""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db import idlist
from astrolog.db.connect import connect
from astrolog.spine import gear_usage
from conftest import db
from group_bench import ROMA, attrezzo, corri, filtro, luogo, posa, prepara

SCALA = 1.23  # arcosecondi per pixel, come li misura il riconoscitore


def corredo(conn, optics_id, camera_id, focal_mm):
    return conn.execute(
        "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES(?, ?, ?, 1, ?)",
        (optics_id, camera_id, focal_mm, now_iso()),
    ).lastrowid


def risolta(conn, frame_id, *, scala=SCALA, larghezza=1.5, altezza=1.0):
    """Il cielo misurato su quella posa: e' da qui che esce quanto inquadra un corredo."""
    conn.execute(
        "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
        " height_deg, solved_at) VALUES(?, 10.0, 41.0, ?, ?, ?, ?)",
        (frame_id, scala, larghezza, altezza, now_iso()),
    )


def gear(client):
    risposta = client.get("/api/v1/gear")
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


def pezzi(pagina, kind):
    return [p for p in pagina["instruments"] if p["kind"] == kind]


@pytest.fixture
def archivio(db_path):
    """Un corredo che ha ripreso -- ottica, camera, due pose risolte in Ha -- piu' una montatura
    che nessun file lega a niente, che e' il caso su cui la pagina deve dire la verita'."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        ottica = attrezzo(conn, "optics", "TS 130 APO", aperture_mm=130.0, focal_mm=910.0)
        camera = attrezzo(conn, "camera", "ASI2600MM", camera_type="mono", pixel_size_um=3.76)
        attrezzo(conn, "mount", "EQ6-R", payload_kg=20.0)
        addosso = {
            k: attrezzo(conn, k, f"Il mio {k}") for k in ("filter_wheel", "focuser", "guide_camera")
        }
        rig = corredo(conn, ottica, camera, 910.0)
        ha = filtro(conn, "Ha", "HA")
        for n, quando in enumerate(("2024-05-18T22:00:00Z", "2024-05-18T23:00:00Z")):
            f = posa(conn, quando=quando, filtro_id=ha, esposizione=300.0, hash_=f"p{n}")
            conn.execute(
                "UPDATE frames SET rig_id = ?, filter_wheel_id = ?, focuser_id = ?,"
                " guide_camera_id = ? WHERE id = ?",
                (rig, *addosso.values(), f),
            )
            risolta(conn, f)
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


@pytest.mark.parametrize("genere", ["filter_wheel", "focuser", "guide_camera"])
def test_a_piece_the_files_name_on_every_frame_has_its_hours(archivio, genere):
    """La ruota portafiltri, il focheggiatore e la camera di guida stanno **sulla posa**, non sul
    corredo: i file dicono quale hai usato per ogni scatto, quindi le loro ore si sanno davvero.

    E' la differenza con la **montatura**, che nessun header lega a una posa e che infatti dice
    perche' non ne ha. Provati tutti e tre: con uno solo si potevano togliere le altre due strade
    senza che niente cadesse."""
    pezzo = pezzi(gear(archivio), genere)[0]

    assert pezzo["frames"] == 2
    assert pezzo["integration_s"] == 600.0
    assert pezzo["nights"] == 1
    assert [o["key"] for o in pezzo["objects"]] == ["m-31"]


def test_a_kind_no_frame_of_yours_names_has_hours_the_app_cannot_know(db_path):
    """Chi riprende con un programma che la ruota non la scrive se la puo' **scrivere a mano** --
    ma allora le sue ore l'app non le sa, e un bel `0 pose` sarebbe un dato falso, non una misura.

    La regola e' **per archivio**, non per genere: la stessa ruota dice due cose diverse a due
    utenti, e a deciderlo e' cio' che i loro file dicono. Senza questa riga, chi usa Voyager o SGP
    leggeva zero accanto a un pezzo di cui non si sa niente."""
    conn = connect(db_path)
    try:
        prepara(conn)
        attrezzo(conn, "filter_wheel", "EFW 7x36", slots=7)
        corri(conn)
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        ruota = pezzi(gear(client), "filter_wheel")[0]

    assert ruota["frames"] is None
    assert ruota["integration_s"] is None
    assert ruota["no_hours"] == "files_silent"


def test_a_frame_with_no_rig_still_says_what_you_shot_with_the_wheel(db_path):
    """Una posa che nomina la ruota ma **non ha corredo** -- l'header non dice la camera -- deve
    comunque raccontare cosa ci hai ripreso. La giunzione sui corredi va fatta in modo che quella
    posa non sparisca: con una giunzione secca resterebbe fuori, e la riga della ruota direbbe
    "1 posa" e **nessun oggetto**, cioe' un numero senza la sua storia.

    E' il caso di chi riprende con N.I.N.A. senza `INSTRUME`: il corredo non nasce, la ruota si'."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        ruota = attrezzo(conn, "filter_wheel", "EFW 7x36")
        senza = posa(conn, quando="2024-05-18T22:00:00Z", esposizione=300.0, hash_="p0")
        conn.execute(
            "UPDATE frames SET rig_id = NULL, filter_wheel_id = ? WHERE id = ?", (ruota, senza)
        )
        corri(conn)
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        scritta = pezzi(gear(client), "filter_wheel")[0]

    assert scritta["frames"] == 1
    assert [o["key"] for o in scritta["objects"]] == ["m-31"]


def test_the_objects_of_a_piece_do_not_search_the_rigs_row_by_row(db_path):
    """Il piano di quella query non deve cercare i corredi **una volta per coppia** (posa, pezzo).

    E' la ragione per cui esiste la forma giunta del legame, e il piano e' deterministico: si
    chiede a SQLite invece di cronometrare, che su una macchina lenta direbbe un altro numero."""
    conn = connect(db_path)
    try:
        prepara(conn)
        # L'elenco vero, non un `(1)` finto: con una costante SQLite sceglie un altro ordine di
        # giunzione, e il piano che si guarderebbe non sarebbe quello che gira.
        with idlist.holding(conn, [1]) as elencati:
            piano = [
                r["detail"]
                for r in conn.execute(
                    "EXPLAIN QUERY PLAN " + gear_usage._PIECE_OBJECTS.replace("{listed}", elencati)
                )
            ]
    finally:
        conn.close()

    # Il segno della ricerca riga per riga e' **`CORRELATED LIST SUBQUERY`**: nella forma in uso
    # non c'e' (la sotto-select degli id e' una `LIST SUBQUERY` e basta, e le due `CORRELATED
    # SCALAR` sono i nomi degli oggetti), nella forma sabotata compare. Si guarda quel segno e non
    # il nome della tabella, che a seconda della versione SQLite stampa come alias o per esteso.
    assert not any("CORRELATED LIST SUBQUERY" in r for r in piano), piano


def test_the_shapes_of_the_link_pick_the_same_frames(archivio):
    """Il legame fra una posa e un pezzo ha **tre forme**: una che cerca i corredi da se', per chi
    non ce li ha nel `FROM`, una che li usa dove sono gia' -- senza la ricerca correlata -- e le
    coppie (pezzo, posa) per chi conta tutti i pezzi insieme.

    Non sono due legami: li compone la stessa funzione, e questa prova e' la macchina che li tiene
    uguali. Se divergessero, ore e oggetti della stessa riga verrebbero da pose diverse."""
    from astrolog.spine import counts

    with connect(archivio.app.state.db_path) as conn:
        sola = set(
            conn.execute(
                f"SELECT i.id, f.id FROM instruments i JOIN frames f"  # noqa: S608 - frammenti nostri
                f" ON {counts.of('instrument')}"
            )
        )
        giunta = set(
            conn.execute(
                "SELECT i.id, f.id FROM frames f LEFT JOIN rigs g ON g.id = f.rig_id"  # noqa: S608
                f" JOIN instruments i ON {counts.of('instrument', rigs_joined=True)}"
            )
        )

        # e la terza, per chi conta tutti i pezzi insieme raggruppando (`gear_usage`)
        coppie = {tuple(r) for r in conn.execute(f"SELECT * FROM ({counts.PIECE_FRAMES})")}  # noqa: S608

    assert sola == giunta
    assert {tuple(r) for r in sola} == coppie
    assert sola, "il banco non lega nessuna posa a nessun pezzo: la prova non direbbe niente"


def test_the_page_lists_the_gear_you_own(archivio):
    """I pezzi che possiedi, **raccolti per genere**: un telescopio e una camera non si
    confrontano, e mescolarli farebbe leggere l'elenco come un mucchio."""
    pagina = gear(archivio)

    assert [p["name"] for p in pezzi(pagina, "optics")] == ["TS 130 APO"]
    assert [p["name"] for p in pezzi(pagina, "camera")] == ["ASI2600MM"]
    assert [p["name"] for p in pezzi(pagina, "mount")] == ["EQ6-R"]
    assert [f["name"] for f in pagina["filters"]] == ["Ha"]
    # il corredo che ha ripreso e' in cima: l'ordine lo decide il backend, per tempo dato
    assert pagina["rigs"][0]["optics"] == "TS 130 APO"


def test_a_piece_says_how_much_you_shot_with_it(archivio):
    """Ore, frame e notti di ogni pezzo: e' il consuntivo per cui la pagina esiste. Le ore
    escono dalla stessa casa che le conta per oggetto e per notte, non da un conto suo."""
    corredo_letto = gear(archivio)["rigs"][0]

    assert corredo_letto["frames"] == 2
    assert corredo_letto["integration_s"] == 600.0
    assert corredo_letto["nights"] == 1


def test_a_piece_says_what_you_shot_with_it(archivio):
    """Cosa ci hai ripreso, **dal piu' ripreso**: e' il modo in cui si riconosce un pezzo
    guardandolo, piu' di quanto non lo facciano marca e modello. Vale per il corredo, per
    l'ottica e la camera che lo compongono, e per il filtro."""
    pagina = gear(archivio)

    assert [o["key"] for o in pagina["rigs"][0]["objects"]] == ["m-31"]
    assert [o["key"] for o in pezzi(pagina, "optics")[0]["objects"]] == ["m-31"]
    assert [o["key"] for o in pagina["filters"][0]["objects"]] == ["m-31"]
    assert pezzi(pagina, "mount")[0]["objects"] == [], "senza ore non c'e' nemmeno un oggetto"


def test_what_a_piece_shot_comes_most_shot_first(archivio):
    """Two objects, the most shot by time first even with fewer frames: one object alone could not
    tell the order from none (`counts.ORDER_BY_TIME`)."""
    with db(archivio) as conn:
        rig, ha = conn.execute("SELECT rig_id, filter_id FROM frames LIMIT 1").fetchone()
        posa(conn, quando="2024-05-19T22:00:00Z", oggetto=2, corredo=rig, filtro_id=ha,
             esposizione=1200.0, hash_="m45")  # fmt: skip
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()
    pagina = gear(archivio)

    assert [o["key"] for o in pagina["rigs"][0]["objects"]] == ["m-45", "m-31"]
    assert [o["key"] for o in pezzi(pagina, "optics")[0]["objects"]] == ["m-45", "m-31"]
    assert [o["key"] for o in pagina["filters"][0]["objects"]] == ["m-45", "m-31"]


def test_the_hours_of_a_piece_come_from_its_rigs(archivio):
    """Un'ottica e una camera non stanno su una posa: stanno su un **corredo**, e le loro ore sono
    quelle dei corredi che le portano -- non quelle dell'archivio. (Gli altri tre generi ci
    arrivano per l'altra strada, ed e' la prova qui sopra.)

    Nell'archivio c'e' apposta una posa ripresa con **un altro** corredo: senza, un conto che
    prendesse tutte le pose darebbe gli stessi numeri e questa prova direbbe di si' senza
    guardare niente (visto verde sabotando, prima di aggiungerla)."""
    with db(archivio) as conn:
        altra = attrezzo(conn, "optics", "RC8", focal_mm=1624.0)
        camera = attrezzo(conn, "camera", "ASI533", pixel_size_um=3.76)
        altro = corredo(conn, altra, camera, 1624.0)
        f = posa(conn, quando="2024-07-01T22:00:00Z", esposizione=900.0, hash_="altro corredo")
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (altro, f))
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    ottica = next(p for p in pezzi(gear(archivio), "optics") if p["name"] == "TS 130 APO")
    assert (ottica["frames"], ottica["integration_s"], ottica["nights"]) == (2, 600.0, 1)


def test_a_piece_on_two_rigs_does_not_count_its_hours_twice(archivio):
    """La stessa camera su due corredi: le sue ore sono la somma, **una volta sola**. Un conto
    scritto a mano su una giunzione le raddoppierebbe, ed e' il difetto che la casa comune evita."""
    with db(archivio) as conn:
        camera = conn.execute("SELECT id FROM instruments WHERE kind = 'camera'").fetchone()["id"]
        altra = attrezzo(conn, "optics", "RC8", focal_mm=1624.0)
        secondo = corredo(conn, altra, camera, 1624.0)
        f = posa(conn, quando="2024-06-01T22:00:00Z", esposizione=120.0, hash_="altro corredo")
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (secondo, f))
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    letta = pezzi(gear(archivio), "camera")[0]
    assert (letta["frames"], letta["integration_s"]) == (3, 720.0)


def test_the_sky_of_a_rig_is_the_middle_value_not_the_average(archivio):
    """**Mediana, non media**: una posa risolta storta -- capita su un campo povero di stelle --
    sposterebbe la media e lascia ferma la mediana, e qui si descrive com'e' fatto un corredo,
    non un caso. Con 1,2 / 1,23 / 6,0 la mediana e' 1,23 e la media 2,81."""
    with db(archivio) as conn:
        rig = conn.execute("SELECT id FROM rigs WHERE focal_mm = 910").fetchone()["id"]
        conn.execute("UPDATE frame_wcs SET scale_arcsec_px = 1.2 WHERE frame_id = 1")
        storta = posa(conn, quando="2024-05-19T22:00:00Z", esposizione=300.0, hash_="storta")
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (rig, storta))
        risolta(conn, storta, scala=6.0)
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    corredo_letto = next(r for r in gear(archivio)["rigs"] if r["focal_mm"] == 910)
    assert corredo_letto["scale_arcsec_px"] == pytest.approx(SCALA), "il valore di mezzo"


def test_the_sky_of_a_rig_is_written_as_the_screen_reads_it(archivio):
    """La scala e il campo escono a due decimali: la mediana delle soluzioni ne porta quindici, e
    lo schermo ne mostrerebbe tre che non sono una misura."""
    with db(archivio) as conn:
        conn.execute(
            "UPDATE frame_wcs SET scale_arcsec_px = 1.234567, width_deg = 1.498765,"
            " height_deg = 0.987654"
        )
        gear_usage.write(conn)
        conn.commit()

    corredo = next(r for r in gear(archivio)["rigs"] if r["focal_mm"] == 910)
    assert (corredo["scale_arcsec_px"], corredo["width_deg"], corredo["height_deg"]) == (
        1.23,
        1.5,
        0.99,
    )


def test_a_frame_that_did_not_say_its_field_does_not_drag_the_others(archivio):
    """Una soluzione buona puo' non portare il rettangolo -- l'header non dice quanti pixel ha il
    sensore -- e quel vuoto **non e' uno zero**: esce dal conto invece di tirare giu' la mediana."""
    with db(archivio) as conn:
        conn.execute("UPDATE frame_wcs SET width_deg = NULL WHERE frame_id = 1")
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    corredo_letto = next(r for r in gear(archivio)["rigs"] if r["focal_mm"] == 910)
    assert corredo_letto["width_deg"] == pytest.approx(1.5)


def test_a_rig_says_the_sky_it_really_frames(archivio):
    """La scala e il campo **misurati** sulle pose risolte, non calcolati da focale e pixel: su
    un corredo con un riduttore il conto teorico direbbe un altro numero, giusto sulla carta e
    sbagliato nel cielo."""
    corredo_letto = gear(archivio)["rigs"][0]

    assert corredo_letto["scale_arcsec_px"] == pytest.approx(SCALA)
    assert corredo_letto["width_deg"] == pytest.approx(1.5)
    assert corredo_letto["height_deg"] == pytest.approx(1.0)


def test_a_rig_that_never_shot_says_nothing_about_the_sky(archivio):
    """Un corredo senza pose risolte non ha una scala: la riga tace, invece di riempirsi con il
    numero che la scheda direbbe."""
    with db(archivio) as conn:
        ottica = attrezzo(conn, "optics", "RC8", aperture_mm=203.0, focal_mm=1624.0)
        camera = attrezzo(conn, "camera", "ASI533", pixel_size_um=3.76)
        corredo(conn, ottica, camera, 1624.0)
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    nuovo = next(r for r in gear(archivio)["rigs"] if r["optics"] == "RC8")
    assert nuovo["scale_arcsec_px"] is None
    assert nuovo["width_deg"] is None and nuovo["frames"] == 0


def test_a_mount_has_no_hours_and_the_page_says_why(archivio):
    """Nessuna posa porta questa montatura -- i file non la nominano e nessun corredo ce l'ha: la
    riga non prende uno zero, che sarebbe un dato, ma dice che nessun corredo la porta ancora."""
    montatura = pezzi(gear(archivio), "mount")[0]
    assert montatura["no_hours"] == "no_rig"

    assert montatura["integration_s"] is None
    assert montatura["frames"] is None
    assert montatura["payload_kg"] == 20.0, "la scheda pero' si legge tutta"


def test_no_filter_at_all_is_not_a_filter_you_own(archivio):
    """La riga con cui l'app segna una posa **senza vetro davanti** non e' un filtro che
    possiedi: in un elenco di cose tue sarebbe la prima voce di qualcosa che non hai -- e chi
    riprende a colori ce l'ha in cima."""
    with db(archivio) as conn:
        conn.execute(
            "INSERT INTO filters(name, passband, is_none, created_at) VALUES('None', 'NONE', 1, ?)",
            (now_iso(),),
        )
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    assert [f["name"] for f in gear(archivio)["filters"]] == ["Ha"]


def test_a_filter_says_which_band_it_passes(archivio):
    """Un filtro porta le bande **dichiarate** e le loro larghezze: e' cio' che distingue due
    filtri che a nome si somigliano. La banda che l'app ricava dal nome non si mostra: per un
    filtro che il vocabolario non riconosce vale `UNKNOWN`, che a schermo non dice niente."""
    with db(archivio) as conn:
        conn.execute(
            "INSERT INTO filter_bands(filter_id, band, width_nm)"
            " SELECT id, 'HA', 3.0 FROM filters WHERE name = 'Ha'"
        )
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    letto = gear(archivio)["filters"][0]
    assert letto["bands"] == [{"band": "HA", "width_nm": 3.0}]
    assert letto["integration_s"] == 600.0


def test_a_rewritten_copy_is_not_another_hour_of_gear(archivio):
    """La stessa regola dell'Archivio e delle Notti, e la stessa casa: una copia calibrata
    accanto al suo originale non e' un'altra ora di cielo."""
    prima = gear(archivio)["rigs"][0]
    with db(archivio) as conn:
        originale = conn.execute("SELECT id, rig_id FROM frames ORDER BY id LIMIT 1").fetchone()
        copia = posa(
            conn,
            quando="2024-05-18T22:00:00Z",
            esposizione=300.0,
            hash_="copia",
            copia_di=originale["id"],
        )
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (originale["rig_id"], copia))
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    dopo = gear(archivio)["rigs"][0]
    assert (dopo["frames"], dopo["integration_s"]) == (prima["frames"], prima["integration_s"])


def test_a_frame_without_a_time_is_not_zero_hours_of_gear(archivio):
    """ "Non lo so" e "zero ore" restano due risposte diverse anche qui: la posa muta esce dalla
    somma e si conta a parte."""
    with db(archivio) as conn:
        conn.execute("UPDATE frames SET exposure_s = NULL WHERE frame_hash = 'p1'")
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    corredo_letto = gear(archivio)["rigs"][0]
    assert corredo_letto["integration_s"] == 300.0
    assert corredo_letto["untimed"] == 1


def test_the_page_counts_nothing_and_the_writer_asks_per_page(archivio):
    """La pagina non conta niente: legge cio' che la spina ha scritto (Marco, 22/9/2026). E chi
    scrive chiede gli oggetti di ogni pezzo **per elenco, non per pezzo**: tre elenchi e il cielo
    dei corredi, quattro domande, che ci sia un corredo o venti.

    La guardia e' sul **numero di chiamate**, non sul tempo: un tempo dipende dalla macchina, il
    conto no -- e cambia subito se un domani la domanda finisse dentro il giro dei pezzi."""
    quante = []
    vero = idlist.grouped

    def contando(conn, sql, ids, key, row):
        quante.append(len(ids))
        return vero(conn, sql, ids, key, row)

    with db(archivio) as conn:
        for n in range(12):
            ottica = attrezzo(conn, "optics", f"telescopio {n}", focal_mm=500.0 + n)
            corredo(conn, ottica, None, 500.0 + n)
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    with mock.patch.object(idlist, "grouped", contando):
        pagina = gear(archivio)
        assert quante == [], "la pagina ha contato"
        with db(archivio) as conn:
            gear_usage.write(conn)

    assert len(pagina["rigs"]) > 10, "servono abbastanza pezzi perche' la domanda abbia senso"
    assert len(quante) == 4, f"pezzi, corredi (oggetti e cielo) e filtri: {quante}"


def test_an_empty_gear_page_is_an_answer_not_an_error(db_path):
    """A mani vuote non c'e' niente da mostrare, e non e' un guasto: e' lo stato di chi ha appena
    installato l'app."""
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        pagina = gear(c)

    assert pagina["instruments"] == [] and pagina["filters"] == [] and pagina["rigs"] == []


def test_a_mount_carried_by_the_frames_has_their_hours(archivio):
    """Quando le pose portano la montatura -- perche' il file la nomina o perche' l'hai data al
    corredo -- la montatura ha ore, notti e cosa ci hai ripreso, come gli altri pezzi."""
    with db(archivio) as conn:
        montatura = conn.execute("SELECT id FROM instruments WHERE kind = 'mount'").fetchone()[0]
        conn.execute("UPDATE frames SET mount_id = ?", (montatura,))
        gear_usage.write(conn)  # come a fine giro di uno stadio
        conn.commit()

    montata = pezzi(gear(archivio), "mount")[0]
    assert (montata["frames"], montata["integration_s"], montata["nights"]) == (2, 600.0, 1)
    assert [o["key"] for o in montata["objects"]] == ["m-31"]


def test_a_mount_no_frame_carries_says_so_even_where_others_have_hours(archivio):
    """Dove altre montature hanno pose, una che non ne ha non ha fatto "zero ore": nessun corredo
    la porta ancora, e la pagina lo dice. Le ore, dove ci sono, non portano un perche'."""
    with db(archivio) as conn:
        altra = conn.execute(
            "INSERT INTO instruments(kind, name, created_at) VALUES('mount', 'AM5', 'ora')"
        ).lastrowid
        conn.execute("UPDATE frames SET mount_id = ?", (altra,))
        gear_usage.write(conn)
        conn.commit()

    per_nome = {p["name"]: p for p in pezzi(gear(archivio), "mount")}
    assert (per_nome["EQ6-R"]["frames"], per_nome["EQ6-R"]["no_hours"]) == (0, "no_rig")
    assert per_nome["AM5"]["no_hours"] is None
