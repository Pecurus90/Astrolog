"""The pipeline's own thread, apart from the pipeline: the app starts without the measuring stack
(scipy, numba), loaded by the thread on its first round."""

import logging
import sqlite3
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ..clock import now_iso
from ..db.connect import connect
from ..db.transaction import transaction
from .scan import ScanResult, Watch, scan_root

log = logging.getLogger(__name__)

type Exe = Callable[[sqlite3.Connection], str | None]
type Follow = Callable[[sqlite3.Connection], object]


@dataclass
class _Ask:
    """A scan the user waits on: served before the queue, on this thread (ADR 0030)."""

    root_id: int
    watch: Watch
    done: threading.Event = field(default_factory=threading.Event)
    result: ScanResult | None = None
    error: BaseException | None = None


class Behind:
    """The new pipeline's own thread, one only, never the user's worker: nothing on screen waits
    on it. Folders kicked while it runs wait their turn; a stop kills its ASTAP, a kick goes on."""

    # `follow`: what the app derives from sites, given by the app, run after the sites' sky
    def __init__(
        self, db_path: str | Path, work: Path, exe: Exe, follow: Follow | None = None
    ) -> None:
        self._db_path, self._work, self._exe, self._follow = db_path, work, exe, follow
        self._lock = threading.Lock()
        self._pending: list[int] = []  # root ids
        self._sky = False  # the site's sky asked again
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._asks: list[_Ask] = []
        self._scanning: set[int] = set()  # roots a user's scan holds, asked or running

    def scan_now(self, root_id: int, watch: Watch) -> ScanResult:
        """The user's scan, on this thread: the round in course yields (its ASTAP killed, its
        roots back in the queue), the scan runs, the queue goes on. Blocks the caller."""
        ask = _Ask(root_id, watch)
        with self._lock:
            self._asks.append(ask)
            self._scanning.add(root_id)
            if not self._stop.is_set():  # the round yields on its own event; a Stop after holds
                self._stop.set()
                self._stop = threading.Event()
            self._start()
        try:
            ask.done.wait()
        finally:
            with self._lock:
                self._scanning.discard(root_id)
        if ask.error is not None:
            raise ask.error
        assert ask.result is not None
        return ask.result

    def scanning(self, root_id: int) -> bool:
        """A user's scan holds the root: a second one is refused. Solving does not count."""
        with self._lock:
            return root_id in self._scanning

    def kick(self, root_ids: Iterable[int]) -> None:
        with self._lock:
            self._pending += [r for r in root_ids if r not in self._pending]
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
                    asks, self._asks = self._asks, []
                    stop = self._stop
                    roots = [] if stop.is_set() or asks else self._pending
                    self._pending = self._pending if stop.is_set() or asks else []
                    sky, self._sky = (False, self._sky) if asks else (self._sky, False)
                    if not asks and not roots and not sky:
                        self._thread = None
                        return
                if asks:
                    self._serve(asks)
                elif roots:
                    self._run(roots, stop)  # the sky at its end
                else:
                    self._rebuild_sky()
        except Exception:
            log.exception("pipeline nuova: il giro e' caduto")
        finally:
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None

    def _serve(self, asks: list[_Ask]) -> None:
        conn = connect(self._db_path, check_same_thread=False)
        try:
            for ask in asks:
                try:
                    ask.result = scan_root(conn, ask.root_id, now_iso(), watch=ask.watch)
                except BaseException as err:  # noqa: BLE001 - the caller raises it, in its thread
                    ask.error = err
                finally:
                    ask.done.set()
        finally:
            conn.close()

    def _run(self, roots: list[int], stop: threading.Event) -> None:
        from . import run  # the measuring stack: here, not at the app's start

        done = 0
        conn = connect(self._db_path, check_same_thread=False)
        try:
            for event in run.run_roots(conn, roots, now_iso(), self._exe(conn), (self._work, stop)):
                done = event.get("current", done)
            self._followed(conn)  # a sky asked with the folders was taken by this round
        finally:
            conn.close()
            with self._lock:  # yielded to a user's scan: what it did not reach waits its turn
                if self._asks:
                    left = [r for r in roots[max(0, done - 1) :] if r not in self._pending]
                    self._pending = left + self._pending

    def _rebuild_sky(self) -> None:
        from . import run  # the measuring stack: here, not at the app's start

        conn = connect(self._db_path, check_same_thread=False)
        try:
            run.sky_of_sites(conn, now_iso())
            self._followed(conn)
        finally:
            conn.close()

    def _followed(self, conn: sqlite3.Connection) -> None:
        if self._follow is None:
            return
        try:
            with transaction(conn):
                self._follow(conn)
        except Exception:  # behind the scenes, as the sites' sky
            log.warning("pipeline nuova: cio' che segue i siti non riscritto", exc_info=True)
