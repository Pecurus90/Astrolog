"""A frame's measures from the API: every measure of the catalogue, its value or why it has none,
read as the stages wrote them (docs/domini/misure.md)."""

import re

import pytest
from fastapi.testclient import TestClient

from astrolog import measure_read
from astrolog.api.app import create_app
from astrolog.api.models_measures import Level, MeasureOutcome, SamplingClassOut, SqmOutcome
from astrolog.db.connect import SCHEMA_PATH
from astrolog.measure_list import MEASURES, NOT_MEASURES, Table
from astrolog.pipeline.measure import measure_root
from astrolog.pipeline.sky_measure import sky_root
from conftest import LATER
from test_pipeline_measure import _light, _scanned
from test_pipeline_sky_measure import _CARDS, _measured, _solve
from test_pipeline_stars import _field


def _columns(table: str) -> set[str]:
    body = SCHEMA_PATH.read_text(encoding="utf-8").split(f"CREATE TABLE {table} (")[1]
    body = body.split(") STRICT;")[0]
    return {m.group(1) for m in re.finditer(r"^  ([a-z_0-9]+) ", body, re.MULTILINE)} - {"CHECK"}


def _get(db_path, frame_id: int) -> dict:
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        answer = client.get(f"/api/v1/pipeline/frames/{frame_id}/measures")
    assert answer.status_code == 200, answer.text
    return answer.json()


def _by_key(body: dict) -> dict[str, dict]:
    return {m["key"]: m for m in body["measures"]}


def _frame(conn) -> int:
    return conn.execute("SELECT id FROM pipeline_frames").fetchone()[0]


@pytest.mark.parametrize("table", list(Table))
def test_every_column_is_a_measure_of_the_catalogue_or_named_as_none(table: Table) -> None:
    listed = {e.key for e in MEASURES if e.table is table}
    assert listed | NOT_MEASURES[table] == _columns(table)
    assert not listed & NOT_MEASURES[table]


def test_the_catalogue_names_each_measure_once() -> None:
    keys = [e.key for e in MEASURES]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize(
    ("words", "column"),
    [(MeasureOutcome, "outcome"), (Level, "tilt_level"), (SamplingClassOut, "sampling_class")],
)
def test_the_models_words_are_the_schemas(words, column) -> None:
    body = SCHEMA_PATH.read_text(encoding="utf-8").split("CREATE TABLE pipeline_measures (")[1]
    found = re.search(rf"^  {column} .*?IN \(([^)]*)\)", body, re.MULTILINE | re.DOTALL)
    assert found is not None
    assert set(words.__args__) == set(re.findall(r"'([a-z_]+)'", found.group(1)))


def test_the_sqm_outcomes_are_the_schemas() -> None:
    body = SCHEMA_PATH.read_text(encoding="utf-8").split("CREATE TABLE pipeline_sqm (")[1]
    found = re.search(r"outcome .*?IN \(([^)]*)\)", body, re.DOTALL)
    assert found is not None
    assert set(SqmOutcome.__args__) == set(re.findall(r"'([a-z_]+)'", found.group(1)))


def test_no_such_frame_is_a_404(db_path) -> None:
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        answer = client.get("/api/v1/pipeline/frames/99/measures")
    assert (answer.status_code, answer.json()["detail"]) == (404, "frame_not_found")


def test_a_frame_not_measured_yet_says_so_for_every_measure(conn, db_path, tmp_path) -> None:
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 2.5), *_CARDS)
    _scanned(conn, tmp_path / "nas")
    body = _get(db_path, _frame(conn))
    assert (body["measure_outcome"], body["solved"], body["tilt_level"]) == (None, None, None)
    assert len(body["measures"]) == len(MEASURES)
    assert {(m["value"], m["silent"]) for m in body["measures"]} == {(None, "not_measured_yet")}


