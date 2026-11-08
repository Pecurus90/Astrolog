"""A night's measures from the API: what `night_measures` wrote, ready for the window of the night
(handoff/design/pagine/componenti/MisureFrame.dc.html), with the frames one by one."""

import pytest
from fastapi.testclient import TestClient

from astrolog import night_measures
from astrolog.api.app import create_app
from astrolog.measure_list import MEASURES
from test_night_measures import _World

T1 = "2026-10-12T21:00:00.000000+00:00"
T2 = "2026-10-12T22:00:00.000000+00:00"


@pytest.fixture
def world(conn, tmp_path):
    return _World(conn, tmp_path / "Acquisizioni")


def _get(db_path, night: int):
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        return client.get(f"/api/v1/nights/{night}/measures")


def test_no_such_night_is_a_404(db_path) -> None:
    answer = _get(db_path, 99)
    assert (answer.status_code, answer.json()["detail"]) == (404, "night_not_found")


def test_a_night_with_its_objects_filters_sets_and_frames(conn, db_path, world) -> None:
    m31 = world.object("M 31")
    lum = world.filter("L")
    late = world.shot(4.0, start=T2, obj=m31, flt=lum)
    early = world.shot(2.0, start=T1, obj=m31, flt=lum)
    waiting = world.frame(obj=m31, flt=lum)
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert (body["frames"], body["pending"], body["timezone"]) == (3, 1, "Europe/Rome")
    assert body["objects"] == [{"key": "M 31", "name": "M 31", "frames": 3, "pending": 1}]
    assert body["filters"] == [{"name": "L", "passband": "L", "frames": 3}]
    whole = next(s for s in body["sets"] if s["object_key"] is None and s["filter"] is None)
    assert (whole["frames"], whole["pending"], whole["comparable"]) == (3, 1, True)
    assert [m["key"] for m in whole["measures"]] == [e.key for e in MEASURES]
    hfd = next(m for m in whole["measures"] if m["key"] == "hfd_px")
    assert (hfd["measured"], hfd["median"], hfd["q1"], hfd["q3"], hfd["silent"]) == (
        2, 3.0, 2.5, 3.5, None,
    )  # fmt: skip
    assert hfd["unit"] == "px"
    both = {(s["object_key"], s["filter"]) for s in body["sets"]}
    assert both == {(None, None), ("M 31", None), (None, "L"), ("M 31", "L")}
    # in shooting order, the frame without measures last with its state
    assert [f["frame_id"] for f in body["series"]] == [early, late, waiting]
    first = body["series"][0]
    assert (first["start"], first["state"], first["values"]["hfd_px"]) == (T1, "measured", 2.0)
    assert (first["object_key"], first["filter"]) == ("M 31", "L")
    assert body["series"][2]["state"] == "pending"


def test_a_measure_nobody_has_says_why(conn, db_path, world) -> None:
    world.frame()  # not measured yet
    world.shot(3.0)
    night_measures.rebuild(conn)
    conn.commit()
    whole = _get(db_path, world.night).json()["sets"][0]
    fwhm = next(m for m in whole["measures"] if m["key"] == "fwhm_px")
    assert (fwhm["measured"], fwhm["median"], fwhm["silent"]) == (0, None, "no_value")


def test_a_night_still_being_measured_says_so(conn, db_path, world) -> None:
    world.frame()
    night_measures.rebuild(conn)
    conn.commit()
    whole = _get(db_path, world.night).json()["sets"][0]
    assert {m["silent"] for m in whole["measures"]} == {"measuring"}


def test_a_frame_of_a_program_not_read_says_so_and_is_not_measuring(conn, db_path, world) -> None:
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.skipped(rel, "not_supported")
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert body["series"][0]["state"] == "not_supported"
    assert {m["silent"] for m in body["sets"][0]["measures"]} == {"no_value"}


def test_a_night_not_rebuilt_yet_has_no_sets(conn, db_path, world) -> None:
    """Grouped but the measures not written yet: no sets, not an error."""
    world.frame()
    conn.commit()
    body = _get(db_path, world.night).json()
    assert (body["sets"], body["frames"]) == ([], 1)
