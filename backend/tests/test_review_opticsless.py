"""Da confermare, la domanda **quale ottica era**: le pose i cui file non nominano l'ottica.

Con l'ASIAIR `TELESCOP` e' la montatura e l'ottica non sta da nessuna parte; altri file non
scrivono `TELESCOP` affatto. Quelle pose hanno un corredo **senza ottica**, e si chiede una volta
per camera e focale. La risposta si scrive sulla camera a quella focale, e `normalize` la da' a
ogni posa che non nomina l'ottica -- anche a quelle che arriveranno. Le regole stanno in
`spine/rig_optics.py`.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from astrolog.spine.stages import invalidate
from conftest import apply, correct, db, gear, populate, review, write_fits

CAM, ALTRA, NEWTON = "ZWO ASI2600MC Pro", "QHY268M", "Newton 200/800"
ASIAIR = {"CREATOR": "ZWO ASIAIR Plus", "TELESCOP": "ZWO AM5", "INSTRUME": CAM, "FOCALLEN": 800}


def _posa(path, minuto, **header):
    card = {
        "IMAGETYP": "Light Frame",
        "EXPTIME": 300.0,
        "DATE-OBS": f"2026-03-14T21:{minuto:02d}:00",
        "OBJECT": "M 51",
        "FILTER": "L",
    }
    return write_fits(path, {**card, **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):  # l'ASIAIR: la montatura in TELESCOP, l'ottica da nessuna parte
        _posa(root / "asiair" / f"a_{i}.fits", i, **ASIAIR)
    # la stessa camera, alla stessa focale, da un programma che l'ottica la scrive
    _posa(root / "nina" / "n_0.fits", 30, CREATOR="N.I.N.A.", TELESCOP=NEWTON, INSTRUME=CAM,
          FOCALLEN=800)  # fmt: skip
    # un file che TELESCOP non lo scrive affatto: un'altra camera, a un'altra focale
    _posa(root / "muta" / "m_0.fits", 40, INSTRUME=ALTRA, FOCALLEN=400)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _domande(client):
    return review(client)["opticsless"]


def _chiave(client, camera):
    return next(d["key"] for d in _domande(client) if d["camera"] == camera)


def _ottica_della_posa(client, nome):
    with db(client) as conn:
        riga = conn.execute(
            "SELECT o.name FROM frames f JOIN positions p ON p.frame_id = f.id"
            " JOIN rigs g ON g.id = f.rig_id LEFT JOIN instruments o ON o.id = g.optics_id"
            " WHERE p.rel_path LIKE ?",
            (f"%{nome}",),
        ).fetchone()
    return riga["name"]


def _corredo_della_posa(client, nome):
    with db(client) as conn:
        return conn.execute(
            "SELECT f.rig_id FROM frames f JOIN positions p ON p.frame_id = f.id"
            " WHERE p.rel_path LIKE ?",
            (f"%{nome}",),
        ).fetchone()[0]


def test_poses_that_do_not_name_the_optics_are_asked_once_per_camera_and_focal(pagina):
    """**La domanda.** Le tre pose ASIAIR sono una domanda sola, con la loro camera, la focale, le
    pose, le ore e cosa ci hai ripreso; il file senza `TELESCOP` un'altra. La posa di N.I.N.A.
    l'ottica la dice, e non si chiede."""
    domande = _domande(pagina)

    assert [(d["camera"], d["focal_mm"], d["frames"], d["integration_s"]) for d in domande] == [
        (CAM, 800.0, 3, 900.0),
        (ALTRA, 400.0, 1, 300.0),
    ]
    assert all(d["answer"] is None for d in domande)
    ripreso = domande[0]["subjects"]
    assert len(ripreso["found"]) + ripreso["not_found"] + ripreso["not_yet"] > 0


def test_the_answer_gives_the_optics_and_the_poses_join_the_rig_that_has_it(pagina):
    """Detta l'ottica, le pose ASIAIR stanno nel corredo che quell'ottica ha gia' con quella camera:
    lo stesso della posa di N.I.N.A., non un gemello. La domanda resta in pagina con la sua
    risposta, per cambiare idea, e non conta piu' fra le cose da confermare."""
    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": NEWTON}])

    assert _ottica_della_posa(pagina, "a_0.fits") == NEWTON
    assert _corredo_della_posa(pagina, "a_0.fits") == _corredo_della_posa(pagina, "n_0.fits")
    # e il corredo senza ottica, rimasto senza pose, non resta in Attrezzatura con zero ore
    corredi = {(g["optics"], g["camera"]) for g in gear(pagina)["rigs"]}
    assert (None, CAM) not in corredi and (NEWTON, CAM) in corredi
    risposta = next(d for d in _domande(pagina) if d["camera"] == CAM)
    assert (risposta["answer"], risposta["frames"]) == (NEWTON, 3)
    # il conto si misura fra due risposte: l'Applica conferma anche gli oggetti che ha visto
    con_una = review(pagina)["to_confirm"]
    apply(pagina, opticsless=[{"key": _chiave(pagina, ALTRA), "optics": "Takahashi FSQ-85"}])
    assert review(pagina)["to_confirm"] == con_una - 1


