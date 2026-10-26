"""Drives the ASTAP solver. Never `-update` (it rewrites the user's FITS) nor `-extract` (it leaves
a CSV beside the file, ignoring `-o`); ASTAP prints numbers with the machine's decimal separator."""

import contextlib
import ctypes
import logging
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path, PureWindowsPath

from .fits.header_keys import as_float
from .fits.header_wcs import solved, wcs_rotation_deg, wcs_scale

log = logging.getLogger(__name__)

# `astap_cli` first: it opens no window, the only one that works on a headless NAS.
EXE_NAMES = ("astap_cli", "astap")
ENV_EXE = "ASTROLOG_ASTAP"

# Where it installs itself on the three targets, when not in PATH.
CANDIDATES = (
    r"C:\Program Files\astap\astap_cli.exe",
    r"C:\Program Files (x86)\astap\astap_cli.exe",
    "/Applications/ASTAP.app/Contents/MacOS/astap_cli",
    "/opt/astap/astap_cli",
    "/usr/local/bin/astap_cli",
)

# Star catalogue codes from the author's download list: current and old ones, which ASTAP still
# reads where they were never removed.
DB_KINDS = ("d05", "d20", "d50", "d80", "v05", "v50", "g05", "w08",
            "h17", "h18", "v17", "g17", "g18")  # fmt: skip

# By name, since the extension changes with the format; the code is checked against the list, or
# any `x99_1.zip` would be a false "you have it". A new catalogue reads missing until listed.
DB_NAME = re.compile(r"(" + "|".join(DB_KINDS) + r")_[0-9]+\.", re.IGNORECASE)

# [M over twice the slowest blind solve that succeeds, 23 s, docs/domini/spina.md]; a free-field
# blind search that finds nothing runs past it (285 s measured).
TIMEOUT_S = 60
# [C N.I.N.A. PlateSolveSettings.cs searchRadius = 30]; speed depends on field, not radius.
SEARCH_RADIUS_DEG = 30
BLIND_RADIUS_DEG = 180  # [C ASTAP default radius_search1; N.I.N.A. forces 180 without coordinates]


# Closed list of codes, never ASTAP's sentence: sentences change between versions and would
# reach the screen in English.
class Reason(StrEnum):
    NO_STARS = "no_stars"  # with no stars, a typeless file is a calibration frame (`typeless`)
    NO_SOLUTION = "no_solution"
    TIMEOUT = "timeout"
    ASTAP_MISSING = "astap_missing"
    FILE_MISSING = "file_missing"
    NO_STAR_DATABASE = "no_star_database"
    INTERNAL_ERROR = "internal_error"
    UNREADABLE = "unreadable"  # file gone, .fz to an older ASTAP, name outside the code page
    FZ_UNSUPPORTED = "fz_unsupported"
    PATH_UNSUPPORTED = "path_unsupported"


# Printed first on every launch (CLI-2025.11.19); the .ini does not say it.
_CATALOGUE = re.compile(r"Using star database (\w+)", re.IGNORECASE)

# Lines of words, not numbers, in ASTAP's result file.
_TEXT = frozenset({"ERROR", "WARNING", "CMDLINE"})
_POLE_DEG = 90.0  # [T]

# Compared lowercase and by containment: the exact text changes, the key words do not.
_ERROR_WORDS = (
    ("not enough stars", Reason.NO_STARS),
    # same sentence for a missing file, a .fz and a CJK name (CLI-2025.11.19, measured)
    ("error reading image file", Reason.UNREADABLE),
    # Both `No star database found.` (missing) and `Error reading star database.` (truncated
    # download), as ASTAP CLI-2025.11.19 prints them: a half download is as common as none.
    ("star database", Reason.NO_STAR_DATABASE),
)


