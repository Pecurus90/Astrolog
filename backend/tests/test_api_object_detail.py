"""An object for its window (handoff/design/pagine/componenti/Riepilogo.dc.html, tipo oggetto): the
Archive's row, its nights as the Nights page shows them with what the object took in each, the
setups that took it, and what the catalog says of it."""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.catalog.load import parsecs
from conftest import LATER
from test_api_night_detail import _catalog, _rig, _timed
from test_night_measures import _World
from test_spine_archive_mosaic import CHIAVE, mosaico


@pytest.fixture
def world(conn, tmp_path):
    return _World(conn, tmp_path / "Acquisizioni")


def _get(db_path, key: str, **params):
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        return client.get(f"/api/v1/objects/{key}", params=params)


def _second_night(conn, date: str = "2026-10-20", site: str = "Cima Ekar") -> int:
    place = conn.execute(
        "INSERT INTO sites (name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES (?, 45.8, 11.6, 'Europe/Rome', 0, ?)",
        (site, LATER),
    ).lastrowid
    return conn.execute(
        "INSERT INTO nights (site_id, night_date, created_at) VALUES (?, ?, ?)",
        (place, date, LATER),
    ).lastrowid


def test_no_such_object_is_a_404(db_path) -> None:
    answer = _get(db_path, "M 999")
    assert (answer.status_code, answer.json()["detail"]) == (404, "object_not_found")