def test_an_optics_written_by_name_is_born_like_from_a_header(pagina):
    """Un'ottica che l'Attrezzatura non ha si scrive, e nasce dal nome come da un file."""
    apply(pagina, opticsless=[{"key": _chiave(pagina, ALTRA), "optics": "Takahashi FSQ-85"}])

    assert _ottica_della_posa(pagina, "m_0.fits") == "Takahashi FSQ-85"
    ottiche = {p["name"] for p in gear(pagina)["instruments"] if p["kind"] == "optics"}
    assert "Takahashi FSQ-85" in ottiche


def test_a_pose_that_arrives_later_takes_the_answer_by_itself(pagina, tmp_path):
    """La risposta sta sulla camera a quella focale, non sulle pose di oggi: una posa ASIAIR della
    notte dopo, a una focale che balla di poco, prende l'ottica da sola."""
    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": NEWTON}])
    _posa(tmp_path / "lib" / "asiair" / "dopo.fits", 50, **{**ASIAIR, "FOCALLEN": 803})
    with db(pagina) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))

    assert _ottica_della_posa(pagina, "dopo.fits") == NEWTON


def test_the_answer_is_for_that_camera_only(pagina, tmp_path):
    """Un'altra camera alla stessa focale e' un'altra domanda: la risposta data per una non vale per
    l'altra."""
    _posa(tmp_path / "lib" / "muta" / "altra.fits", 45, INSTRUME="QHY600M", FOCALLEN=800)
    with db(pagina) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))

    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": NEWTON}])

    assert _ottica_della_posa(pagina, "altra.fits") is None
    assert next(d for d in _domande(pagina) if d["camera"] == "QHY600M")["answer"] is None


def test_changing_the_answer_moves_the_poses(pagina):
    """Si cambia idea rispondendo di nuovo: le pose che l'ottica non la dicono vanno con quella
    nuova, e la posa di N.I.N.A., che la sua la dice, resta dov'era."""
    chiave = _chiave(pagina, CAM)
    apply(pagina, opticsless=[{"key": chiave, "optics": NEWTON}])
    apply(pagina, opticsless=[{"key": chiave, "optics": "Askar 107PHQ"}])
    # rilavorata anche lei: la risposta non passa sopra all'ottica che il file dice
    _rilavora_tutto(pagina)

    assert _ottica_della_posa(pagina, "a_1.fits") == "Askar 107PHQ"
    assert _ottica_della_posa(pagina, "n_0.fits") == NEWTON


def test_renaming_the_optics_carries_the_answer(pagina):
    """La risposta porta il **nome** dell'ottica: rinominata dall'Attrezzatura, la risposta la
    segue, e al giro dopo il nome vecchio non fa rinascere un pezzo."""
    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": NEWTON}])
    newton = next(p for p in gear(pagina)["instruments"] if p["name"] == NEWTON)

    assert correct(pagina, newton["id"], name="Newton 8").status_code == 200
    _rilavora_tutto(pagina)

    ottiche = {p["name"] for p in gear(pagina)["instruments"] if p["kind"] == "optics"}
    assert NEWTON not in ottiche
    assert _ottica_della_posa(pagina, "a_2.fits") == "Newton 8"
    assert next(d for d in _domande(pagina) if d["camera"] == CAM)["answer"] == "Newton 8"


def _rilavora_tutto(client):
    """Tutte le pose di nuovo in `normalize`: e' li' che un nome vecchio rinascerebbe."""
    with db(client) as conn:
        invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "normalize")
        list(normalize_frames(conn))


def _pezzo(client, nome):
    return next(p for p in gear(client)["instruments"] if p["name"] == nome)["id"]


def test_renaming_the_camera_carries_the_answer(pagina):
    """La risposta sta sulla camera a quella focale: rinominata la camera, la risposta la segue, e
    le pose restano con la loro ottica."""
    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": NEWTON}])

    assert correct(pagina, _pezzo(pagina, CAM), name="ASI2600MC").status_code == 200
    _rilavora_tutto(pagina)

    assert _ottica_della_posa(pagina, "a_0.fits") == NEWTON
    domanda = next(d for d in _domande(pagina) if d["camera"] == "ASI2600MC")
    assert (domanda["answer"], domanda["frames"]) == (NEWTON, 3)


def test_merging_the_optics_into_another_carries_the_answer(pagina):
    """Scritta con un nome nuovo, e poi detta la stessa di un'ottica che c'era: l'unione porta la
    risposta sull'ottica tenuta, e quella tolta non rinasce."""
    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": "Newton 8"}])

    r = correct(pagina, _pezzo(pagina, "Newton 8"), merge_into=_pezzo(pagina, NEWTON))
    assert r.status_code == 200
    _rilavora_tutto(pagina)

    ottiche = {p["name"] for p in gear(pagina)["instruments"] if p["kind"] == "optics"}
    assert "Newton 8" not in ottiche
    assert _ottica_della_posa(pagina, "a_0.fits") == NEWTON


