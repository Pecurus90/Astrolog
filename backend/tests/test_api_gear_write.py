"""I gesti sull'attrezzatura: **creare** un pezzo che i file non nominano e **correggere** la sua
scheda, dalla pagina dove lo si guarda.

Un pezzo puo' nascere in due modi -- la scansione lo riconosce, oppure lo scrivi tu -- e **resta
uno solo**: un pezzo e' il suo nome dentro il suo genere, quindi cio' che crei a mano e' esattamente
cio' che la scansione riconoscera' (`docs/domini/attrezzatura.md`). Correggere passa dalla stessa
casa di *Da confermare*: la grafia vecchia si impara, se no la scansione dopo lo ricrea com'era.
"""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api import work
from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.worker.worker import WorkerBusyError
from group_bench import ROMA, attrezzo, corri, filtro, luogo, posa, prepara

CARTA = {"brand": "Baader", "model": "CMOS-optimized", "weight_kg": 0.2}


def cercato(client, kind, nome):
    """Il pezzo come la pagina Attrezzatura lo mostra, o None: si guarda da li' e non dal DB
    perche' e' quello che l'utente vede."""
    pagina = client.get("/api/v1/gear").json()
    return next((p for p in pagina["instruments"] if p["kind"] == kind and p["name"] == nome), None)


def pezzo(client, kind, nome):
    trovato = cercato(client, kind, nome)
    assert trovato is not None, f"{kind} {nome} non e' nella pagina"
    return trovato


def crea(client, **corpo):
    return client.post("/api/v1/gear/instruments", json=corpo)


def correggi(client, instrument_id, **corpo):
    return client.patch(f"/api/v1/gear/instruments/{instrument_id}", json=corpo)


