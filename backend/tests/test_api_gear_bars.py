"""I campi della pagina Attrezzatura (tavola v82) che la pagina non calcola: la barra delle ore
di un setup, di un pezzo e di un filtro sul piu' usato del suo gruppo, la Luna piena del
confronto dei campi, e quali campi di una scheda vengono dai file.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from group_bench import ROMA, attrezzo, corri, filtro, luogo, posa, prepara


def _rig(conn, ottica, camera, focale):
    return conn.execute(
        "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES(?, ?, ?, 1, ?)",
        (ottica, camera, focale, now_iso()),
    ).lastrowid


@pytest.fixture
def due_setup(db_path):
    """Due setup: il primo con 3 ore, il secondo con mezz'ora; due filtri, 3 ore e mezz'ora."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        ottica = attrezzo(conn, "optics", "TS 130 APO")
        corta = attrezzo(conn, "optics", "RedCat 51")
        camera = attrezzo(conn, "camera", "ASI2600MM", pixel_size_um=3.76, width_px=6248)
        lungo = _rig(conn, ottica, camera, 910.0)
        breve = _rig(conn, corta, camera, 250.0)
        ha = filtro(conn, "Ha", "HA")
        oiii = filtro(conn, "OIII", "OIII")
        for n in range(3):
            f = posa(conn, quando=f"2024-05-18T2{n}:00:00Z", filtro_id=ha, esposizione=3600)
            conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (lungo, f))
        f = posa(conn, quando="2024-05-19T22:00:00Z", filtro_id=oiii, esposizione=1800)
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (breve, f))
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_a_bar_is_the_hours_on_the_most_used_of_its_group(due_setup):
    pagina = due_setup.get("/api/v1/gear").json()

    per_focale = {r["focal_mm"]: r["bar_pct"] for r in pagina["rigs"] if r["frames"]}
    assert per_focale == {910.0: 100.0, 250.0: 16.7}
    assert sorted(f["bar_pct"] for f in pagina["filters"]) == [16.7, 100.0]
    # le ottiche fra loro, la camera da sola: ogni genere ha il suo piu' usato
    per_nome = {p["name"]: p["bar_pct"] for p in pagina["instruments"]}
    assert per_nome == {"TS 130 APO": 100.0, "RedCat 51": 16.7, "ASI2600MM": 100.0}


def test_a_bar_never_vanishes_and_unknown_hours_have_none(due_setup):
    """Un pezzo con zero ore ha la barra al minimo della tavola, non nessuna; uno di un genere che
    nessun file nomina non ha ore da mettere in barra."""
    due_setup.post("/api/v1/gear/instruments", json={"kind": "optics", "name": "Nuova"})
    due_setup.post("/api/v1/gear/instruments", json={"kind": "focuser", "name": "EAF"})

    per_nome = {
        p["name"]: p["bar_pct"] for p in due_setup.get("/api/v1/gear").json()["instruments"]
    }
    assert per_nome["Nuova"] == 3.0
    assert per_nome["EAF"] is None


def test_the_full_moon_of_the_comparison_comes_from_the_api(due_setup):
    """Il diametro apparente medio della NASA, 1896 secondi d'arco: la pagina lo disegna e basta."""
    assert due_setup.get("/api/v1/gear").json()["moon_deg"] == pytest.approx(0.5267, abs=1e-4)


def test_the_card_says_which_fields_the_files_told(due_setup):
    """«dai file» accanto al pixel letto dagli header; scritto da te, diventa «inserito»."""
    camera = next(
        p for p in due_setup.get("/api/v1/gear").json()["instruments"] if p["name"] == "ASI2600MM"
    )
    assert camera["from_files"] == ["pixel_size_um", "width_px"]

    due_setup.patch(f"/api/v1/gear/instruments/{camera['id']}", json={"pixel_size_um": 3.8})

    dopo = next(
        p for p in due_setup.get("/api/v1/gear").json()["instruments"] if p["name"] == "ASI2600MM"
    )
    assert dopo["from_files"] == ["width_px"]
