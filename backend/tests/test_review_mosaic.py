"""Da confermare, i pannelli affiancati: l'app propone un mosaico e l'utente risponde una volta.

Il banco riproduce il caso che ha deciso le regole (Marco, 12/9/2026): quattro pannelli veri
identificati come **oggetti diversi** -- quattro, rimisurati il 14/9/2026 sull'archivio intero --
quindi si raggruppa per corredo e regione; e due regioni dello stesso corredo, ognuna con la sua
risposta. Le regole stanno in `spine/mosaic.py` e nel contratto `docs/domini/mosaico.md`.
"""

import re

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.spine import declarations as decl
from astrolog.spine import gear, mosaic, mosaic_proposals, mosaic_weight, stages
from astrolog.spine.group import group_frames
from astrolog.spine.identify import identify_frames
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from conftest import apply, correct, db, populate, review, to_confirm_without, write_fits


def _piano(conn, query, parametri=()):
    return [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query, parametri)]


@pytest.mark.parametrize(
    ("query", "parametri"),
    [
        (mosaic_proposals.LIVE, ()),
        (mosaic_proposals._MOSAICS, (decl.EntityType.MOSAIC, decl.MOSAIC_FIELD)),
        (mosaic_proposals._SUBJECTS, ()),
        (mosaic_weight._WORK, ("[]",)),
    ],
    ids=["LIVE", "_MOSAICS", "_SUBJECTS", "mosaic_weight._WORK"],
)
def test_mosaic_proposals_read_the_poses_of_the_panels_from_the_index_alone(conn, query, parametri):
    """I mosaici proposti e chi pesa i pannelli contano le pose dei pannelli e ne cercano gli
    oggetti dall'indice, senza la tabella: leggerle dalla tabella costerebbe una riga per posa."""
    piano = _piano(conn, query, parametri)
    pose = [p for p in piano if re.match(r"(SCAN|SEARCH) f\b", p)]
    assert pose and all(re.search(r"COVERING INDEX frames_panel\b", p) for p in pose), piano


def test_mosaic_subjects_are_named_once_per_object_not_once_per_pose(conn):
    """Gli oggetti dei pannelli si tolgono dai doppi prima di cercarne il nome: cercarlo prima
    vorrebbe dire due ricerche per ogni posa di ogni pannello, per poi buttarne quasi tutte."""
    piano = _piano(conn, mosaic_proposals._SUBJECTS)
    doppi = next(i for i, p in enumerate(piano) if "FOR DISTINCT" in p)
    nomi = next(i for i, p in enumerate(piano) if "CORRELATED" in p)
    assert doppi < nomi, piano


CAM, OTT = "ZWO ASI2600MM", "Newton 200/800"
# L'inquadratura di quel corredo, e il passo fra un pannello e il successivo: i rettangoli si
# sovrappongono (1.5 di lato contro un passo di 1.0) e nessuno contiene l'altro, che e' la
# definizione di due pannelli. Il dithering e' un ventesimo del passo: non spezza un pannello.
LATO, ALTO, PASSO, DITHER = 1.5, 1.0, 1.0, 0.05
RA0, DEC = 80.0, 34.0
# I quattro pannelli di QUESTO banco portano tre nomi: ogni pannello inquadra una parte diversa
# del complesso, e l'app li identifica come oggetti diversi -- e' la ragione per cui il soggetto
# non e' il criterio. Quanti siano non e' il punto: sull'archivio vero sono quattro (14/9/2026).
NOMI = ["LDN 1516", "IC 405", "IC 405", "SH2 230"]
ALTROVE = (200.0, 20.0)  # una regione ripresa in un'inquadratura sola: non c'e' niente da proporre


def _posa(path, minuto, oggetto, *, corredo=True):
    """Una posa di quel corredo: ottica, camera e focale, cosi' il corredo e' uno solo. Senza
    corredo, una posa che non dice con che cosa e' stata ripresa."""
    card = {
        "IMAGETYP": "Light Frame",
        "EXPTIME": 300.0,
        "DATE-OBS": f"2026-03-14T21:{minuto:02d}:00",
        "OBJECT": oggetto,
    }
    if corredo:
        card |= {"TELESCOP": OTT, "INSTRUME": CAM, "FOCALLEN": 800.0}
    return write_fits(path, card)