@pytest.fixture
def archivio(db_path):
    """Un corredo che ha ripreso, e una camera le cui pose non dicono il filtro: il secondo caso
    serve perche' il colore di una camera e' anche una risposta sulle sue pose."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        ottica = attrezzo(conn, "optics", "TS 130 APO", aperture_mm=130.0, focal_mm=910.0)
        camera = attrezzo(conn, "camera", "ASI2600MM", pixel_size_um=3.76)
        rig = conn.execute(
            "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
            " VALUES(?, ?, 910.0, 1, ?)",
            (ottica, camera, now_iso()),
        ).lastrowid
        ha = filtro(conn, "Ha", "HA")
        con_filtro = posa(conn, quando="2024-05-18T22:00:00Z", filtro_id=ha, hash_="p0")
        senza = posa(conn, quando="2024-05-18T23:00:00Z", hash_="p1")
        conn.execute("UPDATE frames SET rig_id = ? WHERE id IN (?, ?)", (rig, con_filtro, senza))
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


@pytest.fixture
def vuoto(db_path):
    """Nessun frame e nessun pezzo: chi apre l'app il primo giorno e scrive cosa possiede."""
    conn = connect(db_path)
    try:
        prepara(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_a_piece_written_by_hand_says_its_hours_at_once(archivio):
    """Un'ottica scritta a mano non ha ancora ripreso: zero frame, subito, e non "si sta contando"
    fino al prossimo giro della spina. Chi la crea scrive la **sua** riga, senza ricontare tutto
    l'archivio dentro la richiesta: su un archivio grande costerebbe secondi."""
    from astrolog.spine import gear_usage

    with mock.patch.object(gear_usage, "write", side_effect=AssertionError("ha ricontato tutto")):
        assert crea(archivio, kind="optics", name="RC8").status_code == 201
    nuova = pezzo(archivio, "optics", "RC8")
    assert (nuova["counted"], nuova["frames"], nuova["integration_s"]) == (True, 0, 0)


def test_you_can_add_a_piece_the_files_never_named(vuoto):
    """Una guida, un riduttore, una montatura: nessun header di quelli che sappiamo leggere li
    scrive, e finche' non si potevano creare a mano non esistevano per l'app. Si crea **a mani
    vuote**, prima di aver ripreso: e' proprio chi non ha ancora scansionato che ha piu' bisogno
    di dirlo."""
    risposta = crea(vuoto, kind="guide_scope", name="60/240")

    assert risposta.status_code == 201, risposta.text
    assert cercato(vuoto, "guide_scope", "60/240") is not None


def test_a_piece_you_wrote_is_not_a_discovery_of_the_scan(vuoto):
    """`detected` distingue cio' che l'app ha trovato da cio' che hai detto tu, e la pagina lo
    scrive accanto al pezzo. Un pezzo creato a mano e' **tuo**: nasce gia' dichiarato."""
    crea(vuoto, kind="mount", name="EQ6-R")

    assert pezzo(vuoto, "mount", "EQ6-R")["detected"] is False


def test_a_piece_is_born_with_its_card(vuoto):
    """Nasce con la sua scheda in un colpo solo: creare e poi correggere sarebbero due gesti per
    una cosa sola, e fra i due il pezzo esisterebbe a meta'."""
    crea(vuoto, kind="filter_wheel", name="EFW 7x36", slots=7, **CARTA)

    scritto = pezzo(vuoto, "filter_wheel", "EFW 7x36")
    assert scritto["slots"] == 7
    assert scritto["brand"] == "Baader"
    assert scritto["weight_kg"] == 0.2


def test_the_page_knows_which_fields_a_kind_asks_even_without_owning_one(vuoto):
    """I campi di una scheda li decide il backend, **genere per genere e non pezzo per pezzo**:
    per scrivere il primo focheggiatore non c'e' nessun focheggiatore da cui copiarli. Se
    arrivassero attaccati ai pezzi, il gesto funzionerebbe solo per cio' che possiedi gia'."""
    cards = vuoto.get("/api/v1/gear").json()["cards"]

    assert "payload_kg" in cards["mount"]  # la portata e' della montatura
    assert "payload_kg" not in cards["optics"]  # e di nessun altro
    assert "slots" in cards["filter_wheel"]


def test_a_name_you_already_own_is_a_refusal_not_a_second_piece(archivio):
    """**Un pezzo nasce in due modi e resta uno solo.** Il nome e' unico dentro il genere, quindi
    scrivere un nome che gia' possiedi non fa nascere un doppione: e' un rifiuto con una parola
    che la pagina puo' mostrare. Senza, il giorno della prima ripresa l'elenco sarebbe doppio."""
    risposta = crea(archivio, kind="optics", name="TS 130 APO")

    assert risposta.status_code == 409
    assert risposta.json()["detail"]["code"] == "name_taken"
    pagina = archivio.get("/api/v1/gear").json()
    assert [p["name"] for p in pagina["instruments"] if p["kind"] == "optics"] == ["TS 130 APO"]


def test_the_same_name_in_another_kind_is_another_piece(archivio):
    """Il nome e' unico **dentro il genere**, non nell'archivio: una guida e un telescopio
    possono chiamarsi tutti e due "80/480", e sono due cose diverse."""
    assert crea(archivio, kind="guide_scope", name="TS 130 APO").status_code == 201


def test_you_can_correct_a_card_without_leaving_the_page(archivio):
    """La correzione si fa dove si vede l'errore. Prima si passava da *Da confermare*, che e' la
    pagina delle domande aperte: un pezzo a posto non ci compare, e non si poteva correggere."""
    id_ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]

    assert correggi(archivio, id_ottica, aperture_mm=132.0, notes="misurata").status_code == 200

    scritto = pezzo(archivio, "optics", "TS 130 APO")
    assert scritto["aperture_mm"] == 132.0
    assert scritto["notes"] == "misurata"
    assert scritto["detected"] is False  # da adesso l'ha detto l'utente, non la spina


def test_renaming_a_piece_teaches_the_old_spelling(archivio):
    """Rinominare **impara la grafia vecchia**: senza la regola, la scansione dopo ritroverebbe
    quel nome nell'header e farebbe nascere di nuovo il pezzo che hai appena ribattezzato. E' la
    stessa casa di *Da confermare* (`spine.gear.declare_instrument`), non una seconda strada."""
    id_ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]

    correggi(archivio, id_ottica, name="Takahashi FSQ")

    assert cercato(archivio, "optics", "Takahashi FSQ") is not None
    conn = connect(archivio.app.state.db_path)
    try:
        imparate = conn.execute(
            "SELECT target_key FROM header_aliases WHERE kind = 'optics'"
        ).fetchall()
    finally:
        conn.close()
    assert [r["target_key"] for r in imparate] == ["Takahashi FSQ"]