@dataclass(frozen=True)
class Solution:
    ok: bool
    reason: Reason | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    scale_arcsec_px: float | None = None
    rotation_deg: float | None = None
    catalogue: str | None = None  # the one ASTAP says it used, lowercase code
    cd: tuple[float, float, float, float] | None = None  # CD1_1, CD1_2, CD2_1, CD2_2 degrees
    crpix: tuple[float, float] | None = None
    # ASTAP's own words beside a solution ("scale was inaccurate! ... FL=561mm"), as written
    warning: str | None = None


# Codes, not sentences: they are shown on screen, and a new word would arrive untranslated.
class Source(StrEnum):
    DECLARED = "declared"
    ENV = "env"
    PATH = "path"
    KNOWN_PLACE = "known_place"


type Which = Callable[[str], str | None]


def find_exe(
    declared: str | None = None,
    env: Mapping[str, str] | None = None,
    which: Which = shutil.which,
    candidates: Iterable[str | Path] = CANDIDATES,
) -> str | None:
    """Calls `_search`, not `where_exe`: the suite's fence replaces both public ones, and one going
    through the other would pick up the stub even when captured on purpose beforehand."""
    return _search(declared, env, which, candidates)[0]


def where_exe(
    declared: str | None = None,
    env: Mapping[str, str] | None = None,
    which: Which = shutil.which,
    candidates: Iterable[str | Path] = CANDIDATES,
) -> tuple[str | None, Source | None]:
    """The channel is shown because the automatic search is wrong exactly when it finds something
    (an old ASTAP in PATH). The user's choice beats the variable, set by the NAS admin."""
    return _search(declared, env, which, candidates)


def _search(
    declared: str | None,
    env: Mapping[str, str] | None,
    which: Which,
    candidates: Iterable[str | Path],
) -> tuple[str | None, Source | None]:
    env = os.environ if env is None else env
    written, channel = (declared, Source.DECLARED) if declared else (env.get(ENV_EXE), Source.ENV)
    if written:
        # Windows' *Copy as path* wraps it in quotes: with them inside the file is never found,
        # and the warning would blame the wrong thing.
        written = written.strip().strip("\"'")
        # A written wrong path, or a folder, stops the search: falling back on PATH would say
        # "found" to whoever wrote it wrong.
        return (written, channel) if Path(written).is_file() else (None, None)
    for name in EXE_NAMES:
        found = which(name)
        if found:
            return found, Source.PATH
    for candidate in candidates:
        if Path(candidate).is_file():
            return str(candidate), Source.KNOWN_PLACE
    return None, None


def star_databases(exe: str | Path | None) -> tuple[str, ...]:
    """Only beside the resolved executable, not in known install folders, which would show another
    program's catalogue. Looked at, not asked: asking ASTAP means running it."""
    if exe is None:
        return ()
    with contextlib.suppress(OSError):
        return catalogues_in(Path(exe).resolve().parent)
    return ()


def catalogues_in(folder: str | Path) -> tuple[str, ...]:
    """Catalogue codes found in folder, sorted; none readable: empty."""
    with contextlib.suppress(OSError):  # folder gone, disk unplugged, permission denied
        matches = (DB_NAME.match(f.name) for f in Path(folder).iterdir())
        return tuple(sorted({m.group(1).lower() for m in matches if m}))
    return ()


# The process launch each caller receives, so tests never run the solver.
type Run = Callable[[Sequence[str], float], tuple[int, str]]


def _run(cmd: Sequence[str], timeout_s: float) -> tuple[int, str]:
    done = subprocess.run(  # noqa: S603 - our own arguments, no shell
        cmd, capture_output=True, text=True, timeout=timeout_s, check=False
    )
    return done.returncode, done.stdout


def _number(text: object) -> float | None:
    """The machine's decimal comma counts as a point. Never a fallback zero."""
    if text is None:
        return None
    return as_float(str(text).strip().replace(",", "."))


def read_ini_text(text: str | None) -> dict[str, str]:
    """ASTAP writes `KEY=value` lines both in the result file and on screen: one reader."""
    out = {}
    for line in (text or "").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip():
            out[key.strip().upper()] = value.strip()
    return out


