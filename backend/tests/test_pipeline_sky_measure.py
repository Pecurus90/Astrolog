"""Stadio sky: le misure di una posa col cielo, dalla misura dei pixel, la soluzione, il sito e
l'ora della scheda (ADR 0022 punti 5 e 7, docs/domini/misure.md)."""

import datetime as dt
import threading

import pytest

from astrolog.pipeline.airmass import airmass_of, apparent_altitude, at_zenith
from astrolog.pipeline.altitude import true_altitudes
from astrolog.pipeline.footprint import position_angle
from astrolog.pipeline.measure import measure_root
from astrolog.pipeline.sky_measure import mid_exposure, sky_axis, sky_root
from astrolog.pipeline.solve import forget
from conftest import LATER
from test_pipeline_measure import _light, _scanned
from test_pipeline_stars import _field

# M13 dal sito della scheda, poco dopo il transito: alto, massa d'aria vicino a 1
_CARDS = (
    "DATE-OBS= '2025-06-29T21:30:00.000'", "EXPTIME =                300.0",
    "SITELAT =               45.494", "SITELONG=              11.5218",
    "RA      =     241.254763508206", "DEC     =     17.7165957446809",
)  # fmt: skip
_CENTRE = (241.25198643662179, 17.726894038989336)
_SCALE = 1.39
# CD1_1, CD1_2, CD2_1, CD2_2 of tests/astap/solved.ini
_CD = (-2.6277393210341225e-004, 2.7944155214576776e-004,
       -2.7944266362463124e-004, -2.6285912858408056e-004)  # fmt: skip
_MID = dt.datetime(2025, 6, 29, 21, 32, 30, tzinfo=dt.UTC)


def _measured(conn, tmp_path, *cards: str) -> int:
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 2.5), *cards)
    root = _scanned(conn, tmp_path / "nas")
    measure_root(conn, root, LATER)
    return root


def _solve(conn, cd=_CD) -> None:
    (frame_id,) = conn.execute("SELECT frame_id FROM pipeline_measures").fetchone()
    conn.execute(
        "INSERT INTO pipeline_solutions (frame_id, outcome, ra_deg, dec_deg, scale_arcsec_px,"
        " cd1_1, cd1_2, cd2_1, cd2_2, tried_at) VALUES (?, 'solved', ?, ?, ?, ?, ?, ?, ?, ?)",
        (frame_id, *_CENTRE, _SCALE, *cd, LATER),
    )


