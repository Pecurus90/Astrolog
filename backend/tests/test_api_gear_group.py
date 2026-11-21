"""Il gruppo di un tipo e il modulo di un pezzo nella pagina Attrezzatura (tavola v82, passo 33 D):
cio' che la pagina mostra prima di un gesto arriva dall'API, la pagina non lo ricava."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog import night_measures
from astrolog.api import work
from astrolog.api.app import create_app
from astrolog.clock import now_iso
from test_api_gear_delete import filtro_nella_pagina
from test_api_gear_write import archivio, correggi, crea, pezzo, scegli  # noqa: F401
from test_night_measures import _World


def test_a_filter_says_its_passband_which_gives_its_colour(archivio):  # noqa: F811
    assert filtro_nella_pagina(archivio, "Ha")["passband"] == "HA"


def test_the_page_has_the_makers_already_written_once_each(archivio):  # noqa: F811
    crea(archivio, kind="focuser", name="EAF", brand="ZWO")
    crea(archivio, kind="mount", name="AM5", brand="ZWO")
    crea(archivio, kind="mount", name="EQ6-R", brand="Sky-Watcher")
    crea(archivio, kind="guide_camera", name="ASI120", brand="Zwo")
    assert archivio.get("/api/v1/gear").json()["brands"] == ["Sky-Watcher", "ZWO"]


def test_a_new_filter_colours_its_bands_as_the_saved_one_will(archivio):  # noqa: F811
    """The new filter's disc (board v82 `discoK`) before Salva: the same road from bands to a
    passband the write takes, as a table, so the page does not keep a second rule."""
    combos = archivio.get("/api/v1/gear").json()["band_passbands"]
    assert combos["HA"] == "HA"
    assert combos["HA+OIII"] == "DUO_HAOIII"
    assert combos["OIII+SII"] == "DUO_SIIOIII"
    assert combos["HA+OIII+SII"] == "TRI_NB"
    assert combos["G+R"] == "UNKNOWN"
    assert len(combos) == 2**8 - 1


def test_the_refusal_read_before_is_the_one_the_delete_gives(archivio):  # noqa: F811
    """Un distanziale non sta in nessun frame: le sue ore sono quelle dei setup che lo montano."""
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]
    distanziale = crea(archivio, kind="spacer", name="D10").json()["id"]
    archivio.put(f"/api/v1/gear/rigs/{rig}/spacers", json={"piece_ids": [distanziale]})

    letto = pezzo(archivio, "spacer", "D10")["delete_refused"]
    detto = archivio.delete(f"/api/v1/gear/instruments/{distanziale}").json()["detail"]

    assert letto == detto


def test_an_optics_card_carries_its_focal_ratio(archivio):  # noqa: F811
    """«Rapporto focale» calcolato nel modulo dell'ottica: focale nativa su apertura."""
    ottica = pezzo(archivio, "optics", "TS 130 APO")
    assert ottica["numbers"]["focal_ratio"]["value"] == pytest.approx(7.0)

    nuova = crea(archivio, kind="optics", name="RedCat 51", focal_mm=250.0).json()["id"]
    assert correggi(archivio, nuova, notes="x").status_code == 200
    detta = pezzo(archivio, "optics", "RedCat 51")["numbers"]["focal_ratio"]
    assert detta["missing"] == {"kind": "optics", "field": "aperture_mm"}


def test_a_piece_with_frames_says_before_the_gesture_why_it_stays(archivio):  # noqa: F811
    """Elimina spento prima del clic, col rifiuto che il DELETE darebbe."""
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]
    ottica = pezzo(archivio, "optics", "TS 130 APO")
    assert ottica["delete_refused"] == {"code": "in_use", "frames": 2, "rigs": [rig]}
    assert filtro_nella_pagina(archivio, "Ha")["delete_refused"] == {
        "code": "in_use",
        "frames": 1,
        "rigs": [rig],
    }


