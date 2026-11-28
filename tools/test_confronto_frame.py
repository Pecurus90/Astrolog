"""The step 40.4 bench: what it calls a difference between the frames of two scans."""

import json

import confronto_frame as cf


def _frame(file: str, **cols: object) -> dict[str, object]:
    return {"id": 1, "image_type": "light", "exposure_s": 300.0, "header": {}, "file": file, **cols}


def test_a_frame_on_one_side_is_named_with_its_file_and_kind():
    a = {"h1": _frame("M97/a.fits"), "h2": _frame("Dark/d.fits", image_type="dark")}
    b = {"h1": _frame("M97/a.fits")}
    lines = cf.report(a, b)
    assert lines[:3] == [
        "frames: 2 in A, 1 in B, 1 in both",
        "only in A: 1 {'dark': 1}",
        "  Dark/d.fits (dark)",
    ]
    assert "only in B: 0 {}" in lines


def test_a_column_that_differs_is_counted_and_ids_are_not_a_difference():
    a = {"h1": _frame("a.fits", id=1, gain=100.0), "h2": _frame("b.fits", id=2, gain=100.0)}
    b = {"h1": _frame("a.fits", id=7, gain=101.0), "h2": _frame("b.fits", id=8, gain=100.0)}
    lines = cf.report(a, b)
    assert "gain: 1 differ" in lines
    assert "  a.fits: 100.0 -> 101.0" in lines
    assert not any(line.startswith("id:") for line in lines)


def test_a_column_on_one_side_only_is_listed_once():
    a = {"h1": _frame("a.fits", site_elev_m=133.0)}
    b = {"h1": _frame("a.fits")}
    assert "columns only in A: ['site_elev_m']" in cf.report(a, b)


def test_a_reference_reads_as_the_name_it_points_at():
    names = {"instruments": {6: "mount EQ6"}, "filters": {2: "Ha"}, "rigs": {}}
    row = {"mount_id": 6, "filter_id": 2, "rig_id": None, "night_id": 9}
    cf._named(row, names)
    assert row == {"mount_id": "mount EQ6", "filter_id": "Ha", "rig_id": None, "night_id": 9}


def test_notes_leave_the_header_and_pairs_read_as_a_dict():
    pairs = [["GAIN", 100], ["HISTORY", "calibrated"], ["COMMENT", "x"]]
    assert cf._header(json.dumps(pairs)) == {"GAIN": 100}
    assert cf._header(json.dumps({"GAIN": 100, "HISTORY": "y"})) == {"GAIN": 100}