def _cielo(conn, nome, ra, dec):
    """Il cielo che il solver avrebbe misurato su quella posa. Si scrive la riga e si rifa'
    l'identificazione, come fa il giro vero quando il solve va a buon fine."""
    frame_id = conn.execute(
        "SELECT f.id FROM frames f JOIN positions p ON p.frame_id = f.id WHERE p.rel_path LIKE ?",
        (f"%{nome}",),
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
        " height_deg, rotation_deg, solved_at) VALUES(?, ?, ?, 2.0, ?, ?, 0, 'x')",
        (frame_id, ra, dec, LATO, ALTO),
    )
    stages.set_status(conn, frame_id, "solve", "done")
    stages.invalidate(conn, [frame_id], "identify")


def _archivio(root, db_path, *, corredo=True):
    """Quattro pannelli affiancati da due pose ciascuno, piu' un'inquadratura sola altrove."""
    minuto = 0
    for i, nome in enumerate(NOMI):
        for j in range(2):
            _posa(root / f"p{i}_{j}.fits", minuto, nome, corredo=corredo)
            minuto += 1
    for j in range(2):
        _posa(root / f"sola_{j}.fits", minuto + j, "M 51", corredo=corredo)
    populate(db_path, root)
    conn = connect(db_path)
    try:
        for i in range(len(NOMI)):
            for j in range(2):
                # la seconda posa di ogni pannello e' dithered: e' lo stesso puntamento
                _cielo(conn, f"p{i}_{j}.fits", RA0 + i * PASSO + j * DITHER, DEC)
        for j in range(2):
            _cielo(conn, f"sola_{j}.fits", ALTROVE[0] + j * DITHER, ALTROVE[1])
        list(identify_frames(conn))
        list(group_frames(conn))  # le proposte le scrive chi raggruppa, come nella spina vera
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def pagina(db_path, tmp_path):
    _archivio(tmp_path / "lib", db_path)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _mosaici(client):
    return review(client)["mosaics"]


def _risposta(client, riga, answer, name="IC 405"):
    """Si risponde con cio' che la pagina ha in mano: la chiave del mosaico, e col si' **di cosa**
    e' il mosaico, che col no non c'e'."""
    corpo = {"key": riga["key"], "answer": answer}
    if answer == "yes":
        corpo["name"] = name
    return apply(client, mosaics=[corpo])


def _chiavi(client):
    """`{nome del file: mosaico}` come lo dice la colonna della posa."""
    with db(client) as conn:
        return {
            r["rel_path"].rsplit("/", 1)[-1]: r["mosaic_key"]
            for r in conn.execute(
                "SELECT p.rel_path, f.mosaic_key FROM frames f"
                " JOIN positions p ON p.frame_id = f.id"
            )
        }


def test_the_question_asks_what_the_mosaic_is_of_and_the_answer_names_it(pagina):
    """Una domanda sola: si', e' un mosaico, **ed e' IC 405**. Il campo arriva compilato con una
    proposta, e il nome che resta e' quello detto dall'utente, portato sulla voce di catalogo."""
    riga = _mosaici(pagina)[0]
    assert riga["proposed"] in riga["names"]
    assert set(riga["object"].split(", ")) <= set(riga["names"]), "i soggetti sono suggerimenti"
    _risposta(pagina, riga, "yes", name="IC 405")
    assert (_mosaici(pagina)[0]["answer"], _mosaici(pagina)[0]["answer_name"]) == ("yes", "IC 405")


