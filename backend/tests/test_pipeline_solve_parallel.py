"""Mattone solve, ASTAP 9 (D7, ADR 0033): ASTAP in parallelo su meta' dei core fisici, mai oltre
un quarto della RAM; scrive uno solo; allo stop i processi figli muoiono; una passata per radice."""

import os
import sys
import threading
import time

import pytest

from astrolog import astap
from astrolog.pipeline import capacity
from astrolog.pipeline.scan import ScanRunningError, busy
from astrolog.pipeline.solve import solve_root
from conftest import LATER, nina_light
from test_pipeline_solve import _SKY, FakeAstap, _scanned, _solutions

_GIB = 2**30
_V1 = {
    "memory/memory.limit_in_bytes": "536870912",
    "cpu/cpu.cfs_quota_us": "200000",
    "cpu/cpu.cfs_period_us": "100000",
}
_SPAWN = astap._spawn  # the real one, before the suite's fence: here it starts Python, not ASTAP


@pytest.mark.parametrize(
    ("cores", "ram", "workers"),
    [(16, 64 * _GIB, 8), (16, 2 * _GIB, 3), (1, 64 * _GIB, 1), (4, 64 * _GIB, 2), (8, 0, 1)],
)
def test_half_the_physical_cores_never_past_a_quarter_of_the_ram(cores, ram, workers):
    """160 MB per ASTAP (D7): 2 GiB / 4 = 512 MB, tre processi."""
    assert capacity.workers(cores, ram, logical=None) == workers


def test_unknown_physical_cores_count_half_the_logical_ones():
    """Senza il conto dei core fisici: i logici a meta' (due thread per core), poi la meta'."""
    assert capacity.workers(None, 64 * _GIB, logical=16) == 4
    assert capacity.workers(None, None, logical=None) == 1


@pytest.mark.parametrize(
    ("files", "memory", "cpus"),
    [
        ({}, None, None),
        ({"memory.max": "max", "cpu.max": "max 100000"}, None, None),  # v2, no limit
        ({"memory.max": "536870912", "cpu.max": "250000 100000"}, 536870912, 3),  # v2: 2,5 cpu
        (_V1, 536870912, 2),  # v1, older kernels
        ({"cpu/cpu.cfs_quota_us": "-1", "cpu/cpu.cfs_period_us": "100000"}, None, None),
    ],
)
def test_a_container_says_its_limits_old_kernel_or_new(tmp_path, files, memory, cpus):
    """Docker sul NAS: `--memory` e `--cpus` contano piu' della macchina."""
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="ascii")
    assert capacity.cgroup_memory(tmp_path) == memory
    assert capacity.cgroup_cpus(tmp_path) == cpus


def test_this_machine_says_its_cores_and_ram():
    cores, ram = capacity.physical_cores(), capacity.total_ram()
    assert cores is None or 1 <= cores <= (os.cpu_count() or cores)
    assert ram is None or ram > 256 * 2**20


def _many(conn, tmp_path, n: int) -> int:
    nas = tmp_path / "nas"
    for k in range(n):
        nina_light(nas / f"a{k:02}.fits", k + 1, _SKY)
    return _scanned(conn, nas)


def _counted(conn, root: int, tmp_path, workers: int):
    """Solved with a fake that counts the launches at once; returns the peak and the result."""
    fake, lock = FakeAstap("solved.ini"), threading.Lock()
    running = peak = 0

    def run(cmd, timeout_s):
        nonlocal running, peak
        if "-h" in cmd:
            return fake(cmd, timeout_s)
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.2)
        with lock:
            running -= 1
        return fake(cmd, timeout_s)

    solver = astap.Solver("astap_cli", run, databases=tmp_path / "db")
    result = solve_root(conn, root, LATER, solver, tmp_path / "work", workers=workers)
    return peak, result


