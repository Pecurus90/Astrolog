"""The measures of an Archive row, written with the night's (docs/domini/misure.md): an object
outside mosaics or a mosaic, per production or all of them, per night and filter."""

import pytest

from astrolog import night_measures
from conftest import LATER
from test_night_measures import KEY, _World


@pytest.fixture
def world(conn, tmp_path):
    return _World(conn, tmp_path / "Acquisizioni")


def _instrument(conn, kind: str, name: str | None) -> int | None:
    if name is None:
        return None
    conn.execute(
        "INSERT OR IGNORE INTO instruments (kind, name, created_at) VALUES (?, ?, ?)",
        (kind, name, LATER),
    )
    return conn.execute(
        "SELECT id FROM instruments WHERE kind = ? AND name = ?", (kind, name)
    ).fetchone()[0]


def _rig(conn, optics: str | None, camera: str | None) -> int:
    ids = [_instrument(conn, "optics", optics), _instrument(conn, "camera", camera)]
    return conn.execute(
        "INSERT INTO rigs (optics_id, camera_id, created_at) VALUES (?, ?, ?)", (*ids, LATER)
    ).lastrowid


def _shot(conn, world, hfd, *, rig=None, mosaic=None, **frame) -> int:
    spine = world.shot(hfd, **frame)
    conn.execute("UPDATE frames SET rig_id = ?, mosaic_key = ? WHERE id = ?", (rig, mosaic, spine))
    return spine


def _pieces(conn, rig: int) -> tuple[int | None, int | None]:
    row = conn.execute("SELECT optics_id, camera_id FROM rigs WHERE id = ?", (rig,)).fetchone()
    return row["optics_id"], row["camera_id"]


def _row(conn, *, obj=None, mosaic=None, production=None, night=None, flt=None, key=KEY):
    every = int(production is None)
    optics, camera = production if production is not None else (None, None)
    return conn.execute(
        "SELECT * FROM object_measures WHERE object_id IS ? AND mosaic_key IS ?"
        " AND every_production = ? AND optics_id IS ? AND camera_id IS ? AND night_id IS ?"
        " AND filter_id IS ? AND unfiltered = 0 AND key = ?",
        (obj, mosaic, every, optics, camera, night, flt, key),
    ).fetchone()


def test_an_object_per_night_and_over_all_its_nights(conn, world) -> None:
    m31 = world.object()
    other = world._night(1, "2026-10-13")
    for hfd in (1.0, 2.0, 3.0):
        _shot(conn, world, hfd, obj=m31)
    _shot(conn, world, 9.0, obj=m31, night=other)
    night_measures.rebuild(conn)
    first = _row(conn, obj=m31, night=world.night)
    assert (first["frames"], first["median"]) == (3, 2.0)
    assert _row(conn, obj=m31, night=other)["median"] == 9.0
    whole = _row(conn, obj=m31)
    assert (whole["frames"], whole["median"]) == (4, 2.5)


def test_frames_in_a_mosaic_belong_to_the_mosaic_not_to_the_object(conn, world) -> None:
    """As the Archive counts them: the object's row keeps the frames outside mosaics."""
    m31 = world.object()
    _shot(conn, world, 2.0, obj=m31)
    _shot(conn, world, 6.0, obj=m31, mosaic="m31-mosaico")
    _shot(conn, world, 8.0, obj=m31, mosaic="m31-mosaico")
    night_measures.rebuild(conn)
    assert _row(conn, obj=m31)["frames"] == 1
    mosaic = _row(conn, mosaic="m31-mosaico")
    assert (mosaic["frames"], mosaic["median"]) == (2, 7.0)


def test_each_production_alone_and_all_of_them(conn, world) -> None:
    """Never across setups when one is asked: the row's whole only when the window asks it."""
    m31 = world.object()
    small, big = _rig(conn, "Askar FRA400", "ASI2600MM"), _rig(conn, "RC8", "ASI2600MM")
    _shot(conn, world, 2.0, obj=m31, rig=small)
    _shot(conn, world, 4.0, obj=m31, rig=small)
    _shot(conn, world, 10.0, obj=m31, rig=big)
    night_measures.rebuild(conn)
    assert _row(conn, obj=m31, production=_pieces(conn, small))["median"] == 3.0
    assert _row(conn, obj=m31, production=_pieces(conn, big))["median"] == 10.0
    assert _row(conn, obj=m31)["median"] == 4.0


def test_a_frame_without_a_rig_is_a_production_of_null_pieces(conn, world) -> None:
    m31 = world.object()
    _shot(conn, world, 5.0, obj=m31)
    half = _rig(conn, None, "ASI2600MM")
    _shot(conn, world, 7.0, obj=m31, rig=half)
    night_measures.rebuild(conn)
    assert _row(conn, obj=m31, production=(None, None))["median"] == 5.0
    assert _row(conn, obj=m31, production=_pieces(conn, half))["median"] == 7.0


def test_per_filter_and_the_set_of_frames_naming_none(conn, world) -> None:
    m31 = world.object()
    lum = world.filter("L")
    _shot(conn, world, 2.0, obj=m31, flt=lum)
    _shot(conn, world, 6.0, obj=m31)
    night_measures.rebuild(conn)
    assert _row(conn, obj=m31, flt=lum)["median"] == 2.0
    none = conn.execute(
        "SELECT frames, pending FROM object_measure_groups WHERE object_id = ? AND unfiltered = 1"
        " AND night_id = ? AND every_production = 1",
        (m31, world.night),
    ).fetchone()
    assert (none["frames"], none["pending"]) == (1, 0)


def test_a_frame_with_no_object_is_in_no_row(conn, world) -> None:
    _shot(conn, world, 3.0)
    night_measures.rebuild(conn)
    assert conn.execute("SELECT COUNT(*) FROM object_measures").fetchone()[0] == 0