def test_the_answer_is_written_on_the_poses_of_the_mosaic_only(pagina):
    """Dopo il si' le otto pose dei pannelli portano il mosaico, le due riprese altrove no."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    chiavi = _chiavi(pagina)
    pannelli = {v for k, v in chiavi.items() if k.startswith("p")}
    assert len(pannelli) == 1 and None not in pannelli
    assert {v for k, v in chiavi.items() if k.startswith("sola")} == {None}


def test_after_the_yes_the_archive_shows_the_mosaic_as_one_row(pagina):
    """**L'uscita del piano**: rispondo che quei pannelli sono IC 405, apro
    l'Archivio e c'e' una riga sola, IC 405, con i frame di tutti i pannelli. I tre oggetti dei
    pannelli non hanno piu' una riga loro; M 51, ripreso altrove, si'."""
    _risposta(pagina, _mosaici(pagina)[0], "yes", name="IC 405")

    righe = pagina.get("/api/v1/archive").json()["items"]

    assert sorted((r["name"], r["frames"]) for r in righe) == [("IC 405", 8), ("M 51", 2)]
    mosaico = next(r for r in righe if r["name"] == "IC 405")
    assert mosaico["key"] == next(iter({v for k, v in _chiavi(pagina).items() if k[0] == "p"}))
    assert mosaico["integration_s"] == 8 * 300.0
    assert mosaico["panels"] == 4, "quanti pannelli li ha scritti chi ha risposto, non la lettura"


def test_the_page_reads_the_proposals_without_redoing_the_geometry(pagina, monkeypatch):
    """Una lettura non calcola (Marco, 22/9/2026): con la geometria che esplode, Da confermare
    risponde lo stesso, coi suoi mosaici. Il contratto degli import guarda chi importa cosa; questa
    guarda cosa gira davvero, anche passando da un'altra strada."""

    def esplode(*_a, **_k):
        raise AssertionError("la pagina ha rifatto la geometria")

    monkeypatch.setattr(mosaic, "overlap", esplode)
    monkeypatch.setattr(mosaic, "same_pointing", esplode)

    assert [(m["panels"], m["frames"]) for m in _mosaici(pagina)] == [(4, 8)]


def test_the_route_narrows_to_the_mosaics_and_counts_them_apart(pagina):
    """Dalla rotta: "solo i mosaici" tiene la riga del mosaico, e la conta dice quanti oggetti e
    quanti mosaici ha trovato. Un valore che non e' un si' o un no e' un 422, non un filtro."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")

    tutte = pagina.get("/api/v1/archive").json()
    solo = pagina.get("/api/v1/archive", params={"mosaic": "true"}).json()

    assert tutte["found"] == {"objects": 1, "mosaics": 1}
    assert tutte["choices"]["mosaics"] is True
    assert [(r["name"], r["panels"]) for r in solo["items"]] == [("IC 405", 4)]
    assert solo["found"] == {"objects": 0, "mosaics": 1}
    assert pagina.get("/api/v1/archive", params={"mosaic": "pippo"}).status_code == 422


def _pannelli(client):
    return {v for k, v in _chiavi(client).items() if k.startswith("p")}


def test_renaming_the_camera_keeps_the_mosaic(pagina):
    """La chiave del mosaico non porta la camera: rinominata, il mosaico resta com'era."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    prima = _pannelli(pagina)
    with db(pagina) as conn:
        cam = conn.execute("SELECT id FROM instruments WHERE name = ?", (CAM,)).fetchone()["id"]
    assert correct(pagina, cam, name="La mia camera").status_code == 200
    assert [r["answer"] for r in _mosaici(pagina)] == ["yes"]
    assert _pannelli(pagina) == prima and None not in prima


