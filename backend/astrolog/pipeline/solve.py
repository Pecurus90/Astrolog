"""Shots of a root solved by ASTAP: one solution per shot, from one present file and its card.
Calibrations never launched: no stars, the run only fails."""

import json
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
from .footprint import footprint
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
# tried at next pass once more, then wait for another ASTAP or catalogue [P ADR 0036, D5]
WAITING = ("timeout", "crashed", "unreadable")
PASSES = 2  # [P ADR 0036, D5]
# solved scale against the card's, either way round [C ASTAP manual, "preferably 5% accuracy"]
SCALE_TOLERANCE = 0.05

PENDING = (  # plain file before its fpack copy: ASTAP before astap.FZ_SINCE reads no .fz
    "SELECT f.id AS file_id, f.frame_id, f.rel_path, c.frame_type, c.width, c.height,"
    " c.pixel_um, c.focal_mm, c.pointing_ra_deg, c.pointing_dec_deg, c.object_name, c.camera,"
    " c.bin_x, c.bin_y, c.optics,"
    " h.header ->> '$.ROWORDER' AS row_order"
    " FROM pipeline_files AS f JOIN pipeline_cards AS c ON c.file_id = f.id"
    " JOIN pipeline_headers AS h ON h.file_id = f.id"
    " WHERE f.root_id = :root AND f.state = 'present' AND f.skip_reason IS NULL"
    # typeless too: a light written wrong finds its sky, a calibration fails fast
    " AND c.frame_type IN ('light', 'unknown')"
    # settled: the shot is done; waiting: only the file tried waits, its copies go
    " AND NOT EXISTS (SELECT 1 FROM pipeline_solutions AS s WHERE s.frame_id = f.frame_id AND ("
    "   s.outcome IN ('solved', 'no_solution', 'no_stars')"
    "   OR (s.file_id = f.id AND s.astap_version IS coalesce(:version, s.astap_version) AND ("
    "     s.outcome = 'fz_unsupported' OR (s.outcome IN ('timeout', 'crashed', 'unreadable')"
    "       AND s.attempts >= :passes AND s.installed IS :installed)))))"
    # shots with their own hint and field first: solved, they lend them to their sisters; per
    # shot, not per file, or a hinted .fz copy would pass its plain one
    " ORDER BY min(c.pointing_ra_deg IS NULL OR c.focal_mm IS NULL OR c.pixel_um IS NULL)"
    " OVER (PARTITION BY f.frame_id), f.frame_id, lower(f.rel_path) LIKE '%.fz', f.rel_path"
)

# Measured centre of a solved shot of the same object, never of a session: two shots without
# OBJECT are not sisters (docs/domini/spina.md, "indizio").
SISTER_POINTING = (
    "SELECT s.ra_deg, s.dec_deg FROM pipeline_solutions AS s"
    " JOIN pipeline_cards AS c ON c.file_id = s.file_id"
    " WHERE s.outcome = 'solved' AND c.object_name = :object_name ORDER BY s.frame_id LIMIT 1"
)
# Measured scale of a solved shot of the same setup: same camera, binning and optics.
SISTER_SCALE = (
    "SELECT s.scale_arcsec_px FROM pipeline_solutions AS s"
    " JOIN pipeline_cards AS c ON c.file_id = s.file_id"
    " WHERE s.outcome = 'solved' AND c.camera = :camera AND c.bin_x IS :bin_x"
    " AND c.bin_y IS :bin_y AND c.optics IS :optics ORDER BY s.frame_id LIMIT 1"
)

