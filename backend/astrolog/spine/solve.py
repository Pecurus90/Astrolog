"""The `solve` stage: each frame's sky measured by ASTAP, never read from the header. One frame
per order key goes first: that alone is enough to place and group the whole archive."""

import contextlib
import logging
import os
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Final

from .. import astap
from ..clock import now_iso
from ..db import config
from ..db.paths import cache_dir
from ..db.transaction import transaction
from ..fits.walk import long_path
from ..units import field_deg, scale_arcsec_px
from . import camera_sky, gear_usage, typeless_folders
from . import solve_store as store
from .stage_run import Event, FrameError, frame_safely, receipt, watched
from .stages import StageName, StageStatus, ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("solved", "cached", "unsolved", "waiting", "measured", "errors")

# ASTAP without its star catalogue starts and recognises nothing. One word for a frame's reason,
# for what stops the run, and for the `missing` line that warns before a whole scan.
NO_STAR_DATABASE: Final = astap.Reason.NO_STAR_DATABASE

# Not marked `failed`: nobody would requeue it, and installing ASTAP or reattaching the disk the
# next day would never solve anything again. It stays pending and the next run retries it.
RETRIABLE = (astap.Reason.ASTAP_MISSING, astap.Reason.FILE_MISSING, NO_STAR_DATABASE)

# Without the catalogue every frame fails the same way: stop at the first and say so.
ABORTS_THE_RUN = (NO_STAR_DATABASE,)


class _Sentinel(Enum):
    FIND_IT = "find_it"


# "Look for it" and "there is none" differ: a test passing `exe=None` must get no solver, not a
# search that finds the developer's own ASTAP.
FIND_IT: Final = _Sentinel.FIND_IT

# The word `GET /settings` lists among what is missing; it lives with the stage that suffers it.
NO_SOLVER = "no_solver"


@dataclass(frozen=True, slots=True)
class _Solver:
    """What one run solves with: looked up once, not per frame."""

    exe: str | None
    run: astap.Run | None
    cache: Path


def solver_path(conn: sqlite3.Connection) -> str | None:
    """One home for the run and for the warning, or they would disagree on whether ASTAP is there.
    The declared path wins over the automatic search."""
    return astap.find_exe(config.read(conn).astap_path)


def solver_where(conn: sqlite3.Connection) -> tuple[str | None, astap.Source | None]:
    """`(path, channel)`, so the user can say "not that one" (`astap.where_exe`)."""
    return astap.where_exe(config.read(conn).astap_path)


def databases_next_to(exe: str | Path | None) -> tuple[str, ...]:
    """The executable is passed because the question is also asked of a proposed one. Here and not
    in `api/` because the API does not read ASTAP."""
    return astap.star_databases(exe)


def solver_found() -> tuple[str | None, astap.Source | None]:
    """What the search finds ignoring the preferences; why it only proposes: `api/settings`."""
    return astap.where_exe(None)


def solve_frames(
    conn: sqlite3.Connection,
    *,
    exe: str | _Sentinel | None = FIND_IT,
    run: astap.Run | None = None,
    cache: Path | None = None,
) -> Iterator[Event]:
    """One event per frame, then the receipt. The executable is looked up once per run, not per
    frame."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    status, reason = "ok", None
    errors: list[FrameError] = []
    seen = 0
    solver = _Solver(solver_path(conn) if exe is FIND_IT else exe, run, _cache_dir(cache))

    def at_end() -> None:
        if seen:  # counting costs: only if some frame was looked at
            _at_round_end(conn)

    with watched(StageName.SOLVE, counts, at_end, astap=solver.exe) as outcome:
        frame_ids = _in_order(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            stop_reason = frame_safely(
                conn,
                StageName.SOLVE,
                frame_id,
                partial(_one_frame, conn, frame_id, counts, solver),
                counts,
                errors,
            )
            seen += 1
            yield {"current": seen, "total": total, **counts}
            if stop_reason:
                status, reason = "aborted", stop_reason
                outcome.update(status=status, reason=reason)
                break
    yield receipt(status, reason, counts, errors, total=seen)


def _at_round_end(conn: sqlite3.Connection) -> None:
    camera_sky.write(conn)
    gear_usage.write(conn)
    typeless_folders.write(conn)  # the sky decides which typeless frames it cannot tell


def _cache_dir(cache: Path | None) -> Path:
    """Solutions live on disk, not in the database: a database reset reads them back instead of
    solving again."""
    base = (cache or cache_dir()) / "solve"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _in_order(conn: sqlite3.Connection) -> list[int]:
    pending = ready(conn, StageName.SOLVE)
    first = store.first_per_order_key(conn, pending)
    rest = [i for i in pending if i not in set(first)]
    return first + store.newest_first(conn, rest)


def _one_frame(
    conn: sqlite3.Connection, frame_id: int, counts: dict[str, int], solver: _Solver
) -> str | None:
    """The reason that stops the run (`ABORTS_THE_RUN`), or None: a frame's fault never stops it,
    an installation's fault does."""
    frame = store.frame(conn, frame_id)
    now = now_iso()
    solution, cached = _solution_for(conn, frame, solver)
    hfd: float | None = None
    stars: int | None = None
    path = _path_of(frame)
    # The cache answers with the disk detached too: without the path check one process per frame
    # would be launched on a missing file.
    if solution.ok and path and not store.has_metrics(conn, frame["id"]):
        # Asked even for a cached sky: after a database reset the solution comes back from the
        # cache, but HFD and stars would be lost for good.
        hfd, stars = astap.analyse(path, exe=solver.exe, run=solver.run)

    with transaction(conn):
        if not solution.ok:
            if solution.reason in RETRIABLE:
                counts["waiting"] += 1
            else:
                set_status(
                    conn,
                    frame["id"],
                    StageName.SOLVE,
                    StageStatus.FAILED,
                    reason=solution.reason,
                    now=now,
                )
                counts["unsolved"] += 1
        else:
            width, height = _field_of(frame, solution.scale_arcsec_px)
            store.save_wcs(
                conn,
                frame["id"],
                ra_deg=solution.ra_deg,
                dec_deg=solution.dec_deg,
                scale=solution.scale_arcsec_px,
                rotation=solution.rotation_deg,
                width=width,
                height=height,
                now=now,
            )
            if hfd is not None or stars is not None:
                store.save_metrics(conn, frame["id"], hfd_px=hfd, stars=stars, now=now)
                counts["measured"] += 1
            set_status(conn, frame["id"], StageName.SOLVE, StageStatus.DONE, now=now)
            counts["cached" if cached else "solved"] += 1
    return solution.reason if solution.reason in ABORTS_THE_RUN else None


