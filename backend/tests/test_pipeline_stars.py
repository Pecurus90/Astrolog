"""Measure of one frame on synthetic stars of known shape (ADR 0022): background, noise, stars,
HFD. Stars integrated on the pixel, as a sensor sees them; the HFD of a shape is analytic."""

import math
import tracemalloc

import numpy as np
import pytest

from astrolog.pipeline.shape import SIGMA_TO_FWHM
from astrolog.pipeline.stars import (
    MIN_STARS,
    ROOM_FWHM,
    Measured,
    TooFewStars,
    _kept,  # pyright: ignore[reportPrivateUsage] -- the check itself, without sep
    measure_frame,
    median3x3,
)

_SIDE = 600
_BACKGROUND = 1000.0
_NOISE = 10.0
_SUB = 5  # samples per pixel side: the star integrated on the pixel


def _gaussian_hfd(sigma: float) -> float:
    return 2 * sigma * math.sqrt(2 * math.log(2))


def _moffat_hfd(alpha: float, beta: float) -> float:
    return 2 * alpha * math.sqrt(2 ** (1 / (beta - 1)) - 1)


def _true_hfd(shape: str, width: float, beta: float = 2.5) -> float:
    """HFD of the star as the sensor holds it: its pixels, each flat over its square. Small stars
    come out wider than the analytic shape (+3% at sigma 1.8): the pixel, not the method."""
    stamp = _stamp(12 * width, shape, width, beta)
    fine = np.repeat(np.repeat(stamp, 16, axis=0), 16, axis=1)
    centre = (fine.shape[0] - 1) / 2
    rows, cols = np.indices(fine.shape)
    radius = (np.hypot(rows - centre, cols - centre) / 16).ravel()
    order = np.argsort(radius)
    enclosed = np.cumsum(fine.ravel()[order])
    return 2 * float(np.interp(enclosed[-1] / 2, enclosed, radius[order]))


def test_the_truth_is_the_analytic_hfd_once_the_pixel_is_small() -> None:
    assert _true_hfd("gauss", 4.0) == pytest.approx(_gaussian_hfd(4.0), rel=0.005)
    assert _true_hfd("moffat", 6.0, 2.5) == pytest.approx(_moffat_hfd(6.0, 2.5), rel=0.01)


def _stamp(radius: float, shape: str, width: float, beta: float) -> np.ndarray:
    """A unit-flux star centred at (radius, radius) in a (2r+1)^2 stamp, integrated on pixels."""
    side = 2 * int(radius) + 1
    fine = (np.arange(side * _SUB) + 0.5) / _SUB - 0.5 - int(radius)
    yy, xx = np.meshgrid(fine, fine, indexing="ij")
    r2 = xx**2 + yy**2
    if shape == "gauss":
        profile = np.exp(-r2 / (2 * width**2))
    else:
        profile = (1 + r2 / width**2) ** -beta
    binned = profile.reshape(side, _SUB, side, _SUB).sum(axis=(1, 3))
    return binned / binned.sum()


def _field(
    shape: str = "gauss",
    width: float = 2.0,
    beta: float = 2.5,
    count: int = 60,
    flux: float = 60000.0,
    seed: int = 1,
) -> np.ndarray:
    """Stars on a grid, far apart, on a flat sky with Gaussian noise."""
    rng = np.random.default_rng(seed)
    data = np.full((_SIDE, _SIDE), _BACKGROUND)
    stamp = _stamp(12 * width, shape, width, beta)
    half = stamp.shape[0] // 2
    per_side = math.ceil(math.sqrt(count))
    step = (_SIDE - 2 * 60) // max(per_side - 1, 1)
    placed = 0
    for row in range(per_side):
        for col in range(per_side):
            if placed == count:
                break
            y, x = 60 + row * step, 60 + col * step
            data[y - half : y + half + 1, x - half : x + half + 1] += flux * stamp
            placed += 1
    data += rng.normal(0, _NOISE, data.shape)
    return data.astype(np.float32)


def _measured(data: np.ndarray, *, pattern: str | None = None) -> Measured:
    result = measure_frame(data, saturation=65535.0, pattern=pattern)
    assert isinstance(result, Measured), result
    return result


