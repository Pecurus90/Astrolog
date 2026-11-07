"""The camera's bias for the sky brightness, one per offset the files wrote (ADR 0021, ADR 0022):
listed and declared through the API, carried by the answers' backup."""

from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.api.backup import is_user_write
from astrolog.db.connect import connect, create_database
from astrolog.pipeline.sqm_measure import declare_bias, sqm_root
from astrolog.spine import backup
from conftest import LATER
from test_pipeline_sqm_measure import _CARDS, _row, _shot

CAMERA = "ZWO ASI2600MM Pro"
ROUTE = "/api/v1/gear/camera-biases"


def _client(db_path):
    return TestClient(create_app(db_path), base_url="http://localhost")


def test_a_new_database_has_no_bias_to_ask(client_vuoto):
    answer = client_vuoto.get(ROUTE)
    assert (answer.status_code, answer.json()) == (200, [])


def test_each_camera_and_offset_of_the_files_is_listed_with_its_bias_or_none(
    db_path, conn, tmp_path
):
    _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    conn.commit()
    with _client(db_path) as c:
        listed = c.get(ROUTE).json()
    assert listed == [{"camera": CAMERA, "offset": 50, "bias_adu": None, "frames": 1}]


def test_a_declared_bias_rewrites_the_sky_brightness_of_those_shots(db_path, conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    conn.commit()
    with _client(db_path) as c:
        answer = c.put(ROUTE, json={"camera": CAMERA, "offset": 50, "bias_adu": 500.0})
        assert answer.status_code == 200, answer.text
        assert answer.json() == {"camera": CAMERA, "offset": 50, "bias_adu": 500.0, "frames": 1}
    row = _row(connect(db_path))
    assert row is not None and row["bias_adu"] == 500.0


def test_a_bias_for_a_camera_no_file_names_is_refused(client_vuoto):
    answer = client_vuoto.put(ROUTE, json={"camera": CAMERA, "offset": 50, "bias_adu": 500.0})
    assert (answer.status_code, answer.json()["detail"]) == (404, {"code": "camera_not_found"})


def test_a_bias_waits_while_the_worker_runs(client_vuoto, monkeypatch):
    monkeypatch.setattr(client_vuoto.app.state.worker, "is_running", lambda: True)
    answer = client_vuoto.put(ROUTE, json={"camera": CAMERA, "offset": 50, "bias_adu": 500.0})
    assert (answer.status_code, answer.json()["detail"]) == (409, {"code": "worker_busy"})


def test_a_bias_must_be_above_zero(client_vuoto):
    answer = client_vuoto.put(ROUTE, json={"camera": CAMERA, "offset": 50, "bias_adu": 0})
    assert answer.status_code == 422


def test_declaring_a_bias_is_a_write_of_the_user():
    assert is_user_write("PUT", ROUTE)


def test_the_backup_carries_the_bias_and_a_new_database_gets_it_back(conn, tmp_path):
    declare_bias(conn, CAMERA, None, 500.0, LATER)
    data = backup.collect(conn, this_machine=False)
    assert data["camera_biases"] == [{"camera": CAMERA, "offset": None, "bias_adu": 500.0}]
    assert backup.has_answers({"camera_biases": data["camera_biases"]})

    create_database(tmp_path / "nuovo.db")
    other = connect(tmp_path / "nuovo.db")
    backup.restore(other, data)
    backup.restore(other, data)  # twice: one row per camera and offset
    rows = other.execute("SELECT camera, offset, bias_adu FROM pipeline_camera_bias").fetchall()
    assert [tuple(r) for r in rows] == [(CAMERA, None, 500.0)]


def test_an_imported_bias_rewrites_the_sky_brightness_as_declaring_it_does(db_path, conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    conn.commit()
    before = _row(conn)
    create_database(tmp_path / "altro.db")
    other = connect(tmp_path / "altro.db")
    declare_bias(other, CAMERA, 50, 500.0, LATER)
    exported = backup.collect(other, this_machine=False)
    with _client(db_path) as c:
        answer = c.post("/api/v1/backup/import", json=exported)
        assert answer.status_code == 200, answer.text
    row = _row(connect(db_path))
    assert row is not None and before is not None
    assert row["bias_adu"] == 500.0 and row["sqm"] != before["sqm"]


def test_a_restored_bias_rewrites_the_sky_brightness_too(db_path, conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    conn.commit()
    before = _row(conn)
    create_database(tmp_path / "altro.db")
    other = connect(tmp_path / "altro.db")
    declare_bias(other, CAMERA, 50, 500.0, LATER)
    backup.path_for(db_path).write_text(
        backup.json_text(backup.collect(other, this_machine=True)), encoding="utf-8"
    )
    with _client(db_path) as c:
        answer = c.post("/api/v1/backup/restore")
        assert answer.status_code == 200, answer.text
    row = _row(connect(db_path))
    assert row is not None and before is not None
    assert row["bias_adu"] == 500.0 and row["sqm"] != before["sqm"]


def test_a_restored_bias_without_files_is_still_listed(db_path):
    conn = connect(db_path)
    declare_bias(conn, CAMERA, 30, 480.0, LATER)
    conn.commit()
    conn.close()
    with _client(db_path) as c:
        listed = c.get(ROUTE).json()
    assert listed == [{"camera": CAMERA, "offset": 30, "bias_adu": 480.0, "frames": 0}]
