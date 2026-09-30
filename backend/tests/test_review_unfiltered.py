"""Da confermare, le pose che non dicono il filtro: una domanda per camera (Marco, 2026-09-11).

Senza `BAYERPAT` l'app non distingue una mono da una camera a colori, quindi "FILTER assente" e
"FILTER=none" sono la stessa domanda: che camera e'. Una camera che i suoi file dicono a colori
non si chiede (Marco, 23/9/2026). Le regole stanno in `spine/unfiltered.py` e nel contratto
`docs/domini/spina.md`. L'archivio e' fatto qui, piccolo: una mono che non scrive il filtro (con
una copia calibrata), una camera con un solo file che porta la matrice, e una OSC.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from astrolog.spine.unfiltered import says_no_filter
from conftest import (
    apply,
    by_name,
    correct,
    da_rivedere,
    db,
    gear,
    populate,
    review,
    senza_soggetti,
    write_fits,
)

# In ordine alfabetico la seconda verrebbe prima: la pagina mette in cima la piu' numerosa.
MONO, COLORI, OSC = "ZWO ASI6200MM", "ZWO ASI533MC", "ZWO ASI2600MC"


def _posa(path, minuto, **header):
    # il pixel c'e', come in ogni header vero; e l'ottica, o il banco chiederebbe anche quella
    card = {"IMAGETYP": "Light Frame", "OBJECT": "M 31", "EXPTIME": 300.0, "TELESCOP": "RC8"}
    card |= {"XPIXSZ": 3.76, "XBINNING": 1}
    return write_fits(path, {**card, "DATE-OBS": f"2024-05-17T21:{minuto:02d}:00", **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):
        _posa(root / f"mono_{i}.fits", i, INSTRUME=MONO)  # il file non scrive il filtro
    _posa(root / "mono_none.fits", 10, INSTRUME=MONO, FILTER="none")
    _posa(root / "mono_open.fits", 11, INSTRUME=MONO, FILTER="open")
    _posa(root / "mono_ha.fits", 12, INSTRUME=MONO, FILTER="Ha")  # questa lo dice: non si chiede
    _posa(root / "mono_l.fits", 13, INSTRUME=MONO, FILTER="L")  # un filtro a banda larga
    _posa(root / "calibrate" / "mono_0.fits", 0, INSTRUME=MONO, CALSTAT="BDF")  # la copia
    _posa(root / "colori_0.fits", 20, INSTRUME=COLORI, BAYERPAT="RGGB")
    for i in range(2):
        _posa(root / f"colori_senza_{i}.fits", 30 + i, INSTRUME=COLORI)  # un altro programma
    for i in range(4):  # una OSC: la matrice c'e', il filtro no
        _posa(root / f"osc_{i}.fits", 40 + i, INSTRUME=OSC, BAYERPAT="RGGB")
    _posa(root / "osc_senza.fits", 44, INSTRUME=OSC)  # un altro programma, sulla stessa OSC
    _posa(root / "osc_duo.fits", 45, INSTRUME=OSC, BAYERPAT="RGGB", FILTER="L-eXtreme")
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _gruppi(client):
    return {g["key"]: g for g in review(client)["unfiltered"]}


def _filtri_senza_nome(client, camera):
    """I nomi dei filtri delle pose di quella camera che non dicono il filtro (e nemmeno la
    matrice di Bayer)."""
    with db(client) as conn:
        righe = conn.execute(
            "SELECT f.filter_raw, fi.name FROM frames f JOIN rigs r ON r.id = f.rig_id"
            " JOIN instruments i ON i.id = r.camera_id LEFT JOIN filters fi ON fi.id = f.filter_id"
            " WHERE i.name = ? AND f.bayer_pattern IS NULL",
            (camera,),
        ).fetchall()
    return {r["name"] for r in righe if says_no_filter(r["filter_raw"])}


def _scheda(client, nome):
    return by_name(gear(client)["instruments"], nome)


def _filtro_del_file(client, nome):
    with db(client) as conn:
        riga = conn.execute(
            "SELECT fi.name FROM frames f JOIN positions p ON p.frame_id = f.id"
            " LEFT JOIN filters fi ON fi.id = f.filter_id WHERE p.rel_path LIKE ?",
            (f"%{nome}",),
        ).fetchone()
    return riga["name"]


def _scansiona_ancora(client):
    with db(client) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))


def test_a_question_per_camera_with_the_largest_first(pagina):
    """Una domanda per camera, la piu' numerosa in cima, con quante pose -- `open` e' come `none`,
    la copia calibrata non e' un'altra posa. Un solo file con la matrice su tre non fa la camera a
    colori: decide la maggioranza dei file, e le due senza restano da chiedere. Quella con la
    matrice non si conta: e' OSC, e nessuna risposta la sposta."""
    assert [senza_soggetti(g) for g in review(pagina)["unfiltered"]] == [
        {"key": MONO, "frames": 5, "answer": None, "filter_id": None},
        {"key": COLORI, "frames": 2, "answer": None, "filter_id": None},
    ]
    assert _filtri_senza_nome(pagina, COLORI) == {None}


