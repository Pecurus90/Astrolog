"""One frame on every core (plan 26.57, ADR 0042): stages side by side on threads, row strips of a
local filter on threads, per-star work in processes on shared pixels. Same numbers as one core."""

import atexit
import multiprocessing
import os
import sys
import threading
from collections.abc import Callable, Sequence
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import shared_memory
from multiprocessing.process import BaseProcess
from typing import Any

import numpy as np

from .capacity import physical_cores

# numpy and ndimage free the GIL on whole frames: 2.1-3.6x on 4 threads (sonde 26.57, gil57).
CORES = physical_cores() or 1
MIN_STRIP_ROWS = 256  # [T] thinner strips spend more on margins and threads than they save
MIN_PARALLEL_VALUES = 1_000_000  # [T] fewer: one partition is quicker than the threads
MEDIAN_SAMPLE = 100_000  # [T] values sorted to bracket the middle
MEDIAN_SAMPLE_SIGMAS = 6.0  # [T] the bracket misses once in ~1e9 frames, then np.median
SHM_DIR = "/dev/shm"  # noqa: S108 -- only its free space read. [D POSIX shm_open on Linux: a tmpfs mounted here]
_lock = threading.Lock()
_writing = threading.Lock()
_pool: list[Executor] = []


def side_by_side(*calls: Callable[[], Any]) -> list[Any]:
    """Each call on its own thread, results in order; an exception raises here."""
    if len(calls) < 2:
        return [call() for call in calls]
    with ThreadPoolExecutor(len(calls)) as threads:
        return [f.result() for f in [threads.submit(call) for call in calls]]


def each(fn: Callable[[Any], Any], items: Sequence[Any]) -> list[Any]:
    """`fn` on every item, CORES threads at most, results in order."""
    if len(items) < 2:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(min(CORES, len(items))) as threads:
        return list(threads.map(fn, items))


def by_strips(fn: Callable[[np.ndarray], np.ndarray], image: np.ndarray, margin: int) -> np.ndarray:
    """`fn` on row strips, each with `margin` rows more a side, cut back and joined. Exact for a
    filter reaching under `margin` rows that keeps the shape."""
    rows = image.shape[0]
    count = max(1, min(CORES, rows // max(MIN_STRIP_ROWS, 2 * margin)))
    if count == 1:
        return fn(image)
    edges = np.linspace(0, rows, count + 1).astype(int)

    def strip(k: int) -> np.ndarray:
        lo, hi = int(edges[k]), int(edges[k + 1])
        top = max(0, lo - margin)
        return fn(image[top : min(rows, hi + margin)])[lo - top : hi - top]

    return np.concatenate(side_by_side(*(lambda k=k: strip(k) for k in range(count))))


def median(values: np.ndarray) -> float:
    """float(np.median(values)), the same value: a sample brackets the middle, the cores count
    under it and gather between, a small partition ends it; NaN or a miss, np.median's own."""
    flat = values.ravel()
    n = flat.size
    if n < MIN_PARALLEL_VALUES:
        return float(np.median(flat))
    sample = np.sort(flat[:: max(1, n // MEDIAN_SAMPLE)])
    ranks = ((n - 1) // 2, n // 2)
    spread = MEDIAN_SAMPLE_SIGMAS * np.sqrt(sample.size) / 2 + 1  # binomial sd at the middle
    at = [ranks[0] / n * sample.size - spread, ranks[1] / n * sample.size + spread]
    lo, hi = (sample[int(np.clip(a, 0, sample.size - 1))] for a in at)
    parts = np.array_split(flat, CORES)
    tallies = side_by_side(*(lambda p=p: _bracketed(p, lo, hi) for p in parts))
    under = sum(t[0] for t in tallies)
    inside = np.concatenate([t[1] for t in tallies])
    over = sum(t[2] for t in tallies)
    first, last = ranks[0] - under, ranks[1] - under
    if under + inside.size + over != n or first < 0 or last >= inside.size:
        return float(np.median(flat))
    middle = np.partition(inside, (first, last))[[first, last]]
    return float(middle[0]) if n % 2 else float(np.mean(middle))


def _bracketed(part: np.ndarray, lo: float, hi: float) -> tuple[int, np.ndarray, int]:
    return (
        int(np.count_nonzero(part < lo)),
        part[(part >= lo) & (part <= hi)],
        int(np.count_nonzero(part > hi)),
    )


def processes() -> Executor:
    """The processes per-star work goes to, one per physical core, started once (spawn: the
    same on Windows, Mac and Linux)."""
    with _lock:
        if not _pool:
            context = multiprocessing.get_context("spawn")
            pool = ProcessPoolExecutor(CORES, mp_context=context, initializer=_die_with_parent)
            _pool.append(pool)
            atexit.register(_pool[0].shutdown, cancel_futures=True)
        return _pool[0]


def forget(broken: Executor) -> None:
    """Drop `broken`, a worker of it dead: the next processes() starts a new one. A newer pool,
    started meanwhile by another plane, stays."""
    with _lock:
        if _pool and _pool[0] is broken:
            _pool.clear()
    broken.shutdown(wait=False, cancel_futures=True)


def _die_with_parent() -> None:
    """In a worker: a watcher thread ends it when the app dies, even killed (no atexit then)."""
    parent = multiprocessing.parent_process()
    if parent is not None:
        threading.Thread(target=_exit_after, args=(parent,), daemon=True).start()


def _exit_after(parent: BaseProcess) -> None:
    parent.join()
    os._exit(1)


class Shared:
    """An array in shared memory, for processes to read without a copy; closed on exit. OSError
    when it does not fit: a full tmpfs kills the writer with SIGBUS, no exception."""

    def __init__(self, image: np.ndarray) -> None:
        with _writing:  # colour's three planes at once: each check sees the others' pages
            room = _shared_room()
            if room is not None and room < image.nbytes:
                raise OSError(f"shared memory: {room} bytes free, {image.nbytes} needed")
            self._memory = shared_memory.SharedMemory(create=True, size=max(1, image.nbytes))
            np.ndarray(image.shape, image.dtype, self._memory.buf)[...] = image
        self.ref = (self._memory.name, image.shape, image.dtype.str)

    def __enter__(self) -> "Shared":
        return self

    def __exit__(self, *_: object) -> None:
        self._memory.close()
        self._memory.unlink()


def _shared_room() -> int | None:
    """Bytes free in /dev/shm (Linux; Docker's is 64 MB); None elsewhere, the pagefile backs it."""
    if sys.platform != "linux" or not os.path.isdir(SHM_DIR):
        return None
    disk = os.statvfs(SHM_DIR)
    return disk.f_bavail * disk.f_frsize


def attached(ref: tuple[str, Sequence[int], str], fn: Callable[[np.ndarray], Any]) -> Any:
    """`fn` on the shared array `ref` names, in a worker; detached after."""
    name, shape, dtype = ref
    memory = shared_memory.SharedMemory(name=name)
    try:
        return fn(np.ndarray(tuple(shape), np.dtype(dtype), memory.buf))
    finally:
        memory.close()
