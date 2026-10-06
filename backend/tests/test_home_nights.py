"""La notte delle pose che non dicono dove sono state fatte segue il fuso di casa, e con lei il
gruppo dei frame senza nome. Nessuna risposta porta la notte: l'oggetto sta sull'impronta del
frame (ADR 0014, S2), l'attrezzatura sulla firma dell'header (S1). Le regole stanno in
`spine/home_nights.py`.

A Tokyo il confine della notte (mezzogiorno locale) cade alle 03:00 UTC, e quello UTC alle 21:00
locali, a meta' sessione: le pose di prova sono scelte perche' una notte UTC si divida in due notti
di Tokyo e due notti UTC diventino una.
"""

import json
import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import signature, unnamed
from conftest import db, frame_by_file, populate, write_fits

TOKYO = {"name": "Tokyo", "latitude": 35.68, "longitude": 139.69}
ROMA = {"latitude": 41.9, "longitude": 12.5}
HONOLULU = {"name": "Honolulu", "latitude": 21.31, "longitude": -157.86}
# UTC: a e b nella notte del 13, c in quella del 14. Tokyo: a nel 13, b e c nel 14.
POSE = {"a": "2026-03-14T02:00:00", "b": "2026-03-14T04:00:00", "c": "2026-03-14T13:00:00"}


def _posa(path, date_obs=None, **header):
    """Una posa che, se `header` non aggiunge niente, non dice camera, nome ne' coordinate: la notte
    la decide casa, e la domanda sull'oggetto, che porta la notte nella chiave, la chiede."""
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0, "TELESCOP": "Newton 200"}
    if date_obs:
        card["DATE-OBS"] = date_obs
    return write_fits(path, {**card, **header})


def _archivio(db_path, root, pose):
    """L'app su un archivio di `(nome, DATE-OBS, header in piu')` gia' letto, senza casa."""
    for nome, quando, header in pose:
        _posa(root / f"{nome}.fits", quando, **header)
    populate(db_path, root)
    return TestClient(create_app(db_path), base_url="http://localhost")


# d dice dove: il suo fuso e' quello del posto. Un altro telescopio, un altro gruppo
_A_ROMA = {"SITELAT": ROMA["latitude"], "SITELONG": ROMA["longitude"], "TELESCOP": "Rifrattore 80"}
# e non dice quando: la sua ora e' quella del file, messa a cavallo del confine come quella di b
_ORA_DI_E = datetime(2026, 3, 14, 4, tzinfo=UTC).timestamp()


@pytest.fixture
def pagina(db_path, tmp_path, offline):
    root = tmp_path / "lib"
    pose = [(nome, quando, {}) for nome, quando in POSE.items()]
    pose += [("d", POSE["b"], _A_ROMA), ("f", "2026-01-01T20:00:00", _A_ROMA)]
    # g non dice dove, ma a Tokyo resta nella stessa data: cambia fuso e non si sposta
    pose += [("g", "2026-02-01T15:00:00", {})]
    _posa(root / "e.fits", None, TELESCOP="Mak 127")
    os.utime(root / "e.fits", (_ORA_DI_E, _ORA_DI_E))
    with _archivio(db_path, root, pose) as c:
        yield c


def _casa(client, **body):
    r = client.post("/api/v1/sites", json={**TOKYO, **body})
    assert r.status_code == 201, r.text
    return r.json()


def _notte(client, nome):
    with db(client) as conn:
        riga = frame_by_file(conn, f"{nome}.fits")
    return riga["local_night"], riga["local_tz"]


def test_before_a_home_the_poses_that_do_not_say_where_are_in_utc(pagina):
    """Il punto di partenza: senza casa, la notte di una posa senza coordinate e' in UTC."""
    assert _notte(pagina, "b") == ("2026-03-13", None)
    assert _notte(pagina, "d") == ("2026-03-13", "Europe/Rome")


def test_the_first_home_moves_the_nights_of_the_poses_that_do_not_say_where(pagina):
    """Nata casa, le pose senza coordinate passano al suo fuso; quelle con le coordinate restano
    nel fuso del posto dove sono state fatte."""
    _casa(pagina)
    assert _notte(pagina, "a") == ("2026-03-13", "Asia/Tokyo")
    assert _notte(pagina, "b") == ("2026-03-14", "Asia/Tokyo")
    assert _notte(pagina, "c") == ("2026-03-14", "Asia/Tokyo")
    assert _notte(pagina, "d") == ("2026-03-13", "Europe/Rome")


def test_a_pose_without_date_obs_takes_the_night_of_its_file_in_the_home_timezone(pagina):
    """Senza `DATE-OBS` l'istante e' quello in cui il file e' stato scritto, come alla scansione:
    alle 04:00 UTC del 14 e' la notte del 13 in UTC e quella del 14 a Tokyo."""
    assert _notte(pagina, "e") == ("2026-03-13", None)
    _casa(pagina)
    assert _notte(pagina, "e") == ("2026-03-14", "Asia/Tokyo")


