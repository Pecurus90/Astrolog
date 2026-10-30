"""Measures across the frame (ADR 0022 point 5, ADR 0037, ADR 0041): saturated stars at the
declared full scale, PSF SNR, the sky gradient, tilt and curvature from five zones."""

import math

import numpy as np
import pytest

from astrolog.pipeline import stars
from astrolog.pipeline.field import (
    PSF_SNR_C3,
    PSF_SNR_C4,
    gradient_of,
    psf_snr,
    zones_of,
)
from astrolog.pipeline.shape import MIN_STARS
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


def test_psf_snr_gives_back_the_programs_own_value() -> None:
    """Its PSFFlux, Noise and PSFSNR on one frame (Shark n.0, ImageAnalysis = SubframeSelector):
    the formula with the documented constants returns its PSF SNR. software-ok"""
    assert psf_snr(2756.598924285991, 0.0010614623312019081) == pytest.approx(
        0.17797316030630608, rel=1e-4
    )


def test_the_frame_psf_snr_takes_the_stars_flux_with_no_scale() -> None:
    """Gaussian: 1 - 0.1 of the flux inside the tenth of the peak (psf_flux.py), 36 of 6e4. The
    structure over 3 sigma of its scales cuts the wings: moments, so the flux, 2.6% short. [M]"""
    data = _sky()
    _stars(data, _grid(6), 2.0, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    flux = 36 * 6e4 * 0.9
    assert found.psf_snr == pytest.approx(psf_snr(flux, _NOISE), rel=0.06)


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


def test_a_sky_on_a_plane_gives_its_spread_over_its_median_and_its_bright_side() -> None:
    """From 900 at the left to 1100 at the right, sampled at the mesh centres 32 and 608:
    200 (608 - 32) / 639 over 1000, brighter at +x."""
    cols = np.indices((640, 640))[1]
    back = (900 + 200 * cols / 639).astype(np.float32)
    gradient = gradient_of(back)
    assert gradient.pct == pytest.approx(100 * 200 * (608 - 32) / 639 / 1000, rel=0.01)
    assert _turn(gradient.angle_deg, 0.0) < 1.0


def _turn(angle: float | None, expected: float) -> float:
    assert angle is not None
    return abs((angle - expected + 180) % 360 - 180)


def test_the_bright_side_turns_with_the_plane() -> None:
    rows, cols = np.indices((640, 640))
    back = (1000 - 100 * cols / 639 + 100 * rows / 639).astype(np.float32)  # bright at -x, +y
    assert _turn(gradient_of(back).angle_deg, 135.0) < 1.0


def test_a_flat_sky_has_no_gradient_and_no_side() -> None:
    gradient = gradient_of(np.full((640, 640), 1000.0, dtype=np.float32))
    assert gradient.pct == pytest.approx(0.0, abs=1e-6)
    assert gradient.angle_deg is None


def test_a_sky_at_zero_or_under_has_no_gradient() -> None:
    """A calibrated frame's sky can sit at 0 or under: a share of nothing is no number."""
    cols = np.indices((640, 640))[1]
    gradient = gradient_of((cols / 639 - 0.6).astype(np.float32))
    assert gradient.pct is None


def test_the_gradient_reaches_the_frame_through_measure() -> None:
    cols = np.indices((_SIDE, _SIDE))[1]
    data = _sky() + (200 * cols / (_SIDE - 1) - 100).astype(np.float32)
    _stars(data, _grid(6), 2.0, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert found.gradient_pct == pytest.approx(18.0, rel=0.15)
    assert _turn(found.gradient_angle_deg, 0.0) < 5.0


# Tilt and curvature


def _zone_stars(
    hfd_of, per_zone: int = 25, spread: float = 0.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """`per_zone` stars in each of the 3x3 cells of a 900 px frame, HFD given by the cell, each
    star off it by `spread` relative, the same pattern in every cell (a flat sensor stays flat)."""
    xs, ys, hfds = [], [], []
    offsets = np.random.default_rng(3).normal(0, spread, per_zone)
    for row in range(3):
        for col in range(3):
            for k in range(per_zone):
                xs.append(col * 300 + 20 + (260 * k) // per_zone)
                ys.append(row * 300 + 150)
                hfds.append(hfd_of(row, col) * (1 + offsets[k]))
    return np.array(hfds, float), np.array(xs, float), np.array(ys, float)


def test_tilt_is_worst_less_best_corner_over_the_median_hfd() -> None:
    """ASTAP: 100 (worst - best corner) / median HFD. Corners 3.0, 3.3, 3.6, 3.0; rest 3.0."""
    corners = {(0, 0): 3.0, (0, 2): 3.3, (2, 0): 3.6, (2, 2): 3.0}
    hfd, x, y = _zone_stars(lambda r, c: corners.get((r, c), 3.0))
    zones = zones_of(hfd, x, y, (900, 900))
    assert zones is not None
    assert zones.tilt_pct == pytest.approx(100 * 0.6 / 3.0)


def test_curvature_is_corners_against_the_centre_with_its_sign() -> None:
    """Corners 3.6, centre 3.0, the median 3.6: 100 (3.6 - 3.0) / 3.6. Centre worse: negative."""
    hfd, x, y = _zone_stars(lambda r, c: 3.0 if (r, c) == (1, 1) else 3.6)
    zones = zones_of(hfd, x, y, (900, 900))
    assert zones is not None
    assert zones.curvature_pct == pytest.approx(100 * 0.6 / 3.6)
    assert zones.tilt_pct == pytest.approx(0.0)
    hfd, x, y = _zone_stars(lambda r, c: 4.0 if (r, c) == (1, 1) else 3.0)
    flipped = zones_of(hfd, x, y, (900, 900))
    assert flipped is not None
    assert flipped.curvature_pct == pytest.approx(-100 * 1.0 / 3.0)


def test_the_stars_a_zone_needs_follow_the_frame_s_own_hfd_spread() -> None:
    """Four corner medians on a flat sensor stay inside ASTAP's first tilt band (5%) when
    d2(4) sqrt(pi/2) s / sqrt(n) is under it: s 2% asks 2 stars, s 20% asks 107."""
    tight = _zone_stars(lambda r, c: 3.0, per_zone=10, spread=0.02)
    assert zones_of(*tight, (900, 900)) is not None
    loose = _zone_stars(lambda r, c: 3.0, per_zone=50, spread=0.20)
    assert zones_of(*loose, (900, 900)) is None
    assert zones_of(*_zone_stars(lambda r, c: 3.0, per_zone=120, spread=0.20), (900, 900))


def test_never_under_min_stars_a_zone() -> None:
    hfd, x, y = _zone_stars(lambda r, c: 3.0, per_zone=MIN_STARS)
    lonely = np.ones(len(x), dtype=bool)
    lonely[np.flatnonzero((x < 300) & (y < 300))[0]] = False  # one corner a star short
    assert zones_of(hfd[lonely], x[lonely], y[lonely], (900, 900)) is None


def test_tilt_reaches_the_frame_through_measure() -> None:
    """Wider stars in one corner of a measured frame: tilt over 0, flat field near 0."""
    side, per_side = 900, 18  # 36 stars a cell
    data = _sky(side=side)
    for y, x in _grid(per_side, margin=30, side=side):
        _stars(data, [(y, x)], 2.4 if (y < 300 and x < 300) else 2.0, 6e4)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert isinstance(found, Measured)
    assert found.tilt_pct == pytest.approx(100 * 0.4 / 2.0, rel=0.25)
    flat = _sky(side=side)
    _stars(flat, _grid(per_side, margin=30, side=side), 2.0, 6e4)
    even = measure_frame(flat, saturation=65535.0, pattern=None)
    assert isinstance(even, Measured)
    assert even.tilt_pct is not None
    assert even.tilt_pct < 3.0
    assert math.isfinite(even.curvature_pct or 0.0)
