"""Il dettaglio di un setup nella pagina Attrezzatura (tavola v82): il confronto dei campi con la
Luna, l'anello dei filtri e i pezzi di ottica e camera, gia' pronti dall'API -- la pagina li
disegna e basta.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.spine import gear_usage, inventory, rig_card
from astrolog.units import MOON_DIAMETER_DEG
from group_bench import ROMA, attrezzo, corri, filtro, luogo, posa, prepara


def _rig(conn, ottica, camera, focale):
    return conn.execute(
        "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES(?, ?, ?, 1, ?)",
        (ottica, camera, focale, now_iso()),
    ).lastrowid


def _risolta(conn, frame_id, larghezza, altezza):
    conn.execute(
        "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
        " height_deg, solved_at) VALUES(?, 10.0, 41.0, 1.5, ?, ?, ?)",
        (frame_id, larghezza, altezza, now_iso()),
    )


@pytest.fixture
def tre_setup(db_path):
    """Un setup largo (3,36 x 2,25), uno stretto (1,5 x 1), uno senza cielo misurato. Il largo
    ha tre frame in Ha e uno in OIII."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        camera = attrezzo(conn, "camera", "ASI2600MM", pixel_size_um=3.76, width_px=6248)
        largo = _rig(conn, attrezzo(conn, "optics", "FRA400"), camera, 405.0)
        stretto = _rig(conn, attrezzo(conn, "optics", "TS 130 APO"), camera, 905.0)
        _rig(conn, attrezzo(conn, "optics", "EdgeHD 8"), camera, 2032.0)
        ha, oiii = filtro(conn, "Ha", "HA"), filtro(conn, "OIII", "OIII")
        for n, filtro_id in enumerate((ha, ha, ha, oiii)):
            f = posa(conn, quando=f"2024-05-18T2{n}:00:00Z", filtro_id=filtro_id, esposizione=300)
            conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (largo, f))
            _risolta(conn, f, 3.36, 2.25)
        f = posa(conn, quando="2024-05-19T22:00:00Z", esposizione=300)
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (stretto, f))
        _risolta(conn, f, 1.5, 1.0)
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _per_focale(pagina):
    return {r["focal_mm"]: r for r in pagina["rigs"]}


def test_the_fields_come_widest_first_on_the_same_frame_with_the_moon(tre_setup):
    """La cornice e' il campo piu' largo piu' un 15%, alta due terzi (`confronto`, 323): ogni
    riquadro e la Luna in percento di quella."""
    pagina = tre_setup.get("/api/v1/gear").json()
    rig = _per_focale(pagina)
    larghezza = 3.36 * 1.15
    assert [b["rig_id"] for b in pagina["fields"]] == [rig[405.0]["id"], rig[905.0]["id"]]
    largo, stretto = pagina["fields"]
    assert largo["width_pct"] == pytest.approx(3.36 / larghezza * 100, abs=0.1)
    assert largo["height_pct"] == pytest.approx(2.25 / (larghezza / 1.5) * 100, abs=0.1)
    assert stretto["width_pct"] == pytest.approx(1.5 / larghezza * 100, abs=0.1)
    assert pagina["moon_pct"] == pytest.approx(MOON_DIAMETER_DEG / larghezza * 100, abs=0.1)


def test_the_boxes_and_the_moon_are_written_to_the_hundredth(tre_setup):
    """Al centesimo, come li scrive `write_fields`: il terzo decimale non arriva alla pagina."""
    pagina = tre_setup.get("/api/v1/gear").json()
    rig = _per_focale(pagina)
    riquadri, luna = rig_card.field_boxes({1: (3.36, 2.25), 2: (1.5, 1.0)}, MOON_DIAMETER_DEG)
    attesi = [
        {"rig_id": rig[f]["id"], "width_pct": round(w, 2), "height_pct": round(h, 2)}
        for f, (w, h) in ((405.0, riquadri[1]), (905.0, riquadri[2]))
    ]
    assert pagina["fields"] == attesi
    assert pagina["moon_pct"] == round(luna, 2)


def test_one_rig_alone_has_its_box_and_the_moon(db_path):
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        camera = attrezzo(conn, "camera", "ASI2600MM", pixel_size_um=3.76, width_px=6248)
        solo = _rig(conn, attrezzo(conn, "optics", "FRA400"), camera, 405.0)
        f = posa(conn, quando="2024-05-18T22:00:00Z", esposizione=300)
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (solo, f))
        _risolta(conn, f, 3.0, 2.0)
        corri(conn)
        riquadri, luna = inventory.fields(conn)
    finally:
        conn.close()
    assert [b["rig_id"] for b in riquadri] == [solo]
    # 15,266...: il terzo decimale non e' zero, e non si scrive
    assert luna == round(MOON_DIAMETER_DEG / (3.0 * 1.15) * 100, 2)


@pytest.mark.parametrize(
    ("frames", "anello"),
    [
        ([1, 2], [(0.0, 33.33), (33.33, 100.0)]),
        ([1, 1, 1], [(0.0, 33.33), (33.33, 66.67), (66.67, 100.0)]),
        ([0, 0], None),
        ([], None),
    ],
)
def test_the_ring_cuts_are_to_the_hundredth(frames, anello):
    """Ogni fetta dal suo inizio alla sua fine in percento, al centesimo; senza frame, niente."""
    assert gear_usage._ring(frames) == anello


def test_a_tiny_field_is_drawn_on_a_frame_of_at_least_nine_tenths_of_a_degree():
    """Sotto 0,9 gradi la cornice non stringe piu': un campo da planetario resta piccolo."""
    riquadri, luna = rig_card.field_boxes({1: (0.2, 0.1)}, MOON_DIAMETER_DEG)
    cornice = 0.9 * 1.15
    assert riquadri[1] == pytest.approx((0.2 / cornice * 100, 0.1 / (cornice / 1.5) * 100))
    assert luna == pytest.approx(MOON_DIAMETER_DEG / cornice * 100)


def test_a_tall_field_never_overflows_the_frame():
    riquadri, _ = rig_card.field_boxes({1: (2.0, 4.0)}, MOON_DIAMETER_DEG)
    assert riquadri[1][1] == 100.0


def test_without_a_solved_rig_there_is_nothing_to_compare(db_path):
    conn = connect(db_path)
    try:
        prepara(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        pagina = c.get("/api/v1/gear").json()
    assert pagina["fields"] == []
    assert pagina["moon_pct"] is None


def test_the_filter_ring_is_in_proportion_to_the_frames(tre_setup):
    """Tre frame in Ha e uno in OIII: tre quarti e un quarto, con la banda che da' il colore."""
    rig = _per_focale(tre_setup.get("/api/v1/gear").json())[405.0]
    anello = [
        (p["name"], p["passband"], p["ring_from"], p["ring_to"])
        for p in rig["parts"]
        if p["kind"] == "filter"
    ]
    assert anello == [("Ha", "HA", 0.0, 75.0), ("OIII", "OIII", 75.0, 100.0)]


def test_a_rig_says_which_pieces_are_its_optics_and_camera(tre_setup):
    """Per aprire il pezzo fra i componenti e leggerne la scheda."""
    pagina = tre_setup.get("/api/v1/gear").json()
    per_nome = {p["name"]: p["id"] for p in pagina["instruments"]}
    rig = _per_focale(pagina)[905.0]
    assert rig["optics_id"] == per_nome["TS 130 APO"]
    assert rig["camera_id"] == per_nome["ASI2600MM"]