def test_a_camera_its_files_say_colour_is_not_asked_and_its_poses_are_osc(pagina):
    """Se i file dicono il sensore a colori la camera e' a colori, e non si chiede (Marco,
    23/9/2026): le sue pose che non dicono il filtro sono OSC, anche quella di un programma che la
    matrice non la scrive: i file votano prima del giro. La posa che il filtro lo scrive resta col
    suo filtro."""
    assert OSC not in _gruppi(pagina)
    assert _filtro_del_file(pagina, "osc_0.fits") == "OSC"
    assert _filtro_del_file(pagina, "osc_senza.fits") == "OSC"
    assert _filtro_del_file(pagina, "osc_duo.fits") == "L-eXtreme"


def test_answering_no_filter_on_a_colour_camera_does_not_call_it_mono(pagina):
    """Su una camera a colori "nessun filtro" vuol dire il sensore nudo, cioe' OSC: la risposta
    parla del filtro e non riscrive il sensore sulla scheda. La pagina non la chiede piu', ma una
    pagina aperta prima del voto dei file puo' ancora mandarla."""
    apply(pagina, unfiltered=[{"key": OSC, "answer": "no_filter"}])
    assert _scheda(pagina, OSC)["camera_type"] == "color"
    assert _filtro_del_file(pagina, "osc_0.fits") == "OSC"
    # restano le altre due camere (la COLORI ha un file con la matrice e due senza, e la
    # maggioranza non la dice a colori)
    assert review(pagina)["to_confirm"] == 2


def test_answering_colour_makes_those_poses_osc_and_the_next_ones_too(pagina, tmp_path):
    """ "A colori" vale per le pose che ci sono e per quelle che verranno, e come per chi scrive
    `BAYERPAT` un filtro a banda larga su una camera a colori e' OSC. Da li' la camera e' a colori
    e non si chiede piu': la risposta si cambia sulla sua scheda."""
    out = apply(pagina, unfiltered=[{"key": MONO, "answer": "color"}])
    assert out["requeued"] == 8  # le pose di quella camera senza matrice, copia compresa
    assert _filtri_senza_nome(pagina, MONO) == {"OSC"}
    assert _filtro_del_file(pagina, "mono_l.fits") == "OSC"
    assert MONO not in _gruppi(pagina)
    # resta la COLORI
    assert review(pagina)["to_confirm"] == 1
    _posa(tmp_path / "lib" / "mono_dopo.fits", 40, INSTRUME=MONO)
    _scansiona_ancora(pagina)
    assert _filtro_del_file(pagina, "mono_dopo.fits") == "OSC"


def test_answering_mono_with_no_filter_puts_them_on_no_filter(pagina):
    """ "Mono, nessun filtro": le pose vanno sulla riga esplicita "nessun filtro", che nel database
    non e' una frase italiana (a tradurla e' la pagina). E si puo' cambiare idea, in tutti e due i
    versi."""
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    assert _filtri_senza_nome(pagina, MONO) == {"None"}
    assert da_rivedere(pagina) == 0  # una risposta data: il filtro adesso si sa
    with db(pagina) as conn:
        riga = conn.execute("SELECT name, passband FROM filters WHERE is_none = 1").fetchall()
    assert [tuple(r) for r in riga] == [("None", "NONE")]
    assert _gruppi(pagina)[MONO]["answer"] == "no_filter"
    # la riga nata dalla risposta non si richiede, e resta aperta la COLORI
    assert review(pagina)["to_confirm"] == 1
    apply(pagina, unfiltered=[{"key": MONO, "answer": "color"}])
    assert _filtri_senza_nome(pagina, MONO) == {"OSC"}
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    assert _filtri_senza_nome(pagina, MONO) == {"None"}


