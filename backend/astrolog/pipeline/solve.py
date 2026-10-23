"""Shots of a root solved by ASTAP: one solution per shot, from one present file and its card.
Calibrations never launched: no stars, the run only fails."""

import shutil
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .. import astap, units
from ..db.transaction import transaction
from .walk import long_path

# The whole pass would fail the same way: stop at the first.
STOPS = (astap.Reason.ASTAP_MISSING, astap.Reason.NO_STAR_DATABASE)
OUTCOMES = {
    astap.Reason.NO_STARS: "no_stars",
    astap.Reason.NO_SOLUTION: "no_solution",
}

PENDING = (  # plain file before its fpack copy: ASTAP before 2026.07.16 reads no .fz
    "SELECT f.frame_id, f.rel_path, c.height, c.pixel_um, c.focal_mm, c.pointing_ra_deg,"
    " c.pointing_dec_deg FROM pipeline_files AS f JOIN pipeline_cards AS c ON c.file_id = f.id"
    " WHERE f.root_id = ? AND f.state = 'present' AND f.skip_reason IS NULL"
    # typeless too: a light written wrong finds its sky, a calibration fails fast
    " AND c.frame_type IN ('light', 'unknown')"
    " AND NOT EXISTS (SELECT 1 FROM pipeline_solutions AS s WHERE s.frame_id = f.frame_id)"
    " ORDER BY f.frame_id, lower(f.rel_path) LIKE '%.fz', f.rel_path"
)


@dataclass
class SolveResult:
    solved: int = 0
    failed: Counter[str] = field(default_factory=Counter)  # outcome -> shots
    untried: Counter[str] = field(default_factory=Counter)  # reason -> shots, tried next pass
    stopped: astap.Reason | None = None


def solve_root(
    conn: sqlite3.Connection, root_id: int, now: str, solver: astap.Solver, work: Path
) -> SolveResult:
    """Shots of root without a solution row. Catalogue folder not said: none passed, ASTAP looks
    in its own (beside it on Windows, elsewhere on Mac and Linux)."""
    result = SolveResult()
    if not solver.exe:
        result.stopped = astap.Reason.ASTAP_MISSING
        return result
    root = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()
    work.mkdir(parents=True, exist_ok=True)
    named = astap.code_page_path(str(work))  # every `-o` lives here
    if named is None:
        result.stopped = astap.Reason.PATH_UNSUPPORTED
        return result
    takes = _takes(solver)
    done: set[int] = set()
    for row in conn.execute(PENDING, (root_id,)).fetchall():
        if row["frame_id"] in done:
            continue
        done.add(row["frame_id"])
        if not takes(row["rel_path"]):
            result.untried[astap.Reason.FZ_UNSUPPORTED] += 1
            continue
        found = _launch(Path(root["path"], row["rel_path"]), row, solver, Path(named))
        if found.reason in STOPS:
            result.stopped = found.reason
            return result
        outcome = "solved" if found.ok else OUTCOMES.get(found.reason)  # type: ignore[arg-type]
        if outcome is None:
            result.untried[str(found.reason)] += 1
            continue
        _write(conn, row["frame_id"], outcome, found, now)
        if found.ok:
            result.solved += 1
        else:
            result.failed[outcome] += 1
    return result


def _is_fz(rel_path: str) -> bool:
    return rel_path.lower().endswith(".fz")


def _takes(solver: astap.Solver) -> Callable[[str], bool]:
    """Whether this ASTAP reads the file. Version asked once, at first .fz; unread: try."""
    answer: list[bool] = []

    def takes(rel_path: str) -> bool:
        if not _is_fz(rel_path):
            return True
        if not answer:
            release = astap.version(solver)
            answer.append(release is None or release >= astap.FZ_SINCE)
        return answer[0]

    return takes


def _launch(path: Path, card: sqlite3.Row, solver: astap.Solver, work: Path) -> astap.Solution:
    """Fresh folder per launch: a crash writes no .ini, an earlier one would read as solved
    (measured). Base without a dot: ASTAP cuts the name at it. No .ini: crash, not tried."""
    scale = units.scale_arcsec_px(card["pixel_um"], card["focal_mm"])  # pixel_um has binning
    with tempfile.TemporaryDirectory(dir=work) as fresh:
        given = _readable_name(long_path(path), Path(fresh))
        if given is None:
            return astap.Solution(ok=False, reason=astap.Reason.UNREADABLE)
        base = Path(fresh) / "solve"
        ra, dec = card["pointing_ra_deg"], card["pointing_dec_deg"]  # both or neither (schema)
        found = astap.solve(
            given,
            base,
            solver,
            field_deg=units.field_deg(card["height"], scale),
            pointing=None if ra is None else (ra, dec),
        )
        written = astap.read_ini(base.with_suffix(".ini"))
        # no .ini (crash) or half written: not a sky that fails
        if not found.ok and (not written or astap.half_written(written)):
            return astap.Solution(ok=False, reason=astap.Reason.INTERNAL_ERROR)
        return found


def _readable_name(path: str, fresh: Path) -> str | None:
    """Name ASTAP can read: as is, 8.3, else copy in launch folder (N.I.N.A. solves a copy too).
    Never a hard link: shares read-only flag, cleanup clears it on user's file."""
    fz = _is_fz(path)
    named = astap.code_page_path(path)
    # 8.3 of a .fz ends .FZ; ASTAP wants .fits.fz (hnsky.org)
    if named is not None and not (fz and named != path):
        return named
    stand_in = fresh / ("frame.fits.fz" if fz else f"frame{Path(path).suffix}")
    try:
        shutil.copyfile(path, stand_in)
    except OSError:
        return None
    return str(stand_in)


def _write(
    conn: sqlite3.Connection, frame_id: int, outcome: str, found: astap.Solution, now: str
) -> None:
    with transaction(conn, immediate=True):
        conn.execute(
            # OR IGNORE: another pass wrote it meanwhile, first one stays
            "INSERT OR IGNORE INTO pipeline_solutions (frame_id, outcome, ra_deg, dec_deg,"
            " scale_arcsec_px, rotation_deg, tried_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (frame_id, outcome, found.ra_deg, found.dec_deg, found.scale_arcsec_px,
             found.rotation_deg, now),
        )  # fmt: skip
