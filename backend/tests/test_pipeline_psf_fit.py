"""Each star's PSF as Image Analysis fits it (psf_fit.py, misure.md Forma): sampling region by
median stabilization, Moffat beta 4 at the pixel centres, refused fits, PSF residual. software-ok"""

import math

import numpy as np
import pytest

from astrolog.pipeline import psf_fit
from astrolog.pipeline.psf_fit import fit_stars, region, winsorized_mean

_SKY = 1000.0


def _star(side: int, centre: tuple[float, float], amplitude: float, sigma: float) -> np.ndarray:
    """A Moffat beta 4 sampled at the pixel centres, as the fit models it, on a flat sky."""
    ys, xs = np.mgrid[0:side, 0:side]
    q = ((xs - centre[0]) ** 2 + (ys - centre[1]) ** 2) / sigma**2
    return _SKY + amplitude * (1 + q) ** -psf_fit.BETA


def _box(x: float, y: float, half: int) -> np.ndarray:
    return np.array([round(x) - half, round(x) + half + 1, round(y) - half, round(y) + half + 1])


def test_an_exact_moffat_gives_back_its_widths_and_no_residual() -> None:
    plane = _star(81, (40.3, 39.6), 5000.0, 3.0)
    box = _box(40.3, 39.6, 3)[None]
    fits = fit_stars(plane, np.array([40.3]), np.array([39.6]), box, np.ones(1))
    assert fits.fwhm_px == pytest.approx([2 * 3.0 * math.sqrt(2 ** (1 / 4) - 1)], rel=1e-4)
    assert fits.eccentricity[0] < 0.01
    assert fits.residual[0] < 1e-4


def test_the_aperture_flux_holds_the_moffat_out_to_its_full_width_at_a_tenth() -> None:
    """PJSR PSF growth 1.0 in FWTM: the ellipse of semi-axes the FWTM holds 1 - (1 + 4 (10^(1/4)
    - 1))^(1 - beta) of a Moffat beta 4, the fitted sky off; the detected star carried along."""
    alpha, amplitude = 3.0, 5000.0
    plane = _star(81, (40.3, 39.6), amplitude, alpha)
    box = _box(40.3, 39.6, 3)[None]
    fits = fit_stars(plane, np.array([40.3]), np.array([39.6]), box, np.ones(1))
    total = math.pi * amplitude * alpha**2 / (psf_fit.BETA - 1)
    held = 1 - (1 + 4 * (10 ** (1 / psf_fit.BETA) - 1)) ** (1 - psf_fit.BETA)
    assert fits.aperture_flux[0] == pytest.approx(held * total, rel=0.01)
    assert fits.star.tolist() == [0]


def test_each_fit_knows_its_detected_star() -> None:
    plane = _star(81, (20.0, 20.0), 3000.0, 2.0) + _star(81, (60.0, 60.0), 6000.0, 2.0) - _SKY
    x, y = np.array([20.0, 60.0]), np.array([20.0, 60.0])
    boxes = np.array([_box(20, 20, 2), _box(60, 60, 2)])
    fits = fit_stars(plane, x, y, boxes, np.array([1.0, 2.0]))
    assert fits.star.tolist() == [1, 0]  # brightest first
    assert fits.rank.tolist() == [0, 1]


def test_the_residual_does_not_see_the_scale_and_grows_with_noise() -> None:
    """ImageAnalysis eq. 24: relative to the star's mean signal 4 S / (pi Wx Wy)."""
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 20, (81, 81))
    plane = _star(81, (40.0, 40.0), 2000.0, 3.0) + noise
    args = (np.array([40.0]), np.array([40.0]), _box(40, 40, 3)[None], np.ones(1))
    one = fit_stars(plane, *args).residual[0]
    ten = fit_stars(plane * 10, *args).residual[0]
    assert ten == pytest.approx(one, rel=1e-6)
    noisier = fit_stars(_star(81, (40.0, 40.0), 2000.0, 3.0) + 3 * noise, *args).residual[0]
    assert noisier > 2 * one


def test_the_region_grows_while_the_median_falls_and_stops_on_flat_sky() -> None:
    """PJSR PSF, Adaptive sampling region: half side the structure's larger side to start."""
    bright = _star(201, (100.0, 100.0), 60000.0, 4.0)
    rows, cols = region(bright, 100, 100, _box(100, 100, 2))
    assert rows.stop - rows.start == cols.stop - cols.start
    flat = np.full((201, 201), _SKY)
    rows_flat, _ = region(flat, 100, 100, _box(100, 100, 2))
    assert rows_flat.stop - rows_flat.start == 2 * 5 + 1  # larger side 5: no growth on flat sky
    assert rows.stop - rows.start > rows_flat.stop - rows_flat.start


def test_the_region_is_cut_by_the_frame_edge() -> None:
    plane = _star(60, (3.0, 30.0), 5000.0, 2.0)
    rows, cols = region(plane, 3, 30, _box(3, 30, 2))
    assert cols.start == 0 and rows.start >= 0


