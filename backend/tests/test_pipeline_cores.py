"""One frame on every core (cores.py, plan 26.57): the parallel ways give the one-core numbers."""

import numpy as np
import pytest
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from astrolog.pipeline import cores, psf_fit
from astrolog.pipeline.median import _median3x3, median3x3
from astrolog.pipeline.psf_fit import fit_stars

_RNG = np.random.default_rng(57)


def _frame(rows: int = 1300, cols: int = 90) -> np.ndarray:
    return _RNG.normal(100, 10, (rows, cols)).astype(np.float32)


def test_side_by_side_keeps_the_order_and_raises_what_a_call_raises() -> None:
    assert cores.side_by_side(lambda: 1, lambda: 2, lambda: 3) == [1, 2, 3]
    with pytest.raises(ZeroDivisionError):
        cores.side_by_side(lambda: 1, lambda: 1 / 0)


def test_each_keeps_the_order() -> None:
    assert cores.each(lambda v: v * 2, list(range(40))) == [v * 2 for v in range(40)]


@pytest.mark.parametrize(
    ("fn", "halo"),
    [
        (lambda a: ndimage.gaussian_filter(a, 5.27, mode="mirror", truncate=16 / 5.27), 16),
        (lambda a: ndimage.maximum_filter(a, 5, mode="constant", cval=-np.inf), 2),
        (_median3x3, 1),
    ],
)
def test_a_filter_by_strips_is_the_filter_on_the_whole_frame(fn, halo, monkeypatch) -> None:
    monkeypatch.setattr(cores, "CORES", 4)
    image = _frame()
    assert np.array_equal(cores.by_strips(fn, image, halo), fn(image))


def test_strips_without_their_halo_differ_so_the_check_above_sees_a_seam(monkeypatch) -> None:
    monkeypatch.setattr(cores, "CORES", 4)
    image = _frame()
    blur = lambda a: ndimage.gaussian_filter(a, 5.27, mode="mirror", truncate=16 / 5.27)  # noqa: E731
    assert not np.array_equal(cores.by_strips(blur, image, 4), blur(image))


def test_the_3x3_median_goes_by_strips_on_a_tall_frame(monkeypatch) -> None:
    monkeypatch.setattr(cores, "CORES", 4)
    calls = []
    real = cores.side_by_side
    monkeypatch.setattr(cores, "side_by_side", lambda *c: (calls.append(len(c)), real(*c))[1])
    image = _frame()
    assert np.array_equal(median3x3(image), _median3x3(image))
    assert calls == [4]


@pytest.mark.parametrize(
    "values",
    [
        _RNG.normal(100, 10, 1_000_001).astype(np.float32),  # odd: the middle value
        _RNG.normal(100, 10, (1000, 1200)).astype(np.float32),  # even: mean of two, float32
        _RNG.normal(0, 1, 1_200_000),
        _RNG.poisson(30, 1_200_000).astype(np.float32),  # many equal values in the bracket
        np.arange(1_200_000, dtype=np.float64),  # sorted: the strided sample is the order
        np.r_[_RNG.normal(0, 1, 1_200_000), np.nan],  # NaN: np.median's NaN
    ],
)
def test_the_median_on_every_core_is_numpy_s_to_the_bit(values) -> None:
    ours, numpy_s = cores.median(values), float(np.median(values))
    assert ours == numpy_s or (np.isnan(ours) and np.isnan(numpy_s))


def test_a_bracket_that_misses_the_middle_falls_back_to_numpy(monkeypatch) -> None:
    monkeypatch.setattr(cores, "MEDIAN_SAMPLE_SIGMAS", -1e6)  # a bracket of nothing
    values = _RNG.normal(0, 1, 1_200_000)
    assert cores.median(values) == float(np.median(values))


def _stars(count: int, side: int = 400) -> tuple[np.ndarray, ...]:
    ys, xs = np.mgrid[0:side, 0:side]
    plane = np.full((side, side), 1000.0) + _RNG.normal(0, 3, (side, side))
    x = _RNG.uniform(10, side - 10, count)
    y = _RNG.uniform(10, side - 10, count)
    flux = _RNG.uniform(500, 5000, count)
    for cx, cy, a in zip(x, y, flux, strict=True):
        near = (abs(xs - cx) < 8) & (abs(ys - cy) < 8)
        plane[near] += a * (1 + ((xs[near] - cx) ** 2 + (ys[near] - cy) ** 2) / 4) ** -4
    box = np.column_stack([x.round() - 2, x.round() + 3, y.round() - 2, y.round() + 3])
    return plane.astype(np.float32), x, y, box.astype(np.intp), flux


def test_stars_fitted_in_processes_are_those_fitted_on_one_core(monkeypatch) -> None:
    plane, x, y, box, flux = _stars(60)
    monkeypatch.setattr(psf_fit, "POOL_STARS", 10**9)
    alone = fit_stars(plane, x, y, box, flux)
    monkeypatch.setattr(psf_fit, "POOL_STARS", 1)
    monkeypatch.setattr(cores, "CORES", 2)
    monkeypatch.setattr(cores, "_pool", [])
    try:
        pooled = fit_stars(plane, x, y, box, flux)
    finally:
        for pool in cores._pool:
            pool.shutdown()
    assert len(alone.signal) > 30
    for name in ("fwhm_px", "signal", "residual", "x_px", "star", "rank"):
        assert np.allclose(getattr(pooled, name), getattr(alone, name), rtol=1e-9, equal_nan=True)