def read_ini(path: str | Path) -> dict[str, str]:
    """Its keys are a FITS header's (`PLTSOLVD`, `CRVAL1`, `CD`), so the existing WCS reader reads
    it unchanged. A missing file is an empty dict."""
    try:
        return read_ini_text(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def _reason_of(ini: Mapping[str, str]) -> Reason:
    message = str(ini.get("ERROR", "")).lower()
    for words, code in _ERROR_WORDS:
        if words in message:
            return code
    return Reason.NO_SOLUTION


@dataclass(frozen=True)
class Solver:
    """Which ASTAP and how it runs: one value for every launch."""

    exe: str | None
    run: Run | None = None  # tests inject it: the suite never launches ASTAP
    timeout_s: float = TIMEOUT_S
    databases: str | Path | None = None  # catalogue folder; ASTAP picks one for the field


@dataclass(frozen=True)
class Search:
    """Where and how ASTAP looks: header's hints, its own downsampling."""

    field_deg: float | None = None
    pointing: tuple[float, float] | None = None  # ra, dec degrees
    downsample: int = 0  # 0: ASTAP picks (N.I.N.A. default too)


def command(
    fits_path: str | Path, out_base: str | Path, solver: Solver, search: Search = Search()
) -> list[str]:
    """Built without running it, so a test proves the forbidden flags are absent and the units
    are the ones ASTAP wants. No `-wcs`: nobody reads the .wcs, ASTAP writes one anyway."""
    field_deg, pointing = search.field_deg, search.pointing
    cmd = [
        str(solver.exe),
        "-f",
        str(fits_path),
        "-o",
        str(out_base),
        # The field is the speed lever: where the header lacks focal or pixel size, the blind
        # field search pays for it. Always said: left out, ASTAP takes its last solve's.
        "-fov",
        f"{field_deg:.3f}" if field_deg else "0",
        "-z",
        str(search.downsample),
    ]
    if solver.databases is not None:  # folder only, never `-D`: NINA and StellarSolver alike
        cmd += ["-d", str(solver.databases)]
    if pointing is not None:
        ra_deg, dec_deg = pointing
        # ASTAP wants HOURS of right ascension and the distance from the SOUTH pole: getting them
        # wrong gives no error, it gives the sky of another point.
        cmd += ["-ra", f"{ra_deg / 15.0:.5f}", "-spd", f"{dec_deg + 90.0:.4f}", "-r",
                str(SEARCH_RADIUS_DEG)]  # fmt: skip
    else:
        cmd += ["-r", str(BLIND_RADIUS_DEG)]
    return cmd


def solve(
    fits_path: str | Path, out_base: str | Path, solver: Solver, search: Search = Search()
) -> Solution:
    """Writes `<out_base>.ini` and `.wcs` where we say, never beside the user's FITS. Never raises
    for the solver's fault: a missing or hung ASTAP is a frame without sky and its reason."""
    if not solver.exe:
        return Solution(ok=False, reason=Reason.ASTAP_MISSING)
    cmd = command(fits_path, out_base, solver, search)
    try:
        _code, out = (solver.run or _run)(cmd, solver.timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError):
        log.info("astap: tempo scaduto", extra={"file": str(fits_path)})
        return Solution(ok=False, reason=Reason.TIMEOUT)
    except OSError as err:
        log.warning("astap: non si e' potuto lanciare", extra={"error": str(err)})
        return Solution(ok=False, reason=Reason.ASTAP_MISSING)
    used = _CATALOGUE.search(out or "")
    found = from_ini(read_ini(f"{out_base}.ini"))
    return replace(found, catalogue=used[1].lower() if used else None)


def half_written(ini: dict[str, str]) -> bool:
    """`PLTSOLVD=T` without the centre: cut mid-write, not a sky that fails."""
    return solved(ini) and not {"CRVAL1", "CRVAL2"} <= ini.keys()


def from_ini(ini: dict[str, str]) -> Solution:
    """Also the cache's path. A half-written result can say `PLTSOLVD=T` without the numbers: it
    counts as no solution, so the cache reader drops it and solves again."""
    if not solved(ini):
        return Solution(ok=False, reason=_reason_of(ini))
    # numbers only: the machine's decimal comma counts as a point
    wcs = {key: value.replace(",", ".") for key, value in ini.items() if key not in _TEXT}
    ra, dec, scale = as_float(wcs.get("CRVAL1")), as_float(wcs.get("CRVAL2")), wcs_scale(wcs)
    # a sky that cannot be (|dec| > 90, no scale) is no solution; RA is an angle, wraps
    if ra is None or dec is None or scale is None or abs(dec) > _POLE_DEG or scale <= 0:
        return Solution(ok=False, reason=Reason.NO_SOLUTION)
    cd = tuple(as_float(wcs.get(k)) for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2"))
    crpix = (as_float(wcs.get("CRPIX1")), as_float(wcs.get("CRPIX2")))
    if None not in cd and cd[0] * cd[3] - cd[1] * cd[2] == 0:  # type: ignore[operator]
        return Solution(ok=False, reason=Reason.NO_SOLUTION)  # degenerate: no pixel area
    ra %= 360.0
    return Solution(
        ok=True,
        ra_deg=0.0 if ra == 360.0 else ra,  # -1e-17 % 360 is 360.0
        dec_deg=dec,
        scale_arcsec_px=scale,
        rotation_deg=wcs_rotation_deg(wcs),
        cd=cd if None not in cd else None,  # type: ignore[arg-type]
        crpix=crpix if None not in crpix else None,  # type: ignore[arg-type]
        warning=ini.get("WARNING", "").strip() or None,
    )


def analyse(fits_path: str | Path, solver: Solver) -> tuple[float | None, int | None]:
    """`(median HFD, stars)` from a second ASTAP pass: the only way to these two numbers that
    leaves no file in the user's folder."""
    if not solver.exe:
        return None, None
    cmd = [solver.exe, "-f", str(fits_path), "-analyse", "30"]
    try:
        _code, out = (solver.run or _run)(cmd, solver.timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError, OSError):
        return None, None
    values = read_ini_text(out)
    stars = _number(values.get("STARS"))
    return _number(values.get("HFD_MEDIAN")), None if stars is None else int(stars)


# [C ASTAP source: RICE_1 in astap_cli from 2026.07.17] hnsky.org says 2026.07.16: GUI only.
FZ_SINCE = (2026, 7, 17)
_VERSION = re.compile(r"version\s+(?:CLI-)?(\d{4})\.(\d{1,2})\.(\d{1,2})", re.IGNORECASE)


def version(solver: Solver) -> tuple[int, int, int] | None:
    """Release date from `-h` help (`version CLI-2025.11.19`). Unread: None."""
    # the one with a window opens it on -h and never exits (measured): not asked
    if not solver.exe or PureWindowsPath(solver.exe).stem.lower() == "astap":
        return None
    try:
        _code, out = (solver.run or _run)([solver.exe, "-h"], solver.timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError, OSError):
        return None
    found = _VERSION.search(out or "")
    return None if found is None else (int(found[1]), int(found[2]), int(found[3]))


def code_page_path(path: str) -> str | None:
    """ASTAP on Windows gets its command line in the ANSI code page: other letters turn `?`
    (measured, CJK). Then the 8.3 short name; None if volume keeps none."""
    if os.name != "nt" or _in_code_page(path):
        return path
    short = _short_name(path)
    return short if short and _in_code_page(short) else None


def _in_code_page(text: str) -> bool:
    try:
        text.encode("mbcs")  # strict: no best-fit `a` for `a-macron`
    except UnicodeEncodeError:
        return False
    return True


def _short_name(path: str) -> str | None:
    if sys.platform != "win32":
        return None
    buffer = ctypes.create_unicode_buffer(32768)  # longest Windows path
    size = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, len(buffer))
    return buffer.value if 0 < size < len(buffer) else None
