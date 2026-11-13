"""Le carte dei setup nell'indice della pagina Attrezzatura (tavola v82): il titolo corto e le
dieci parti a tacche, gia' pronti dall'API -- la pagina li disegna e basta.
"""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api import work
from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.spine import rig_card
from group_bench import ROMA, attrezzo, corri, luogo, posa, prepara


@pytest.fixture
def un_setup(db_path):
    """Un setup con marca e modello sui pezzi, e uno coi nomi soli."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        ottica = attrezzo(conn, "optics", "Askar FRA400", brand="Askar", model="FRA400")
        camera = attrezzo(conn, "camera", "ZWO ASI2600MM Pro", brand="ZWO")
        nuda = attrezzo(conn, "optics", "Il mio rifrattore")
        for n, o in enumerate((ottica, nuda)):
            rig = conn.execute(
                "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
                " VALUES(?, ?, 400, 1, ?)",
                (o, camera, now_iso()),
            ).lastrowid
            f = posa(conn, quando=f"2024-05-18T2{n}:00:00Z", esposizione=300)
            conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (rig, f))
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _per_ottica(client):
    return {r["optics"]: r for r in client.get("/api/v1/gear").json()["rigs"]}


def test_a_rig_without_a_name_is_titled_by_its_pieces_without_the_brand(un_setup):
    """Il modello se c'e', se no il nome senza la marca, se no il nome intero."""
    rig = _per_ottica(un_setup)
    assert rig["Askar FRA400"]["title"] == "FRA400 · ASI2600MM Pro"
    assert rig["Il mio rifrattore"]["title"] == "Il mio rifrattore · ASI2600MM Pro"


def test_a_rig_without_a_name_missing_a_piece_says_it_with_a_question_mark():
    """Come la tavola (`corto`, 444): «? · 700D», non «700D», che sembra un nome dato."""
    camera = rig_card.Piece("Canon EOS 700D", "Canon", None)
    assert rig_card.title(None, None, camera) == "? · EOS 700D"
    assert rig_card.title(None, camera, None) == "EOS 700D · ?"
    assert rig_card.title(None, None, None) is None


def test_a_named_rig_is_titled_by_its_name(un_setup):
    rig_id = _per_ottica(un_setup)["Askar FRA400"]["id"]
    un_setup.patch(f"/api/v1/gear/rigs/{rig_id}", json={"name": "Grande campo"})
    assert _per_ottica(un_setup)["Askar FRA400"]["title"] == "Grande campo"


def test_the_ten_slots_come_in_the_card_order_and_say_what_is_missing(un_setup):
    """Ottica e camera ci sono; nessun file nomina il resto: otto da indicare."""
    rig = _per_ottica(un_setup)["Askar FRA400"]
    assert [s["kind"] for s in rig["slots"]] == [
        "optics",
        "camera",
        "reducer",
        "filter_wheel",
        "spacer",
        "mount",
        "focuser",
        "guide",
        "guide_camera",
        "software",
    ]
    assert [s["filled"] for s in rig["slots"]] == [True, True] + [False] * 8
    assert rig["slots_missing"] == 8


def test_a_chosen_part_fills_its_slot(un_setup):
    """Una montatura data a mano riempie la sua tacca; una guida fuori asse riempie «guida»."""
    rig_id = _per_ottica(un_setup)["Askar FRA400"]["id"]
    mount = un_setup.post("/api/v1/gear/instruments", json={"kind": "mount", "name": "AM5"})
    oag = un_setup.post("/api/v1/gear/instruments", json={"kind": "oag", "name": "OAG-L"})
    for kind, risposta in (("mount", mount), ("oag", oag)):
        # il giro che riparte dopo la scelta non e' cio' che si prova qui
        with mock.patch.object(work, "after", return_value=True):
            un_setup.put(
                f"/api/v1/gear/rigs/{rig_id}/parts/{kind}",
                json={"piece_id": risposta.json()["id"]},
            )

    rig = _per_ottica(un_setup)["Askar FRA400"]
    pieni = {s["kind"] for s in rig["slots"] if s["filled"]}
    assert pieni == {"optics", "camera", "mount", "guide"}
    assert rig["slots_missing"] == 6