def _id_nessun_filtro(client):
    """La riga "nessun filtro": non e' una domanda ne' una scelta, quindi si legge dal database."""
    with db(client) as conn:
        return conn.execute("SELECT id FROM filters WHERE is_none = 1").fetchone()["id"]


def _id_del_filtro(client, nome):
    return next(f["id"] for f in review(client)["filter_choices"] if f["name"] == nome)


def test_answering_one_of_my_filters_puts_them_on_it(pagina):
    """ "Uno dei tuoi filtri" (Marco, 25/9/2026): le pose vanno su quel filtro, che si sceglie fra
    quelli con la banda nota -- mai la riga "nessun filtro", che e' un'altra risposta. La camera ha
    risposto e non conta piu'."""
    scelte = {f["name"] for f in review(pagina)["filter_choices"]}
    assert {"H\u03b1", "Lum"} <= scelte and "None" not in scelte
    apply(
        pagina,
        unfiltered=[{"key": MONO, "answer": "filter", "filter_id": _id_del_filtro(pagina, "Lum")}],
    )
    assert _filtri_senza_nome(pagina, MONO) == {"Lum"}
    assert da_rivedere(pagina) == 0
    assert {k: _gruppi(pagina)[MONO][k] for k in ("answer", "filter_id")} == {
        "answer": "filter",
        "filter_id": _id_del_filtro(pagina, "Lum"),
    }
    # resta la COLORI
    assert review(pagina)["to_confirm"] == 1


def test_the_answer_follows_its_filter_when_it_is_renamed_or_merged(pagina):
    """La risposta tiene il NOME del filtro: rinominarlo o unirlo a un altro la porta con se', o
    quelle pose lo perderebbero con un avviso in un log."""
    apply(
        pagina,
        unfiltered=[{"key": MONO, "answer": "filter", "filter_id": _id_del_filtro(pagina, "Lum")}],
    )
    apply(pagina, filters=[{"id": _id_del_filtro(pagina, "Lum"), "name": "Astronomik L"}])
    assert _filtri_senza_nome(pagina, MONO) == {"Astronomik L"}
    assert _gruppi(pagina)[MONO]["filter_id"] == _id_del_filtro(pagina, "Astronomik L")
    ha = _id_del_filtro(pagina, "H\u03b1")
    apply(pagina, filters=[{"id": _id_del_filtro(pagina, "Astronomik L"), "merge_into": ha}])
    assert _filtri_senza_nome(pagina, MONO) == {"H\u03b1"}


def test_one_of_my_filters_does_not_beat_colour(pagina, tmp_path):
    """La risposta dice cosa c'era davanti a una mono: passando ad "a colori" quei frame vanno su
    OSC, e un frame con la matrice che arriva dopo e' OSC, qualunque cosa dica la risposta."""
    lum = _id_del_filtro(pagina, "Lum")
    apply(pagina, unfiltered=[{"key": MONO, "answer": "filter", "filter_id": lum}])
    _posa(tmp_path / "lib" / "mono_matrice.fits", 45, INSTRUME=MONO, BAYERPAT="RGGB")
    _scansiona_ancora(pagina)
    assert _filtro_del_file(pagina, "mono_matrice.fits") == "OSC"
    apply(pagina, unfiltered=[{"key": MONO, "answer": "color"}])
    assert _filtri_senza_nome(pagina, MONO) == {"OSC"}


def test_a_filter_named_like_an_answer_stays_a_filter(pagina):
    """Il filtro scelto sta in un campo suo, non in quello della risposta: un filtro che l'utente
    chiama proprio `no_filter` resta quel filtro, e non diventa la risposta "nessun filtro"."""
    lum = _id_del_filtro(pagina, "Lum")
    apply(pagina, filters=[{"id": lum, "name": "no_filter"}])
    apply(pagina, unfiltered=[{"key": MONO, "answer": "filter", "filter_id": lum}])
    assert _filtri_senza_nome(pagina, MONO) == {"no_filter"}


def test_one_of_my_filters_is_one_of_the_choices(pagina, tmp_path):
    """ "Uno dei tuoi" si sceglie fra i filtri con la banda nota: la riga "nessun filtro" e'
    un'altra risposta, e un filtro di cui non si sa la banda non dice cosa c'era davanti."""
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    _posa(tmp_path / "lib" / "mono_strano.fits", 46, INSTRUME=MONO, FILTER="Filter 3")
    _scansiona_ancora(pagina)
    strano = next(f for f in review(pagina)["filters"] if f["name"] == "Filter 3")
    assert strano["passband"] == "UNKNOWN"
    assert strano["id"] not in {f["id"] for f in review(pagina)["filter_choices"]}
    for filtro in (_id_nessun_filtro(pagina), strano["id"]):
        corpo = {"unfiltered": [{"key": MONO, "answer": "filter", "filter_id": filtro}]}
        assert pagina.post("/api/v1/review/apply", json=corpo).status_code == 404