def test_merging_the_camera_into_another_keeps_the_mosaic(pagina):
    """Unita la camera a un'altra, le pose tornano in coda e ripassano dalla spina: restano nel
    loro mosaico, anche a spina ferma, perche' la sua chiave non porta la camera."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    prima = _pannelli(pagina)
    with db(pagina) as conn:
        cam = conn.execute("SELECT id FROM instruments WHERE name = ?", (CAM,)).fetchone()["id"]
        tenuta = conn.execute(
            "INSERT INTO instruments(kind, name, created_at) VALUES('camera', 'La mia camera', 'x')"
        ).lastrowid
        # dalla spina e non dall'Applica, che fa ripartire il lavoro da solo: qui si guarda il
        # momento in mezzo, con le pose in coda e la spina ferma
        gear.merge_instrument(conn, cam, tenuta)
        conn.commit()
    assert _pannelli(pagina) == prima
    with db(pagina) as conn:
        list(normalize_frames(conn))
        list(identify_frames(conn))
        list(group_frames(conn))
        conn.commit()
    assert [r["answer"] for r in _mosaici(pagina)] == ["yes"]
    assert _pannelli(pagina) == prima


def test_a_group_run_stopped_halfway_still_writes_the_mosaic(pagina, tmp_path):
    """Ogni posa di `group` si salva da sola, e una corsa si puo' fermare: il mosaico si scrive
    all'inizio, o le pose gia' raggruppate -- non piu' pronte -- resterebbero fuori per sempre."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    _posa(tmp_path / "lib" / "p4_0.fits", 30, "IC 410")
    _posa(tmp_path / "lib" / "p4_1.fits", 31, "IC 410")
    with db(pagina) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))
        _cielo(conn, "p4_0.fits", RA0 - PASSO, DEC)
        _cielo(conn, "p4_1.fits", RA0 - PASSO + DITHER, DEC)
        list(identify_frames(conn))
        corsa = group_frames(conn)
        next(corsa)  # la prima posa, e poi ci si ferma
        corsa.close()
        conn.commit()
    chiavi = _chiavi(pagina)
    assert chiavi["p4_0.fits"] == chiavi["p4_1.fits"] == chiavi["p0_0.fits"] is not None


def test_poses_that_arrive_later_join_the_mosaic_when_the_spine_groups_them(pagina, tmp_path):
    """Un pannello nuovo entra nel mosaico gia' confermato quando la spina lo raggruppa: lo scrive
    chi scrive, e l'Archivio non ricalcola niente."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    _posa(tmp_path / "lib" / "p4_0.fits", 30, "IC 410")
    with db(pagina) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))
        _cielo(conn, "p4_0.fits", RA0 - PASSO, DEC)
        list(identify_frames(conn))
        list(group_frames(conn))
        conn.commit()
    chiavi = _chiavi(pagina)
    assert chiavi["p4_0.fits"] is not None
    assert chiavi["p4_0.fits"] == chiavi["p0_0.fits"]


@pytest.mark.parametrize(
    "corpo, perche_",
    [
        ({"answer": "yes"}, "un si' senza dire di cosa"),
        ({"answer": "yes", "name": "   "}, "un nome di soli spazi"),
        ({"answer": "no", "name": "IC 405"}, "un no con un nome"),
    ],
)
def test_a_yes_says_what_and_a_no_does_not(pagina, corpo, perche_):
    riga = _mosaici(pagina)[0]
    corpo = {"key": riga["key"], **corpo}
    r = pagina.post("/api/v1/review/apply", json={"mosaics": [corpo]})
    assert r.status_code == 422, perche_


def test_the_app_proposes_a_mosaic_and_never_merges_by_itself(pagina):
    """Una proposta per regione ripresa a pannelli, con quanti pannelli e quante pose: e' cio' che
    l'utente legge per decidere. L'inquadratura sola non compare -- non c'e' niente da proporre --
    e la risposta nasce **vuota**: l'app propone e non decide mai da sola."""
    righe = _mosaici(pagina)
    assert len(righe) == 1
    assert (righe[0]["panels"], righe[0]["frames"], righe[0]["answer"]) == (4, 8, None)


def test_the_panels_are_gathered_even_though_they_are_three_different_objects(pagina):
    """I quattro pannelli di questo banco portano **tre** nomi diversi: ogni pannello inquadra
    una parte diversa del complesso. Raggruppando per soggetto il mosaico si spezzerebbe, quindi il
    criterio e' corredo e regione -- e la proposta dice quali soggetti tocca, in ordine alfabetico.

    Qui l'alfabetico e l'ordine di lettura sono diversi apposta -- i pannelli si leggono LDN, IC,
    SH2 -- perche' con dei nomi gia' in ordine la regola non si vedrebbe: chi cambiasse il `sorted`
    non troverebbe un rosso ad aspettarlo."""
    riga = _mosaici(pagina)[0]
    soggetti = riga["object"].split(", ")
    assert len(soggetti) == 3
    assert riga["panels"] == 4
    assert soggetti == sorted(soggetti)


