"""The new pipeline behind the app's scans, the one door from the old (ADR 0030): each folder
scanned and solved, nothing shown; a folder that cannot start is logged and skipped."""

import logging
import sqlite3
import threading
from collections.abc import Callable, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

from .. import astap
from ..clock import now_iso
from ..db.connect import connect
from .changes import add_root
from .scan import scan_root
from .solve import solve_root

log = logging.getLogger(__name__)


def run_roots(
    conn: sqlite3.Connection,
    paths: Sequence[str],
    now: str,
    solver: astap.Solver | str | None,
    where: tuple[Path, threading.Event | None],
) -> Iterator[dict[str, Any]]:
    """One event per folder, then `done`; the solver or its exe; the launch folder, the stop."""
    if not isinstance(solver, astap.Solver):
        solver = astap.Solver(solver)
    work, stop = where
    for number, path in enumerate(paths, 1):
        if stop is not None and stop.is_set():
            break
        try:
            root = add_root(conn, path, now)
            scan_root(conn, root, now, stop=stop)
            solve_root(conn, root, now, solver, work, stop=stop)
        except Exception:  # behind the scenes: the user's scan never breaks here
            log.warning("pipeline nuova: cartella saltata %s", path, exc_info=True)
        yield {"current": number, "total": len(paths)}
    yield {"done": True, "total": len(paths)}


type Exe = Callable[[sqlite3.Connection], str | None]


class Behind:
    """The new pipeline's own thread, one only, never the user's worker: nothing on screen waits
    on it. Folders kicked while it runs wait their turn; a stop kills its ASTAP, a kick goes on."""

    def __init__(self, db_path: str | Path, work: Path, exe: Exe) -> None:
        self._db_path, self._work, self._exe = db_path, work, exe
        self._lock = threading.Lock()
        self._pending: list[str] = []
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def kick(self, paths: Iterable[str]) -> None:
        with self._lock:
            self._pending += [p for p in paths if p not in self._pending]
            if self._stop.is_set():  # a new go: the round being stopped ends, then the queue runs
                self._stop = threading.Event()
            if self._thread is not None:
                return
            self._thread = threading.Thread(
                target=self._loop, name="astrolog-pipeline", daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        """Does not wait: a request asks it, the app's close then joins."""
        with self._lock:
            self._stop.set()

    def join(self, timeout: float | None = None) -> None:
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def _loop(self) -> None:
        try:
            while True:
                with self._lock:  # stopped or empty, gone in one step: a kick never finds it dying
                    stop = self._stop
                    if stop.is_set() or not self._pending:
                        self._thread = None
                        return
                    paths, self._pending = self._pending, []
                self._run(paths, stop)
        except Exception:
            log.exception("pipeline nuova: il giro e' caduto")
        finally:
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None

    def _run(self, paths: list[str], stop: threading.Event) -> None:
        conn = connect(self._db_path, check_same_thread=False)
        try:
            for _ in run_roots(conn, paths, now_iso(), self._exe(conn), (self._work, stop)):
                pass
        finally:
            conn.close()