def test_what_you_declare_about_a_camera_is_what_the_page_shows(archivio):
    """Colore e pixel di una camera l'app li scrive **fra le dichiarazioni**, non nella colonna,
    che e' dei file e che la spina ricalcola a ogni corsa. Se la pagina leggesse la sola colonna,
    dopo la tua correzione continuerebbe a mostrare cio' che dicono i file -- visto dal vivo:
    scelto "mono", la riga restava senza colore."""
    id_camera = pezzo(archivio, "camera", "ASI2600MM")["id"]

    correggi(archivio, id_camera, camera_type="mono", pixel_size_um=3.8)

    scritto = pezzo(archivio, "camera", "ASI2600MM")
    assert scritto["camera_type"] == "mono"
    assert scritto["pixel_size_um"] == 3.8


def test_the_same_guard_holds_on_the_correction(archivio):
    """La guardia sui campi di un genere e' **una casa sola**, e ci passano due porte: la nascita
    (`test_a_field_that_does_not_belong_to_the_kind_does_not_enter`) e la correzione. Provata su
    una sola, l'altra potrebbe saltarla senza che niente cada."""
    id_montatura = crea(archivio, kind="mount", name="EQ6-R").json()["id"]

    corretto = correggi(archivio, id_montatura, aperture_mm=130.0)

    assert corretto.status_code == 422, corretto.text
    assert corretto.json()["detail"]["code"] == "field_not_of_kind"
    assert pezzo(archivio, "mount", "EQ6-R")["aperture_mm"] is None


def test_you_cannot_write_gear_while_the_archive_is_being_read(archivio):
    """**Un lavoro alla volta.** Col worker in corsa non si scrive: e' la stessa regola
    dell'Applica, e la ragione e' la stessa -- meglio dirlo prima che lasciare l'archivio a meta'.
    Si risponde con un codice che la pagina sa leggere, non con un guasto."""
    with mock.patch.object(archivio.app.state.worker, "is_running", return_value=True):
        nato = crea(archivio, kind="focuser", name="EAF")
        corretto = correggi(archivio, pezzo(archivio, "optics", "TS 130 APO")["id"], notes="ciao")

    assert nato.status_code == 409
    assert nato.json()["detail"]["code"] == "worker_busy"
    assert corretto.status_code == 409
    # e nessuna delle due ha scritto niente
    assert cercato(archivio, "focuser", "EAF") is None
    assert pezzo(archivio, "optics", "TS 130 APO")["notes"] is None


def test_a_busy_worker_is_not_an_error_for_whoever_answered():
    """La risposta **e' gia' scritta** quando si prova a far ripartire il lavoro, e le pose da
    rilavorare sono gia' segnate nel database: le raccoglie la corsa in corso o il prossimo
    *Avvia*. Fallire qui direbbe a chi ha risposto che la sua risposta e' andata persa."""
    finto = mock.Mock()
    finto.worker.start.side_effect = WorkerBusyError()

    assert work.after(finto, {"normalize"}) is False


def test_writing_a_piece_does_not_start_the_work(vuoto):
    """Un pezzo appena scritto non ha pose: non c'e' niente da rilavorare, e avviare il worker
    sarebbe una corsa che non cambia una riga. Lo stesso vale per una correzione che non sposta
    niente -- una nota, una marca: il lavoro riparte **solo** se qualche posa cambia senso."""
    nato = crea(vuoto, kind="focuser", name="EAF")
    corretto = correggi(vuoto, nato.json()["id"], notes="comprato usato")

    assert nato.json()["run_started"] is False
    assert nato.json()["requeued"] == 0
    assert corretto.json()["run_started"] is False
    assert corretto.json()["requeued"] == 0


def test_a_correction_with_nothing_in_it_writes_nothing(archivio):
    """Una scheda mandata vuota non e' una modifica: si risponde di si' e non si tocca niente --
    il pezzo resta com'era, **compreso** il fatto che l'aveva trovato la spina."""
    id_ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]

    risposta = correggi(archivio, id_ottica)

    assert risposta.status_code == 200
    assert pezzo(archivio, "optics", "TS 130 APO")["detected"] is True


def test_a_piece_that_is_not_there_is_not_found(archivio):
    """Un pezzo cancellato da un'altra scheda aperta, o un indirizzo scritto a mano: si risponde
    che non c'e', invece di scrivere una scheda su un id che non esiste."""
    assert correggi(archivio, 9999, notes="ciao").status_code == 404


def test_a_measure_of_zero_is_not_a_measure(vuoto):
    """Zero non e' "non lo so", e' un vuoto scritto male: una focale a zero fa sparire la scala di
    un corredo senza che nessuno se ne accorga. Vale creando come correggendo."""
    assert crea(vuoto, kind="optics", name="Zero", focal_mm=0).status_code == 422


