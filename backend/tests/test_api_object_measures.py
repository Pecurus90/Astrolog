"""An object's measures from the API: what `night_measures` wrote for its Archive row, its nights
as the groups (handoff/design/pagine/componenti/Riepilogo.dc.html 58, MisureFrame tipo oggetto)."""

import pytest
from fastapi.testclient import TestClient

from astrolog import night_measures
from astrolog.api.app import create_app
from astrolog.measure_list import MEASURES
from test_api_object_detail import _second_night
from test_night_measures import _World
from test_object_measures import _rig

T1 = "2026-10-12T21:00:00.000000+00:00"
T2 = "2026-10-20T20:00:00.000000+00:00"


@pytest.fixture
def world(conn, tmp_path):
    return _World(conn, tmp_path / "Acquisizioni")


def _get(db_path, key: str, **params):
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        return client.get(f"/api/v1/objects/{key}/measures", params=params)


def _on(conn, frame: int, rig: int | None) -> None:
    conn.execute("UPDATE frames SET rig_id = ? WHERE id = ?", (rig, frame))


def test_no_such_object_is_a_404(db_path) -> None:
    answer = _get(db_path, "M 999")
    assert (answer.status_code, answer.json()["detail"]) == (404, "object_not_found")


def test_its_nights_are_the_groups_in_shooting_order(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    lum = world.filter("L")
    later = _second_night(conn)
    late = world.shot(6.0, start=T2, obj=veil, flt=lum, night=later)
    early = world.shot(2.0, start=T1, obj=veil, flt=lum)
    world.shot(9.0, start=T1, obj=world.object("M 31"), flt=lum)  # another object, same night
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, "NGC 6992").json()
    assert (body["key"], body["frames"], body["pending"], body["one_production"]) == (
        "NGC 6992", 2, 0, True,
    )  # fmt: skip
    assert body["groups"] == [
        {"key": str(world.night), "name": None, "night_date": "2026-10-12", "frames": 1,
         "pending": 0},
        {"key": str(later), "name": None, "night_date": "2026-10-20", "frames": 1, "pending": 0},
    ]  # fmt: skip
    assert body["filters"] == [{"name": "L", "passband": "L", "frames": 2}]
    whole = next(s for s in body["sets"] if s["group"] is None and s["filter"] is None)
    assert [m["key"] for m in whole["measures"]] == [e.key for e in MEASURES]
    hfd = next(m for m in whole["measures"] if m["key"] == "hfd_px")
    assert (hfd["measured"], hfd["median"]) == (2, 4.0)
    both = {(s["group"], s["filter"]) for s in body["sets"]}
    assert both == {
        (None, None), (None, "L"), (str(world.night), None), (str(world.night), "L"),
        (str(later), None), (str(later), "L"),
    }  # fmt: skip
    series = body["series"]
    assert [(f["frame_id"], f["group"]) for f in series] == [
        (early, str(world.night)), (late, str(later)),
    ]  # fmt: skip
    # each in its own site's zone: 21:00 UTC is 23:00 in Rome in October
    assert series[0]["start"] == "2026-10-12T23:00:00+02:00"


def test_two_productions_alone_and_together(conn, db_path, world) -> None:
    """Together the SNR does not compare (ADR 0022): the answer says so, the window hides it."""
    veil = world.object("NGC 6992")
    small, big = _rig(conn, "Askar FRA400", "ASI2600MM"), _rig(conn, "RC8", "ASI294MC")
    _on(conn, world.shot(2.0, obj=veil), small)
    _on(conn, world.shot(10.0, obj=veil), big)
    night_measures.rebuild(conn)
    conn.commit()
    together = _get(db_path, "NGC 6992").json()
    assert (together["frames"], together["one_production"]) == (2, False)
    optics, camera = conn.execute(
        "SELECT optics_id, camera_id FROM rigs WHERE id = ?", (big,)
    ).fetchone()
    alone = _get(db_path, "NGC 6992", production=f"{optics}:{camera}").json()
    assert (alone["frames"], alone["one_production"]) == (1, True)
    hfd = next(
        m
        for s in alone["sets"]
        if s["group"] is None and s["filter"] is None
        for m in s["measures"]
        if m["key"] == "hfd_px"
    )
    assert hfd["median"] == 10.0
    assert len(alone["series"]) == 1


def test_before_the_measures_are_written_every_frame_waits(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    world.frame(obj=veil)
    conn.commit()
    body = _get(db_path, "NGC 6992").json()
    assert (body["frames"], body["pending"], body["sets"]) == (1, 1, [])


def test_a_mosaic_has_its_own_measures(conn, db_path, world) -> None:
    veil = world.object("NGC 6992")
    world.shot(2.0, obj=veil)
    panel = world.shot(8.0, obj=veil)
    conn.execute("UPDATE frames SET mosaic_key = 'velo-mosaico' WHERE id = ?", (panel,))
    night_measures.rebuild(conn)
    conn.commit()
    assert _get(db_path, "NGC 6992").json()["frames"] == 1
    assert _get(db_path, "velo-mosaico").json()["frames"] == 1
