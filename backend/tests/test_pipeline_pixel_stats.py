"""Pixel statistics as Image Analysis (pixel_stats.py; ImageAnalysis par. 2.1.2, 2.1.4) and the
MMT background estimates M* and N* (mmt.py; ImageWeighting par. 2.3, 2.4). software-ok"""

import math

import numpy as np
import pytest

from astrolog.pipeline.mmt import background_residual, mstar_nstar
from astrolog.pipeline.pixel_stats import PixelStats, pixel_stats, snr

_SIDE = 512


def _noise(sigma: float = 10.0, level: float = 1000.0, seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).normal(level, sigma, (_SIDE, _SIDE)).astype(np.float32)


def _stats(data: np.ndarray, pedestal: float = 0.0) -> PixelStats:
    return pixel_stats(data, full_scale=65535.0, pedestal=pedestal)  # 16 bit: e is one DN


def test_the_median_leaves_out_the_pedestal_the_empty_border_and_the_saturated_pixels() -> None:
    data = _noise()
    data[:, :200] = 0.0  # empty border of a registered frame, more than half of it
    data[:5, -5:] = 65535.0
    stats = _stats(data, pedestal=100.0)
    assert stats.median_adu == pytest.approx(900.0, abs=1.0)


def test_the_open_range_is_one_65535th_of_the_full_scale_whatever_the_depth() -> None:
    """ImageAnalysis par. 2.1.2: e = 1/65535 of [0, 1]; an 8-bit frame keeps min + 1 DN."""
    data = np.full((64, 64), 50.0, np.float32)
    data[0, :8], data[0, -8:] = 0.0, 200.0
    data[1:40] = 1.0  # one DN over the minimum: valid at 8 bit, out at 16
    assert pixel_stats(data, full_scale=255.0).median_adu == pytest.approx(1.0)
    assert pixel_stats(data, full_scale=65535.0).median_adu == pytest.approx(50.0)


def test_sigma_is_the_spread_of_a_normal_sample_and_ignores_the_stars() -> None:
    data = _noise(sigma=10.0)
    data[::17, ::13] += 5000.0  # stars: rejected by the biweight
    assert _stats(data).sigma_adu == pytest.approx(10.0, rel=0.01)


def test_the_entropy_of_gaussian_noise_is_half_log2_of_2_pi_e() -> None:
    """ImageAnalysis eq. 12: 2.047 bits."""
    assert _stats(_noise()).entropy_bits == pytest.approx(
        0.5 * math.log2(2 * math.pi * math.e), abs=0.01
    )


def test_the_entropy_does_not_change_with_pedestal_exposure_or_gain() -> None:
    data = _noise()
    data[::9, ::7] += 300.0
    once = _stats(data).entropy_bits
    assert _stats(data * 3.0 + 500.0).entropy_bits == pytest.approx(once, abs=0.005)


def test_stars_raise_the_entropy() -> None:
    data = _noise()
    data[::9, ::7] += (
        np.random.default_rng(4).uniform(50.0, 3000.0, data[::9, ::7].shape).astype(np.float32)
    )
    assert _stats(data).entropy_bits > _stats(_noise()).entropy_bits + 0.1


def test_the_scaling_factors_are_the_spreads_below_and_above_the_median() -> None:
    """A normal sample: two equal sides. Three times wider above: three times the high factor."""
    symmetric = _stats(_noise())
    assert symmetric.scale_low_adu == pytest.approx(symmetric.scale_high_adu, rel=0.01)
    rng = np.random.default_rng(3)
    low = 1000.0 - np.abs(rng.normal(0, 5.0, _SIDE * _SIDE // 2))
    high = 1000.0 + np.abs(rng.normal(0, 15.0, _SIDE * _SIDE // 2))
    stats = _stats(np.concatenate([low, high]).reshape(_SIDE, _SIDE).astype(np.float32))
    assert stats.scale_high_adu / stats.scale_low_adu == pytest.approx(3.0, rel=0.02)


def test_snr_is_the_squared_mean_scale_over_the_noise() -> None:
    """ImageAnalysis eq. 16."""
    assert snr(4.0, 6.0, 2.5) == pytest.approx(4.0)
    assert snr(4.0, 6.0, 0.0) is None


def test_the_background_residual_holds_the_pixels_under_the_model_only() -> None:
    data = _noise()
    data[::31, ::29] = 0.0  # empty pixels are never in R*
    residual = background_residual(data)
    assert residual.size == pytest.approx(0.5 * (_SIDE * _SIDE - data[::31, ::29].size), rel=0.03)
    assert np.all(residual > 0)
    assert residual.max() < 10 * 10.0  # never the empty pixels' distance from the sky


def test_mstar_and_nstar_of_white_noise_are_its_half_normal_median_and_its_sigma() -> None:
    """ImageWeighting eq. 13-17: M* 0.6745 sigma, N* (Sn, 2.054326) sigma."""
    found = mstar_nstar(_noise(sigma=10.0, level=1000.0))
    assert found is not None
    assert found.mstar_adu == pytest.approx(6.745, rel=0.03)
    assert found.nstar_adu == pytest.approx(10.0, rel=0.03)


def test_a_gradient_and_stars_do_not_move_mstar_and_nstar() -> None:
    flat = mstar_nstar(_noise())
    data = _noise()
    yy, xx = np.mgrid[0:_SIDE, 0:_SIDE]
    data += (0.3 * xx + 0.2 * yy).astype(np.float32)
    data[::23, ::19] += 3000.0
    sloped = mstar_nstar(data)
    assert flat is not None and sloped is not None
    assert sloped.mstar_adu == pytest.approx(flat.mstar_adu, rel=0.05)
    assert sloped.nstar_adu == pytest.approx(flat.nstar_adu, rel=0.05)


def test_a_frame_with_nothing_under_its_model_has_no_mstar() -> None:
    assert mstar_nstar(np.zeros((64, 64), np.float32)) is None