@pytest.mark.parametrize(
    "risposta",
    [{"answer": "filter"}, {"answer": "no_filter", "filter_id": 1}],
)
def test_a_filter_goes_with_one_of_my_filters_and_only_there(pagina, risposta):
    """ "Uno dei tuoi" senza dire quale non e' una risposta, e un filtro accanto a un'altra risposta
    sarebbe un secondo bersaglio fra cui scegliere noi."""
    r = pagina.post("/api/v1/review/apply", json={"unfiltered": [{"key": MONO, **risposta}]})
    assert r.status_code == 422


def test_a_filter_that_is_not_there_is_refused(pagina):
    """Un filtro che non c'e' piu' (la pagina era vecchia) si dice, prima di scrivere."""
    corpo = {"unfiltered": [{"key": MONO, "answer": "filter", "filter_id": 999}]}
    assert pagina.post("/api/v1/review/apply", json=corpo).status_code == 404


def test_writing_colour_on_the_card_answers_too(pagina):
    """Il colore scritto sulla scheda della camera e' la stessa risposta: sposta le pose anche
    lui, invece di restare una scritta che nessuno legge, e la camera non si chiede piu'."""
    camera = _scheda(pagina, MONO)
    out = correct(pagina, camera["id"], camera_type="color").json()
    assert out["requeued"] == 8
    assert _filtri_senza_nome(pagina, MONO) == {"OSC"}
    assert MONO not in _gruppi(pagina)


def test_the_answer_about_the_filter_survives_a_change_of_sensor(pagina):
    """La risposta dice cosa c'era davanti, la scheda dice che sensore e': scrivere "a colori" non
    ritira "nessun filtro", la rilegge -- a colori e a nudo vuol dire OSC -- e tornando a mono le
    pose tornano sulla riga "nessun filtro", invece di lasciare una domanda riaperta a vuoto."""
    camera = _scheda(pagina, MONO)
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    correct(pagina, camera["id"], camera_type="mono")
    assert _gruppi(pagina)[MONO]["answer"] == "no_filter"
    correct(pagina, camera["id"], camera_type="color")
    assert MONO not in _gruppi(pagina)
    assert _filtri_senza_nome(pagina, MONO) == {"OSC"}
    correct(pagina, camera["id"], camera_type="mono")
    assert _gruppi(pagina)[MONO]["answer"] == "no_filter"
    assert _filtri_senza_nome(pagina, MONO) == {"None"}


def test_renaming_no_filter_does_not_answer_for_the_other_cameras(pagina, tmp_path):
    """Rinominare la riga "nessun filtro" non insegna una regola: una regola su `none`
    risponderebbe per ogni camera, anche per quella a cui nessuno ha chiesto e per quella che la
    matrice dice a colori."""
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    apply(pagina, filters=[{"id": _id_nessun_filtro(pagina), "name": "Nessun filtro"}])
    _posa(tmp_path / "lib" / "mono_dopo.fits", 43, INSTRUME=MONO)  # la riga si ritrova rinominata
    _posa(tmp_path / "lib" / "colori_none.fits", 40, INSTRUME=COLORI, FILTER="none")
    _posa(
        tmp_path / "lib" / "matrice_none.fits", 41, INSTRUME=COLORI, FILTER="none", BAYERPAT="RGGB"
    )
    _scansiona_ancora(pagina)
    assert _filtro_del_file(pagina, "colori_none.fits") is None
    assert _filtro_del_file(pagina, "matrice_none.fits") == "OSC"
    assert _filtri_senza_nome(pagina, MONO) == {"Nessun filtro"}
    assert _filtro_del_file(pagina, "mono_dopo.fits") == "Nessun filtro"
    # e il contro-caso: rinominare un filtro vero impara la regola sulla sua grafia, come sempre
    with db(pagina) as conn:
        ha = conn.execute("SELECT id FROM filters WHERE passband = 'HA'").fetchone()["id"]
    apply(pagina, filters=[{"id": ha, "name": "Baader Ha"}])
    with db(pagina) as conn:
        regole = {r[0] for r in conn.execute("SELECT target_key FROM header_aliases")}
    assert regole == {"Baader Ha"}  # e nessuna verso "Nessun filtro"


