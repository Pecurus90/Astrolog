"""Shots of a root solved by ASTAP: one solution per shot, from one present file and its card.
Calibrations never launched: no stars, the run only fails."""

import shutil
import sqlite3
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from .. import astap, units
from ..db.transaction import transaction
from .walk import long_path

# The whole pass would fail the same way: stop at the first.
STOPS = (astap.Reason.ASTAP_MISSING, astap.Reason.NO_STAR_DATABASE)
OUTCOMES = {
    astap.Reason.NO_STARS: "no_stars",
    astap.Reason.NO_SOLUTION: "no_solution",
    astap.Reason.TIMEOUT: "timeout",
    astap.Reason.INTERNAL_ERROR: "crashed",  # no .ini, or half written
    astap.Reason.UNREADABLE: "unreadable",
    astap.Reason.FZ_UNSUPPORTED: "fz_unsupported",
}
SETTLED = ("solved", "no_solution", "no_stars")
# D5 (ASTAP plan): tried at next pass once more, then wait for another ASTAP or catalogue
WAITING = ("timeout", "crashed", "unreadable")
PASSES = 2

PENDING = (  # plain file before its fpack copy: ASTAP before 2026.07.16 reads no .fz
    "SELECT f.id AS file_id, f.frame_id, f.rel_path, c.frame_type, c.height, c.pixel_um,"
    " c.focal_mm, c.pointing_ra_deg, c.pointing_dec_deg"
    " FROM pipeline_files AS f JOIN pipeline_cards AS c ON c.file_id = f.id"
    " WHERE f.root_id = :root AND f.state = 'present' AND f.skip_reason IS NULL"
    # typeless too: a light written wrong finds its sky, a calibration fails fast
    " AND c.frame_type IN ('light', 'unknown')"
    # settled: the shot is done; waiting: only the file tried waits, its copies go
    " AND NOT EXISTS (SELECT 1 FROM pipeline_solutions AS s WHERE s.frame_id = f.frame_id AND ("
    "   s.outcome IN ('solved', 'no_solution', 'no_stars')"
    "   OR (s.file_id = f.id AND s.astap_version IS coalesce(:version, s.astap_version) AND ("
    "     s.outcome = 'fz_unsupported' OR (s.outcome IN ('timeout', 'crashed', 'unreadable')"
    "       AND s.attempts >= :passes AND s.installed IS :installed)))))"
    " ORDER BY f.frame_id, lower(f.rel_path) LIKE '%.fz', f.rel_path"
)

UPSERT = (
    "INSERT INTO pipeline_solutions (frame_id, outcome, step, file_id, astap_version, catalogue,"
    " installed, duration_s, ra_deg, dec_deg, scale_arcsec_px, rotation_deg, tried_at)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    " ON CONFLICT (frame_id) DO UPDATE SET outcome = excluded.outcome, step = excluded.step,"
    " file_id = excluded.file_id, attempts = attempts + 1, astap_version = excluded.astap_version,"
    " catalogue = excluded.catalogue, installed = excluded.installed,"
    " duration_s = excluded.duration_s, ra_deg = excluded.ra_deg, dec_deg = excluded.dec_deg,"
    " scale_arcsec_px = excluded.scale_arcsec_px, rotation_deg = excluded.rotation_deg,"
    " tried_at = excluded.tried_at"
    # settled by another pass meanwhile: stays
    " WHERE pipeline_solutions.outcome NOT IN ('solved', 'no_solution', 'no_stars')"
)


class Step(StrEnum):
    """Ladder climbed only on no solution. Blind last: N.I.N.A. failover (ImageSolver.cs), same
    parameters without pointing. z1 and fov0: measured."""

    FIRST = "first"
    FULL_RES = "full_res"  # -z 1: OSC frame failing at z0 solved
    ANY_FIELD = "any_field"  # -fov 0: header field x2 or x0.5 solved
    BLIND = "blind"  # pointing 60 degrees off solved only so


def _ladder(
    pointing: tuple[float, float] | None, field_deg: float | None, typeless: bool
) -> list[tuple[Step, astap.Search]]:
    """Same launch twice never: unknown field, `any_field` repeats `first`, skipped."""
    tries = [
        (Step.FIRST, astap.Search(field_deg, pointing)),
        (Step.FULL_RES, astap.Search(field_deg, pointing, downsample=1)),
        (Step.ANY_FIELD, astap.Search(None, pointing)),
    ]
    if pointing is not None:  # no blind with free field: unsolvable frame ran 285 s (measured)
        tries.append((Step.BLIND, astap.Search(field_deg)))
    if typeless:  # one try (D6): mostly calibrations
        tries = tries[:1]
    seen: set[astap.Search] = set()
    ladder = []
    for step, search in tries:
        if search not in seen:
            seen.add(search)
            ladder.append((step, search))
    return ladder


@dataclass
class SolveResult:
    solved: int = 0
    failed: Counter[str] = field(default_factory=Counter)  # settled outcome -> shots
    untried: Counter[str] = field(default_factory=Counter)  # waiting outcome -> shots
    stopped: astap.Reason | None = None


