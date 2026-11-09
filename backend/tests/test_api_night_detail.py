"""A night for its window (handoff/design/pagine/componenti/Riepilogo.dc.html, tipo notte): the
night as the Nights page shows it, when the shooting began and ended in the site's zone, the
setups that took it and what the catalog says of its objects."""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.catalog.load import beside_the_moon, extent_ly, parsecs
from conftest import LATER
from test_night_measures import _World


@pytest.fixture
def world(conn, tmp_path):
    return _World(conn, tmp_path / "Acquisizioni")


def _get(db_path, night: int):
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        return client.get(f"/api/v1/nights/{night}")


def _timed(conn, frame: int, start: str, exposure: float | None, rig: int | None = None) -> None:
    conn.execute(
        "UPDATE frames SET date_obs = ?, exposure_s = ?, rig_id = ? WHERE id = ?",
        (start, exposure, rig, frame),
    )


def _rig(conn) -> int:
    optics = conn.execute(
        "INSERT INTO instruments (kind, name, created_at) VALUES ('optics', 'Askar FRA400', ?)",
        (LATER,),
    ).lastrowid
    camera = conn.execute(
        "INSERT INTO instruments (kind, name, created_at) VALUES ('camera', 'ASI2600MM Pro', ?)",
        (LATER,),
    ).lastrowid
    return conn.execute(
        "INSERT INTO rigs (optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES (?, ?, 400, 1, ?)",
        (optics, camera, LATER),
    ).lastrowid


def _catalog(conn, obj: int, *, distance_ly: float | None, size_arcmin: float | None) -> None:
    conn.execute(
        "INSERT INTO catalog_entries (slug, name, common_name, ra_deg, dec_deg, x, y, z,"
        " constellation, type_code, distance_ly, size_major_arcmin, extent_ly, distance_pc,"
        " moon_compare, moon_count)"
        " VALUES ('ngc-6992', 'NGC 6992', 'Veil', 314, 31, 0.1, 0.2, 0.3, 'Cyg',"
        " 'SUPERNOVA_REMNANT', ?, ?, ?, ?, ?, ?)",
        (
            distance_ly,
            size_arcmin,
            extent_ly(distance_ly, size_arcmin),
            parsecs(distance_ly),
            *beside_the_moon(size_arcmin),
        ),
    )
    conn.execute("UPDATE objects SET catalog_slug = 'ngc-6992' WHERE id = ?", (obj,))


def test_no_such_night_is_a_404(db_path) -> None:
    answer = _get(db_path, 99)
    assert (answer.status_code, answer.json()["detail"]) == (404, "night_not_found")


def test_the_shooting_from_the_first_start_to_the_last_end_in_the_sites_zone(
    conn, db_path, world
) -> None:
    _timed(conn, world.frame(), "2026-10-12T19:00:00", 300.0)
    _timed(conn, world.frame(), "2026-10-13T01:30:00", 360.0)
    _timed(conn, world.frame(), "2026-10-12T22:00:00", None)  # without a time: its start
    conn.commit()
    body = _get(db_path, world.night).json()
    assert body["night"]["id"] == world.night
    assert (body["first_start"], body["last_end"]) == (
        "2026-10-12T21:00:00+02:00",
        "2026-10-13T03:36:00+02:00",
    )


def test_frames_that_do_not_say_when_have_no_hours(conn, db_path, world) -> None:
    world.frame()
    conn.commit()
    body = _get(db_path, world.night).json()
    assert (body["first_start"], body["last_end"]) == (None, None)


def test_the_setups_of_the_night_with_what_they_took_that_night(conn, db_path, world) -> None:
    rig = _rig(conn)
    _timed(conn, world.frame(), "2026-10-12T19:00:00", 300.0, rig)
    _timed(conn, world.frame(), "2026-10-12T19:10:00", 300.0, rig)
    _timed(conn, world.frame(), "2026-10-12T19:20:00", None)  # the rig not known
    conn.commit()
    rigs = _get(db_path, world.night).json()["rigs"]
    assert [(r["id"], r["optics"], r["camera"]) for r in rigs] == [
        (rig, "Askar FRA400", "ASI2600MM Pro")
    ]
    assert (rigs[0]["frames"], rigs[0]["integration_s"], rigs[0]["untimed"]) == (2, 600.0, 0)
    assert rigs[0]["parts"] == []


def test_an_object_in_the_catalog_says_what_it_is_and_how_big(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    world.frame(obj=veil)
    _catalog(conn, veil, distance_ly=2400.0, size_arcmin=60.0)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert [o["key"] for o in body["night"]["objects"]] == ["ngc-6992"]
    assert body["objects"] == [
        {
            "key": "ngc-6992",
            "common_name": "Veil",
            "type_code": "SUPERNOVA_REMNANT",
            "constellation": "Cyg",
            "distance": {"value": 2400.0, "unit": "ly"},
            # 2400 ly x 60' x pi / 10800: 41.9, two figures
            "extent_ly": 42.0,
        }
    ]


def test_a_far_galaxy_reads_in_millions_of_light_years(conn, db_path, world) -> None:
    far = world.object("M 31")
    world.frame(obj=far)
    _catalog(conn, far, distance_ly=2_540_000.0, size_arcmin=None)
    conn.commit()
    fact = _get(db_path, world.night).json()["objects"][0]
    assert (fact["distance"], fact["extent_ly"]) == ({"value": 2.5, "unit": "million_ly"}, None)


def test_an_object_outside_the_catalog_has_no_facts(conn, db_path, world) -> None:
    world.frame(obj=world.object("Cometa"))
    conn.commit()
    fact = _get(db_path, world.night).json()["objects"][0]
    assert fact == {
        "key": "Cometa",
        "common_name": None,
        "type_code": None,
        "constellation": None,
        "distance": None,
        "extent_ly": None,
    }