@pytest.mark.parametrize("sigma", [1.8, 2.5, 4.0])
def test_the_hfd_of_gaussian_stars_is_the_diameter_holding_half_the_flux(sigma: float) -> None:
    measured = _measured(_field("gauss", sigma))
    assert measured.hfd_px == pytest.approx(_true_hfd("gauss", sigma), rel=0.03)


@pytest.mark.parametrize(("alpha", "beta"), [(2.5, 2.5), (3.0, 4.5)])
def test_the_hfd_of_moffat_stars_holds_their_wings(alpha: float, beta: float) -> None:
    measured = _measured(_field("moffat", alpha, beta))
    assert measured.hfd_px == pytest.approx(_true_hfd("moffat", alpha, beta), rel=0.03)


def test_background_and_noise_are_the_sky_and_its_spread() -> None:
    measured = _measured(_field())
    assert measured.background_adu == pytest.approx(_BACKGROUND, abs=1.0)
    assert measured.noise_adu == pytest.approx(_NOISE, rel=0.03)


def test_every_star_is_counted_once() -> None:
    assert _measured(_field(count=49)).stars == 49


def test_hot_pixels_are_not_stars() -> None:
    data = _field(count=25)
    rng = np.random.default_rng(7)
    ys, xs = rng.integers(5, _SIDE - 5, 400), rng.integers(5, _SIDE - 5, 400)
    data[ys, xs] = 60000.0  # single pixels, as an uncalibrated light has them
    measured = _measured(data)
    assert measured.stars == 25
    assert measured.hfd_px == pytest.approx(_true_hfd("gauss", 2.0), rel=0.03)