def _sky(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM pipeline_sky ORDER BY frame_id")]


def _altitude(centre) -> float:
    [true] = true_altitudes([centre], [_MID], [(45.494, 11.5218)])
    return apparent_altitude(true)


def test_a_solved_shot_gets_its_airmass_arcseconds_and_zenith_values(conn, tmp_path):
    root = _measured(conn, tmp_path, *_CARDS)
    _solve(conn)
    assert sky_root(conn, root, LATER).written == 1
    [row] = _sky(conn)
    [hfd, fwhm] = conn.execute("SELECT hfd_px, fwhm_px FROM pipeline_measures").fetchone()
    assert row["solved"] == 1 and row["computed_at"] == LATER
    assert row["mid_utc"] == "2025-06-29T21:32:30.000000+00:00"
    assert row["altitude_deg"] == pytest.approx(_altitude(_CENTRE))
    assert 60 < row["altitude_deg"] < 75
    assert row["airmass"] == pytest.approx(airmass_of(row["altitude_deg"]))
    assert row["hfd_arcsec"] == pytest.approx(hfd * _SCALE)
    assert row["fwhm_arcsec"] == pytest.approx(fwhm * _SCALE)
    assert row["hfd_zenith_arcsec"] == pytest.approx(at_zenith(hfd * _SCALE, row["airmass"]))
    assert row["fwhm_zenith_arcsec"] < row["fwhm_arcsec"]


def test_round_stars_and_a_flat_sky_have_no_direction(conn, tmp_path):
    root = _measured(conn, tmp_path, *_CARDS)
    _solve(conn)
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert (row["angle_pa_deg"], row["angle_axis"], row["gradient_pa_deg"]) == (None, None, None)


def test_the_shape_and_the_bright_side_turn_with_the_sky(conn, tmp_path):
    """Gli angoli dei pixel, girati dalla CD della soluzione (formule: test_pipeline_footprint)."""
    root = _measured(conn, tmp_path, *_CARDS)
    conn.execute("UPDATE pipeline_measures SET eccentricity = 0.6, angle_deg = 10.0,"
                 " gradient_pct = 5.0, gradient_angle_deg = 200.0")  # fmt: skip
    _solve(conn)
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert row["angle_pa_deg"] == pytest.approx(position_angle(_CD, 10.0) % 180)
    assert row["angle_axis"] == sky_axis(row["angle_pa_deg"])
    assert row["gradient_pa_deg"] == pytest.approx(position_angle(_CD, 200.0))


def test_without_a_site_there_is_no_altitude_but_the_arcseconds_stay(conn, tmp_path):
    root = _measured(conn, tmp_path, *(c for c in _CARDS if not c.startswith("SITE")))
    _solve(conn)
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert (row["altitude_deg"], row["airmass"], row["hfd_zenith_arcsec"]) == (None, None, None)
    assert row["hfd_arcsec"] is not None


def test_without_a_start_there_is_no_time_nor_altitude(conn, tmp_path):
    root = _measured(conn, tmp_path, *(c for c in _CARDS if not c.startswith("DATE-OBS")))
    _solve(conn)
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert (row["mid_utc"], row["altitude_deg"]) == (None, None)


def test_an_unsolved_shot_takes_its_altitude_from_the_card_then_its_solution(conn, tmp_path):
    """Senza soluzione: altezza dal puntamento, niente secondi d'arco; la soluzione arrivata dopo
    riscrive la riga, una riga gia' risolta non si rifa'."""
    root = _measured(conn, tmp_path, *_CARDS)
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert row["solved"] == 0 and row["hfd_arcsec"] is None and row["hfd_zenith_arcsec"] is None
    assert row["altitude_deg"] == pytest.approx(_altitude((241.254763508206, 17.7165957446809)))
    assert sky_root(conn, root, LATER).written == 0
    _solve(conn)
    assert sky_root(conn, root, "dopo").written == 1
    [row] = _sky(conn)
    assert (row["solved"], row["computed_at"]) == (1, "dopo") and row["hfd_arcsec"] is not None
    assert sky_root(conn, root, "ancora").written == 0


def test_a_solution_without_its_matrix_gives_arcseconds_but_no_direction(conn, tmp_path):
    root = _measured(conn, tmp_path, *_CARDS)
    conn.execute("UPDATE pipeline_measures SET eccentricity = 0.6, angle_deg = 10.0")
    _solve(conn, cd=(None, None, None, None))
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert row["hfd_arcsec"] is not None and row["angle_pa_deg"] is None


def test_an_unreadable_measure_waits(conn, tmp_path):
    root = _measured(conn, tmp_path, *_CARDS)
    conn.execute("UPDATE pipeline_measures SET outcome = 'unreadable', stars = NULL, kept = NULL,"
                 " hfd_px = NULL, background_adu = NULL, noise_adu = NULL, shape = NULL,"
                 " shape_stars = NULL, fwhm_px = NULL, eccentricity = NULL, angle_deg = NULL,"
                 " ceiling_adu = NULL, saturated = NULL, psf_snr = NULL, gradient_pct = NULL,"
                 " gradient_angle_deg = NULL, tilt_pct = NULL, curvature_pct = NULL")  # fmt: skip
    assert sky_root(conn, root, LATER).written == 0 and _sky(conn) == []


def test_a_forgotten_solution_takes_its_sky_measures_along(conn, tmp_path):
    root = _measured(conn, tmp_path, *_CARDS)
    _solve(conn)
    sky_root(conn, root, LATER)
    [row] = _sky(conn)
    assert forget(conn, row["frame_id"]) is True and _sky(conn) == []


def test_a_stop_writes_nothing(conn, tmp_path):
    root = _measured(conn, tmp_path, *_CARDS)
    stop = threading.Event()
    stop.set()
    assert sky_root(conn, root, LATER, stop=stop).written == 0 and _sky(conn) == []


@pytest.mark.parametrize(
    ("start", "exposure", "mid"),
    [
        ("2025-06-29T21:30:00.000000+00:00", 300.0, "2025-06-29T21:32:30.000000+00:00"),
        ("2025-06-29T23:59:59.500000+00:00", 1.0, "2025-06-30T00:00:00.000000+00:00"),
        ("2025-06-29T21:30:00.000000+00:00", None, "2025-06-29T21:30:00.000000+00:00"),
        (None, 300.0, None),
    ],
)
def test_the_mid_exposure_is_the_start_plus_half(start, exposure, mid):
    assert mid_exposure(start, exposure) == mid


@pytest.mark.parametrize(
    ("pa", "axis"), [(0.0, "dec"), (44.0, "dec"), (46.0, "ra"), (90.0, "ra"), (134.0, "ra"),
                     (136.0, "dec"), (179.0, "dec")],
)  # fmt: skip
def test_the_nearer_sky_axis_names_the_direction(pa, axis):
    """PA 90: Est-Ovest, lungo l'AR; PA 0: Nord-Sud, lungo la Dec."""
    assert sky_axis(pa) == axis