def test_a_no_filter_name_already_taken_is_said_not_crashed(pagina, caplog):
    """Se la riga "nessun filtro" non c'e' e il suo nome e' gia' di un altro filtro, non si
    indovina quale sia: le pose restano da rivedere, invece di fallire tutte."""
    with db(pagina) as conn:
        ha = conn.execute("SELECT id FROM filters WHERE passband = 'HA'").fetchone()["id"]
    apply(pagina, filters=[{"id": ha, "name": "None"}])
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    assert _filtri_senza_nome(pagina, MONO) == {None}
    assert da_rivedere(pagina) == 6  # restano da rivedere, copia compresa
    assert "nessun filtro, nome preso" in caplog.text  # e si dice
    stadi = pagina.app.state.worker.snapshot()["stages"]
    assert next(s for s in stadi if s["name"] == "normalize")["tally"]["errors"] == 0


def test_merging_two_cameras_carries_the_answer_to_the_one_kept(pagina, tmp_path):
    """Due grafie, una camera: la risposta della camera assorbita passa a quella tenuta, e le pose
    di quella tenuta la sentono anche loro."""
    _posa(tmp_path / "lib" / "asi6200_0.fits", 50, INSTRUME="ASI6200")
    _scansiona_ancora(pagina)
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    pezzi = {i["name"]: i["id"] for i in gear(pagina)["instruments"]}
    correct(pagina, pezzi[MONO], merge_into=pezzi["ASI6200"])
    assert _filtro_del_file(pagina, "asi6200_0.fits") == "None"
    assert _gruppi(pagina)["ASI6200"]["answer"] == "no_filter"


def test_renaming_a_camera_carries_its_answer(pagina):
    """La risposta sta sotto il nome della camera: rinominarla dall'Attrezzatura se la porta
    dietro, invece di lasciarla a un nome che non c'e' piu'."""
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    correct(pagina, _scheda(pagina, MONO)["id"], name="Mia mono")
    assert _gruppi(pagina)["Mia mono"]["answer"] == "no_filter"
    assert _filtri_senza_nome(pagina, "Mia mono") == {"None"}


def test_no_filter_is_not_merged_into_another_filter(pagina):
    """La riga "nessun filtro" non si unisce a un altro filtro: la sua grafia diventerebbe una
    regola su `none`, che risponderebbe per ogni camera. Si cambia la risposta sulla camera."""
    apply(pagina, unfiltered=[{"key": MONO, "answer": "no_filter"}])
    ha = next(f for f in review(pagina)["filter_choices"] if f["passband"] == "HA")
    corpo = {"filters": [{"id": _id_nessun_filtro(pagina), "merge_into": ha["id"]}]}
    r = pagina.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "merge_refused"


def test_merging_into_a_colour_camera_keeps_the_answer_that_arrives(pagina, tmp_path):
    """La risposta dell'assorbita passa alla tenuta anche quando la tenuta dice "a colori": li' e'
    il sensore a essere scritto, non il filtro. Finche' dice "a colori" le pose sono OSC; se la
    scheda torna mono la risposta e' ancora li', invece di essere sparita nell'unione."""
    _posa(tmp_path / "lib" / "asi6200_0.fits", 50, INSTRUME="ASI6200")
    _scansiona_ancora(pagina)
    apply(pagina, unfiltered=[{"key": "ASI6200", "answer": "no_filter"}])
    pezzi = {i["name"]: i["id"] for i in gear(pagina)["instruments"]}
    correct(pagina, pezzi[MONO], camera_type="color")
    correct(pagina, pezzi["ASI6200"], merge_into=pezzi[MONO])
    assert MONO not in _gruppi(pagina)
    correct(pagina, pezzi[MONO], camera_type="mono")
    assert _gruppi(pagina)[MONO]["answer"] == "no_filter"


def test_an_answer_about_a_camera_that_is_not_there_is_refused(pagina):
    """Una camera che non c'e' (la pagina era vecchia) si dice, invece di scrivere una regola
    verso il nulla."""
    r = pagina.post(
        "/api/v1/review/apply", json={"unfiltered": [{"key": "Nessuna", "answer": "color"}]}
    )
    assert r.status_code == 404
