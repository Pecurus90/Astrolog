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
    assert body["groups"] == [
        {"key": "M 31", "name": "M 31", "night_date": None, "frames": 3, "pending": 1}
    ]
    assert body["filters"] == [{"name": "L", "passband": "L", "frames": 3}]
    whole = next(s for s in body["sets"] if s["group"] is None and s["filter"] is None)
    assert (whole["frames"], whole["pending"], whole["differs"]) == (3, 1, [])
    assert whole["differs_values"] == {}
    assert [m["key"] for m in whole["measures"]] == [e.key for e in MEASURES]
    hfd = next(m for m in whole["measures"] if m["key"] == "hfd_px")
    assert (hfd["measured"], hfd["median"], hfd["q1"], hfd["q3"], hfd["silent"]) == (
        2, 3.0, 2.5, 3.5, None,
    )  # fmt: skip
    assert (hfd["unit"], hfd["per_filter"]) == ("px", False)
    both = {(s["group"], s["filter"]) for s in body["sets"]}
    assert both == {(None, None), ("M 31", None), (None, "L"), ("M 31", "L")}
    # in shooting order, the frame without measures last with its state
    assert [f["frame_id"] for f in body["series"]] == [early, late, waiting]
    first = body["series"][0]
    # in the site's zone: 21:00 UTC is 23:00 in Rome in October
    assert (first["start"], first["state"]) == ("2026-10-12T23:00:00+02:00", "measured")
    assert (first["values"]["hfd_px"], first["tilt_level"], first["sampling"]) == (2.0, None, None)
    assert (first["group"], first["filter"]) == ("M 31", "L")
    assert body["series"][2]["state"] == "pending"


def test_frames_naming_no_filter_have_their_own_key(conn, db_path, world) -> None:
    """The Nights' `__no_filter__`, last among the filters, in the sets and on each frame."""
    m31 = world.object("M 31")
    lum = world.filter("L")
    world.shot(2.0, start=T1, obj=m31, flt=lum)
    world.shot(4.0, start=T2, obj=m31)
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert body["filters"] == [
        {"name": "L", "passband": "L", "frames": 1},
        {"name": "__no_filter__", "passband": "UNKNOWN", "frames": 1},
    ]
    both = {(s["group"], s["filter"]) for s in body["sets"]}
    assert both == {
        (None, None), ("M 31", None), (None, "L"), ("M 31", "L"),
        (None, "__no_filter__"), ("M 31", "__no_filter__"),
    }  # fmt: skip
    sets = {(s["group"], s["filter"]): s for s in body["sets"]}
    none = sets[None, "__no_filter__"]
    hfd = next(m for m in none["measures"] if m["key"] == "hfd_px")
    assert (none["frames"], hfd["median"]) == (1, 4.0)
    assert [f["filter"] for f in body["series"]] == ["L", "__no_filter__"]


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


def test_a_frame_never_measured_is_counted_and_not_shown(conn, db_path, world) -> None:
    """A program not read, a rewritten or broken file: in "of N frames", not in the series and
    without a word (Marco, 8/11: the README says which programs are read)."""
    world.shot(2.0, start=T1)
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.skipped(rel, "not_supported")
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert (body["frames"], body["pending"], len(body["series"])) == (2, 0, 1)
    assert body["series"][0]["state"] == "measured"


def test_a_file_unreadable_now_waits_like_one_not_measured_yet(conn, db_path, world) -> None:
    spine = world.frame()
    rel = conn.execute("SELECT rel_path FROM positions WHERE frame_id = ?", (spine,)).fetchone()[0]
    world.file(rel)
    conn.execute(
        "INSERT INTO pipeline_measures (frame_id, file_id, outcome, measured_at)"
        " SELECT frame_id, id, 'unreadable', ? FROM pipeline_files WHERE rel_path = ?",
        ("2026-10-13T10:00:00+00:00", rel),
    )
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert (body["series"][0]["state"], body["pending"]) == ("pending", 1)
    assert {m["silent"] for m in body["sets"][0]["measures"]} == {"measuring"}


