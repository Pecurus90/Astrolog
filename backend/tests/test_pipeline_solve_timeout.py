"""Mattone solve, ADR 0039: il tempo di ASTAP per lancio si impara dai lanci riusciti di questa
macchina, per modo (indizio o cieco); prima di 20 riusciti resta quello di sempre."""

import math
import platform
import random

import pytest

from astrolog.pipeline import timeouts
from astrolog.pipeline.scan import scan_root
from astrolog.pipeline.timeouts import Mode
from conftest import LATER, nina_light
from test_pipeline_solve import _SKY, FakeAstap, _scanned, _solutions, _solve


@pytest.mark.parametrize(
    ("df", "t"),
    [(1, 318.309), (2, 22.327), (5, 5.893), (10, 4.144), (19, 3.579), (30, 3.385), (120, 3.160)],
)
def test_the_student_quantile_matches_the_printed_table(df, t):
    """Quantile 0,999 a una coda, tavola della t di Student (Abramowitz & Stegun, tab. 26.10)."""
    assert timeouts.t_quantile(0.999, df) == pytest.approx(t, abs=2e-3)


def test_the_limit_is_the_prediction_bound_on_the_logs():
    """Hahn & Meeker 1991 pp. 61-62: media + t(n-1) s radice(1 + 1/n), qui sui logaritmi."""
    durations = [2.0, 3.0, 4.0, 5.0] * 5
    logs = [math.log(d) for d in durations]
    mean = sum(logs) / 20
    s = math.sqrt(sum((x - mean) ** 2 for x in logs) / 19)
    expected = math.exp(mean + timeouts.t_quantile(0.999, 19) * s * math.sqrt(1 + 1 / 20))
    assert timeouts.prediction_limit(durations) == pytest.approx(expected)


def test_the_limit_cuts_about_one_success_in_a_thousand():
    """Tempi lognormali: su 20.000 storie di 20 riusciti, il lancio dopo supera il limite circa
    20 volte (0,1%)."""
    rng = random.Random(7)
    cut = 0
    for _ in range(20_000):
        history = [math.exp(rng.gauss(1.5, 0.6)) for _ in range(20)]
        cut += math.exp(rng.gauss(1.5, 0.6)) > timeouts.prediction_limit(history)
    assert 5 <= cut <= 40


def test_before_twenty_successes_the_default_stays():
    assert timeouts.limit_of([5.0] * 19, [], default_s=60) == 60


def test_fast_successes_never_go_under_the_floor():
    assert timeouts.limit_of([1.0, 1.2, 0.9, 1.1] * 5, [], default_s=60) == timeouts.FLOOR_S


def test_slow_successes_raise_the_limit_and_a_failed_blind_caps_it():
    slow = [20.0, 30.0, 40.0, 50.0] * 5
    free = timeouts.limit_of(slow, [], default_s=60)
    assert free > 60
    assert timeouts.limit_of(slow, [70.0, 75.0], default_s=60) == 75.0


def test_a_launch_gets_the_time_learnt_on_this_machine_for_its_mode(conn, tmp_path):
    """Venti pose con indizio risolte in un attimo: la posa della passata dopo ha il pavimento,
    30 s; il tempo del lancio e la macchina restano scritti."""
    nas = tmp_path / "nas"
    for k in range(20):
        nina_light(nas / f"a{k:02}.fits", k + 1, _SKY)
    first, root = FakeAstap("solved.ini"), _scanned(conn, nas)
    _solve(conn, root, first, tmp_path)
    nina_light(nas / "a20.fits", 21, _SKY)
    scan_root(conn, root, LATER)
    later = FakeAstap("solved.ini")
    _solve(conn, root, later, tmp_path)
    assert first.timeouts == [60] * 20 and later.timeouts == [timeouts.FLOOR_S]
    rows = _solutions(conn)
    assert all(r["launch_s"] >= 0 and r["machine"] == platform.node() for r in rows)


def test_a_launch_cut_by_the_time_is_not_a_measured_failure(conn, tmp_path):
    """ASTAP interrotto non ha detto "no": il suo tempo e' il limite, e come tetto lo terrebbe
    fermo per sempre."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    _solve(conn, _scanned(conn, nas), FakeAstap("no_solution.ini", "timeout"), tmp_path)
    [row] = _solutions(conn)
    assert row["outcome"] == "no_solution" and row["step"] == "full_res"
    assert (row["launch_s"], row["machine"]) == (None, None)


def test_another_machine_or_mode_learns_nothing_from_these(conn, tmp_path):
    nas = tmp_path / "nas"
    for k in range(20):
        nina_light(nas / f"a{k:02}.fits", k + 1, _SKY)
    root = _scanned(conn, nas)
    _solve(conn, root, FakeAstap("solved.ini"), tmp_path)
    assert timeouts.limits(conn, "altra-macchina", 60) == {Mode.HINTED: 60, Mode.BLIND: 60}
    learnt = timeouts.limits(conn, platform.node(), 60)
    assert learnt == {Mode.HINTED: timeouts.FLOOR_S, Mode.BLIND: 60}