def _solution_for(
    conn: sqlite3.Connection, frame: sqlite3.Row, solver: _Solver
) -> tuple[astap.Solution, bool]:
    """The solution and whether it came from the cache, keyed on the frame's hash: it survives a
    move, a rename and a database reset."""
    out_base = solver.cache / frame["frame_hash"]
    saved = astap.from_ini(astap.read_ini(f"{out_base}.ini"))
    if saved.ok:
        return saved, True
    path = _path_of(frame)
    if path is None:
        return astap.Solution(ok=False, reason=astap.Reason.FILE_MISSING), False
    if solver.exe:
        solution = _launch(conn, frame, path, out_base, solver)
    else:
        # Every run walks all waiting frames just to ask the cache: hint and cleanup are for a
        # launch.
        solution = astap.Solution(ok=False, reason=astap.Reason.ASTAP_MISSING)
    return solution, False


def _launch(
    conn: sqlite3.Connection, frame: sqlite3.Row, path: str, out_base: Path, solver: _Solver
) -> astap.Solution:
    # A leftover that is not a solution goes first, or an ASTAP failing without writing would
    # leave it to be read back.
    _forget(out_base)
    ra, dec = _hint_for(conn, frame)
    solution = astap.solve(
        path,
        out_base,
        field_deg=_field_hint(frame),
        ra_deg=ra,
        dec_deg=dec,
        exe=solver.exe,
        run=solver.run,
    )
    if not solution.ok:
        # Not cached: tomorrow ASTAP may have a denser catalogue, or the frame a sister's hint.
        _forget(out_base)
    return solution


def _forget(out_base: Path) -> None:
    for suffix in (".ini", ".wcs"):
        # missing or locked: the next run redoes it anyway
        with contextlib.suppress(OSError):
            (out_base.parent / f"{out_base.name}{suffix}").unlink()


def _path_of(frame: sqlite3.Row) -> str | None:
    if not frame["root_path"] or not frame["rel_path"]:
        return None
    return long_path(os.path.join(frame["root_path"], frame["rel_path"]))


def _hint_for(conn: sqlite3.Connection, frame: sqlite3.Row) -> tuple[float | None, float | None]:
    """The header's pointing; if silent, the MEASURED sky of a sister: the same piece of sky."""
    if frame["ra_hint_deg"] is not None and frame["dec_hint_deg"] is not None:
        return frame["ra_hint_deg"], frame["dec_hint_deg"]
    sister = store.sister_solution(conn, frame)
    return (sister["ra_deg"], sister["dec_deg"]) if sister else (None, None)


def _scale_of(frame: sqlite3.Row) -> float | None:
    """Binning is not multiplied: `XPIXSZ` already includes it (`units.physical_pixel_um`)."""
    return scale_arcsec_px(frame["pixel_size_um"], frame["focal_mm_raw"])


def _field_hint(frame: sqlite3.Row) -> float | None:
    """The field height, the speed lever of `astap.command`; `None` without focal or pixel."""
    return field_deg(frame["naxis2"], _scale_of(frame))


def _field_of(frame: sqlite3.Row, scale: float | None) -> tuple[float | None, float | None]:
    """From the MEASURED scale: the rectangle drawn on the sky comes from the solution."""
    return field_deg(frame["naxis1"], scale), field_deg(frame["naxis2"], scale)