def test_a_rig_written_by_hand_stays_even_without_poses(pagina):
    """I corredi rilevati rimasti senza pose spariscono a fine giro; uno scritto a mano no, anche
    vuoto: e' tuo, e lo aspetta la scansione che verra'."""
    body = {"optics_id": _pezzo(pagina, NEWTON), "camera_id": _pezzo(pagina, ALTRA)}
    body["focal_mm"] = 1000
    assert pagina.post("/api/v1/gear/rigs", json=body).status_code in (200, 201)

    _rilavora_tutto(pagina)

    corredi = {(g["optics"], g["camera"], g["focal_mm"]) for g in gear(pagina)["rigs"]}
    assert (NEWTON, ALTRA, 1000.0) in corredi


def test_the_name_and_mount_of_the_rig_without_optics_go_with_its_poses(pagina):
    """Il nome e la montatura che avevi dato al corredo senza ottica non si perdono con la risposta:
    passano al corredo dove vanno le sue pose, e le pose tengono la montatura. Il file senza
    `TELESCOP` la montatura non la dice: senza, resterebbe senza."""
    senza = next(g for g in gear(pagina)["rigs"] if g["camera"] == ALTRA)
    montatura = pagina.post("/api/v1/gear/instruments", json={"kind": "mount", "name": "EQ6-R"})
    assert montatura.status_code in (200, 201), montatura.text
    corredo = f"/api/v1/gear/rigs/{senza['id']}"
    assert pagina.patch(corredo, json={"name": "Il piccolo"}).status_code == 200
    r = pagina.put(f"{corredo}/mount", json={"mount_id": montatura.json()["id"]})
    assert r.status_code == 200, r.text
    pagina.app.state.worker.join(10.0)

    chiave = _chiave(pagina, ALTRA)
    # e anche cambiando idea: il corredo della seconda risposta li ritrova
    for ottica in ("Takahashi FSQ-85", "Askar 107PHQ"):
        apply(pagina, opticsless=[{"key": chiave, "optics": ottica}])

        nuovo = next(g for g in gear(pagina)["rigs"] if g["camera"] == ALTRA)
        assert (nuovo["optics"], nuovo["name"], nuovo["mount_id"]) == (
            ottica,
            "Il piccolo",
            montatura.json()["id"],
        )
        with db(pagina) as conn:
            pose = conn.execute(
                "SELECT f.mount_id FROM frames f JOIN positions p ON p.frame_id = f.id"
                " WHERE p.rel_path LIKE '%m_0.fits'"
            ).fetchone()
        assert pose["mount_id"] == montatura.json()["id"]


def test_a_rig_that_was_already_there_keeps_its_own_word(pagina):
    """Se le pose vanno in un corredo che c'era gia', quello tiene la sua parola, anche quando e'
    "nessun nome": il nome del corredo senza ottica passa solo a un corredo che nasce li'."""
    senza = next(g for g in gear(pagina)["rigs"] if g["camera"] == CAM and g["optics"] is None)
    r = pagina.patch(f"/api/v1/gear/rigs/{senza['id']}", json={"name": "Il gemello"})
    assert r.status_code == 200, r.text

    apply(pagina, opticsless=[{"key": _chiave(pagina, CAM), "optics": NEWTON}])

    assert next(g for g in gear(pagina)["rigs"] if g["optics"] == NEWTON)["name"] is None


def test_an_answer_to_a_question_that_is_not_there_is_refused(pagina):
    """Una risposta per una domanda che non c'e' e' una pagina vecchia: si dice, non si scrive."""
    r = pagina.post(
        "/api/v1/review/apply", json={"opticsless": [{"key": "|Nessuna|100.0", "optics": NEWTON}]}
    )
    assert r.status_code == 404


def test_the_camera_question_does_not_offer_the_mount_as_optics(db_path, tmp_path):
    """**Il buco noto.** Se la posa non dice la camera, la domanda sulla camera propone come ottica
    cio' che dice `TELESCOP` -- ma con l'ASIAIR li' c'e' la montatura, e proporla sarebbe
    riempire il campo con un pezzo sbagliato."""
    root = tmp_path / "lib"
    senza_camera = {k: v for k, v in ASIAIR.items() if k != "INSTRUME"}
    _posa(root / "asiair" / "s_0.fits", 0, **senza_camera)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        gruppi = review(c)["rigless"]

    assert [(g["telescope"], g["optics"]) for g in gruppi] == [("ZWO AM5", None)]


def test_a_mixed_group_does_not_offer_the_mount_as_optics_either(db_path, tmp_path):
    """Lo stesso `TELESCOP` in un gruppo che mescola pose ASIAIR e di un altro programma: se
    l'ASIAIR dice che quel nome e' la montatura, lo e' anche per le altre pose del gruppo."""
    root = tmp_path / "lib"
    senza_camera = {k: v for k, v in ASIAIR.items() if k != "INSTRUME"}
    _posa(root / "asiair" / "s_0.fits", 0, **senza_camera)
    _posa(root / "nina" / "s_1.fits", 1, **{**senza_camera, "CREATOR": "N.I.N.A."})
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        gruppi = review(c)["rigless"]

    assert [(g["telescope"], g["frames"], g["optics"]) for g in gruppi] == [("ZWO AM5", 2, None)]
