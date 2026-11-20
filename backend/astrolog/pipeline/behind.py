"""The pipeline's own thread, apart from the pipeline: the app starts without the measuring stack
(scipy, numba), loaded by the thread on its first round."""

import logging
import sqlite3
import threading
from collections.abc import Callable, Iterable
from pathlib import Path

from ..clock import now_iso
from ..db.connect import connect

log = logging.getLogger(__name__)

type Exe = Callable[[sqlite3.Connection], str | None]


class Behind:
    """The new pipeline's own thread, one only, never the user's worker: nothing on screen waits
    on it. Folders kicked while it runs wait their turn; a stop kills its ASTAP, a kick goes on."""

    def __init__(self, db_path: str | Path, work: Path, exe: Exe) -> None:
        self._db_path, self._work, self._exe = db_path, work, exe
        self._lock = threading.Lock()
        self._pending: list[str] = []
        self._sky = False  # the site's sky asked again
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def kick(self, paths: Iterable[str]) -> None:
        with self._lock:
            self._pending += [p for p in paths if p not in self._pending]
            if self._stop.is_set():  # a new go: the round being stopped ends, then the queue runs
                self._stop = threading.Event()
            self._start()

    def refresh_sky(self) -> None:
        """Sites, an answer on coordinates or a backup changed where frames go: the sites' sky is
        written again here, the door the app already has (ADR 0030). Not a scan: a stop holds."""
        with self._lock:
            self._sky = True
            self._start()

    def _start(self) -> None:
        """Under the lock."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="astrolog-pipeline", daemon=True)
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
                    paths = [] if stop.is_set() else self._pending
                    self._pending = self._pending if stop.is_set() else []
                    sky, self._sky = self._sky, False
                    if not paths and not sky:
                        self._thread = None
                        return
                if paths:
                    self._run(paths, stop)  # the sky at its end
                else:
                    self._rebuild_sky()
        except Exception:
            log.exception("pipeline nuova: il giro e' caduto")
        finally:
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None

    def _run(self, paths: list[str], stop: threading.Event) -> None:
        from . import run  # the measuring stack: here, not at the app's start

        conn = connect(self._db_path, check_same_thread=False)
        try:
            for _ in run.run_roots(conn, paths, now_iso(), self._exe(conn), (self._work, stop)):
                pass
        finally:
            conn.close()

    def _rebuild_sky(self) -> None:
        from . import run  # the measuring stack: here, not at the app's start

        conn = connect(self._db_path, check_same_thread=False)
        try:
            run.sky_of_sites(conn, now_iso())
        finally:
            conn.close()
