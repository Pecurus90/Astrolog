"""Il **corredo della notte**, e le risposte sui gruppi che seguono i pezzi.

Una posa che non dice la camera la prende dalla sua notte (`spine/night_rig.py`). Se non dice
l'ottica, prende quella della notte quando la notte ne dice una sola a una focale sola, con la
focale se la posa non la dice: senza, nasceva un corredo senza ottica accanto a quello delle
pose complete, e le ore si spartivano.
E una risposta sul gruppo porta i NOMI dei pezzi: rinominati o uniti, la risposta li segue, o
al giro dopo il nome vecchio farebbe rinascere il pezzo.
"""

import re

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import night_rig
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.stages import invalidate
from conftest import apply, correct, db, gear, populate, review, write_fits

CAM, NEWTON, ASKAR = "ZWO ASI2600MM Pro", "Newton 200/800", "Askar 107PHQ"
NINA = {"CREATOR": "N.I.N.A.", "INSTRUME": CAM}


def _posa(path, giorno, minuto, **header):
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0, "OBJECT": "M 51", "FILTER": "L"}
    card["DATE-OBS"] = f"2026-03-{giorno:02d}T21:{minuto:02d}:00"
    return write_fits(path, {**card, **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    # notte del 14: un corredo solo, e una posa che non dice niente dell'attrezzatura
    for i in range(2):
        _posa(root / "14" / f"n_{i}.fits", 14, i, TELESCOP=NEWTON, FOCALLEN=800, **NINA)
    _posa(root / "14" / "muta.fits", 14, 30)
    # una che scrive FOCALLEN = 0: una focale zero non e' una focale, e' una focale che non dice
    _posa(root / "14" / "zero.fits", 14, 32, FOCALLEN=0)
    # e una che la focale la dice, diversa: con un'altra focale l'ottica della notte non e' sua
    _posa(root / "14" / "altra_focale.fits", 14, 31, FOCALLEN=400)
    # notte del 15: la stessa camera su due ottiche, e una posa muta
    _posa(root / "15" / "n.fits", 15, 0, TELESCOP=NEWTON, FOCALLEN=800, **NINA)
    _posa(root / "15" / "a.fits", 15, 1, TELESCOP=ASKAR, FOCALLEN=749, **NINA)
    _posa(root / "15" / "muta.fits", 15, 30)
    # notte del 16: solo pose ASIAIR, che l'ottica non la scrivono mai, e una muta
    asiair = {"CREATOR": "ZWO ASIAIR Plus", "TELESCOP": "ZWO AM5", "INSTRUME": CAM}
    _posa(root / "16" / "s.fits", 16, 0, FOCALLEN=560, **asiair)
    _posa(root / "16" / "muta.fits", 16, 30)
    # notte del 17: la stessa ottica a due focali (un riduttore), e una muta
    _posa(root / "17" / "n.fits", 17, 0, TELESCOP=NEWTON, FOCALLEN=800, **NINA)
    _posa(root / "17" / "r.fits", 17, 1, TELESCOP=NEWTON, FOCALLEN=600, **NINA)
    _posa(root / "17" / "muta.fits", 17, 30)
    # notte del 18: pose ASIAIR, che l'ottica non la dicono, e pose N.I.N.A. che la dicono
    _posa(root / "18" / "s.fits", 18, 0, FOCALLEN=800, **asiair)
    _posa(root / "18" / "n.fits", 18, 1, TELESCOP=NEWTON, FOCALLEN=800, **NINA)
    _posa(root / "18" / "muta.fits", 18, 30)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _corredo(client, nome):
    """(ottica, camera, focale, id) del corredo di quella posa."""
    with db(client) as conn:
        r = conn.execute(
            "SELECT o.name AS optics, c.name AS camera, g.focal_mm, g.id FROM frames f"
            " JOIN positions p ON p.frame_id = f.id JOIN rigs g ON g.id = f.rig_id"
            " LEFT JOIN instruments o ON o.id = g.optics_id"
            " LEFT JOIN instruments c ON c.id = g.camera_id WHERE p.rel_path LIKE ?",
            (f"%{nome}",),
        ).fetchone()
    return (r["optics"], r["camera"], r["focal_mm"], r["id"])


def _rilavora_tutto(client):
    with db(client) as conn:
        invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "normalize")
        list(normalize_frames(conn))


def test_a_silent_pose_takes_the_rig_of_its_night(pagina):
    """**La regola.** Nella notte c'e' un corredo solo: la posa che non dice niente ci entra, e non
    nasce un corredo senza ottica accanto."""
    assert _corredo(pagina, "14/muta.fits") == _corredo(pagina, "14/n_0.fits")
    # anche quella che scrive una focale zero, che la focale non la dice
    assert _corredo(pagina, "14/zero.fits") == _corredo(pagina, "14/n_0.fits")


def test_a_pose_with_its_own_focal_does_not_take_the_optics_of_another(pagina):
    """La focale che la posa dice e' sua: a 400 mm l'ottica della notte, che lavora a 800, non e'
    la sua. Prende la camera, e l'ottica resta da chiedere."""
    assert _corredo(pagina, "altra_focale.fits")[:3] == (None, CAM, 400.0)


def test_a_night_with_two_optics_gives_only_the_camera(pagina):
    """Due ottiche nella stessa notte: quale fosse non si indovina. La posa prende la camera, e il
    resto lo chiede la domanda "quale ottica era"."""
    ottica, camera, focale, _ = _corredo(pagina, "15/muta.fits")
    assert (ottica, camera, focale) == (None, CAM, None)


def test_one_optics_at_two_focals_gives_only_the_camera(pagina):
    """La stessa ottica a due focali -- un riduttore -- non e' un corredo solo: quale focale avesse
    la posa muta non si indovina."""
    assert _corredo(pagina, "17/muta.fits")[:3] == (None, CAM, None)


def test_a_night_of_asiair_and_other_poses_gives_only_the_camera(pagina):
    """ "Nessuna ottica" dell'ASIAIR e' un valore: accanto a pose che l'ottica la dicono, la notte
    ne dice due, e l'ottica della posa muta non si indovina."""
    assert _corredo(pagina, "18/muta.fits")[:3] == (None, CAM, None)


def test_an_asiair_night_gives_the_rig_without_optics_of_its_poses(pagina):
    """Una notte di sole pose ASIAIR ha un corredo senza ottica: la posa muta ci entra, e la
    domanda sull'ottica e' una sola per tutte e due."""
    assert _corredo(pagina, "16/muta.fits") == _corredo(pagina, "16/s.fits")


def _gruppo_senza_camera(db_path, tmp_path):
    """Una notte senza nessuna posa che dica la camera: il suo gruppo si chiede."""
    root = tmp_path / "lib"
    _posa(root / "14" / "n.fits", 14, 0, TELESCOP=NEWTON, FOCALLEN=800, **NINA)
    _posa(root / "20" / "g.fits", 20, 0, TELESCOP="Newton 8")
    _posa(root / "21" / "h.fits", 21, 0, TELESCOP="Un altro")  # un secondo gruppo, un'altra camera
    populate(db_path, root)
    return TestClient(create_app(db_path), base_url="http://localhost")


def _pezzo(client, nome):
    return next(p for p in gear(client)["instruments"] if p["name"] == nome)["id"]


def test_renaming_a_camera_carries_the_answer_on_the_group(db_path, tmp_path):
    """La risposta sul gruppo porta il nome della camera: rinominata, la risposta la segue, la
    pagina mostra il nome nuovo, e al giro dopo il vecchio non rinasce."""
    with _gruppo_senza_camera(db_path, tmp_path) as c:
        gruppi = {g["night"]: g["key"] for g in review(c)["rigless"]}
        apply(c, rigless=[
            {"key": gruppi["2026-03-20"], "camera": "ASI2600", "optics": NEWTON, "focal_mm": 800},
            {"key": gruppi["2026-03-21"], "camera": "QHY268M", "optics": NEWTON, "focal_mm": 800},
        ])  # fmt: skip

        assert correct(c, _pezzo(c, "ASI2600"), name="ASI2600 Pro").status_code == 200
        _rilavora_tutto(c)

        camere = {p["name"] for p in gear(c)["instruments"] if p["kind"] == "camera"}
        assert "ASI2600" not in camere
        risposte = {g["night"]: g["answer"]["camera"] for g in review(c)["rigless"]}
        # la risposta sull'altra camera non cambia: la rinomina segue solo il suo pezzo
        assert risposte == {"2026-03-20": "ASI2600 Pro", "2026-03-21": "QHY268M"}
        assert _corredo(c, "20/g.fits")[:2] == (NEWTON, "ASI2600 Pro")


def test_merging_the_optics_carries_the_answer_on_the_group(db_path, tmp_path):
    """Lo stesso per l'unione: l'ottica della risposta, unita a una che c'era, non rinasce."""
    with _gruppo_senza_camera(db_path, tmp_path) as c:
        chiave = next(g["key"] for g in review(c)["rigless"] if g["night"] == "2026-03-20")
        risposta = {"key": chiave, "camera": CAM, "optics": "Newton 8", "focal_mm": 800}
        apply(c, rigless=[risposta])

        r = correct(c, _pezzo(c, "Newton 8"), merge_into=_pezzo(c, NEWTON))
        assert r.status_code == 200, r.text
        _rilavora_tutto(c)

        ottiche = {p["name"] for p in gear(c)["instruments"] if p["kind"] == "optics"}
        assert "Newton 8" not in ottiche
        gruppo = next(g for g in review(c)["rigless"] if g["key"] == chiave)
        assert gruppo["answer"]["optics"] == NEWTON
        assert _corredo(c, "20/g.fits")[0] == NEWTON


def test_night_rig_asked_for_some_nights_reads_only_those(pagina):
    """La pagina chiede il corredo delle sole notti delle pose che chiedono, e lo trova con
    l'indice: il corredo di una notte dipende solo dalle pose di quella notte, e rileggere
    l'archivio intero per saperlo sarebbe la parte cara della domanda sulla camera."""
    with db(pagina) as conn:
        tutte = night_rig.night_rigs(conn)
        assert len(tutte) >= 2, "il banco ha una notte sola: la prova non distingue niente"
        una = min(tutte)
        assert night_rig.night_rigs(conn, {una}) == {una: tutte[una]}
        # con l'elenco la pagina, senza la normalizzazione che le chiede tutte: entrambe dall'indice
        for elenco, parametri in ((True, ("[]",)), (False, ())):
            query = "EXPLAIN QUERY PLAN " + night_rig.rigs_by_night(elenco)
            piano = " ".join(r[3] for r in conn.execute(query, parametri))
            assert re.search(r"COVERING INDEX frames_local_night\b", piano), piano
