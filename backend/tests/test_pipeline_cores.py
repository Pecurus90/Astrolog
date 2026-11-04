"""One frame on every core (cores.py, plan 26.57): the parallel ways give the one-core numbers."""

import contextlib
import threading
import time
from concurrent.futures import Future
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import shared_memory

import numpy as np
import pytest
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from astrolog import __main__ as entry
from astrolog.pipeline import cores, psf_fit
from astrolog.pipeline.median import median3x3
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


def test_the_3x3_median_goes_by_parts_on_a_tall_frame(monkeypatch) -> None:
    """Each part reads the rows past its own: no seam, the edge pixel repeated at the border."""
    monkeypatch.setattr(cores, "CORES", 4)
    calls = []
    real = cores.side_by_side
    monkeypatch.setattr(cores, "side_by_side", lambda *c: (calls.append(len(c)), real(*c))[1])
    image = _frame()
    whole = ndimage.median_filter(image, size=3, mode="nearest")
    assert np.array_equal(median3x3(image), whole)
    assert calls == [4]


def test_the_3x3_median_reads_big_endian_pixels_as_fits_holds_them() -> None:
    image = _frame(40, 30)
    assert np.array_equal(median3x3(image.astype(">f4")), median3x3(image))


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


class _Broken:
    """A pool whose worker died: every result raises, as ProcessPoolExecutor's then."""

    def submit(self, *_: object) -> Future:
        done: Future = Future()
        done.set_exception(BrokenProcessPool("a worker died"))
        return done

    def shutdown(self, **_: object) -> None:
        pass


def test_a_broken_pool_fits_on_one_core_and_starts_afresh_next_time(monkeypatch) -> None:
    plane, x, y, box, flux = _stars(60)
    alone = fit_stars(plane, x, y, box, flux)
    monkeypatch.setattr(psf_fit, "POOL_STARS", 1)
    monkeypatch.setattr(cores, "_pool", [_Broken()])
    pooled = fit_stars(plane, x, y, box, flux)
    assert np.allclose(pooled.signal, alone.signal, rtol=1e-9)
    assert cores._pool == []


def test_no_room_in_shared_memory_fits_on_one_core(monkeypatch) -> None:
    plane, x, y, box, flux = _stars(60)
    alone = fit_stars(plane, x, y, box, flux)
    monkeypatch.setattr(psf_fit, "POOL_STARS", 1)
    monkeypatch.setattr(cores, "_shared_room", lambda: 0)  # Docker's /dev/shm, 64 MB, full
    monkeypatch.setattr(cores, "_pool", [_Unused()])
    assert np.allclose(fit_stars(plane, x, y, box, flux).signal, alone.signal, rtol=1e-9)


class _Unused(_Broken):
    def submit(self, *_: object) -> Future:
        pytest.fail("no work to the processes without the memory")


def test_planes_shared_at_once_each_see_the_others_pages(monkeypatch) -> None:
    plane = np.zeros((1000, 1000), np.float32)  # 4 MB
    written: list[int] = []
    meet = threading.Barrier(3, timeout=0.5)  # unlocked, all three check before any writes

    def room() -> int:
        with contextlib.suppress(threading.BrokenBarrierError):
            meet.wait()
        return 10 * 2**20 - sum(written)  # room for two

    def created(**kwargs: object) -> shared_memory.SharedMemory:
        memory = real(**kwargs)  # type: ignore[arg-type]
        written.append(memory.size)  # its pages, as tmpfs counts them once written
        return memory

    def share() -> str:
        try:
            with cores.Shared(plane):
                time.sleep(0.3)
            return "shared"
        except OSError:
            return "one core"

    real = shared_memory.SharedMemory
    monkeypatch.setattr(cores.shared_memory, "SharedMemory", created)
    monkeypatch.setattr(cores, "_shared_room", room)
    assert sorted(cores.side_by_side(share, share, share)) == ["one core", "shared", "shared"]


def test_the_frozen_app_lets_spawned_workers_start_before_anything_else(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(entry.multiprocessing, "freeze_support", lambda: calls.append("freeze"))

    def stop(_: object) -> None:
        calls.append("logging")
        raise SystemExit

    monkeypatch.setattr(entry, "setup_logging", stop)
    with pytest.raises(SystemExit):
        entry.main()
    assert calls == ["freeze", "logging"]
