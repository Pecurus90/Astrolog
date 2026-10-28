"""Stadio sqm: la luminosita' del cielo di una posa risolta, col catalogo accanto ad ASTAP e il
bias della camera a quell'offset (ADR 0022 punto 8, ADR 0021)."""

import pytest

from astrolog.pipeline.filters import Band, answer
from astrolog.pipeline.measure import measure_root
from astrolog.pipeline.sky_measure import sky_root
from astrolog.pipeline.solve import forget
from astrolog.pipeline.sqm import sky_brightness
from astrolog.pipeline.sqm_measure import declare_bias, sqm_root
from conftest import LATER
from test_pipeline_measure import _light, _scanned
from test_pipeline_sqm import WCS, ZERO_POINT, sky_field

# RA 100, Dec 20 dal sito della scheda a meta' gennaio, verso mezzanotte: alto
_CARDS = (
    "DATE-OBS= '2025-01-15T23:00:00.000'", "EXPTIME =                120.0",
    "SITELAT =               45.494", "SITELONG=              11.5218",
    "INSTRUME= 'ZWO ASI2600MM Pro'", "OFFSET  =                   50",
)  # fmt: skip


def _shot(conn, tmp_path, *cards: str, sky: bool = True) -> int:
    catalogue = tmp_path / "astap"
    catalogue.mkdir(exist_ok=True)
    _light(tmp_path / "nas" / "a.fits", sky_field(catalogue), *cards)
    root = _scanned(conn, tmp_path / "nas")
    measure_root(conn, root, LATER)
    (frame_id,) = conn.execute("SELECT frame_id FROM pipeline_measures").fetchone()
    conn.execute(
        "INSERT INTO pipeline_solutions (frame_id, outcome, ra_deg, dec_deg, scale_arcsec_px,"
        " cd1_1, cd1_2, cd2_1, cd2_2, crpix1, crpix2, tried_at)"
        " VALUES (?, 'solved', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (frame_id, WCS.ra_deg, WCS.dec_deg, WCS.scale_arcsec, *WCS.cd, *WCS.crpix, LATER),
    )
    if sky:
        sky_root(conn, root, LATER)
    return root


def _row(conn) -> dict | None:
    row = conn.execute("SELECT * FROM pipeline_sqm").fetchone()
    return None if row is None else dict(row)


def _airmass(conn) -> float:
    return conn.execute("SELECT airmass FROM pipeline_sky").fetchone()[0]


def test_a_mono_l_shot_gets_its_sky_brightness_without_bias(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 1
    row = _row(conn)
    assert row is not None
    assert (row["outcome"], row["catalogue"], row["colour"]) == ("measured", "d80", 0)
    assert row["zero_point_mag"] == pytest.approx(ZERO_POINT, abs=0.01)
    assert row["sky_adu"] == pytest.approx(1000, abs=2)
    assert row["bias_adu"] is None
    expected = sky_brightness(row["zero_point_mag"], row["sky_adu"], 0.0, 2.0, _airmass(conn))
    assert row["sqm"] == pytest.approx(expected)
    assert row["computed_at"] == LATER


def test_a_bias_declared_before_is_taken_off(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    declare_bias(conn, "ZWO ASI2600MM Pro", 50, 500.0)
    sqm_root(conn, root, LATER, tmp_path / "astap")
    row = _row(conn)
    assert row is not None and row["bias_adu"] == 500.0
    expected = sky_brightness(row["zero_point_mag"], row["sky_adu"], 500.0, 2.0, _airmass(conn))
    assert row["sqm"] == pytest.approx(expected)


def test_a_bias_declared_after_rewrites_the_shots_of_that_camera_and_offset(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    before = _row(conn)
    declare_bias(conn, "ZWO ASI2600MM Pro", 30, 500.0)  # altro offset: niente
    assert _row(conn) == before
    declare_bias(conn, "ZWO ASI2600MM Pro", 50, 500.0)
    after = _row(conn)
    assert after is not None and before is not None
    assert after["bias_adu"] == 500.0 and after["sqm"] > before["sqm"]


def test_a_bias_over_the_sky_leaves_no_brightness(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    declare_bias(conn, "ZWO ASI2600MM Pro", 50, 5000.0)
    sqm_root(conn, root, LATER, tmp_path / "astap")
    row = _row(conn)
    assert row is not None and row["outcome"] == "measured" and row["sqm"] is None


def test_a_colour_shot_needs_the_bias(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "BAYERPAT= 'RGGB'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    row = _row(conn)
    assert row is not None
    assert (row["outcome"], row["colour"], row["sqm"]) == ("measured", 1, None)
    declare_bias(conn, "ZWO ASI2600MM Pro", 50, 100.0)
    row = _row(conn)
    assert row is not None and row["sqm"] is not None


@pytest.mark.parametrize("filter_card", ["FILTER  = 'R'", "FILTER  = 'Ha'", None])
def test_a_mono_shot_counts_only_with_the_l_filter(conn, tmp_path, filter_card):
    """ADR 0022 punto 8: mono solo col filtro L; senza filtro scritto non si sa cosa c'era."""
    cards = _CARDS if filter_card is None else (*_CARDS, filter_card)
    root = _shot(conn, tmp_path, *cards)
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 0
    assert _row(conn) is None


def test_a_colour_shot_behind_a_narrow_filter_does_not_count(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "BAYERPAT= 'RGGB'", "FILTER  = 'Ha'")
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 0


def test_your_own_l_filter_counts(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'Lum Astronomik'")
    answer(conn, "Lum Astronomik", "Astronomik L-3", {Band.L: None})
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 1


def test_without_a_catalogue_shots_wait(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    assert sqm_root(conn, root, LATER, None).written == 0
    assert sqm_root(conn, root, LATER, tmp_path / "empty").written == 0
    assert _row(conn) is None
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 1


def test_a_shot_without_altitude_is_said_without_reading_it(conn, tmp_path):
    root = _shot(conn, tmp_path, "FILTER  = 'L'", "INSTRUME= 'ZWO ASI2600MM Pro'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    row = _row(conn)
    assert row is not None
    assert (row["outcome"], row["zero_point_mag"], row["file_id"]) == ("no_altitude", None, None)


def test_a_shot_waits_for_its_sky_row(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'", sky=False)
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 0


def test_a_forgotten_solution_takes_the_sky_brightness_with_it(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    (frame_id,) = conn.execute("SELECT frame_id FROM pipeline_sqm").fetchone()
    forget(conn, frame_id)
    assert _row(conn) is None


def test_a_shot_is_measured_once(conn, tmp_path):
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    sqm_root(conn, root, LATER, tmp_path / "astap")
    assert sqm_root(conn, root, LATER, tmp_path / "astap").written == 0


def test_a_bias_is_one_per_camera_and_offset(conn):
    declare_bias(conn, "ZWO ASI2600MM Pro", None, 500.0)
    declare_bias(conn, "ZWO ASI2600MM Pro", None, 510.0)
    rows = conn.execute("SELECT offset, bias_adu FROM pipeline_camera_bias").fetchall()
    assert [tuple(r) for r in rows] == [(None, 510.0)]
