"""Rettangolo del frame sul cielo dalla soluzione di ASTAP: scala, specchio, skew, campo, angoli.
Numeri da tests/astap/solved.ini (N.I.N.A., 560 mm)."""

import math

import pytest
from astropy.wcs import WCS

from astrolog.pipeline.footprint import footprint
from astrolog.pipeline.sky import deproject

CD = (-2.6277393210341225e-004, 2.7944155214576776e-004,
      -2.7944266362463124e-004, -2.6285912858408056e-004)  # fmt: skip
CRPIX = (3.1125e003, 2.0845e003)
CENTRE = (2.4125198643662179e002, 1.7726894038989336e001)
SIZE = (6224, 4168)
FLIPPED = (-CD[0], CD[1], -CD[2], CD[3])  # first pixel axis reversed: left-right mirror


def test_the_scale_is_the_root_of_the_matrix_determinant():
    """Paper II: area del pixel; la prima colonna sola sbaglia se gli assi non sono uguali."""
    det = CD[0] * CD[3] - CD[1] * CD[2]
    sky = footprint(CD, CRPIX, CENTRE, SIZE, bottom_up=False)
    assert sky.scale_arcsec_px == pytest.approx(math.sqrt(abs(det)) * 3600)


@pytest.mark.parametrize(
    ("cd", "bottom_up", "mirrored"),
    [(CD, False, False), (FLIPPED, False, True), (CD, True, True), (FLIPPED, True, False)],
)
def test_a_mirrored_frame_is_told_by_the_sign_of_the_matrix(cd, bottom_up, mirrored):
    """Misura su copie specchiate: N.I.N.A. e ASIAIR (righe dall'alto) normali con det>0; righe
    dal basso, regola rovesciata (come ASTAP). La rotazione da sola non lo vede."""
    assert footprint(cd, CRPIX, CENTRE, SIZE, bottom_up=bottom_up).mirrored is mirrored


def test_the_skew_is_the_gap_between_the_two_axis_angles():
    """Paper II: assi non ortogonali, due rotazioni; ASTAP scrive CROTA1 e CROTA2 (da una sua
    soluzione, non dalla CD: scarto 0,0002 gradi)."""
    sky = footprint(CD, CRPIX, CENTRE, SIZE, bottom_up=False)
    assert sky.skew_deg == pytest.approx(abs(-133.23929105535353 - -133.24844658376983), abs=1e-3)
    assert sky.skew_deg > 0
    assert footprint(FLIPPED, CRPIX, CENTRE, SIZE, bottom_up=False).skew_deg == sky.skew_deg


def _rotated(rho_a: float, rho_b: float, mirror: float = 1.0) -> tuple[float, float, float, float]:
    """CD from two axis angles (Paper II eq. 189, CDELT 1e-4, first axis sign `mirror`)."""
    a, b = math.radians(rho_a), math.radians(rho_b)
    d1 = 1e-4 * mirror
    return (d1 * math.cos(a), -1e-4 * math.sin(b), d1 * math.sin(a), 1e-4 * math.cos(b))


@pytest.mark.parametrize(
    ("rho_a", "rho_b", "skew"), [(10.0, 10.3, 0.3), (10.3, 10.0, 0.3), (179.9, -179.8, 0.3)]
)
@pytest.mark.parametrize("mirror", [1.0, -1.0])
def test_the_skew_is_the_angle_between_axes_whatever_the_order_or_the_turn(
    rho_a, rho_b, skew, mirror
):
    """Sempre positivo, e attraverso 180 gradi la differenza corta, non 359,7."""
    cd = _rotated(rho_a, rho_b, mirror)
    assert footprint(cd, CRPIX, CENTRE, SIZE, bottom_up=False).skew_deg == pytest.approx(skew)


def test_the_field_is_the_frame_size_at_the_measured_scale():
    sky = footprint(CD, CRPIX, CENTRE, SIZE, bottom_up=False)
    assert sky.width_deg == pytest.approx(6224 * sky.scale_arcsec_px / 3600)
    assert sky.height_deg == pytest.approx(4168 * sky.scale_arcsec_px / 3600)


@pytest.mark.parametrize("cd", [CD, FLIPPED])
def test_the_corners_are_the_pixel_edges_on_the_sky(cd):
    """Proiezione TAN inversa (Paper II) dagli spigoli esterni; oracolo: astropy.wcs."""
    wcs = WCS(naxis=2)
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    wcs.wcs.crval = list(CENTRE)
    wcs.wcs.crpix = list(CRPIX)
    wcs.wcs.cd = [[cd[0], cd[1]], [cd[2], cd[3]]]
    edges = [(0.5, 0.5), (6224.5, 0.5), (6224.5, 4168.5), (0.5, 4168.5)]
    expected = [float(v) for edge in edges for v in wcs.wcs_pix2world([edge], 1)[0]]
    corners = footprint(cd, CRPIX, CENTRE, SIZE, bottom_up=False).corners
    assert corners is not None
    assert [v for corner in corners for v in corner] == pytest.approx(expected, abs=1e-9)


def test_a_frame_across_zero_hours_keeps_its_corners_in_range():
    sky = footprint(CD, CRPIX, (0.1, 17.7), SIZE, bottom_up=False)
    assert sky.corners is not None and all(0 <= ra < 360 for ra, _ in sky.corners)


def test_a_point_a_hair_west_of_zero_hours_is_not_360():
    """-1e-17 % 360 da' 360.0 in virgola mobile: fuori dall'intervallo dello schema."""
    ra, _dec = deproject((0.0, 0.0), -1e-19, 0.0)
    assert 0 <= ra < 360


@pytest.mark.parametrize("size", [(None, 4168), (6224, None)])
def test_without_the_frame_size_there_is_no_field_nor_corners(size):
    sky = footprint(CD, CRPIX, CENTRE, size, bottom_up=False)
    assert sky.corners is None and (sky.width_deg is None or sky.height_deg is None)