@dataclass(frozen=True)
class _Pass:
    """What this pass knows of ASTAP: same for every shot."""

    now: str
    release: tuple[int, int, int] | None
    installed: str  # catalogue codes, comma separated

    @property
    def version(self) -> str | None:
        return None if self.release is None else "{}.{:02d}.{:02d}".format(*self.release)


@dataclass(frozen=True)
class _Tried:
    found: astap.Solution
    step: Step | None  # None: never launched
    duration_s: float = 0.0


def solve_root(
    conn: sqlite3.Connection, root_id: int, now: str, solver: astap.Solver, work: Path
) -> SolveResult:
    """Shots of root without a settled row, or waiting ones whose turn came. Catalogue folder
    not said: none passed, ASTAP looks in its own (beside it on Windows, elsewhere on Mac)."""
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
    this = _Pass(now, astap.version(solver), ",".join(_installed(solver)))
    asked = {"root": root_id, "passes": PASSES, "version": this.version,
             "installed": this.installed}  # fmt: skip
    done: set[int] = set()
    for row in conn.execute(PENDING, asked).fetchall():
        if row["frame_id"] in done:
            continue
        done.add(row["frame_id"])
        tried = _try(Path(root["path"], row["rel_path"]), row, solver, (Path(named), this))
        if tried.found.reason in STOPS:
            result.stopped = tried.found.reason
            return result
        outcome = _write(conn, row, tried, this)
        if outcome is None:
            continue
        if outcome == "solved":
            result.solved += 1
        elif outcome in SETTLED:
            result.failed[outcome] += 1
        else:
            result.untried[outcome] += 1
    return result


def _installed(solver: astap.Solver) -> tuple[str, ...]:
    """Where ASTAP reads its catalogue: folder said, else beside it (Windows; Mac not)."""
    if solver.databases is not None:
        return astap.catalogues_in(solver.databases)
    return astap.star_databases(solver.exe)


def _is_fz(rel_path: str) -> bool:
    return rel_path.lower().endswith(".fz")


def _try(path: Path, card: sqlite3.Row, solver: astap.Solver, where: tuple[Path, _Pass]) -> _Tried:
    work, this = where
    # unread version: try
    if _is_fz(path.name) and this.release is not None and this.release < astap.FZ_SINCE:
        return _Tried(astap.Solution(ok=False, reason=astap.Reason.FZ_UNSUPPORTED), None)
    start = time.monotonic()
    found, step = _climb(path, card, solver, work)
    return _Tried(found, step, time.monotonic() - start)


def _climb(
    path: Path, card: sqlite3.Row, solver: astap.Solver, work: Path
) -> tuple[astap.Solution, Step | None]:
    """Up the ladder while no solution; other ends stop it. Timeout after no solution: no
    solution. Fresh base per launch: crash writes no .ini, old one read as solved."""
    scale = units.scale_arcsec_px(card["pixel_um"], card["focal_mm"])  # pixel_um has binning
    ra, dec = card["pointing_ra_deg"], card["pointing_dec_deg"]  # both or neither (schema)
    ladder = _ladder(
        None if ra is None else (ra, dec),
        units.field_deg(card["height"], scale) or None,
        typeless=card["frame_type"] == "unknown",
    )
    with tempfile.TemporaryDirectory(dir=work) as fresh:
        given = _readable_name(long_path(path), Path(fresh))
        if given is None:
            return astap.Solution(ok=False, reason=astap.Reason.UNREADABLE), None
        ended = (astap.Solution(ok=False, reason=astap.Reason.NO_SOLUTION), Step.FIRST)
        for number, (step, search) in enumerate(ladder):
            found = _launch(given, Path(fresh) / f"solve{number}", solver, search)
            if number and found.reason == astap.Reason.TIMEOUT:  # ASTAP already said no
                return ended[0], step
            ended = (found, step)
            if found.reason != astap.Reason.NO_SOLUTION:
                break
        return ended


def _launch(given: str, base: Path, solver: astap.Solver, search: astap.Search) -> astap.Solution:
    """Base without a dot: ASTAP cuts the name at it. No .ini or half written: crash."""
    found = astap.solve(given, base, solver, search)
    written = astap.read_ini(base.with_suffix(".ini"))
    # read as no solution; timeout keeps its own reason
    if found.reason == astap.Reason.NO_SOLUTION and (not written or astap.half_written(written)):
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


def _write(conn: sqlite3.Connection, row: sqlite3.Row, tried: _Tried, this: _Pass) -> str | None:
    """Outcome written; None: another pass settled it meanwhile."""
    found = tried.found
    outcome = "solved" if found.ok else OUTCOMES[found.reason]  # type: ignore[index]
    with transaction(conn, immediate=True):
        written = conn.execute(
            UPSERT,
            (row["frame_id"], outcome, tried.step, row["file_id"], this.version, found.catalogue,
             this.installed,
             tried.duration_s, found.ra_deg, found.dec_deg, found.scale_arcsec_px,
             found.rotation_deg, this.now),
        ).rowcount  # fmt: skip
    return outcome if written else None