def test_a_file_touched_after_it_entered_keeps_the_instant_of_its_night(pagina, tmp_path):
    """L'ora del file cambia se lo si tocca -- un header riscritto lascia gli stessi pixel, e la
    posa resta la stessa --, ma la notte viene dall'istante con cui la posa e' entrata: e' quello
    che si riscrive nel fuso nuovo, non l'ora di adesso."""
    dopo = datetime(2026, 6, 1, 4, tzinfo=UTC).timestamp()
    os.utime(tmp_path / "lib" / "e.fits", (dopo, dopo))
    r = pagina.post("/api/v1/scan")
    assert r.status_code in (200, 202), r.text
    pagina.app.state.worker.join(20.0)
    assert _notte(pagina, "e") == ("2026-03-13", None)
    _casa(pagina)
    assert _notte(pagina, "e") == ("2026-03-14", "Asia/Tokyo")


def test_moving_home_to_another_timezone_moves_them_again(pagina):
    """Casa spostata in un altro fuso: le pose senza coordinate la seguono ancora."""
    casa = _casa(pagina)
    r = pagina.patch(f"/api/v1/sites/{casa['id']}", json=ROMA)
    assert r.status_code == 200, r.text
    assert _notte(pagina, "b") == ("2026-03-13", "Europe/Rome")


def test_choosing_another_home_moves_them_to_its_timezone(pagina):
    """Un altro sito scelto come casa: le pose senza coordinate passano al suo fuso."""
    _casa(pagina)
    roma = _casa(pagina, name="Roma", **ROMA)
    assert _notte(pagina, "b") == ("2026-03-14", "Asia/Tokyo")
    r = pagina.post(f"/api/v1/sites/{roma['id']}/default")
    assert r.status_code == 200, r.text
    assert _notte(pagina, "b") == ("2026-03-13", "Europe/Rome")


def test_without_a_home_they_go_back_to_utc(pagina):
    """Tolta casa, l'unico fuso che il file sa e' UTC."""
    casa = _casa(pagina)
    r = pagina.delete(f"/api/v1/sites/{casa['id']}")
    assert r.status_code == 200, r.text
    assert _notte(pagina, "b") == ("2026-03-13", None)


def _chiave_oggetto(client, nome):
    with db(client) as conn:
        return frame_by_file(conn, f"{nome}.fits")["unnamed_key"]


def test_an_object_answer_follows_its_poses_into_the_new_night(pagina):
    """Anche i frame senza nome portano la notte nella chiave, scritta sulla posa: b lascia il
    gruppo del 13 per quello del 14, e la risposta del suo gruppo lo segue."""
    detta = _chiave_oggetto(pagina, "b")
    assert detta == _chiave_oggetto(pagina, "a")
    with db(pagina) as conn:
        unnamed.declare(conn, detta, name="Cometa di prova")
    _casa(pagina)
    nuova = _chiave_oggetto(pagina, "b")
    assert json.loads(nuova)[0] == "2026-03-14"
    assert nuova == _chiave_oggetto(pagina, "c")
    with db(pagina) as conn:
        assert unnamed.answer(conn, nuova).name == "Cometa di prova"
        assert unnamed.answer(conn, _chiave_oggetto(pagina, "a")).name == "Cometa di prova"


def test_the_poses_of_the_nights_that_changed_are_worked_again(pagina):
    """Il corredo della notte e le risposte per gruppo si rileggono da `normalize` in poi: le pose
    delle notti toccate tornano in coda da li', anche d, che sta nel suo fuso ma porta la stessa
    data -- il corredo della notte si cerca per data. Le altre notti no."""
    _casa(pagina)
    with db(pagina) as conn:
        stato = dict(
            conn.execute(
                "SELECT p.rel_path, s.status FROM frame_stages s"
                " JOIN positions p ON p.frame_id = s.frame_id WHERE s.stage = 'normalize'"
            ).fetchall()
        )
    assert stato["b.fits"] == "pending"
    assert stato["c.fits"] == "pending"
    assert stato["d.fits"] == "pending"
    assert stato["f.fits"] == "done"
    assert stato["g.fits"] == "done"


def test_two_object_answers_that_disagree_fall_when_their_groups_become_one(pagina):
    """b lascia il gruppo di a (notte UTC del 13) per quello di c (UTC 14), e le due risposte sono
    diverse: la domanda del 14 torna aperta, quella di a resta."""
    with db(pagina) as conn:
        unnamed.declare(conn, _chiave_oggetto(pagina, "a"), name="Cometa di prova")
        unnamed.declare(conn, _chiave_oggetto(pagina, "c"), name="Nebulosa di prova")
    _casa(pagina)
    with db(pagina) as conn:
        assert unnamed.answer(conn, _chiave_oggetto(pagina, "c")) is None
        assert unnamed.answer(conn, _chiave_oggetto(pagina, "a")).name == "Cometa di prova"


def test_a_camera_answer_stays_put_when_home_moves(pagina):
    """La risposta sulla camera sta sulla firma, che non porta la notte: a, b e c dividono e
    riuniscono le notti cambiando fuso, ma la risposta resta una, e vale per tutte e tre."""
    with db(pagina) as conn:
        chiave = signature.key_of(signature.parts_of(frame_by_file(conn, "a.fits")))
        signature.declare(conn, chiave, signature.Answer(camera="ZWO ASI2600MM", focal_mm=800.0))
    _casa(pagina)
    with db(pagina) as conn:
        for nome in ("a", "b", "c"):
            frame = frame_by_file(conn, f"{nome}.fits")
            assert signature.key_of(signature.parts_of(frame)) == chiave
        assert signature.answer(conn, chiave).camera == "ZWO ASI2600MM"