# I campi che lo schema **non** ferma: i suoi quattro CHECK coprono colore, portata, slot e
# fattore di riduzione, e basta. Questi quattro passerebbero, e la riga li stamperebbe.
SENZA_CHECK = {"aperture_mm": 130.0, "focal_mm": 900.0, "pixel_size_um": 3.8, "backfocus_mm": 55.0}


@pytest.mark.parametrize(
    ("genere", "campo", "valore"),
    [
        # i quattro che lo schema NON ferma, su una montatura che non li ha
        *(("mount", campo, valore) for campo, valore in SENZA_CHECK.items()),
        # e uno che lo schema ferma, per controllare che la guardia arrivi prima del database
        ("optics", "payload_kg", 20.0),
    ],
)
def test_a_field_that_does_not_belong_to_the_kind_does_not_enter(vuoto, genere, campo, valore):
    """La portata e' della montatura, l'apertura del telescopio: scriverle sul genere sbagliato
    sarebbe una scheda che dice una cosa che quel pezzo non ha.

    **La regola sta nel backend, non nella pagina**: il browser non e' l'unico che chiama queste
    rotte, e lo schema ferma solo quattro campi su tredici -- gli altri li scriverebbe in silenzio.
    Provati uno per uno proprio i quattro che lo schema **non** copre: con la guardia solo nel
    client, una montatura nasceva con apertura, focale, pixel e backfocus."""
    risposta = crea(vuoto, kind=genere, name="Che non esiste", **{campo: valore})

    assert risposta.status_code == 422, risposta.text
    assert risposta.json()["detail"]["code"] == "field_not_of_kind"
    assert cercato(vuoto, genere, "Che non esiste") is None


def test_the_colour_of_a_camera_sends_its_frames_back_to_be_read(archivio):
    """Il colore di una camera non e' solo una riga di scheda: e' anche la risposta sulle pose che
    non dicono il filtro. Correggerlo dall'Attrezzatura le rimette in coda come lo farebbe da *Da
    confermare* -- se no la stessa risposta varrebbe in una pagina e non nell'altra."""
    id_camera = pezzo(archivio, "camera", "ASI2600MM")["id"]

    risposta = correggi(archivio, id_camera, camera_type="color")

    assert risposta.status_code == 200
    assert risposta.json()["requeued"] > 0


def test_a_piece_you_wrote_yourself_is_not_a_question(archivio):
    """Il conto di *Da confermare* non si muove, e sbaglia in tutte e due le direzioni.

    **In su** vorrebbe dire che un pezzo scritto da te torna a chiederti chi e': l'hai appena
    detto -- anche una camera senza pixel ne' colore (Marco, 25/9/2026: un pezzo nuovo si vede
    nell'Attrezzatura). **In giu'** vorrebbe dire che scrivere un pezzo ha confermato le domande
    degli altri -- e' cio' che sarebbe successo delegando all'Applica, che senza `seen` conferma
    tutto."""
    prima = archivio.get("/api/v1/review").json()["to_confirm"]

    crea(archivio, kind="focuser", name="EAF")
    crea(archivio, kind="camera", name="ASI533MC")

    assert archivio.get("/api/v1/review").json()["to_confirm"] == prima


def monta(client, rig_id, mount_id):
    return client.put(f"/api/v1/gear/rigs/{rig_id}/mount", json={"mount_id": mount_id})


def test_a_rig_gets_its_mount_from_its_card_and_its_frames_go_back_to_be_read(archivio):
    """La montatura si sceglie dalla scheda del corredo (Marco, 26/9/2026), fra quelle che
    possiedi. Le pose di quel corredo tornano a `normalize`, che la scrive su ognuna: e' da li'
    che la montatura prende le ore."""
    montatura = crea(archivio, kind="mount", name="EQ6-R").json()["id"]
    corredo = archivio.get("/api/v1/gear").json()["rigs"][0]
    assert corredo["mount_id"] is None

    with mock.patch.object(work, "after", return_value=True):
        risposta = monta(archivio, corredo["id"], montatura)

    assert risposta.status_code == 200, risposta.text
    assert risposta.json()["requeued"] == 2
    assert archivio.get("/api/v1/gear").json()["rigs"][0]["mount_id"] == montatura

    with mock.patch.object(work, "after", return_value=True):
        monta(archivio, corredo["id"], None)
    assert archivio.get("/api/v1/gear").json()["rigs"][0]["mount_id"] is None


