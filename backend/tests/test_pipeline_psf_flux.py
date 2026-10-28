"""Each star's flux for the PSF SNR (psf_flux.py, ImageWeighting eq. 7): over a tenth of its own
peak, less its local sky. software-ok"""

import math

import numpy as np
import pytest

from astrolog.pipeline.detect import detect
from astrolog.pipeline.stars import median3x3

_SIDE = 600
_NOISE = 10.0
_SUB = 5


def _noise(seed: int = 1) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, _NOISE, (_SIDE, _SIDE))


def _places(count_side: int, margin: int) -> list[tuple[int, int]]:
    steps = np.linspace(margin, _SIDE - margin, count_side).round().astype(int)
    return [(int(y), int(x)) for y in steps for x in steps]


def _moffat(beta: float, fwhm: float, reach: int) -> np.ndarray:
    """A unit-flux circular Moffat integrated on the pixel."""
    alpha = fwhm / (2 * math.sqrt(2 ** (1 / beta) - 1))
    side = 2 * reach + 1
    fine = (np.arange(side * _SUB) + 0.5) / _SUB - 0.5 - reach
    yy, xx = np.meshgrid(fine, fine, indexing="ij")
    profile = (1 + (xx**2 + yy**2) / alpha**2) ** -beta * (beta - 1) / (math.pi * alpha**2)
    return profile.reshape(side, _SUB, side, _SUB).sum(axis=(1, 3)) / _SUB**2


def _field(fwhm: float, flux: float, pedestal: float = 0.0) -> np.ndarray:
    data = _noise() + pedestal
    reach = int(8 * fwhm)
    stamp = _moffat(4.0, fwhm, reach)
    for y, x in _places(5, 60):
        data[y - reach : y + reach + 1, x - reach : x + reach + 1] += flux * stamp
    return data.astype(np.float32)


def _fluxes(residual: np.ndarray) -> np.ndarray:
    found = detect(residual, median3x3(residual), _NOISE)
    assert len(found.x) == 25
    return found.flux


@pytest.mark.parametrize(("fwhm", "over"), [(4.0, 1.00), (6.0, 0.98), (2.0, 1.10)])
def test_a_moffat_of_beta_4_keeps_its_share_inside_the_tenth(fwhm: float, over: float) -> None:
    """Enclosed 1 - (1 + r^2/a^2)^(1 - beta), at the tenth 1 - 0.1^((beta - 1) / beta) = 0.822
    [D Moffat 1969]. Under 3 px the median copy flattens the peak: +10% at 2 px. [M]"""
    share = 1 - 0.1 ** (3 / 4)
    flux = _fluxes(_field(fwhm, 1e5))
    assert np.median(flux) == pytest.approx(over * share * 1e5, rel=0.03)


def test_a_sky_left_under_the_stars_stays_out_of_their_flux() -> None:
    """A nebula the sky map missed: frame 23 of the copies read 1.56 times the SubframeSelector
    when the whole structure was summed. The local sky takes it off."""
    clear = _fluxes(_field(3.0, 1e5)).sum()
    assert _fluxes(_field(3.0, 1e5, pedestal=15.0)).sum() == pytest.approx(clear, rel=0.01)


def test_a_glow_with_its_centre_in_the_dark_adds_no_flux() -> None:
    """Canon 15 of the copies: extended light counted as one star, its barycentre in a hollow,
    held 83% of our F and nothing of the SubframeSelector's. Its centre is outside its region."""
    clear = _fluxes(_field(3.0, 1e5))
    rows, cols = np.indices((_SIDE, _SIDE))
    ring = np.hypot(rows - 120, cols - 120)  # between the stars
    glow = _field(3.0, 1e5) + (200 * np.exp(-(((ring - 25) / 4) ** 2))).astype(np.float32)
    found = detect(glow, median3x3(glow), _NOISE)
    assert len(found.x) == 26
    assert found.flux.sum() == pytest.approx(clear.sum(), rel=0.01)


def test_a_clipped_star_keeps_its_wide_region() -> None:
    """A clipped core's peak is the ceiling: the tenth of it reaches far into the wings, as the
    SubframeSelector's fit of the flat top does. One a zone lost them: 0.33-0.69 of F. [M]"""
    clipped = np.minimum(_field(3.0, 1e7), 30000.0)
    share = 1 - 0.1 ** (3 / 4)
    assert np.median(_fluxes(clipped)) > 3 * share * 1e5
