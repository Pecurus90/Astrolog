"""La scheda tecnica e i conti del setup dalla pagina (ADR 0021): la guida fuori asse, i
distanziali, i conti scritti da chi scrive e letti dalla pagina, il backup che li porta.
I conti uno per uno stanno in `test_rig_numbers.py`."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api import work
from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.spine import backup, rig_numbers
from group_bench import ROMA, attrezzo, corri, luogo, posa, prepara
from test_api_gear_write import correggi, crea, pezzo


@pytest.fixture
def archivio(db_path):
    """Un setup con due frame: TS 130 APO a 910 mm e una ASI2600MM."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        ottica = attrezzo(conn, "optics", "TS 130 APO", focal_mm=910.0)
        camera = attrezzo(conn, "camera", "ASI2600MM", pixel_size_um=3.76)
        rig = conn.execute(
            "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
            " VALUES(?, ?, 910.0, 1, '2024-05-18T00:00:00Z')",
            (ottica, camera),
        ).lastrowid
        uno = posa(conn, quando="2024-05-18T22:00:00Z", hash_="p0")
        due = posa(conn, quando="2024-05-18T23:00:00Z", hash_="p1")
        conn.execute("UPDATE frames SET rig_id = ? WHERE id IN (?, ?)", (rig, uno, due))
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    # i frame del banco non hanno header: un giro di normalize li staccherebbe dal setup
    with (
        mock.patch.object(work, "after", return_value=False),
        TestClient(create_app(db_path), base_url="http://localhost") as c,
    ):
        yield c


def pagina(client):
    return client.get("/api/v1/gear").json()


def il_setup(client):
    return pagina(client)["rigs"][0]


def scegli(client, kind, piece_id):
    rig = il_setup(client)["id"]
    return client.put(f"/api/v1/gear/rigs/{rig}/parts/{kind}", json={"piece_id": piece_id})


def distanziali(client, *ids):
    rig = il_setup(client)["id"]
    return client.put(f"/api/v1/gear/rigs/{rig}/spacers", json={"piece_ids": list(ids)})


def nuovo(client, kind, nome, **scheda):
    risposta = crea(client, kind=kind, name=nome, **scheda)
    assert risposta.status_code == 201, risposta.text
    return risposta.json()["id"]


def test_the_rig_says_what_it_lacks_then_its_number_once_written(archivio):
    """Il rapporto focale manca dell'apertura dell'ottica, e lo dice; scritta, c'e' subito."""
    conti = il_setup(archivio)["numbers"]
    assert conti["focal_ratio"]["missing"] == {"kind": "optics", "field": "aperture_mm"}
    ottica = pezzo(archivio, "optics", "TS 130 APO")
    assert correggi(archivio, ottica["id"], aperture_mm=130.0).status_code == 200
    assert il_setup(archivio)["numbers"]["focal_ratio"]["value"] == pytest.approx(7.0)
    assert pezzo(archivio, "optics", "TS 130 APO")["numbers"]["dawes"]["value"] == pytest.approx(
        116 / 130
    )


def test_the_page_reads_the_numbers_and_never_computes_them(archivio):
    with mock.patch.object(rig_numbers, "numbers", side_effect=AssertionError("ha calcolato")):
        assert archivio.get("/api/v1/gear").status_code == 200


def test_a_rig_guides_with_a_guide_scope_or_an_oag_never_both(archivio):
    cercatore = nuovo(archivio, "guide_scope", "Cercatore 30/120", focal_mm=120.0)
    oag = nuovo(archivio, "oag", "OAG-L", thickness_mm=16.5, prism_mm=8.0)
    assert scegli(archivio, "guide_scope", cercatore).status_code == 200
    assert scegli(archivio, "oag", oag).status_code == 200
    guide = {p["kind"] for p in il_setup(archivio)["parts"] if p["chosen"]}
    assert guide == {"oag"}
    scegli(archivio, "guide_scope", cercatore)
    guide = {p["kind"] for p in il_setup(archivio)["parts"] if p["chosen"]}
    assert guide == {"guide_scope"}


def test_an_oag_guides_with_the_focal_of_the_rig(archivio):
    oag = nuovo(archivio, "oag", "OAG-L", thickness_mm=16.5)
    guida = nuovo(archivio, "guide_camera", "ASI120MM Mini", pixel_size_um=3.75)
    scegli(archivio, "oag", oag)
    scegli(archivio, "guide_camera", guida)
    scala = il_setup(archivio)["numbers"]["guide_scale"]
    assert scala["value"] == pytest.approx(206.265 * 3.75 / 910)
    assert scala["in_range"] is True