def test_saturated_stars_are_counted_but_not_measured() -> None:
    data = _field(count=36)
    clipped = _field(count=36, flux=4e6)  # same places, cores far over the ceiling
    data[:, : _SIDE // 2] = np.minimum(clipped[:, : _SIDE // 2], 65535.0)
    measured = _measured(data)
    assert measured.stars == 36
    assert measured.kept == 18  # only the right half
    assert measured.hfd_px == pytest.approx(_true_hfd("gauss", 2.0), rel=0.03)


def test_a_frame_without_enough_stars_says_so_and_keeps_the_count() -> None:
    result = measure_frame(_field(count=MIN_STARS - 1), saturation=65535.0, pattern=None)
    assert isinstance(result, TooFewStars)
    assert result.stars == MIN_STARS - 1
    flat = measure_frame(_field(count=0), saturation=65535.0, pattern=None)
    assert isinstance(flat, TooFewStars)
    assert flat.stars == 0


def _mosaic(r: float, g: float, b: float) -> np.ndarray:
    return np.tile(np.array([[r, g], [g, b]], dtype=np.float32), (_SIDE // 2, _SIDE // 2))


@pytest.mark.parametrize("sigma", [1.2, 3.0])
def test_a_colour_frame_is_measured_after_vng_in_sensor_pixels(sigma: float) -> None:
    """Small stars were the 2x2 superpixel's undoing: frame 15 of the 24 (Canon 700D) read HFD
    6.94 px against ASTAP's 3.97; here 16% over the truth at sigma 1.2, VNG 3%."""
    measured = _measured(_field("gauss", sigma) * _mosaic(0.82, 1.0, 0.83), pattern="RGGB")
    assert measured.hfd_px == pytest.approx(_true_hfd("gauss", sigma), rel=0.05)
    assert measured.stars == 60


def test_colour_noise_is_the_mid_of_the_cfa_channels_as_pixinsight_says_it() -> None:
    """Debayer's noise per CFA plane (the two greens averaged), then SubframeSelector's (min +
    max) / 2 (PCL): sensor noise 10, 20, 30 ADU gives R 10, G 20 / sqrt 2, B 30, so 20."""
    rng = np.random.default_rng(5)
    rows, cols = np.indices((_SIDE, _SIDE))
    total = np.array([[10.0, 20.0], [20.0, 30.0]])[rows % 2, cols % 2]
    extra = np.sqrt(total**2 - _NOISE**2)  # on top of the field's own
    data = _field(count=36) + (rng.normal(0, 1, total.shape) * extra).astype(np.float32)
    assert _measured(data, pattern="RGGB").noise_adu == pytest.approx(20.0, rel=0.03)


def test_a_colour_star_clipped_in_one_channel_is_saturated() -> None:
    """Green clipped, red and blue not: the sensor pixel is looked at, not the debayered one."""
    pattern = _mosaic(1.0, 1.4, 0.7)
    data = _field("gauss", 3.0, count=36) * pattern
    bright = _field("gauss", 3.0, count=36, flux=2.8e6) * pattern  # green core about 70000
    data[:, : _SIDE // 2] = np.minimum(bright[:, : _SIDE // 2], 65535.0)
    assert _measured(data, pattern="RGGB").kept == 18


def test_a_nebula_under_the_stars_is_sky_the_ring_follows() -> None:
    """Patches of nebula finer than sep's 64-pixel sky mesh: with the mesh alone the HFD reads
    37% low, with the ring 4%; injected stars on a real Rosette frame came back within 1%."""
    data = _field("gauss", 2.0, count=49)
    rows, cols = np.indices(data.shape)
    for y in range(100, 600, 80):  # between the stars, 57 pixels from each
        for x in range(100, 600, 80):
            data += 3000 * np.exp(-((rows - y) ** 2 + (cols - x) ** 2) / (2 * 40**2))
    assert _measured(data).hfd_px == pytest.approx(_true_hfd("gauss", 2.0), rel=0.06)


def _detections(count: int, side: int, seed: int) -> np.ndarray:
    """Fake sep detections, uniform on the field: round, unflagged, 2 px wide."""
    rng = np.random.default_rng(seed)
    kinds = [("x", "f8"), ("y", "f8"), ("a", "f8"), ("b", "f8"), ("flag", "i4"), ("flux", "f8")]
    objects = np.zeros(count, dtype=kinds)
    objects["x"], objects["y"] = rng.uniform(0, side, count), rng.uniform(0, side, count)
    objects["a"], objects["b"], objects["flux"] = 1.0, 0.9, 1.0
    return objects


def test_a_star_with_a_neighbour_closer_than_its_room_is_dropped() -> None:
    objects = _detections(800, 600, seed=5)
    raw = np.zeros((600, 600), dtype=np.float32)
    room = ROOM_FWHM * SIGMA_TO_FWHM * np.sqrt(objects["a"] * objects["b"])
    gap = np.hypot(*(objects[k][:, None] - objects[k][None, :] for k in ("x", "y")))
    np.fill_diagonal(gap, np.inf)
    x, y = objects["x"], objects["y"]
    inside = (x > room) & (y > room) & (x < 599 - room) & (y < 599 - room)
    expected = np.flatnonzero(inside & (gap.min(axis=1) > room))
    assert 0 < len(expected) < inside.sum()  # the field has crowded stars and lone ones
    assert np.array_equal(_kept(raw, objects, 65535.0), expected)


def test_a_dense_field_is_checked_without_a_table_of_every_pair() -> None:
    """20000 detections: a full distance table is 3.2 GB; the check stays under 64 MB."""
    objects = _detections(20_000, 6000, seed=6)
    raw = np.zeros((6000, 6000), dtype=np.float32)
    tracemalloc.start()
    _kept(raw, objects, 65535.0)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert peak < 64 * 2**20


def test_a_frame_of_one_adu_steps_has_no_stars_in_its_steps() -> None:
    """MAD 0 on a quantized sky: without the floor the noise is 0 and every step is a star."""
    rng = np.random.default_rng(1)
    data = (1000 + (rng.random((_SIDE, _SIDE)) < 0.1)).astype(np.float32)
    result = measure_frame(data, saturation=65535.0, pattern=None)
    assert isinstance(result, TooFewStars)
    assert result.noise_adu >= 1 / math.sqrt(12)


def test_the_median_filter_is_the_exact_3x3_median() -> None:
    rng = np.random.default_rng(3)
    data = rng.normal(100, 30, (41, 37)).astype(np.float32)
    padded = np.pad(data, 1, mode="symmetric")
    windows = [padded[dy : dy + 41, dx : dx + 37] for dy in range(3) for dx in range(3)]
    assert np.array_equal(median3x3(data), np.median(np.stack(windows), axis=0))