def test_a_measured_frame_without_its_solution(conn, db_path, tmp_path) -> None:
    root = _measured(conn, tmp_path, *_CARDS)
    sky_root(conn, root, LATER)
    body = _get(db_path, _frame(conn))
    found = _by_key(body)
    assert (body["measure_outcome"], body["solved"]) == ("measured", False)
    assert (body["tilt_level"], body["sampling_class"], body["shape"]) == ("go", "over", "fitted")
    assert found["hfd_px"]["value"] > 0 and found["hfd_px"]["silent"] is None
    assert (found["hfd_px"]["unit"], found["hfd_px"]["group"]) == ("px", "stars_shape")
    assert found["hfd_tilt_pct"]["value"] < 5 and found["hfd_tilt_pct"]["unit"] == "pct"
    assert found["hfd_arcsec"] == {**found["hfd_arcsec"], "value": None, "silent": "not_solved"}
    assert found["altitude_deg"]["value"] > 60  # from the card's pointing
    assert found["sqm"]["silent"] == "not_solved"


def test_a_solved_frame_has_its_arcseconds_and_says_why_no_sqm(conn, db_path, tmp_path) -> None:
    """A mono frame without a filter written: sky brightness is not for it (ADR 0022)."""
    root = _measured(conn, tmp_path, *_CARDS)
    _solve(conn)
    sky_root(conn, root, LATER)
    found = _by_key(_get(db_path, _frame(conn)))
    assert found["hfd_arcsec"]["value"] > 0
    assert found["off_axis_arcsec"]["silent"] is None
    assert found["moon_illumination"]["value"] is not None
    assert (found["sqm"]["value"], found["sqm"]["silent"]) == (None, "sqm_not_this_filter")


def test_a_frame_with_too_few_stars_keeps_what_it_has(conn, db_path, tmp_path) -> None:
    _light(tmp_path / "nas" / "a.fits", _field(count=2))
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    body = _get(db_path, _frame(conn))
    found = _by_key(body)
    assert body["measure_outcome"] == "too_few_stars"
    assert found["stars"] == {**found["stars"], "value": 2.0, "silent": None}
    assert found["hfd_px"]["silent"] == "too_few_stars"
    assert found["hfd_tilt_pct"]["silent"] == "too_few_stars"
    assert found["altitude_deg"]["silent"] == "sky_pending"


def test_a_frame_with_no_pixels_read_keeps_its_sky_from_the_cards(conn, db_path, tmp_path) -> None:
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 2.0), "BAYERPAT= 'CYGM'", *_CARDS)
    root = _scanned(conn, tmp_path / "nas")
    measure_root(conn, root, LATER)
    sky_root(conn, root, LATER)
    body = _get(db_path, _frame(conn))
    found = _by_key(body)
    assert body["measure_outcome"] == "not_supported"
    assert found["altitude_deg"]["value"] > 60 and found["altitude_deg"]["silent"] is None
    assert found["hfd_px"]["silent"] == "not_supported"
    assert found["hfd_arcsec"]["silent"] == "not_supported"
    assert found["sqm"]["silent"] == "not_supported"


_PX_NULL = {"outcome": "measured", "hfd_px": 2.0, "fwhm_px": None, "off_axis_px": None}


@pytest.mark.parametrize(
    ("measure", "key", "silent"),
    [
        ({**_PX_NULL, "outcome": "too_few_stars", "hfd_px": None}, "hfd_arcsec", "too_few_stars"),
        ({**_PX_NULL, "outcome": "too_few_stars"}, "fwhm_zenith_arcsec", "too_few_stars"),
        (_PX_NULL, "fwhm_zenith_arcsec", "under_5_stars"),
        (_PX_NULL, "off_axis_arcsec", "centre_or_ring_empty"),
        ({**_PX_NULL, "fwhm_px": 2.5}, "fwhm_zenith_arcsec", "no_site_time_or_centre"),
    ],
)
def test_a_sky_value_silent_from_its_pixels_says_the_pixels_reason(measure, key, silent) -> None:
    """A solved frame high in the sky: the arcseconds are NULL because the pixels are."""
    sky = {"solved": 1, "altitude_deg": 50.0, "airmass": 1.3}
    entry = next(e for e in MEASURES if e.key == key)
    if silent == "no_site_time_or_centre":
        sky = {**sky, "altitude_deg": None, "airmass": None}
    assert measure_read._why(entry, sky, measure) == silent


def test_below_the_horizon_only_under_it() -> None:
    entry = next(e for e in MEASURES if e.key == "hfd_zenith_arcsec")
    sky = {"solved": 1, "altitude_deg": -3.0, "airmass": None}
    assert measure_read._why(entry, sky, _PX_NULL) == "below_horizon"
