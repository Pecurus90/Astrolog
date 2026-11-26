"""The new pipeline behind the app's scans, the one door from the old (ADR 0030): each folder
scanned, solved and measured, nothing shown; a folder that cannot start is logged and skipped."""

import logging
import os
import sqlite3
import threading
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from .. import astap, night_measures
from ..db.transaction import transaction
from .measure import measure_root
from .scan import MIN_AGE_S, Watch, scan_root
from .site_sky import rebuild
from .sky_measure import sky_root
from .solve import solve_root
from .sqm_measure import sqm_root
from .walk import long_path

log = logging.getLogger(__name__)


def run_roots(
    conn: sqlite3.Connection,
    roots: Sequence[int],
    now: str,
    solver: astap.Solver | str | None,
    where: tuple[Path, threading.Event | None],
) -> Iterator[dict[str, Any]]:
    """One event per root, then `done`; the solver or its exe; the launch folder, the stop.
    Retired, or folder not there: skipped, said in the log."""
    if not isinstance(solver, astap.Solver):
        solver = astap.Solver(solver)
    work, stop = where
    for number, root in enumerate(roots, 1):
        if stop is not None and stop.is_set():
            break
        row = conn.execute(
            "SELECT path, retired_at FROM pipeline_roots WHERE id = ?", (root,)
        ).fetchone()
        try:
            if row is None or row["retired_at"] is not None:
                raise LookupError(f"root {root} not in use")
            if not os.path.isdir(long_path(row["path"])):
                raise NotADirectoryError(row["path"])
            scan_root(conn, root, now, watch=Watch(stop or threading.Event(), min_age_s=MIN_AGE_S))
            solve_root(conn, root, now, solver, work, stop=stop)
            measure_root(conn, root, now, stop=stop)
            sky_root(conn, root, now, stop=stop)
            sqm_root(conn, root, now, astap.catalogue_folder(solver), stop=stop)
        except Exception:  # behind the scenes: the user's scan never breaks here
            log.warning(
                "pipeline nuova: cartella saltata %s", row["path"] if row else root, exc_info=True
            )
        yield {"current": number, "total": len(roots)}
    sky_of_sites(conn, now)
    _measures_of_nights(conn)
    yield {"done": True, "total": len(roots)}


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
