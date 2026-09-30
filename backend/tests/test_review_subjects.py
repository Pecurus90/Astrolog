"""Da confermare, **cosa hai ripreso**: ogni gruppo di pose su cui l'app chiede dice cosa ha trovato
il cielo in quelle pose (Marco, 15/9/2026: "andare a memoria e' difficile").

Chi riprende con una reflex quasi mai scrive `OBJECT`: senza questa riga la notte di M 81 si
leggeva "senza oggetto" mentre l'app l'oggetto l'aveva trovato. Il gruppo non cambia -- la domanda
e la chiave restano quelle -- si aggiunge solo cosa si vede.

Regole:

* **Gli oggetti con quante pose ciascuno, il piu' ripreso in cima** e a pari pose per nome, col
  nome che la pagina degli oggetti mostra.
* **"Non trovato" e "non ancora guardato" sono due cose**: una posa che `identify` non ha ancora
  lavorato, o su cui si e' guastato, non e' una posa in cui il cielo non ha trovato niente.
* **Conta lo stato, non l'oggetto rimasto attaccato**: una posa fallita o saltata tiene il vecchio
  `object_id`, e mostrarlo direbbe un oggetto che il cielo non ha detto.
* **Le copie calibrate non si contano**, come in tutta la pagina.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import objects as obj
from conftest import db, populate, review, write_fits

MONO = "ZWO ASI6200MM"


def _posa(path, quando, **header):
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0, "XPIXSZ": 3.76, "XBINNING": 1}
    return write_fits(path, {**card, "INSTRUME": MONO, "DATE-OBS": quando, **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    """Una notte con otto pose che non dicono il filtro, tutte con M 31 nell'header -- come succede
    quando ci si dimentica di cambiarlo -- piu' la copia calibrata di una. E un'altra notte su M 45,
    perche' la domanda per camera le somma."""
    root = tmp_path / "lib"
    for i in range(8):
        _posa(root / f"a_{i}.fits", f"2024-04-06T21:0{i}:00", OBJECT="M 31")
    _posa(root / "calibrate" / "a_0.fits", "2024-04-06T21:00:00", OBJECT="M 31", CALSTAT="BDF")
    for i in range(2):
        _posa(root / f"b_{i}.fits", f"2024-04-07T21:0{i}:00", OBJECT="M 45")
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        _metti_in_scena(c)
        yield c


_STATO = "UPDATE frame_stages SET status = ? WHERE stage = 'identify' AND frame_id = ?"


def _metti_in_scena(client):
    """Delle otto pose della prima notte: a_0 e a_1 restano su M 31; a_4 e a_5 il cielo le dice
    M 45; a_3 l'ha guardata senza trovare niente; a_2 non l'ha ancora guardata; su a_6 si e'
    guastato; a_7 l'ha saltata. a_6 e a_7 tengono M 31 attaccato, com'e' nel database vero."""
    with db(client) as conn:
        m45 = conn.execute("SELECT object_id FROM frames WHERE object_raw = 'M 45'").fetchone()[0]
        _pose(conn, ("a_4", "a_5"), "UPDATE frames SET object_id = ? WHERE id = ?", m45)
        _pose(conn, ("a_3",), "UPDATE frames SET object_id = NULL WHERE id = ?")
        _pose(conn, ("a_2",), _STATO, "pending")
        _pose(conn, ("a_6",), _STATO, "failed")
        _pose(conn, ("a_7",), _STATO, "skipped")
        conn.commit()


def _pose(conn, nomi, sql, *prima):
    for nome in nomi:
        (frame_id,) = conn.execute(
            "SELECT p.frame_id FROM positions p WHERE p.rel_path = ?", (f"{nome}.fits",)
        ).fetchone()
        conn.execute(sql, (*prima, frame_id))


def test_the_camera_question_sums_the_subjects_of_all_its_nights(pagina):
    # la copia di a_0 non conta; a_6 fallita e' "non ancora", a_7 saltata e' "non trovato"
    (camera,) = review(pagina)["unfiltered"]
    assert camera["subjects"] == {
        "found": [{"name": "M 45", "frames": 4}, {"name": "M 31", "frames": 2}],
        "not_found": 2,
        "not_yet": 2,
    }


def test_at_the_same_frames_the_name_decides_not_the_order_they_came_in(pagina):
    # l'archivio restituisce gli oggetti nell'ordine che vuole: qui arriva prima M 45
    with db(pagina) as conn:
        # dai nomi, non dalle pose: la scena ha messo su M 45 due pose che nell'header dicono M 31
        ids = dict(conn.execute("SELECT name, object_id FROM object_names WHERE is_primary = 1"))
        (gruppo,) = obj.subjects(conn, [{"subjects": {ids["M 45"]: 3, ids["M 31"]: 3}}])
    assert [s["name"] for s in gruppo["subjects"]["found"]] == ["M 31", "M 45"]