def test_a_measure_carries_its_trend(conn, db_path, world) -> None:
    for hour, hfd in ((20, 1.0), (21, 2.0), (22, 3.0), (23, 4.0)):
        world.shot(hfd, start=f"2026-10-12T{hour}:00:00.000000+00:00")
    night_measures.rebuild(conn)
    conn.commit()
    whole = _get(db_path, world.night).json()["sets"][0]
    hfd = next(m for m in whole["measures"] if m["key"] == "hfd_px")
    assert (len(hfd["trend"]), hfd["trend"][0], hfd["trend"][-1]) == (24, 1.0, 4.0)


def _set_measures(conn, spine: int, **values: float | str) -> None:
    sets = ", ".join(f"{k} = ?" for k in values)
    conn.execute(
        f"UPDATE pipeline_measures SET {sets} WHERE frame_id ="  # noqa: S608 - test keys
        " (SELECT pipeline_frame_id FROM night_measure_frames WHERE frame_id = ?)",
        (*values.values(), spine),
    )


def test_a_measure_carries_its_lowest_and_highest_for_one_scale(conn, db_path, world) -> None:
    """*A confronto* draws every row on the same scale: the set's extremes, not computed on
    screen (MisureFrame:325)."""
    for hfd in (2.0, 5.0, 3.0):
        world.shot(hfd)
    night_measures.rebuild(conn)
    conn.commit()
    whole = _get(db_path, world.night).json()["sets"][0]
    hfd = next(m for m in whole["measures"] if m["key"] == "hfd_px")
    assert (hfd["low"], hfd["high"]) == (2.0, 5.0)
    fwhm = next(m for m in whole["measures"] if m["key"] == "fwhm_px")
    assert (fwhm["low"], fwhm["high"]) == (None, None)


def test_the_median_tilt_and_fwhm_carry_their_verdict(conn, db_path, world) -> None:
    """The same rules the pipeline gives one frame (ASTAP 10/20 %, sampling in px), on the set's
    median; the other measures have none."""
    frames = [world.shot(3.0) for _ in range(3)]
    night_measures.rebuild(conn)
    for spine, tilt, fwhm in zip(frames, (8.0, 15.0, 30.0), (1.2, 2.5, 4.0), strict=True):
        _set_measures(
            conn,
            spine,
            hfd_tilt_pct=tilt,
            tilt_level="go",  # a frame's own: the set's verdict comes from the median alone
            **{f"hfd_corner_{i}_px": 3.0 for i in (1, 2, 3, 4)},
            hfd_centre_px=3.0,
            fwhm_px=fwhm,
            sampling_class="over",
            eccentricity=0.3,
            shape="fitted",
            shape_stars=50,
        )
    night_measures.rebuild(conn)
    conn.commit()
    whole = _get(db_path, world.night).json()["sets"][0]
    verdicts = {m["key"]: m["verdict"] for m in whole["measures"]}
    assert (verdicts["hfd_tilt_pct"], verdicts["fwhm_px"]) == ("marginal", "ideal")
    assert verdicts["hfd_px"] is None


def test_a_frame_says_which_way_its_stars_stretch(conn, db_path, world) -> None:
    spine = world.shot(3.0)
    night_measures.rebuild(conn)
    conn.execute(
        "INSERT INTO pipeline_sky (frame_id, solved, angle_pa_deg, angle_axis, computed_at)"
        " SELECT pipeline_frame_id, 1, 90, 'ra', ? FROM night_measure_frames WHERE frame_id = ?",
        ("2026-10-13T10:00:00+00:00", spine),
    )
    conn.commit()
    assert _get(db_path, world.night).json()["series"][0]["angle_axis"] == "ra"


