"""Lo SQM col metodo di ASTAP: a verita' nota, un campo con zero point e cielo scelti qui e il suo
catalogo .1476 costruito accanto."""

import math
from pathlib import Path

import numpy as np
import pytest
from scipy.special import erf

from astrolog.pipeline.sqm import (
    Wcs,
    as_sixteen_bit,
    best_mean,
    calibrate,
    sky_brightness,
    sky_mode,
    star_flux,
    superpixel,
)
from astrolog.pipeline.star_catalogue import DEC_STEP, MAX_FIELD_DEG, RA_STEP, area_of, find_areas

ZERO_POINT = 20.0
SKY = 1000.0
SIDE = 800
WCS = Wcs(ra_deg=100.0, dec_deg=20.0, crpix=((SIDE + 1) / 2, (SIDE + 1) / 2),
          cd=(-2.0 / 3600, 0.0, 0.0, 2.0 / 3600))  # fmt: skip


def _star(img: np.ndarray, x: float, y: float, flux: float, sigma: float = 1.5) -> None:
    """Gaussiana integrata sul pixel: il flusso scritto e' quello vero."""
    lo_x, lo_y = int(x) - 8, int(y) - 8
    edges_x = np.arange(lo_x, lo_x + 18) - 0.5 - x
    edges_y = np.arange(lo_y, lo_y + 18) - 0.5 - y
    cx = np.diff(erf(edges_x / (sigma * math.sqrt(2)))) / 2
    cy = np.diff(erf(edges_y / (sigma * math.sqrt(2)))) / 2
    img[lo_y : lo_y + 17, lo_x : lo_x + 17] += flux * np.outer(cy, cx)


def write_catalogue(folder: Path, ra: np.ndarray, dec: np.ndarray, mag: np.ndarray) -> None:
    """Un file .1476 per zona, magnitudini a decimi, dalla piu' brillante come ASTAP."""
    by_area: dict[str, list[tuple[int, int, int]]] = {}
    for r, d, m in zip(ra, dec, mag, strict=True):
        by_area.setdefault(area_of(r, d).name, []).append(
            (round(m * 10), round(d / DEC_STEP), round(r / RA_STEP))
        )
    head = bytearray(b" " * 110)
    head[108], head[109] = 1, 5
    # zone vicine vuote, e la prima, da cui ASTAP riconosce il catalogo
    for name in ["0101"] + [a.name for a, _ in find_areas(ra.mean(), dec.mean(), MAX_FIELD_DEG)]:
        (folder / f"d80_{name}.1476").write_bytes(bytes(head))
    for name, stars in by_area.items():
        body, last = bytearray(), None
        for mag10, dec_raw, ra_raw in sorted(stars):
            high = dec_raw >> 16
            if (mag10, high) != last:
                body += bytes([0xFF, 0xFF, 0xFF, high + 128, mag10 + 16])
                last = (mag10, high)
            low = dec_raw & 0xFFFF
            body += bytes([ra_raw & 0xFF, ra_raw >> 8 & 0xFF, ra_raw >> 16, low & 0xFF, low >> 8])
        (folder / f"d80_{name}.1476").write_bytes(bytes(head + body))


def sky_field(folder: Path, count: int = 150, seed: int = 3) -> np.ndarray:
    """Campo 800x800 a 2"/px, fondo 1000 e rumore 10, stelle da 8,5 a 11 mag; catalogo in folder."""
    rng = np.random.default_rng(seed)
    img = np.full((SIDE, SIDE), SKY)
    x, y = rng.uniform(40, SIDE - 40, count), rng.uniform(40, SIDE - 40, count)
    mag = np.round(rng.uniform(8.5, 11.0, count), 1)
    for xi, yi, mi in zip(x, y, mag, strict=True):
        _star(img, xi, yi, 10 ** ((ZERO_POINT - mi) / 2.5))
    ra, dec = WCS.to_sky(x, y)
    write_catalogue(folder, ra, dec, mag)
    return np.round(img + rng.normal(0, 10, img.shape))


def test_the_zero_point_and_the_sky_come_back(tmp_path):
    img = sky_field(tmp_path)
    found = calibrate(img, WCS, tmp_path, "d80", colour=False)
    assert found is not None
    assert found.zero_point_mag == pytest.approx(ZERO_POINT, abs=0.01)
    assert found.sky_adu == pytest.approx(SKY, abs=2)
    assert found.stars > 50  # le brillanti cadono sotto il tetto misurato, le altre al 1,5 sigma


def test_a_frame_without_catalogue_stars_does_not_calibrate(tmp_path):
    img = sky_field(tmp_path)
    for f in tmp_path.iterdir():
        f.write_bytes(f.read_bytes()[:110] + bytes([0xFF, 0xFF, 0xFF, 128, 116]))
    assert calibrate(img, WCS, tmp_path, "d80", colour=False) is None


