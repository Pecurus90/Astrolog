"""The frame's noise by the multiresolution support (noise.py, Starck & Murtagh 1998)."""

import numpy as np
import pytest

from astrolog.pipeline.noise import UNIT_SIGMAS, mrs_noise, starlet

_SIDE = 512


def _noise(sigma: float = 10.0, seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).normal(1000.0, sigma, (_SIDE, _SIDE)).astype(np.float32)


def _gauss_stars(data: np.ndarray, count: int, flux: float, sigma: float, seed: int = 2) -> None:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[-8:9, -8:9]
    stamp = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    stamp /= stamp.sum()
    for y, x in rng.integers(10, _SIDE - 10, (count, 2)):
        data[y - 8 : y + 9, x - 8 : x + 9] += flux * stamp


def test_the_first_layer_sigma_is_the_published_one() -> None:
    """Duchamp app-waveletNoise: 0.8908 for the 2D B3 starlet's first scale."""
    assert UNIT_SIGMAS[0] == pytest.approx(0.8908, abs=1e-4)
    assert UNIT_SIGMAS[1] == pytest.approx(0.2007, abs=1e-3)


def test_the_starlet_sums_back_to_the_image() -> None:
    image = _noise()
    planes, smooth = starlet(image, 4)
    assert np.allclose(smooth + sum(planes), image, atol=1e-2)


def test_pure_gaussian_noise_reads_its_sigma() -> None:
    assert mrs_noise(_noise(10.0)) == pytest.approx(10.0, rel=0.02)


def test_a_crowded_field_and_a_nebula_leave_the_noise_as_it_is() -> None:
    """Stars and a broad glow live in the support: the sigma is the sky's own."""
    data = _noise(10.0)
    _gauss_stars(data, 1500, 3e3, 1.5)
    rows, cols = np.indices(data.shape)
    data += (3000 * np.exp(-((rows - 256) ** 2 + (cols - 256) ** 2) / (2 * 80.0**2))).astype(
        np.float32
    )
    assert mrs_noise(data) == pytest.approx(10.0, rel=0.03)
