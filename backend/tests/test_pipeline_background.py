"""Sky gradient and banding as Image Analysis (par. 2.1.3, eq. 13-15), in noise units."""

import numpy as np
import pytest

from astrolog.pipeline.background import Banding, banding, gradient, valid_pixels

_NOISE = 10.0


def _sky(rows: int = 960, cols: int = 1280, seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).normal(1000.0, _NOISE, (rows, cols))


def test_the_gradient_is_the_fitted_surface_peak_to_peak_over_the_noise() -> None:
    """b = 30 u + 20 v^2 over [-1, 1]: from -30 to 50, 80 ADU, 8 noise units."""
    sky = _sky()
    rows, cols = sky.shape
    v, u = np.meshgrid(np.linspace(-1, 1, rows), np.linspace(-1, 1, cols), indexing="ij")
    sky += 30 * u + 20 * v * v
    assert gradient(sky, valid_pixels(sky, 65535.0), _NOISE) == pytest.approx(8.0, rel=0.02)


def test_bright_tiles_do_not_make_a_gradient() -> None:
    """A flat sky, eleven tiles taken by a nebula 50 sigma over it: the biweight drops them."""
    sky = _sky()
    for k in range(11):
        sky[60 * k : 60 * k + 60, 80 * (k + 2) : 80 * (k + 3)] += 500.0
    flat = gradient(sky, valid_pixels(sky, 65535.0), _NOISE)
    assert flat is not None and flat < 0.1


def test_under_six_tiles_there_is_no_gradient() -> None:
    """64 x 64 px makes 2 x 2 tiles of 32: four medians, six coefficients. Not flat: unknown."""
    sky = _sky(64, 64)
    assert gradient(sky, valid_pixels(sky, 65535.0), _NOISE) is None


def test_saturated_pixels_and_empty_borders_are_not_valid() -> None:
    sky = _sky()
    sky[:, :40] = 0.0
    sky[100:110, 100:110] = 65535.0
    valid = valid_pixels(sky, 65535.0)
    assert not valid[:, :40].any() and not valid[100:110, 100:110].any()
    assert valid[:, 40:].sum() == sky[:, 40:].size - 100


def _banding(sky: np.ndarray) -> Banding:
    found = banding(sky, valid_pixels(sky, 65535.0), _NOISE)
    assert found is not None
    return found


def test_white_noise_has_no_banding() -> None:
    found = _banding(_sky())
    assert found.row < 0.02 and found.column < 0.02


def test_row_offsets_are_row_banding_in_noise_units() -> None:
    """Each row lifted by a normal of 0.3 sigma: row banding 0.3, columns untouched."""
    sky = _sky()
    sky += np.random.default_rng(2).normal(0.0, 0.3 * _NOISE, (sky.shape[0], 1))
    found = _banding(sky)
    assert found.row == pytest.approx(0.3, rel=0.1)
    assert found.column < 0.02


def test_alternating_rows_of_a_mosaic_are_not_banding() -> None:
    """Even rows 50 over the odd ones, as a CFA: each row is measured against its own parity."""
    sky = _sky()
    sky[::2] += 50.0
    assert _banding(sky).row < 0.02