def test_the_brightest_stars_near_the_frame_top_are_left_out(tmp_path):
    """Nove pixel sotto il massimo misurato - 1001 (ASTAP): la piu' brillante non entra mai."""
    img = sky_field(tmp_path)
    with_top = calibrate(img, WCS, tmp_path, "d80", colour=False)
    img[5, 5] = img.max() + 30000  # un pixel caldo alza il tetto: le brillanti rientrano
    without_top = calibrate(img, WCS, tmp_path, "d80", colour=False)
    assert with_top is not None and without_top is not None
    assert without_top.stars > with_top.stars


def test_a_colour_frame_is_measured_on_its_2x2_blocks(tmp_path):
    """Superpixel: ogni blocco 2x2 diventa la sua media, stessa dimensione e stesso WCS."""
    img = sky_field(tmp_path)
    found = calibrate(img, WCS, tmp_path, "d80", colour=True)
    assert found is not None
    assert found.zero_point_mag == pytest.approx(ZERO_POINT, abs=0.03)
    assert found.sky_adu == pytest.approx(SKY, abs=2)


def test_superpixel_keeps_the_size_and_averages_each_block():
    data = np.arange(16, dtype=float).reshape(4, 4)
    mean, top = superpixel(data)
    assert mean.shape == data.shape
    assert mean[0, 0] == mean[1, 1] == (0 + 1 + 4 + 5) / 4
    assert top[0, 0] == top[1, 0] == 5


def test_the_sky_is_the_histogram_mode():
    rng = np.random.default_rng(1)
    assert sky_mode(np.round(rng.normal(1000, 10, (300, 300)))) == pytest.approx(1000, abs=3)


def test_a_mean_far_above_the_mode_wins():
    """Moda bassa e strana (sopra 1,5 volte la moda la media): get_background di ASTAP."""
    data = np.full((300, 300), 1000.0)
    data[:200] = 100.0
    # righe 4-295 dopo i bordi: (196 x 100 + 96 x 1000) / 292, con un pixel in piu' al divisore
    assert sky_mode(data) == 396.0


def test_the_mode_leaves_out_the_frame_borders():
    """get_hist salta il 4,2% ai lati e l'1,5% in alto e in basso (aree morte dei RAW)."""
    data = np.full((300, 300), 1000.0)
    data[:, :12] = 50.0
    data[:, -12:] = 50.0
    assert sky_mode(data) == 1000.0


def test_sixteen_bit_ranges_stay_and_wide_ones_are_rescaled():
    data = np.array([[10.0, 60000.0]])
    assert as_sixteen_bit(data)[1] == 60000.0
    wide, top = as_sixteen_bit(np.array([[10.0, 200000.0]]))
    assert top == 65535.0 and wide.max() == pytest.approx(65535.0)


def test_star_flux_sums_the_star_over_its_ring():
    img = np.full((80, 80), 500.0)
    _star(img, 40.3, 39.6, 20000.0)
    found = star_flux(img + np.random.default_rng(2).normal(0, 5, img.shape), 40, 40)
    assert found is not None
    assert found.flux == pytest.approx(20000.0, rel=0.01)
    assert (found.x, found.y) == pytest.approx((40.3, 39.6), abs=0.05)


def test_a_star_against_the_border_is_not_measured():
    img = np.full((80, 80), 500.0)
    _star(img, 8.0, 40.0, 20000.0)
    assert star_flux(img, 8, 40) is None


def test_the_best_mean_drops_outliers_and_weighs_by_snr():
    values = np.array([1.0, 1.0, 1.1, 0.9, 5.0])
    weights = np.array([1.0, 3.0, 1.0, 1.0, 100.0])
    assert best_mean(values, weights) == pytest.approx((1 + 3 + 1.1 + 0.9) / 6)


def test_the_sky_brightness_formula():
    """ZP - 2,5 log10((cielo - tolto)/scala^2) + 0,2811 X - 0,28 (calculate_sqm)."""
    value = sky_brightness(20.0, 1100.0, 100.0, 2.0, 1.0)
    assert value == pytest.approx(20 - 2.5 * math.log10(250) + 0.0011, abs=1e-9)


def test_a_sky_at_or_under_what_is_taken_off_has_no_brightness():
    assert sky_brightness(20.0, 500.0, 500.0, 2.0, 1.0) is None


def test_the_wcs_goes_and_comes_back():
    x, y = np.array([10.0, 400.0, 790.0]), np.array([20.0, 400.0, 700.0])
    ra, dec = WCS.to_sky(x, y)
    back_x, back_y = WCS.to_pixels(ra, dec)
    assert back_x == pytest.approx(x, abs=1e-6) and back_y == pytest.approx(y, abs=1e-6)
    assert WCS.scale_arcsec == pytest.approx(2.0)