def test_a_solved_frame_says_where_its_sky_is_brighter(conn, db_path, world) -> None:
    """Tavola MisureFrame 357, «piu' chiaro verso est»: la rotta manda il lato scritto."""
    spine = world.shot(3.0)
    night_measures.rebuild(conn)
    conn.execute(
        "INSERT INTO pipeline_sky (frame_id, solved, gradient_pa_deg, gradient_side, computed_at)"
        " SELECT pipeline_frame_id, 1, 95, 'E', ? FROM night_measure_frames WHERE frame_id = ?",
        ("2026-10-13T10:00:00+00:00", spine),
    )
    conn.commit()
    assert _get(db_path, world.night).json()["series"][0]["gradient_side"] == "E"


def test_the_pier_side_written_in_the_header_reaches_frames_and_sets(conn, db_path, world) -> None:
    """Tavola MisureFrame 248, «a ovest 1 di 2 frame»: il PIERSIDE del file, per frame e contato
    per insieme quando si scrivono le misure; senza lato, il frame non conta."""
    world.shot(2.0, start=T1)
    world.shot(3.0, start=T2)
    world.shot(4.0)
    for side, start in (("west", T1), ("east", T2)):
        conn.execute("UPDATE pipeline_cards SET pier_side = ? WHERE start_utc = ?", (side, start))
    night_measures.rebuild(conn)
    conn.commit()
    body = _get(db_path, world.night).json()
    assert [f["pier_side"] for f in body["series"]] == ["west", "east", None]
    assert body["sets"][0]["pier_side"] == {"east": 1, "west": 1}


def _solved(conn, spine: int, *, colour_without_bias: bool = False) -> None:
    """The frame solved; with `colour_without_bias` its sky brightness measured on the 2x2 blocks
    of a camera whose bias is not declared, so it has no value."""
    pframe = conn.execute(
        "SELECT pipeline_frame_id FROM night_measure_frames WHERE frame_id = ?", (spine,)
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO pipeline_sky (frame_id, solved, computed_at) VALUES (?, 1, ?)", (pframe, T1)
    )
    if colour_without_bias:
        conn.execute(
            "INSERT INTO pipeline_sqm (frame_id, outcome, catalogue, zero_point_mag,"
            " calibration_stars, sky_adu, colour, computed_at)"
            " VALUES (?, 'measured', 'd50', 21.0, 40, 900, 1, ?)",
            (pframe, T1),
        )


def _sqm(body: dict) -> dict:
    return next(m for m in body["sets"][0]["measures"] if m["key"] == "sqm")


def test_sky_brightness_of_a_set_without_l_or_colour_frames_says_so(conn, db_path, world) -> None:
    """Tavola MisureFrame 236: «nessun frame L o a colori in questa notte». Mono frames behind no
    filter written are not for sky brightness (ADR 0022): the set says it, not "no value"."""
    spines = [world.shot(2.0, start=T1), world.shot(3.0, start=T2)]
    night_measures.rebuild(conn)
    for spine in spines:
        _solved(conn, spine)
    night_measures.rebuild(conn)
    conn.commit()
    sqm = _sqm(_get(db_path, world.night).json())
    assert (sqm["median"], sqm["silent"]) == (None, "sqm_not_this_filter")


def test_sky_brightness_of_colour_frames_without_bias_says_it_needs_it(
    conn, db_path, world
) -> None:
    """Tavola MisureFrame 236: «serve il bias della camera», also when other frames of the set are
    not for sky brightness at all."""
    spines = [world.shot(2.0, start=T1), world.shot(3.0, start=T2)]
    night_measures.rebuild(conn)
    _solved(conn, spines[0], colour_without_bias=True)
    _solved(conn, spines[1])
    night_measures.rebuild(conn)
    conn.commit()
    sqm = _sqm(_get(db_path, world.night).json())
    assert (sqm["median"], sqm["silent"]) == (None, "needs_camera_bias")


def test_a_night_not_rebuilt_yet_has_no_sets(conn, db_path, world) -> None:
    """Grouped but the measures not written yet: no sets, not an error."""
    world.frame()
    conn.commit()
    body = _get(db_path, world.night).json()
    assert (body["sets"], body["frames"]) == ([], 1)