def test_the_optics_of_a_rig_without_frames_says_it_is_part_of_it(archivio):  # noqa: F811
    camera = crea(archivio, kind="camera", name="ASI533MC").json()["id"]
    ottica = crea(archivio, kind="optics", name="RedCat 51").json()["id"]
    nuovo = archivio.post(
        "/api/v1/gear/rigs", json={"optics_id": ottica, "camera_id": camera, "focal_mm": 250}
    ).json()["id"]

    assert pezzo(archivio, "camera", "ASI533MC")["delete_refused"] == {
        "code": "in_rig",
        "frames": 0,
        "rigs": [nuovo],
    }


def test_a_piece_without_frames_can_go(archivio):  # noqa: F811
    crea(archivio, kind="focuser", name="EAF")
    assert pezzo(archivio, "focuser", "EAF")["delete_refused"] is None


def test_a_free_mount_knows_the_rig_still_without_one(archivio):  # noqa: F811
    """«Seleziona montatura» apre la scelta sul primo setup senza montatura; scelta, sparisce."""
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]
    montatura = crea(archivio, kind="mount", name="EQ6-R").json()["id"]
    assert pezzo(archivio, "mount", "EQ6-R")["rig_for_mount"] == rig

    with mock.patch.object(work, "after", return_value=True):
        scegli(archivio, rig, "mount", montatura)
    crea(archivio, kind="mount", name="AM5")

    assert pezzo(archivio, "mount", "EQ6-R")["rig_for_mount"] is None
    # scelta su un setup, non dice piu' "non associata a un setup"
    assert pezzo(archivio, "mount", "EQ6-R")["no_hours"] is None
    senza = [
        r["id"]
        for r in archivio.get("/api/v1/gear").json()["rigs"]
        if not any(s["kind"] == "mount" and s["filled"] for s in r["slots"])
    ]
    assert rig not in senza
    assert pezzo(archivio, "mount", "AM5")["rig_for_mount"] == (senza[0] if senza else None)


@pytest.fixture
def camera_con_offset(db_path, conn, tmp_path):
    """Una camera i cui file scrivono due offset: i frame passano dal ponte (ADR 0045)."""
    mondo = _World(conn, tmp_path / "Acquisizioni")
    camera = conn.execute(
        "INSERT INTO instruments (kind, name, created_at) VALUES ('camera', 'ASI2600MM', ?)",
        (now_iso(),),
    ).lastrowid
    rig = conn.execute(
        "INSERT INTO rigs (camera_id, detected, created_at) VALUES (?, 1, ?)", (camera, now_iso())
    ).lastrowid
    for offset in (50, 50, 30):
        frame = mondo.shot(2.0)
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (rig, frame))
        conn.execute(
            "UPDATE pipeline_cards SET offset = ? WHERE file_id = (SELECT MAX(file_id)"
            " FROM pipeline_cards)",
            (offset,),
        )
    night_measures.rebuild(conn)
    conn.commit()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c, camera


def _camera_che_scrive(conn, tmp_path, scatti):
    """Camera della pagina i cui file scrivono `(offset, grafia)`; un bias dichiarato."""
    mondo = _World(conn, tmp_path / "Acquisizioni")
    camera = conn.execute(
        "INSERT INTO instruments (kind, name, created_at) VALUES ('camera', 'ASI2600MM', ?)",
        (now_iso(),),
    ).lastrowid
    rig = conn.execute(
        "INSERT INTO rigs (camera_id, detected, created_at) VALUES (?, 1, ?)", (camera, now_iso())
    ).lastrowid
    for offset, grafia in scatti:
        frame = mondo.shot(2.0)
        conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (rig, frame))
        conn.execute(
            "UPDATE pipeline_cards SET offset = ?, camera = ? WHERE file_id = (SELECT MAX(file_id)"
            " FROM pipeline_cards)",
            (offset, grafia),
        )
    conn.execute(
        "INSERT INTO pipeline_camera_bias (camera, offset, bias_adu)"
        " VALUES ('ZWO ASI2600MM', 50, 480)"
    )
    night_measures.rebuild(conn)
    conn.commit()
    return camera