def test_a_rig_has_all_its_spacers_with_the_rigs_hours(archivio):
    lungo = nuovo(archivio, "spacer", "Distanziale 10 mm", thickness_mm=10.0)
    corto = nuovo(archivio, "spacer", "Distanziale 5 mm", thickness_mm=5.0)
    assert distanziali(archivio, lungo, corto).status_code == 200
    parti = [p for p in il_setup(archivio)["parts"] if p["kind"] == "spacer"]
    assert {p["id"] for p in parti} == {lungo, corto}
    assert all(p["chosen"] for p in parti)
    assert pezzo(archivio, "spacer", "Distanziale 10 mm")["frames"] == il_setup(archivio)["frames"]


def test_spacers_follow_a_rename_and_an_empty_list_takes_them_off(archivio):
    spessore = nuovo(archivio, "spacer", "D10", thickness_mm=10.0)
    distanziali(archivio, spessore)
    correggi(archivio, spessore, name="Distanziale M48 10")
    parti = [p["name"] for p in il_setup(archivio)["parts"] if p["kind"] == "spacer"]
    assert parti == ["Distanziale M48 10"]
    distanziali(archivio)
    assert not [p for p in il_setup(archivio)["parts"] if p["kind"] == "spacer"]
    assert pezzo(archivio, "spacer", "Distanziale M48 10")["no_hours"] == "no_rig"


def test_only_a_spacer_is_a_spacer(archivio):
    cercatore = nuovo(archivio, "guide_scope", "Cercatore")
    risposta = distanziali(archivio, cercatore)
    assert (risposta.status_code, risposta.json()["detail"]["code"]) == (422, "not_of_kind")


def test_the_backfocus_counts_the_spacers_against_the_optics(archivio):
    ottica = pezzo(archivio, "optics", "TS 130 APO")
    camera = pezzo(archivio, "camera", "ASI2600MM")
    correggi(archivio, ottica["id"], required_backfocus_mm=55.0, backfocus_tolerance_mm=1.0)
    correggi(archivio, camera["id"], thickness_mm=17.5)
    distanziali(archivio, nuovo(archivio, "spacer", "D37.5", thickness_mm=37.5))
    backfocus = il_setup(archivio)["numbers"]["backfocus"]
    assert (backfocus["difference_mm"], backfocus["verdict"]) == (0.0, "exact")


def test_the_train_draws_the_pieces_the_numbers_read(archivio):
    """Il treno ottico disegna i pezzi che i conti leggono: la parte scelta, la guida una sola."""
    ottica = pezzo(archivio, "optics", "TS 130 APO")["id"]
    camera = pezzo(archivio, "camera", "ASI2600MM")["id"]
    scelti = {
        "reducer": nuovo(archivio, "reducer", "Riduttore 0,8x", reducer_factor=0.8),
        "guide_scope": nuovo(archivio, "guide_scope", "Cercatore 30/120", focal_mm=120.0),
        "guide_camera": nuovo(archivio, "guide_camera", "ASI120MM Mini"),
        "filter_wheel": nuovo(archivio, "filter_wheel", "EFW 7x36", slots=7),
        "focuser": nuovo(archivio, "focuser", "EAF"),
    }
    for kind, piece_id in scelti.items():
        assert scegli(archivio, kind, piece_id).status_code == 200
    lungo = nuovo(archivio, "spacer", "D10", thickness_mm=10.0)
    corto = nuovo(archivio, "spacer", "D5", thickness_mm=5.0)
    distanziali(archivio, lungo, corto)
    setup = il_setup(archivio)
    assert "pieces" not in setup["numbers"]
    assert setup["pieces"] == {
        "optics": ottica,
        "camera": camera,
        "reducer": scelti["reducer"],
        "guide": scelti["guide_scope"],
        "guide_camera": scelti["guide_camera"],
        "wheel": scelti["filter_wheel"],
        "focuser": scelti["focuser"],
        "mount": None,
        "spacers": [lungo, corto],
    }


def test_a_filter_carries_its_sheet(archivio):
    risposta = archivio.post(
        "/api/v1/gear/filters",
        json={
            "name": "Ha 3nm", "bands": [{"band": "HA", "width_nm": 3.0}],
            "filter_size": "36mm", "thickness_mm": 2.0, "mounted": False, "fast_optics": True,
        },
    )  # fmt: skip
    assert risposta.status_code == 201, risposta.text
    scritto = next(f for f in pagina(archivio)["filters"] if f["name"] == "Ha 3nm")
    assert (scritto["filter_size"], scritto["mounted"], scritto["fast_optics"]) == (
        "36mm", False, True,
    )  # fmt: skip


def test_the_backup_carries_the_new_fields(archivio):
    nuovo(archivio, "oag", "OAG-L", thickness_mm=16.5, prism_mm=8.0)
    with connect(archivio.app.state.db_path) as conn:
        salvato = backup.collect(conn, this_machine=True)
    oag = next(i for i in salvato["instruments"] if i["name"] == "OAG-L")
    assert (oag["kind"], oag["thickness_mm"], oag["prism_mm"]) == ("oag", 16.5, 8.0)