def test_the_row_is_the_archives_row(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:00:00", 300.0)
    conn.commit()
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        listed = client.get("/api/v1/archive", params={"key": "NGC 6992"}).json()["items"][0]
        body = client.get("/api/v1/objects/NGC 6992").json()
    assert body["row"] == listed


def test_its_nights_in_shooting_order_with_what_it_took_in_each(conn, db_path, world) -> None:
    veil, other = world.object("NGC 6992"), world.object("M 31")
    later = _second_night(conn)
    _timed(conn, world.frame(obj=veil, night=later), "2026-10-20T19:00:00", 300.0)
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:00:00", 300.0)
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:10:00", None)
    _timed(conn, world.frame(obj=other), "2026-10-12T19:20:00", 600.0)
    _timed(conn, world.frame(obj=other, night=later), "2026-10-20T20:00:00", 600.0)
    conn.commit()
    body = _get(db_path, "NGC 6992").json()
    taken = [
        (n["night"]["id"], n["frames"], n["integration_s"], n["untimed"]) for n in body["nights"]
    ]
    assert taken == [(world.night, 2, 300.0, 1), (later, 1, 300.0, 0)]
    # the night itself is the Nights page's row: all its frames
    assert body["nights"][0]["night"]["frames"] == 3
    assert (body["first_night"], body["last_night"]) == ("2026-10-12", "2026-10-20")
    assert body["sites"] == ["Casa", "Cima Ekar"]


def test_a_night_without_the_object_is_not_its_night(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    world.frame(obj=veil)
    world.frame(obj=world.object("M 31"), night=_second_night(conn))
    conn.commit()
    body = _get(db_path, "NGC 6992").json()
    assert [n["night"]["id"] for n in body["nights"]] == [world.night]
    assert body["sites"] == ["Casa"]


def test_the_setups_that_took_it_with_its_frames_only(conn, db_path, world) -> None:
    rig = _rig(conn)
    veil = world.object("NGC 6992")
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:00:00", 300.0, rig)
    _timed(conn, world.frame(obj=world.object("M 31")), "2026-10-12T19:10:00", 300.0, rig)
    conn.commit()
    rigs = _get(db_path, "NGC 6992").json()["rigs"]
    assert [(r["id"], r["optics"], r["frames"], r["integration_s"]) for r in rigs] == [
        (rig, "Askar FRA400", 1, 300.0)
    ]


def test_a_production_narrows_everything_to_its_frames(conn, db_path, world) -> None:
    rig = _rig(conn)
    optics, camera = conn.execute(
        "SELECT optics_id, camera_id FROM rigs WHERE id = ?", (rig,)
    ).fetchone()
    veil = world.object("NGC 6992")
    later = _second_night(conn)
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:00:00", 300.0, rig)
    _timed(conn, world.frame(obj=veil, night=later), "2026-10-20T19:00:00", 300.0)
    conn.commit()
    body = _get(db_path, "NGC 6992", production=f"{optics}:{camera}").json()
    assert [n["night"]["id"] for n in body["nights"]] == [world.night]
    assert (body["row"]["frames"], [r["id"] for r in body["rigs"]]) == (1, [rig])
    produced = [(p["optics_id"], p["camera_id"]) for p in body["row"]["productions"]]
    assert produced == [(optics, camera)]


def test_a_production_with_pieces_the_frames_do_not_say(conn, db_path, world) -> None:
    rig = _rig(conn)
    camera = conn.execute("SELECT camera_id FROM rigs WHERE id = ?", (rig,)).fetchone()[0]
    camera_only = conn.execute(
        "INSERT INTO rigs (camera_id, detected, created_at) VALUES (?, 1, ?)", (camera, LATER)
    ).lastrowid
    veil = world.object("NGC 6992")
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:00:00", 300.0, rig)
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:10:00", 300.0, camera_only)
    _timed(conn, world.frame(obj=veil), "2026-10-12T19:20:00", 300.0)  # no rig at all
    conn.commit()
    one = _get(db_path, "NGC 6992", production=f"none:{camera}").json()
    assert (one["row"]["frames"], [r["id"] for r in one["rigs"]]) == (1, [camera_only])
    bare = _get(db_path, "NGC 6992", production="none:none").json()
    assert (bare["row"]["frames"], bare["rigs"]) == (1, [])


def test_a_production_that_is_not_one_is_a_422(db_path) -> None:
    assert _get(db_path, "NGC 6992", production="12").status_code == 422


def test_what_the_catalog_says_with_its_size_on_the_sky(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    world.frame(obj=veil)
    _catalog(conn, veil, distance_ly=2400.0, size_arcmin=60.0)
    conn.commit()
    facts = _get(db_path, "ngc-6992").json()["facts"]
    assert facts == {
        "key": "ngc-6992",
        "common_name": "Veil",
        "type_code": "SUPERNOVA_REMNANT",
        "constellation": "Cyg",
        "distance": {"value": 2400.0, "unit": "ly"},
        "extent_ly": 42.0,
        # 2400 / 3.2616 = 735.8, to the ten as the board says it
        "distance_pc": 740.0,
        "size_arcmin": 60.0,
        # 60' / 31' = 1.94 Moons: more than one
        "moon": {"compare": "more", "moons": 1},
    }


@pytest.mark.parametrize(
    ("size", "moon"),
    [
        (31.0, {"compare": "like", "moons": None}),
        (28.0, {"compare": "like", "moons": None}),  # 0.90 of a Moon
        (27.0, {"compare": "less", "moons": None}),
        (100.0, {"compare": "more", "moons": 3}),
    ],
)
def test_its_size_beside_the_full_moon(conn, db_path, world, size, moon) -> None:
    veil = world.object("NGC 6992")
    world.frame(obj=veil)
    _catalog(conn, veil, distance_ly=2400.0, size_arcmin=size)
    conn.commit()
    assert _get(db_path, "ngc-6992").json()["facts"]["moon"] == moon


def test_parsecs_round_half_up_as_the_board() -> None:
    # 25 pc exactly: Python's round would give 20
    assert parsecs(25 * 3.2616) == 30.0


def test_a_far_galaxy_has_no_parsecs(conn, db_path, world) -> None:
    far = world.object("M 31")
    world.frame(obj=far)
    _catalog(conn, far, distance_ly=2_540_000.0, size_arcmin=None)
    conn.commit()
    facts = _get(db_path, "ngc-6992").json()["facts"]
    assert (facts["distance_pc"], facts["size_arcmin"], facts["moon"]) == (None, None, None)


def test_a_mosaic_has_the_nights_of_its_panels_and_not_of_its_objects_alone(
    conn, db_path, world
) -> None:
    ic405, lbn796 = world.object("IC 405"), world.object("LBN 796")
    later, alone = _second_night(conn), _second_night(conn, "2026-10-25", "Asiago")
    inside = [world.frame(obj=ic405), world.frame(obj=lbn796, night=later)]
    _timed(conn, inside[0], "2026-10-12T19:00:00", 300.0)
    _timed(conn, inside[1], "2026-10-20T19:00:00", 300.0)
    _timed(conn, world.frame(obj=ic405, night=alone), "2026-10-25T19:00:00", 600.0)
    mosaico(conn, inside)
    conn.commit()
    body = _get(db_path, CHIAVE).json()
    assert body["row"]["key"] == CHIAVE
    panels = [(p["frames"], p["integration_s"]) for p in body["row"]["panel_list"]]
    assert panels == [(1, 300.0), (1, 300.0)]
    taken = [(n["night"]["id"], n["frames"]) for n in body["nights"]]
    assert taken == [(world.night, 1), (later, 1)]
    assert (body["first_night"], body["sites"]) == ("2026-10-12", ["Casa", "Cima Ekar"])
    # IC 405 by itself keeps only the night it was taken alone
    own = _get(db_path, "IC 405").json()
    assert [n["night"]["id"] for n in own["nights"]] == [alone]


def _panel_of(db_path, name: str) -> int:
    listed = _get(db_path, CHIAVE).json()["row"]["panel_list"]
    return next(p["id"] for p in listed if p["object"] == name)


def test_a_panel_narrows_the_window_to_its_frames_and_its_catalog(conn, db_path, world) -> None:
    """Riepilogo.dc.html 116-118, 160: a panel is a tab of its own; its catalog tiles are its
    object's, the mosaic's when its object is not in the catalog."""
    veil, dark = world.object("NGC 6992"), world.object("LDN 1516")
    _catalog(conn, veil, distance_ly=2400.0, size_arcmin=60.0)
    later = _second_night(conn)
    inside = [world.frame(obj=veil), world.frame(obj=dark, night=later)]
    _timed(conn, inside[0], "2026-10-12T19:00:00", 300.0)
    _timed(conn, inside[1], "2026-10-20T19:00:00", 600.0)
    mosaico(conn, inside)
    conn.commit()
    lit = _get(db_path, CHIAVE, panel=_panel_of(db_path, "NGC 6992")).json()
    assert [n["night"]["id"] for n in lit["nights"]] == [world.night]
    assert (lit["row"]["frames"], lit["row"]["integration_s"]) == (1, 300.0)
    assert (lit["facts"]["key"], lit["facts"]["common_name"]) == (CHIAVE, "Veil")
    unlit = _get(db_path, CHIAVE, panel=_panel_of(db_path, "LDN 1516")).json()
    assert [n["night"]["id"] for n in unlit["nights"]] == [later]
    assert (unlit["sites"], unlit["facts"]["common_name"]) == (["Cima Ekar"], None)


def test_a_panel_that_is_not_a_number_is_a_422(db_path) -> None:
    assert _get(db_path, CHIAVE, panel="uno").status_code == 422


@pytest.mark.parametrize("path", ["", "/measures"])
def test_a_panel_and_a_production_together_are_a_422(db_path, path) -> None:
    """A panel's tab is of all productions: its measures are written only so."""
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        answer = client.get(
            f"/api/v1/objects/{CHIAVE}{path}", params={"panel": 1, "production": "1:2"}
        )
    assert (answer.status_code, answer.json()["detail"]) == (422, "panel_with_production")


def test_an_object_outside_the_catalog_has_no_facts(conn, db_path, world) -> None:
    world.frame(obj=world.object("Cometa"))
    conn.commit()
    facts = _get(db_path, "Cometa").json()["facts"]
    assert facts["type_code"] is None
    assert (facts["distance_pc"], facts["moon"]) == (None, None)