def test_a_fit_off_its_detected_structure_is_refused() -> None:
    """ImageWeighting par. 2.2.1: a centroid too far from the detected source is discarded."""
    ys, xs = np.mgrid[20:61, 20:61]
    pixels = (xs.ravel().astype(float), ys.ravel().astype(float))
    box = _box(34, 34, 1)  # columns and rows 33 to 35
    assert psf_fit._placed(34.2, 33.8, pixels, box)
    assert not psf_fit._placed(40.0, 40.0, pixels, box)  # inside the region, off the structure
    wide = np.array([18, 40, 30, 38])
    assert not psf_fit._placed(20.5, 34.0, pixels, wide)  # on the structure, at the region's edge


def test_the_signal_sums_only_the_pixels_over_the_sky() -> None:
    """ImageWeighting eq. 7: v_i > B. Three pixels in the ellipse, 5, 5 and -4 over B: S 10; one
    a pixel past the tenth, inside it grown by GROW_PX, counts; one far out does not."""
    sigma = 3.0
    tenth = sigma * math.sqrt(10 ** (1 / psf_fit.BETA) - 1)
    values = np.array([5.0, 5.0, -4.0, 7.0, 9.0])
    offsets = (np.array([0.0, 1.0, 0.0, tenth + 0.9, 30.0]), np.zeros(5))
    assert psf_fit._signal(values, offsets, (sigma, sigma, 0.0), 0.0) == pytest.approx(17.0)


def test_the_residual_is_over_the_mean_signal_of_the_fwtm_ellipse() -> None:
    """ImageAnalysis eq. 24: |v - f| all 2, so r = 2 / (4 S / (pi Wx Wy)), W the FWTM."""
    values = np.full(20, 7.0)
    sigma = 3.0
    wide = 2 * sigma * math.sqrt(10 ** (1 / psf_fit.BETA) - 1)
    r = psf_fit._residual(values, values - 2, 10.0, (wide, wide))
    assert r == pytest.approx(2 / (4 * 10 / (math.pi * wide * wide)))


def test_an_exact_moffat_gives_its_signal_and_its_mean_flux() -> None:
    """Signal: every pixel within the tenth radius plus GROW_PX (all over the sky); mean flux over
    the tenth ellipse's own area, ImageWeighting eq. 8-10."""
    sigma, centre = 3.0, (40.3, 39.6)
    plane = _star(81, centre, 5000.0, sigma)
    box = _box(*centre, 3)[None]
    fits = fit_stars(plane, np.array([centre[0]]), np.array([centre[1]]), box, np.ones(1))
    tenth = sigma * math.sqrt(10 ** (1 / psf_fit.BETA) - 1)
    ys, xs = np.mgrid[0:81, 0:81]
    inside = np.hypot(xs - centre[0], ys - centre[1]) <= tenth + psf_fit.GROW_PX
    signal = float((plane - _SKY)[inside].sum())
    assert fits.signal[0] == pytest.approx(signal, rel=1e-3)
    assert fits.mean_flux[0] == pytest.approx(signal / (math.pi * tenth * tenth), rel=1e-3)


def test_pure_noise_is_no_fit_and_no_crash() -> None:
    rng = np.random.default_rng(5)
    plane = _SKY + rng.normal(0, 10, (61, 61))
    fits = fit_stars(plane, np.array([30.0]), np.array([30.0]), _box(30, 30, 1)[None], np.ones(1))
    assert len(fits.fwhm_px) <= 1 and np.all(np.isfinite(fits.fwhm_px))


def test_the_brightest_are_fitted_first_up_to_the_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flux on the MAX_FLUX_FITS brightest (ImageCalibration maxStars), shape on the MAX_FITS
    brightest of them (ImageAnalysis maxPSFFits). software-ok"""
    monkeypatch.setattr(psf_fit, "MAX_FLUX_FITS", 2)
    monkeypatch.setattr(psf_fit, "MAX_FITS", 1)
    plane = np.full((60, 120), _SKY)
    xs = np.array([20.0, 60.0, 100.0])
    for x, amp in zip(xs, (1000.0, 8000.0, 4000.0), strict=True):
        plane += _star(120, (x, 30.0), amp, 2.5)[:60] - _SKY
    boxes = np.stack([_box(x, 30, 2) for x in xs])
    fits = fit_stars(plane, xs, np.full(3, 30.0), boxes, np.array([1.0, 8.0, 4.0]))
    assert len(fits.fwhm_px) == 2
    assert fits.signal[0] > fits.signal[1]  # 8000 then 4000
    brightest = fits.brightest()
    assert len(brightest.fwhm_px) == 1 and brightest.signal[0] == fits.signal[0]


def test_the_winsorized_mean_sets_each_tail_to_its_nearest_kept_value() -> None:
    values = np.arange(10, dtype=float)  # 10% a tail: 0 -> 1, 9 -> 8
    assert winsorized_mean(values) == pytest.approx((1 + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 8) / 10)
    assert winsorized_mean(np.array([3.0, 5.0])) == 4.0  # under 10 values nothing to cut
