"""Star detection as the SubframeSelector counts (plan 25.15, docs/domini/misure.md): structures
over the sky on the median copy, a star when its brightest 2x2 aperture clears APERTURE_SNR."""

import numpy as np
import pytest

from astrolog.pipeline.detect import APERTURE_SNR, STRUCTURE_SIGMA, detect
from astrolog.pipeline.stars import measure_frame, median3x3

_SIDE = 300
_NOISE = 10.0


def _gauss(y: float, x: float, sigma: float, flux: float) -> np.ndarray:
    """A star integrated on the pixel, 8 samples a side, on an empty frame."""
    fine = (np.arange(_SIDE * 8) + 0.5) / 8 - 0.5
    gy = np.exp(-((fine - y) ** 2) / (2 * sigma**2)).reshape(_SIDE, 8).sum(axis=1)
    gx = np.exp(-((fine - x) ** 2) / (2 * sigma**2)).reshape(_SIDE, 8).sum(axis=1)
    star = np.outer(gy, gx)
    return (flux * star / star.sum()).astype(np.float32)


def _aperture_snr(star: np.ndarray) -> float:
    """The test's own: best 2x2 sum over the noise of four pixels."""
    sums = star[:-1, :-1] + star[1:, :-1] + star[:-1, 1:] + star[1:, 1:]
    return float(sums.max() / (2 * _NOISE))


def _found(residual: np.ndarray) -> int:
    return len(detect(residual, median3x3(residual), _NOISE).x)


def test_a_star_over_the_aperture_threshold_is_found_one_under_is_not() -> None:
    unit = _gauss(150, 150, 1.5, 1.0)
    over = unit * (1.1 * APERTURE_SNR / _aperture_snr(unit))
    under = unit * (0.9 * APERTURE_SNR / _aperture_snr(unit))
    assert _found(over) == 1
    assert _found(under) == 0


def test_the_position_is_the_barycentre() -> None:
    found = detect(star := _gauss(100.3, 200.7, 2.0, 20000.0), median3x3(star), _NOISE)
    assert (float(found.y[0]), float(found.x[0])) == pytest.approx((100.3, 200.7), abs=0.05)


def test_a_dark_pixel_among_bright_ones_has_a_position() -> None:
    """Five bright of its eight: only its median is over the threshold, its raw pixel is dark;
    barycentre weights of 0 gave NaN (frame 05 of the 24)."""
    residual = np.zeros((_SIDE, _SIDE), dtype=np.float32)
    for y, x in ((99, 99), (99, 100), (99, 101), (101, 99), (101, 101)):
        residual[y, x] = 100 * _NOISE
    residual[100, 100] = -_NOISE
    found = detect(residual, median3x3(residual), _NOISE)
    assert len(found.x) == 1
    assert (float(found.y[0]), float(found.x[0])) == (100.0, 100.0)


def test_a_hot_pixel_is_not_a_star() -> None:
    residual = np.zeros((_SIDE, _SIDE), dtype=np.float32)
    residual[120, 80] = 60000.0
    assert _found(residual) == 0


def test_a_wide_faint_patch_is_not_a_star_however_much_light_it_holds() -> None:
    """Nebula knot: 5 sigma at its peak over 40 px, flux of a bright star, a 2x2 SNR of 10."""
    patch = _gauss(150, 150, 15.0, 1.0)
    patch *= 5 * _NOISE / patch.max()
    assert patch.sum() > 50000
    assert _found(patch) == 0


def test_a_structure_starts_at_its_threshold_on_the_median_copy() -> None:
    """Two stars joined by a bridge over STRUCTURE_SIGMA are one structure, too thin a one for a
    star (MIN_COVERAGE); the bridge cut, two stars."""
    pair = _gauss(150, 140, 1.5, 3000.0) + _gauss(150, 160, 1.5, 3000.0)
    pair[149:152, 140:161] = np.maximum(pair[149:152, 140:161], 2 * STRUCTURE_SIGMA * _NOISE)
    assert _found(pair) == 0
    pair[149:152, 148:153] = 0.0
    assert _found(pair) == 2


def _glow() -> np.ndarray:
    """Light the sky map left, far wider than 32 px: 50 sigma at the peak, sigma 100 px."""
    glow = _gauss(150, 150, 100.0, 1.0)
    return glow * (50 * _NOISE / glow.max())


def test_a_glow_wider_than_the_structure_scales_is_no_star() -> None:
    """Over 3 sigma of the median copy it was one structure, a star of its 2x2 SNR of 100."""
    assert _found(_glow()) == 0


def test_a_star_on_a_wide_glow_keeps_its_own_flux() -> None:
    star = _gauss(150, 170, 1.5, 20000.0)
    alone = detect(star, median3x3(star), _NOISE)
    on_glow = detect(both := star + _glow(), median3x3(both), _NOISE)
    assert len(on_glow.x) == 1
    assert float(on_glow.flux[0]) == pytest.approx(float(alone.flux[0]), rel=0.1)


def test_a_trail_is_not_a_star() -> None:
    """A structure covering under (1 - maxDistortion) pi / 4 of its square: StarDetector docs."""
    trail = np.zeros((_SIDE, _SIDE), dtype=np.float32)
    for x in range(100, 160):
        trail += _gauss(150, x, 1.0, 2000.0)
    assert _found(trail) == 0


def test_one_sensor_pixel_at_the_ceiling_makes_a_star_saturated() -> None:
    """As ASTAP: a pixel at the top is enough."""
    star = _gauss(150, 150, 2.0, 20000.0)
    sensor = star.copy()
    sensor[150, 150] = 60000.0
    found = detect(star, median3x3(star), _NOISE, clip=(sensor, 60000.0))
    assert found.saturated.tolist() == [True]


def test_the_frame_counts_the_stars_the_subframeselector_would() -> None:
    """36 stars at a 2x2 SNR of 14: sep at 5 sigma counted 31, the SubframeSelector none.
    software-ok"""
    rng = np.random.default_rng(2)
    flux = 14 / _aperture_snr(_gauss(150, 150, 2.0, 1.0))
    data = np.full((_SIDE, _SIDE), 1000.0, dtype=np.float32)
    for y in range(40, 280, 40):
        for x in range(40, 280, 40):
            data += _gauss(y, x, 2.0, flux)
    data += rng.normal(0, _NOISE, data.shape).astype(np.float32)
    assert measure_frame(data, saturation=65535.0, pattern=None).stars == 0
