"""The new pipeline behind the app's scans, the one door from the old (ADR 0030): each folder
scanned, solved and measured, nothing shown; a folder that cannot start is logged and skipped."""

import logging
import sqlite3
import threading
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from .. import astap, night_measures
from ..db.transaction import transaction
from .changes import add_root
from .measure import measure_root
from .scan import scan_root
from .site_sky import rebuild
from .sky_measure import sky_root
from .solve import solve_root
from .sqm_measure import sqm_root

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
            measure_root(conn, root, now, stop=stop)
            sky_root(conn, root, now, stop=stop)
            sqm_root(conn, root, now, astap.catalogue_folder(solver), stop=stop)
        except Exception:  # behind the scenes: the user's scan never breaks here
            log.warning("pipeline nuova: cartella saltata %s", path, exc_info=True)
        yield {"current": number, "total": len(paths)}
    sky_of_sites(conn, now)
    _measures_of_nights(conn)
    yield {"done": True, "total": len(paths)}


def _measures_of_nights(conn: sqlite3.Connection) -> None:
    try:
        night_measures.rebuild(conn)
    except Exception:  # behind the scenes, as a folder
        log.warning("pipeline nuova: misure delle notti non riscritte", exc_info=True)


def sky_of_sites(conn: sqlite3.Connection, now: str) -> None:
    try:
        with transaction(conn):  # sites read under the lock: a move waits
            rebuild(conn, now)
    except Exception:  # behind the scenes, as a folder
        log.warning("pipeline nuova: cielo dei siti non riscritto", exc_info=True)
