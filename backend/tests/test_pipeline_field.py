"""Measures across the frame (ADR 0022 point 5, ADR 0041, ADR 0042): saturated stars at the
declared full scale, PSF SNR, the bright side, FWHM tilt and curvature, elongation."""

import math

import numpy as np
import pytest

from astrolog.pipeline import stars
from astrolog.pipeline.field import (
    PSF_SNR_C3,
    PSF_SNR_C4,
    Photometry,
    bright_side,
    elongation,
    fwhm_tilt,
    psf_signal_weight,
    psf_snr,
)
from astrolog.pipeline.psf_fit import Fitted
from astrolog.pipeline.stars import Measured, measure_frame

_SIDE = 600
_BACKGROUND = 1000.0
_NOISE = 10.0
_SUB = 5


def _sky(seed: int = 1, side: int = _SIDE) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (rng.normal(_BACKGROUND, _NOISE, (side, side))).astype(np.float32)


def _gauss(sigma: float, reach: int) -> np.ndarray:
    """A unit-flux Gaussian star integrated on the pixel, centred in a (2 reach + 1)^2 stamp."""
    side = 2 * reach + 1
    fine = (np.arange(side * _SUB) + 0.5) / _SUB - 0.5 - reach
    yy, xx = np.meshgrid(fine, fine, indexing="ij")
    binned = np.exp(-(xx**2 + yy**2) / (2 * sigma**2)).reshape(side, _SUB, side, _SUB)
    stamp = binned.sum(axis=(1, 3))
    return stamp / stamp.sum()


def _stars(data: np.ndarray, places: list[tuple[int, int]], sigma: float, flux: float) -> None:
    reach = max(6, int(6 * sigma))
    stamp = _gauss(sigma, reach)
    for y, x in places:
        data[y - reach : y + reach + 1, x - reach : x + reach + 1] += flux * stamp


def _grid(count_side: int, margin: int = 50, side: int = _SIDE) -> list[tuple[int, int]]:
    steps = np.linspace(margin, side - margin, count_side).round().astype(int)
    return [(int(y), int(x)) for y in steps for x in steps]


# Saturated stars, through measure_frame


def test_stars_at_the_ceiling_are_counted_saturated_and_kept_out() -> None:
    data = _sky()
    places = _grid(6)
    _stars(data, places, 2.0, 6e4)
    clipped = _sky(2) * 0
    _stars(clipped, places[:12], 2.0, 4e6)
    data = np.minimum(data + clipped, 65535.0)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.saturated == 12
    assert found.stars == 36
    assert isinstance(found, Measured)
    assert found.kept == 24
    assert found.ceiling_adu == 65535.0


def test_the_ceiling_is_the_declared_full_scale_as_pixinsight() -> None:
    """ImageWeighting 3.1.1: saturated over the threshold, 1.0 of the full scale. A camera that
    clips under it (Canon 700D at 61208) has no saturated stars, there as here. software-ok"""
    data = _sky()
    places = _grid(6)
    _stars(data, places, 2.0, 6e4)
    clipped = _sky(2) * 0
    _stars(clipped, places[:12], 2.0, 4e6)
    data = np.minimum(data + clipped, 61208.0)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.ceiling_adu == 65535.0
    assert found.saturated == 0


