"""La pipeline nuova dietro le scansioni dell'app: ogni cartella letta e risolta, niente a
schermo; una cartella che non parte e' scritta nel log e saltata."""

import threading

from astrolog import astap
from astrolog.pipeline import run as run_module
from astrolog.pipeline.run import Behind, run_roots
from conftest import NOW, nina_light
from test_pipeline_solve import _SKY, FakeAstap, _solutions


def _solver(tmp_path):
    return astap.Solver("astap_cli", FakeAstap("solved.ini"), databases=tmp_path / "db")


def test_each_folder_is_scanned_and_solved_and_a_missing_one_is_skipped(conn, tmp_path, caplog):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    paths = [str(tmp_path / "gone"), str(nas)]
    events = list(run_roots(conn, paths, NOW, _solver(tmp_path), (tmp_path / "work", None)))
    assert events[-1] == {"done": True, "total": 2}
    assert [e["current"] for e in events[:-1]] == [1, 2]
    assert [r["outcome"] for r in _solutions(conn)] == ["solved"]
    assert "gone" in caplog.text


def _behind(db_path, tmp_path):
    return Behind(db_path, tmp_path / "work", lambda conn: None)  # no ASTAP: reads, then stops


def test_behind_runs_on_its_own_thread_and_folders_kicked_meanwhile_wait(
    conn, db_path, tmp_path, monkeypatch
):
    gate, seen = threading.Event(), []
    real = run_module.run_roots

    def slow(conn_, paths, *rest):
        seen.append(list(paths))
        gate.wait(10.0)
        yield from real(conn_, paths, *rest)

    monkeypatch.setattr(run_module, "run_roots", slow)
    for name in ("a", "b"):
        nina_light(tmp_path / name / "x.fits", ord(name))
    behind = _behind(db_path, tmp_path)
    behind.kick([str(tmp_path / "a")])
    behind.kick([str(tmp_path / "b"), str(tmp_path / "a")])
    gate.set()
    behind.join(10.0)
    # `a` kicked again while it ran: a scan may have brought new files, it runs again
    assert seen == [[str(tmp_path / "a")], [str(tmp_path / "b"), str(tmp_path / "a")]]
    assert conn.execute("SELECT count(*) FROM pipeline_files").fetchone()[0] == 2


def test_a_stopped_behind_starts_again_at_the_next_kick(conn, db_path, tmp_path):
    nina_light(tmp_path / "a" / "x.fits", 1)
    behind = _behind(db_path, tmp_path)
    behind.stop()
    behind.kick([str(tmp_path / "a")])
    behind.join(10.0)
    assert conn.execute("SELECT count(*) FROM pipeline_files").fetchone()[0] == 1


def test_a_stop_before_a_folder_leaves_it_for_next_time(conn, tmp_path):
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, _SKY)
    stop = threading.Event()
    stop.set()
    events = list(run_roots(conn, [str(nas)], NOW, _solver(tmp_path), (tmp_path / "work", stop)))
    assert events == [{"done": True, "total": 1}] and _solutions(conn) == []