def test_the_proposal_carries_the_hours_of_its_panels(pagina):
    """La proposta dice le ore, non solo quante pose: otto pose da 300 secondi fanno 2400, e sono
    la somma dei quattro pannelli. E' cio' che rende la domanda leggibile -- "quattro pannelli,
    337 pose" non dice quanto cielo c'e' dentro."""
    riga = _mosaici(pagina)[0]
    assert (riga["frames"], riga["integration_s"], riga["untimed"]) == (8, 2400.0, 0)


def test_answering_yes_is_an_answer_that_lasts(pagina):
    """Si risponde una volta e la risposta resta, come per i filtri e gli oggetti. Il gruppo resta
    in pagina con la sua risposta, perche' si deve poter cambiare idea."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    assert [r["answer"] for r in _mosaici(pagina)] == ["yes"]


def test_a_no_is_an_answer_like_a_yes(pagina):
    """Un no e' una risposta: senza, l'unico modo di far tacere una proposta sbagliata sarebbe
    accettarla. Resta in pagina, e non si richiede piu'."""
    _risposta(pagina, _mosaici(pagina)[0], "no")
    righe = _mosaici(pagina)
    assert [r["answer"] for r in righe] == ["no"]
    assert all(r["answer"] is not None for r in righe)


def test_answering_again_changes_the_answer(pagina):
    """Si cambia idea rispondendo di nuovo: la seconda risposta sostituisce la prima invece di
    aggiungersi, e la pagina mostra quella di adesso."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    _risposta(pagina, _mosaici(pagina)[0], "no")
    assert [r["answer"] for r in _mosaici(pagina)] == ["no"]


def test_the_page_still_shows_the_answer_after_a_scan_adds_a_panel(pagina, tmp_path):
    """Un pannello in piu' non fa ricominciare da capo: entra nel mosaico gia' risposto. Passa
    dalla **rotta**, con una scansione vera in mezzo, perche' e' li' che la catena si rompe senza
    farsi sentire -- il pezzo puro regge e quello che lo collega no."""
    _risposta(pagina, _mosaici(pagina)[0], "yes")
    _posa(tmp_path / "lib" / "p4_0.fits", 30, "IC 410")
    with db(pagina) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))
        _cielo(conn, "p4_0.fits", RA0 - PASSO, DEC)
        list(identify_frames(conn))
        list(group_frames(conn))
        conn.commit()
    riga = _mosaici(pagina)[0]
    assert (riga["panels"], riga["answer"]) == (5, "yes")


def test_two_regions_of_the_same_rig_keep_their_own_answers(pagina, tmp_path):
    """Un corredo solo ha ripreso 13 regioni distinte sull'archivio vero: una risposta agganciata al
    corredo le avrebbe zittite tutte. Si risponde su una e l'altra resta aperta."""
    for j in range(2):
        _posa(tmp_path / "lib" / f"q_{j}.fits", 40 + j, "NGC 7000")
        _posa(tmp_path / "lib" / f"r_{j}.fits", 50 + j, "Pellicano")
    with db(pagina) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))
        for j in range(2):
            _cielo(conn, f"q_{j}.fits", ALTROVE[0] + j * DITHER, ALTROVE[1])
            _cielo(conn, f"r_{j}.fits", ALTROVE[0] + PASSO + j * DITHER, ALTROVE[1])
        list(identify_frames(conn))
        list(group_frames(conn))
        conn.commit()
    righe = _mosaici(pagina)
    assert len(righe) == 2
    _risposta(pagina, righe[0], "yes")
    assert sorted(r["answer"] or "" for r in _mosaici(pagina)) == ["", "yes"]