def test_two_spellings_of_one_camera_add_up_per_offset_and_the_unknown_offset_goes_first(
    conn, tmp_path
):
    """Due grafie dei driver per la stessa camera: un offset, una riga, i frame sommati; il bias
    dichiarato su una grafia vale per la riga, in qualunque ordine arrivino le grafie."""
    camera = _camera_che_scrive(
        conn, tmp_path,
        [(50, "ZWO ASI2600MM Pro"), (50, "ZWO ASI2600MM"), (50, "ZWO ASI2600MM Pro"),
         (None, "ZWO ASI2600MM Pro"), (0, "ZWO ASI2600MM Pro")],
    )  # fmt: skip
    from astrolog.spine import inventory

    attesi = [
        {"offset": None, "bias_adu": None, "frames": 1},
        {"offset": 0, "bias_adu": None, "frames": 1},
        {"offset": 50, "bias_adu": 480.0, "frames": 3},
    ]
    assert inventory.camera_biases(conn, camera) == attesi
    assert inventory.camera_biases(conn, camera + 99) == []
    assert sorted(inventory.camera_spellings(conn, camera), key=str) == sorted(
        [("ZWO ASI2600MM", 50), ("ZWO ASI2600MM Pro", 0), ("ZWO ASI2600MM Pro", 50),
         ("ZWO ASI2600MM Pro", None)], key=str,
    )  # fmt: skip
    assert inventory.camera_spellings(conn, camera + 99) == []
    pezzo_ = next(p for p in inventory.instruments(conn) if p["id"] == camera)
    assert pezzo_["biases"] == attesi


def test_the_offsets_are_read_as_the_bridge_rebuild_wrote_them(conn, tmp_path):
    """Una lettura non conta le pose (ADR 0048): un numero scritto a mano si vede, e la
    ricostruzione del ponte lo rifa' dalle pose."""
    camera = _camera_che_scrive(conn, tmp_path, [(50, "ZWO ASI2600MM"), (50, "ZWO ASI2600MM")])
    from astrolog.spine import inventory

    conn.execute("UPDATE camera_offsets SET frames = 7")
    assert inventory.camera_biases(conn, camera) == [{"offset": 50, "bias_adu": 480.0, "frames": 7}]
    night_measures.rebuild(conn)
    assert inventory.camera_biases(conn, camera) == [{"offset": 50, "bias_adu": 480.0, "frames": 2}]


def _biases(client, camera):
    pagina = client.get("/api/v1/gear").json()
    return next(p for p in pagina["instruments"] if p["id"] == camera)["biases"]


def test_a_camera_lists_one_bias_per_offset_its_files_write(camera_con_offset):
    client, camera = camera_con_offset
    assert _biases(client, camera) == [
        {"offset": 30, "bias_adu": None, "frames": 1},
        {"offset": 50, "bias_adu": None, "frames": 2},
    ]


def test_a_bias_written_on_the_camera_goes_to_its_files_spelling(camera_con_offset):
    client, camera = camera_con_offset
    risposta = client.put(
        f"/api/v1/gear/instruments/{camera}/biases", json={"offset": 50, "bias_adu": 500}
    )
    assert risposta.status_code == 200, risposta.text
    assert _biases(client, camera)[1] == {"offset": 50, "bias_adu": 500, "frames": 2}
    elenco = client.get("/api/v1/gear/camera-biases").json()
    assert {"camera": "ZWO ASI2600MM Pro", "offset": 50, "bias_adu": 500, "frames": 2} in elenco


def test_a_bias_for_an_offset_the_camera_never_wrote_is_not_found(camera_con_offset):
    client, camera = camera_con_offset
    risposta = client.put(
        f"/api/v1/gear/instruments/{camera}/biases", json={"offset": 10, "bias_adu": 500}
    )
    assert (risposta.status_code, risposta.json()["detail"]["code"]) == (404, "offset_not_found")


def test_a_bias_waits_while_the_worker_runs(camera_con_offset):
    client, camera = camera_con_offset
    with mock.patch.object(client.app.state.worker, "is_running", return_value=True):
        risposta = client.put(
            f"/api/v1/gear/instruments/{camera}/biases", json={"offset": 50, "bias_adu": 500}
        )
    assert (risposta.status_code, risposta.json()["detail"]["code"]) == (409, "worker_busy")