UPSERT = (
    "INSERT INTO pipeline_solutions (frame_id, outcome, step, file_id, astap_version, catalogue,"
    " installed, duration_s, hint_from, field_from, ra_deg, dec_deg, scale_arcsec_px,"
    " expected_scale_arcsec_px, scale_disagrees, measured_focal_mm, astap_warning, rotation_deg,"
    " mirrored, skew_deg, width_deg, height_deg, corners, tried_at) VALUES"
    " (:frame_id, :outcome, :step, :file_id, :astap_version, :catalogue, :installed, :duration_s,"
    " :hint_from, :field_from, :ra_deg, :dec_deg, :scale_arcsec_px, :expected_scale_arcsec_px,"
    " :scale_disagrees, :measured_focal_mm, :astap_warning, :rotation_deg, :mirrored, :skew_deg,"
    " :width_deg, :height_deg, :corners, :tried_at)"
    " ON CONFLICT (frame_id) DO UPDATE SET attempts = attempts + 1, outcome = excluded.outcome,"
    " step = excluded.step, file_id = excluded.file_id, astap_version = excluded.astap_version,"
    " catalogue = excluded.catalogue, installed = excluded.installed,"
    " duration_s = excluded.duration_s, hint_from = excluded.hint_from,"
    " field_from = excluded.field_from, ra_deg = excluded.ra_deg, dec_deg = excluded.dec_deg,"
    " scale_arcsec_px = excluded.scale_arcsec_px,"
    " expected_scale_arcsec_px = excluded.expected_scale_arcsec_px,"
    " scale_disagrees = excluded.scale_disagrees, measured_focal_mm = excluded.measured_focal_mm,"
    " astap_warning = excluded.astap_warning, rotation_deg = excluded.rotation_deg,"
    " mirrored = excluded.mirrored, skew_deg = excluded.skew_deg, width_deg = excluded.width_deg,"
    " height_deg = excluded.height_deg, corners = excluded.corners, tried_at = excluded.tried_at"
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
    if pointing is not None:  # blind, with field; the free-field blind already ran as any_field
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
class _Hint:
    """Where the search starts, and where each half came from (ADR 0026): `card` or `sister`."""

    pointing: tuple[float, float] | None = None
    field_deg: float | None = None
    hint_from: str | None = None
    field_from: str | None = None


@dataclass(frozen=True)
class _Tried:
    found: astap.Solution
    step: Step | None  # None: never launched
    duration_s: float = 0.0
    hint: _Hint = _Hint()


def _hint(conn: sqlite3.Connection, card: sqlite3.Row) -> _Hint:
    """The card's own first; what it lacks, from a shot solved earlier in this pass or before."""
    pointing, hint_from = None, None
    if card["pointing_ra_deg"] is not None:  # both or neither (schema)
        pointing, hint_from = (card["pointing_ra_deg"], card["pointing_dec_deg"]), "card"
    elif card["object_name"] is not None:
        sister = conn.execute(SISTER_POINTING, {"object_name": card["object_name"]}).fetchone()
        if sister is not None:
            pointing, hint_from = (sister["ra_deg"], sister["dec_deg"]), "sister"
    scale = units.scale_arcsec_px(card["pixel_um"], card["focal_mm"])  # pixel_um has binning
    field_deg = units.field_deg(card["height"], scale)
    field_from = None if field_deg is None else "card"
    if field_deg is None and card["camera"] is not None:
        setup = {key: card[key] for key in ("camera", "bin_x", "bin_y", "optics")}
        sister = conn.execute(SISTER_SCALE, setup).fetchone()
        if sister is not None:
            field_deg = units.field_deg(card["height"], sister["scale_arcsec_px"])
            field_from = None if field_deg is None else "sister"
    return _Hint(pointing, field_deg, hint_from, field_from)


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
        hint = _hint(conn, row)  # read now: a sister solved a moment ago counts
        tried = _try(Path(root["path"], row["rel_path"]), (row, hint), solver, (Path(named), this))
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


def _try(
    path: Path, shot: tuple[sqlite3.Row, _Hint], solver: astap.Solver, where: tuple[Path, _Pass]
) -> _Tried:
    work, this = where
    card, hint = shot
    # unread version: try
    if _is_fz(path.name) and this.release is not None and this.release < astap.FZ_SINCE:
        return _Tried(astap.Solution(ok=False, reason=astap.Reason.FZ_UNSUPPORTED), None)
    start = time.monotonic()
    ladder = _ladder(hint.pointing, hint.field_deg, typeless=card["frame_type"] == "unknown")
    found, step = _climb(path, ladder, solver, work)
    return _Tried(found, step, time.monotonic() - start, hint)


def _climb(
    path: Path, ladder: list[tuple[Step, astap.Search]], solver: astap.Solver, work: Path
) -> tuple[astap.Solution, Step | None]:
    """Up the ladder while no solution; other ends stop it. Timeout after no solution: no
    solution. Fresh base per launch: crash writes no .ini, old one read as solved."""
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
    values = {
        "frame_id": row["frame_id"], "outcome": outcome, "step": tried.step,
        "file_id": row["file_id"], "astap_version": this.version, "catalogue": found.catalogue,
        "installed": this.installed, "duration_s": tried.duration_s, "ra_deg": found.ra_deg,
        "dec_deg": found.dec_deg, "scale_arcsec_px": found.scale_arcsec_px,
        "rotation_deg": found.rotation_deg, "tried_at": this.now, "astap_warning": found.warning,
        "hint_from": tried.hint.hint_from, "field_from": tried.hint.field_from,
    } | _measured(found, row)  # fmt: skip
    values |= _scale_check(values["scale_arcsec_px"], row)  # type: ignore[arg-type]
    with transaction(conn, immediate=True):
        written = conn.execute(UPSERT, values).rowcount
    return outcome if written else None


def _scale_check(solved: float | None, row: sqlite3.Row) -> dict[str, object]:
    """The card's pixel and focal against the sky: far off is said, the solution stays (D8)."""
    expected = units.scale_arcsec_px(row["pixel_um"], row["focal_mm"])
    # ADR 0016: the card's pixel has the binning, as the solved scale does
    measured = units.focal_from_scale(row["pixel_um"], solved)
    focal: dict[str, object] = {"measured_focal_mm": measured}
    if solved is None or expected is None:
        return {"expected_scale_arcsec_px": None, "scale_disagrees": None} | focal
    low, high = sorted((solved, expected))
    return {
        "expected_scale_arcsec_px": expected,
        "scale_disagrees": int(high > low * (1 + SCALE_TOLERANCE)),
    } | focal


def forget(conn: sqlite3.Connection, frame_id: int) -> bool:
    """On request (header fixed, new catalogue): the shot is solved again at the next pass.
    False: nothing to forget."""
    with transaction(conn, immediate=True):
        gone = conn.execute("DELETE FROM pipeline_solutions WHERE frame_id = ?", (frame_id,))
    return gone.rowcount > 0


def _measured(found: astap.Solution, row: sqlite3.Row) -> dict[str, object]:
    """Footprint of a solution: the sky's rectangle, written once, never redone by a reader."""
    if not (found.ok and found.cd and found.crpix):
        return {key: None for key in ("mirrored", "skew_deg", "width_deg", "height_deg", "corners")}
    sky = footprint(
        found.cd,
        found.crpix,
        (found.ra_deg, found.dec_deg),  # type: ignore[arg-type]
        (row["width"], row["height"]),
        # read as ASTAP reads it (for Bayer): pos('BOT', roworder), case counts
        bottom_up="BOT" in str(row["row_order"] or ""),
    )
    return {
        "scale_arcsec_px": sky.scale_arcsec_px,
        "mirrored": int(sky.mirrored),
        "skew_deg": sky.skew_deg,
        "width_deg": sky.width_deg,
        "height_deg": sky.height_deg,
        "corners": None if sky.corners is None else json.dumps(sky.corners),
    }