def test_an_unanswered_mosaic_counts_among_the_things_to_confirm(pagina):
    """Un mosaico senza risposta e' una domanda aperta e si conta; quello a cui si e' risposto resta
    in pagina ma non si conta piu'.

    Il resto si rimisura sulla pagina di **dopo**, non su quella di prima: Applica vuol dire anche
    "ho visto la pagina", quindi conferma tutto cio' che elencava, e un resto preso prima
    parlerebbe di un archivio che dopo non c'e' piu'."""
    letta = review(pagina)
    assert letta["to_confirm"] == to_confirm_without(letta, "mosaics") + 1
    _risposta(pagina, letta["mosaics"][0], "no")
    dopo = review(pagina)
    assert dopo["mosaics"][0]["answer"] == "no"
    assert dopo["to_confirm"] == to_confirm_without(dopo, "mosaics")


def test_the_answer_does_not_put_any_pose_back_in_the_queue(pagina):
    """Rispondere non rimette in coda nessuna posa: il mosaico sulle pose lo scrive la risposta
    stessa, e rilavorare le pose di una regione sarebbe lavoro buttato, con l'utente ad aspettarlo.
    Ma la risposta **conta** come una modifica, altrimenti
    l'Applica direbbe di non aver fatto niente proprio mentre scriveva."""
    esito = _risposta(pagina, _mosaici(pagina)[0], "yes")
    assert (esito["requeued"], esito["changed"]) == (0, 1)


def test_a_mosaic_that_is_not_there_is_refused(pagina):
    """Una chiave che non e' di nessun mosaico e' una pagina vecchia, e si dice: scrivere una
    risposta verso il nulla la lascerebbe li' per sempre senza che nessuno la veda."""
    corpo = {"key": "nessuno", "answer": "yes", "name": "IC 405"}
    r = pagina.post("/api/v1/review/apply", json={"mosaics": [corpo]})
    assert r.status_code == 404


@pytest.mark.parametrize(
    "cambio, perche_",
    [
        ({"answer": "forse"}, "ne' un si' ne' un no"),
        ({"answer": ""}, "una risposta vuota"),
        ({"key": ""}, "un mosaico senza chiave"),
    ],
)
def test_an_answer_that_is_not_yes_or_no_is_refused(pagina, cambio, perche_):
    """Le risposte possibili sono due, e la forma della richiesta lo dichiara: cosi' l'OpenAPI lo
    dice al frontend e la risposta e' il 422 di sempre."""
    riga = _mosaici(pagina)[0]
    corpo = {"key": riga["key"], "answer": "yes", "name": "IC 405", **cambio}
    r = pagina.post("/api/v1/review/apply", json={"mosaics": [corpo]})
    assert r.status_code == 422, perche_


@pytest.mark.parametrize("answer", ["yes", "no"])
def test_saying_the_camera_of_the_poses_keeps_the_mosaic(db_path, tmp_path, answer):
    """Pose che non dicono la camera: si risponde sul mosaico, poi sulla scheda della loro firma, e
    le pose passano al corredo vero. Il mosaico resta com'era -- col si' nell'Archivio col suo nome,
    col no senza tornare fra le domande -- invece di sparire in silenzio alla corsa dopo."""
    _archivio(tmp_path / "lib", db_path, corredo=False)
    with TestClient(create_app(db_path), base_url="http://localhost") as pagina:
        _risposta(pagina, _mosaici(pagina)[0], answer)
        firma = next(g["key"] for g in review(pagina)["gear"] if g["asks_camera"])
        apply(pagina, gear=[{"key": firma, "optics": OTT, "camera": CAM, "focal_mm": 800.0}])
        with db(pagina) as conn:
            list(normalize_frames(conn))
            list(identify_frames(conn))
            list(group_frames(conn))
            conn.commit()

        (mosaico,) = _mosaici(pagina)
        assert mosaico["answer"] == answer
        righe = pagina.get("/api/v1/archive").json()["items"]
        nomi = sorted((r["name"], r["frames"]) for r in righe)
        assert (("IC 405", 8) in nomi) == (answer == "yes")