def test_launches_run_side_by_side_and_one_writes(conn, tmp_path):
    """Otto pose, quattro alla volta; la connessione rifiuta un altro thread: scrive chi chiama."""
    peak, result = _counted(conn, _many(conn, tmp_path, 8), tmp_path, 4)
    assert peak == 4 and result.solved == 8
    assert [r["outcome"] for r in _solutions(conn)] == ["solved"] * 8


def test_blind_shots_with_no_sister_to_ask_run_side_by_side_too(conn, tmp_path):
    """Senza OBJECT ne' camera nessuna sorella presta niente: aspettare non serve, e sono le
    ricerche cieche, le piu' lente."""
    nas = tmp_path / "nas"
    for k in range(6):
        nina_light(nas / f"b{k}.fits", k + 1)
    peak, _result = _counted(conn, _scanned(conn, nas), tmp_path, 4)
    assert peak == 4


def test_a_launch_that_breaks_kills_the_others_before_it_is_raised(conn, tmp_path, monkeypatch):
    """Tre processi veri che dormirebbero 30 s: un altro lancio rompe, loro muoiono subito."""
    import astrolog.pipeline.solve as solve

    def spawn(cmd):
        slow = any(name in " ".join(cmd) for name in ("a01", "a02", "a04"))
        return _SPAWN([sys.executable, "-c", "import time; time.sleep(30)" if slow else "pass"])

    real_try = solve._try

    def broken(path, *rest):
        if path.name == "a03.fits":
            raise RuntimeError("rotto")
        return real_try(path, *rest)

    monkeypatch.setattr(astap, "_spawn", spawn)
    monkeypatch.setattr(solve, "_try", broken)
    root = _many(conn, tmp_path, 6)
    start = time.monotonic()
    with pytest.raises(RuntimeError, match="rotto"):
        solve_root(conn, root, LATER, astap.Solver("astap_cli", databases=tmp_path / "db"),
                   tmp_path / "work", workers=4)  # fmt: skip
    assert time.monotonic() - start < 10


def test_a_stop_writes_nothing_more_and_launches_nothing_more(conn, tmp_path):
    """Fermata a meta': il primo lancio, da solo, e' scritto; i due in corso no (un processo
    ucciso non e' un esito); le pose restanti non partono e restano per la passata dopo."""
    root = _many(conn, tmp_path, 6)
    fake, stop, release = FakeAstap("solved.ini"), threading.Event(), threading.Event()
    started = threading.Semaphore(0)

    def run(cmd, timeout_s):
        if "-h" not in cmd and fake.commands:
            started.release()
            release.wait(10.0)
        return fake(cmd, timeout_s)

    def stopper():
        started.acquire(timeout=10.0)
        started.acquire(timeout=10.0)
        stop.set()
        release.set()

    threading.Thread(target=stopper, daemon=True).start()
    solver = astap.Solver("astap_cli", run, databases=tmp_path / "db")
    result = solve_root(conn, root, LATER, solver, tmp_path / "work", workers=2, stop=stop)
    assert len(fake.commands) == 3 and result.solved == 1
    assert [r["outcome"] for r in _solutions(conn)] == ["solved"]


def test_a_stop_kills_the_running_children(monkeypatch):
    """Un processo vero che dormirebbe 30 s: ucciso, la chiamata torna subito."""
    monkeypatch.setattr(astap, "_spawn", _SPAWN)
    launcher = astap.Launcher()
    done = []

    def sleeper():
        done.append(launcher([sys.executable, "-c", "import time; time.sleep(30)"], 60))

    thread = threading.Thread(target=sleeper)
    start = time.monotonic()
    thread.start()
    while not launcher.running() and time.monotonic() - start < 10:
        time.sleep(0.01)
    launcher.kill()
    thread.join(10.0)
    assert done and done[0][0] != 0 and time.monotonic() - start < 10


def test_one_pass_per_root_shares_the_scan_lock(conn, tmp_path):
    root = _many(conn, tmp_path, 1)
    with busy(root), pytest.raises(ScanRunningError):
        solve_root(conn, root, LATER, astap.Solver("astap_cli", FakeAstap("solved.ini")),
                   tmp_path / "work")  # fmt: skip
