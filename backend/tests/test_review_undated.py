"""Da confermare, i **frame senza data**: una domanda per cartella (tavola v82 di Design, Marco
6/11/2026: si risponde in Da confermare, non si indovina).

Senza `DATE-OBS` non c'e' notte, e la data del file sul disco e' quella della copia, non della
ripresa: si mostra accanto alla domanda come prova, mai come risposta. Si risponde con la data
della sera, o scegliendo una notte con lo stesso setup; la risposta vale per la cartella, anche
per i file che vi arriveranno, e la domanda resta in pagina per cambiare idea.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.spine.frame_folder import folder_key
from astrolog.spine.group import group_frames
from conftest import apply, db, populate, review, write_fits
from group_bench import ROMA, luogo

DATATI, SENZA = "2026-03-14/M51", "Senza data/M33"
SETUP = {"INSTRUME": "ZWO ASI2600MM", "TELESCOP": "Askar FRA400", "FOCALLEN": 400.0}


def _posa(path, oggetto, quando=None):
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0, "OBJECT": oggetto, **SETUP}
    if quando:
        card["DATE-OBS"] = quando
    return write_fits(path, {**card, "XPIXSZ": 3.76})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / DATATI / f"a_{i}.fits", "M 51", f"2026-03-14T21:0{i}:00")
    for i in range(3):
        _posa(root / SENZA / f"b_{i}.fits", "M 33")
    populate(db_path, root)
    conn = connect(db_path)
    try:
        luogo(conn, ROMA)
        list(group_frames(conn))
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _chiave(client):
    with db(client) as conn:
        radice = conn.execute("SELECT root_path FROM folders").fetchone()[0]
    return folder_key(radice, f"{SENZA}/")


def _notte_di_m33(client):
    with db(client) as conn:
        return conn.execute(
            "SELECT DISTINCT n.night_date, s.name FROM frames f"
            " JOIN objects o ON o.id = f.object_id"
            " JOIN object_names m ON m.object_id = o.id AND m.is_primary = 1"
            " LEFT JOIN nights n ON n.id = f.night_id LEFT JOIN sites s ON s.id = n.site_id"
            " WHERE m.name = 'M 33'"
        ).fetchall()


def test_frames_without_a_date_are_asked_per_folder_with_their_proofs(pagina):
    pagina_letta = review(pagina)
    (gruppo,) = pagina_letta["undated"]
    assert gruppo["key"] == _chiave(pagina)
    assert (gruppo["frames"], gruppo["integration_s"], gruppo["untimed"]) == (3, 900.0, 0)
    assert (gruppo["answer"], gruppo["site"]) == (None, "Casa")
    assert gruppo["subjects"] == [{"name": "M 33", "frames": 3}]
    assert [(r["optics"], r["camera"]) for r in gruppo["rigs"]] == [
        ("Askar FRA400", "ZWO ASI2600MM")
    ]
    # la data del file c'e' come prova: e' quella della copia, non una risposta
    assert len(gruppo["file_nights"]) == 1
    assert gruppo["rig_nights"] == ["2026-03-14"], "le notti con lo stesso setup"
    assert {"key": "undated", "count": 1} in pagina_letta["sections"]


def test_the_evening_said_puts_the_frames_in_that_night_and_the_question_stays(pagina):
    apply(pagina, undated=[{"key": _chiave(pagina), "night": "2026-03-14"}])
    assert [tuple(r) for r in _notte_di_m33(pagina)] == [("2026-03-14", "Casa")]
    pagina_letta = review(pagina)
    (gruppo,) = pagina_letta["undated"]
    assert gruppo["answer"] == "2026-03-14", "si cambia idea"
    assert "undated" not in {s["key"] for s in pagina_letta["sections"]}


def test_changing_ones_mind_moves_the_frames_to_the_other_night(pagina):
    apply(pagina, undated=[{"key": _chiave(pagina), "night": "2026-03-14"}])
    apply(pagina, undated=[{"key": _chiave(pagina), "night": "2026-03-20"}])
    assert [tuple(r) for r in _notte_di_m33(pagina)] == [("2026-03-20", "Casa")]


@pytest.mark.parametrize("notte", ["14/03/2026", "2026-02-30", "", "9999-12-31"])
def test_an_answer_that_is_not_a_date_is_refused(pagina, notte):
    r = pagina.post(
        "/api/v1/review/apply", json={"undated": [{"key": _chiave(pagina), "night": notte}]}
    )
    assert r.status_code == 422


def test_a_folder_that_is_not_asked_is_refused(pagina):
    r = pagina.post(
        "/api/v1/review/apply", json={"undated": [{"key": "/altrove", "night": "2026-03-14"}]}
    )
    assert r.status_code == 404