def test_only_a_mount_you_own_can_be_the_mount_of_a_rig(archivio):
    corredo = archivio.get("/api/v1/gear").json()["rigs"][0]
    ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]

    assert monta(archivio, corredo["id"], ottica).status_code == 422
    assert monta(archivio, corredo["id"], 9999).status_code == 422
    assert monta(archivio, 9999, None).status_code == 404


def test_you_can_write_a_filter_you_have_not_used_yet(archivio):
    """Nasce subito nell'elenco, con la sua banda e zero ore, e non e' una domanda."""
    prima = archivio.get("/api/v1/review").json()["to_confirm"]
    risposta = archivio.post(
        "/api/v1/gear/filters",
        json={"name": "Antlia 3nm", "bands": [{"band": "HA", "width_nm": 3}], "brand": "Antlia"},
    )
    assert risposta.status_code == 201, risposta.text
    # un filtro appena nato non ha pose: niente da rifare, e il lavoro non parte
    assert (risposta.json()["requeued"], risposta.json()["run_started"]) == (0, False)
    scritto = next(
        f for f in archivio.get("/api/v1/gear").json()["filters"] if f["name"] == "Antlia 3nm"
    )
    assert scritto["bands"] == [{"band": "HA", "width_nm": 3.0}]
    assert (scritto["frames"], scritto["counted"], scritto["brand"]) == (0, True, "Antlia")
    assert archivio.get("/api/v1/review").json()["to_confirm"] == prima


def test_a_filter_needs_a_name_you_do_not_own_and_its_band(archivio):
    gia = archivio.post("/api/v1/gear/filters", json={"name": "Ha", "bands": [{"band": "HA"}]})
    assert (gia.status_code, gia.json()["detail"]["code"]) == (409, "name_taken")
    assert (
        archivio.post("/api/v1/gear/filters", json={"name": "Nuovo", "bands": []}).status_code
        == 422
    )


def test_you_can_write_a_rig_before_shooting_with_it(archivio):
    ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]
    camera = crea(archivio, kind="camera", name="ASI533MC").json()["id"]
    risposta = archivio.post(
        "/api/v1/gear/rigs", json={"optics_id": ottica, "camera_id": camera, "focal_mm": 910}
    )
    assert risposta.status_code == 201, risposta.text
    assert (risposta.json()["requeued"], risposta.json()["run_started"]) == (0, False)
    nuovo = next(
        r for r in archivio.get("/api/v1/gear").json()["rigs"] if r["camera"] == "ASI533MC"
    )
    assert (nuovo["optics"], nuovo["focal_mm"], nuovo["frames"], nuovo["counted"]) == (
        "TS 130 APO",
        910.0,
        0,
        True,
    )


def test_a_rig_you_have_or_not_made_of_optics_and_camera_is_refused(archivio):
    ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]
    camera = pezzo(archivio, "camera", "ASI2600MM")["id"]
    uguale = archivio.post(
        "/api/v1/gear/rigs", json={"optics_id": ottica, "camera_id": camera, "focal_mm": 920}
    )
    assert (uguale.status_code, uguale.json()["detail"]["code"]) == (409, "rig_exists")
    storto = archivio.post(
        "/api/v1/gear/rigs", json={"optics_id": camera, "camera_id": ottica, "focal_mm": 910}
    )
    assert (storto.status_code, storto.json()["detail"]["code"]) == (422, "wrong_kind")
    senza = archivio.post("/api/v1/gear/rigs", json={"optics_id": ottica, "camera_id": camera})
    assert senza.status_code == 422


def test_what_you_write_by_hand_goes_to_the_bottom_not_the_top(archivio):
    """L'elenco va dal piu' usato: un filtro o un corredo appena scritto, con zero ore, sta in fondo
    -- visto dal vivo, nasceva in cima."""
    archivio.post("/api/v1/gear/filters", json={"name": "Nuovo", "bands": [{"band": "OIII"}]})
    ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]
    camera = crea(archivio, kind="camera", name="ASI533MC").json()["id"]
    archivio.post(
        "/api/v1/gear/rigs", json={"optics_id": ottica, "camera_id": camera, "focal_mm": 500}
    )

    pagina = archivio.get("/api/v1/gear").json()
    assert pagina["filters"][-1]["name"] == "Nuovo"
    assert pagina["rigs"][-1]["camera"] == "ASI533MC"