def test_a_frame_without_clipped_stars_has_none_saturated() -> None:
    data = _sky()
    _stars(data, _grid(6), 2.0, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.saturated == 0
    assert found.ceiling_adu == 65535.0


# PSF SNR


def test_psf_snr_is_the_documented_formula() -> None:
    """ImageWeighting eq. 23-24: c3 F^2 / (c4 sigma^2); units cancel, ADU or [0,1] alike."""
    assert psf_snr(5000.0, 2.0) == pytest.approx(PSF_SNR_C3 * 5000.0**2 / (PSF_SNR_C4 * 4.0))
    assert psf_snr(5000.0 / 65535, 2.0 / 65535) == pytest.approx(psf_snr(5000.0, 2.0))


def test_psf_signal_weight_gives_back_the_programs_own_value() -> None:
    """ImageWeighting eq. 21-22 on its PSFFlux, PSFTotalMeanFlux, Noise, MStar (Abell 2151 n.0):
    its PSFSignalWeight; no M*, no weight. software-ok"""
    found = Photometry(2531.6810175144487, 33.12986348995004, 2000)
    weight = psf_signal_weight(found, 0.0008990046849219067, 0.0006099659949541092)
    assert weight == pytest.approx(0.09051482273618627, rel=1e-9)
    assert psf_signal_weight(found, 0.0009, 0.0) is None


def test_psf_snr_gives_back_the_programs_own_value() -> None:
    """Its PSFFlux, Noise and PSFSNR on one frame (Shark n.0, ImageAnalysis = SubframeSelector):
    the formula with the documented constants returns its PSF SNR. software-ok"""
    assert psf_snr(2756.598924285991, 0.0010614623312019081) == pytest.approx(
        0.17797316030630608, rel=1e-4
    )


def test_the_frame_psf_snr_takes_the_fitted_stars_signal_with_no_scale() -> None:
    """ImageWeighting eq. 7, 23-24: F the stars' signal over the fitted sky, 36 of 6e4; the Moffat's
    tenth grown 1 px holds a Gaussian whole, noise over B adds a little: 1.013. [M]"""
    data = _sky()
    _stars(data, _grid(6), 2.0, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.psf_count == 36 and found.psf_flux_adu is not None
    assert found.psf_flux_adu == pytest.approx(36 * 6e4, rel=0.03)
    assert found.psf_snr == pytest.approx(psf_snr(found.psf_flux_adu, _NOISE), rel=0.02)
    assert found.psf_mean_flux_adu == pytest.approx(
        found.psf_flux_adu / (math.pi * (2 * math.sqrt(2 * math.log(10))) ** 2), rel=0.1
    )


def test_saturated_stars_stay_in_the_psf_flux_clipped_as_they_are() -> None:
    """The SubframeSelector keeps them (upper limit 1.0, the full scale): so do we."""
    data, without = _sky(), _sky()
    places = _grid(6)
    _stars(data, places[12:], 2.0, 6e4)
    _stars(without, places[12:], 2.0, 6e4)
    clipped = np.zeros_like(data)
    _stars(clipped, places[:12], 2.0, 4e6)
    data = np.minimum(data + clipped, 65535.0)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    alone = measure_frame(without, saturation=65535.0, pattern=None)
    assert found.psf_snr is not None and alone.psf_snr is not None
    assert found.psf_snr > 10 * alone.psf_snr


def test_a_colour_psf_snr_takes_the_intensity_noise_not_the_written_one(monkeypatch) -> None:
    """Compared with the SubframeSelector on the intensity (misure.md): the mosaic's noise, the
    one written, never enters it."""
    data = _sky()
    _stars(data, _grid(6), 2.0, 6e4)
    first = measure_frame(data, saturation=65535.0, pattern="RGGB")
    monkeypatch.setattr(stars, "_mosaic_noise", lambda *_: 1e3)
    second = measure_frame(data, saturation=65535.0, pattern="RGGB")
    assert second.noise_adu == 1e3
    assert second.psf_snr == first.psf_snr


def test_in_a_crowded_field_the_noise_is_read_off_the_stars() -> None:
    """1500 faint stars on a 10 ADU sky: their wings in the MAD read 12.5; off the grown
    structures the sky's own 10 (NGC 6888 of the copies: 1.24 times the SubframeSelector)."""
    data = _sky()
    spots = np.random.default_rng(3).uniform(20, 580, (1500, 2)).astype(int)
    _stars(data, [(int(y), int(x)) for y, x in spots], 1.5, 3e3)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.noise_adu == pytest.approx(_NOISE, rel=0.03)


def test_under_five_stars_no_psf_snr() -> None:
    found = measure_frame(_sky(), saturation=65535.0, pattern=None)
    assert found.psf_snr is None


# Gradient


def test_a_sky_on_a_plane_has_its_bright_side() -> None:
    """From 900 at the left to 1100 at the right: brighter at +x."""
    cols = np.indices((640, 640))[1]
    back = (900 + 200 * cols / 639).astype(np.float32)
    assert _turn(bright_side(back), 0.0) < 1.0


def _turn(angle: float | None, expected: float) -> float:
    assert angle is not None
    return abs((angle - expected + 180) % 360 - 180)


def test_the_bright_side_turns_with_the_plane() -> None:
    rows, cols = np.indices((640, 640))
    back = (1000 - 100 * cols / 639 + 100 * rows / 639).astype(np.float32)  # bright at -x, +y
    assert _turn(bright_side(back), 135.0) < 1.0


def test_a_flat_sky_has_no_side() -> None:
    assert bright_side(np.full((640, 640), 1000.0, dtype=np.float32)) is None


def test_the_bright_side_reaches_the_frame_through_measure() -> None:
    cols = np.indices((_SIDE, _SIDE))[1]
    data = _sky() + (200 * cols / (_SIDE - 1) - 100).astype(np.float32)
    _stars(data, _grid(6), 2.0, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert _turn(found.gradient_angle_deg, 0.0) < 5.0


# FWHM tilt and curvature, elongation (ImageAnalysis eq. 26-29)


def _fits(fwhm: np.ndarray, x: np.ndarray, y: np.ndarray, eccentricity=None, angle=None) -> Fitted:
    n = len(fwhm)
    eccentricity = np.full(n, 0.3) if eccentricity is None else np.asarray(eccentricity, float)
    angle = np.zeros(n) if angle is None else np.asarray(angle, float)
    nothing = np.full(n, np.nan)
    return Fitted(np.asarray(fwhm, float), eccentricity, angle, nothing, nothing, nothing,
                  np.arange(n), np.asarray(x, float), np.asarray(y, float))  # fmt: skip


def _field_of_stars(side_x: int = 1200, side_y: int = 800, per_side: int = 12):
    steps_x = np.linspace(10, side_x - 11, per_side)
    steps_y = np.linspace(10, side_y - 11, per_side)
    x, y = (g.ravel() for g in np.meshgrid(steps_x, steps_y))
    return x, y


def test_tilt_and_curvature_are_the_documented_surface() -> None:
    """w = a + b u + c v + d (u^2 + v^2), u v over the half diagonal R: tilt (|b| W + |c| H) /
    (R a), curvature d / a; a tenth of the stars thrown off do not move them."""
    x, y = _field_of_stars()
    radius = math.hypot(1200, 800) / 2
    u, v = (x - 599.5) / radius, (y - 399.5) / radius
    fwhm = 3.0 + 0.2 * u - 0.1 * v + 0.4 * (u * u + v * v)
    fwhm[::10] += 5.0
    found = fwhm_tilt(_fits(fwhm, x, y), (800, 1200))
    assert found is not None
    assert found.tilt == pytest.approx((0.2 * 1200 + 0.1 * 800) / (radius * 3.0), rel=1e-6)
    assert found.curvature == pytest.approx(0.4 / 3.0, rel=1e-6)


def test_under_32_stars_no_tilt() -> None:
    x, y = _field_of_stars(per_side=5)
    assert fwhm_tilt(_fits(np.full(25, 3.0), x[:25], y[:25]), (800, 1200)) is None
    x, y = _field_of_stars()
    assert fwhm_tilt(_fits(np.full(32, 3.0), x[:32], y[:32]), (800, 1200)) is not None


def test_aligned_elongations_give_their_angle_counterclockwise_and_full_coherence() -> None:
    """Ours from +x towards +y (rows down), his counterclockwise: 180 less ours."""
    x, y = _field_of_stars()
    n = len(x)
    eccentricity = np.linspace(0.2, 0.7, n)
    found = elongation(_fits(np.full(n, 3.0), x, y, eccentricity, np.full(n, 30.0)))
    assert found is not None
    assert found.angle_deg == pytest.approx(150.0)
    assert found.coherence == pytest.approx(1.0)


def test_one_fit_coherence_never_rounds_past_one() -> None:
    """One fit at 0.95 degrees: hypot over the weight gave 1.0000000000000002, past the CHECK."""
    found = elongation(_fits(np.full(1, 3.0), np.zeros(1), np.zeros(1), [0.4], [0.95]))
    assert found is not None
    assert found.coherence <= 1.0


def test_crossed_elongations_have_no_coherence() -> None:
    """Half the stars at 0, half at 90 degrees, alike: the doubled angles cancel."""
    x, y = _field_of_stars()
    n = len(x)
    angle = np.where(np.arange(n) % 2 == 0, 0.0, 90.0)
    found = elongation(_fits(np.full(n, 3.0), x, y, np.full(n, 0.5), angle))
    assert found is not None
    assert found.coherence == pytest.approx(0.0, abs=1e-12)


def test_round_stars_or_none_have_no_elongation() -> None:
    x, y = _field_of_stars()
    assert elongation(_fits(np.full(len(x), 3.0), x, y, np.zeros(len(x)))) is None
    assert elongation(_fits(np.empty(0), np.empty(0), np.empty(0))) is None


def test_tilt_reaches_the_frame_through_measure() -> None:
    """Stars wider towards +x: tilt over 0; an even field near 0."""
    side, per_side = 900, 10
    data = _sky(side=side)
    for y, x in _grid(per_side, margin=30, side=side):
        _stars(data, [(y, x)], 1.8 + 0.6 * x / side, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.fwhm_tilt is not None and found.fwhm_tilt > 0.2
    flat = _sky(side=side)
    _stars(flat, _grid(per_side, margin=30, side=side), 2.0, 6e4)
    even = measure_frame(flat, saturation=65535.0, pattern=None)
    assert even.fwhm_tilt is not None and even.fwhm_tilt < 0.05
    assert even.fwhm_curvature is not None and abs(even.fwhm_curvature) < 0.05
    assert even.elongation_coherence is not None
