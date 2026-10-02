"""Drives the ASTAP solver. Never `-update` (it rewrites the user's FITS) nor `-extract` (it leaves
a CSV beside the file, ignoring `-o`); ASTAP prints numbers with the machine's decimal separator."""

import contextlib
import logging
import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

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

# More than twice the slowest blind solve on a large sensor (docs/domini/spina.md): beyond it,
# ASTAP has hung.
TIMEOUT_S = 60
# A few degrees would do with the header's pointing; 30 absorbs an off-centre mount at no cost,
# since speed depends on the field, not the radius.
SEARCH_RADIUS_DEG = 30
BLIND_RADIUS_DEG = 180

NO_STARS = "no_stars"  # with no stars, a typeless file is a calibration frame (`typeless`)
# Closed list of codes, never ASTAP's sentence: sentences change between versions and would
# reach the screen in English.
REASONS = (NO_STARS, "no_solution", "timeout", "astap_missing", "file_missing",
           "no_star_database", "internal_error")  # fmt: skip

# Compared lowercase and by containment: the exact text changes, the key words do not.
_ERROR_WORDS = (
    ("not enough stars", NO_STARS),
    ("file not found", "file_missing"),
    # Both `No star database found.` (missing) and `Error reading star database.` (truncated
    # download), as ASTAP CLI-2025.11.19 prints them: a half download is as common as none.
    ("star database", "no_star_database"),
)


@dataclass(frozen=True)
class Solution:
    ok: bool
    reason: str | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    scale_arcsec_px: float | None = None
    rotation_deg: float | None = None


# Codes, not sentences: they are shown on screen, and a new word would arrive untranslated.
SOURCES = ("declared", "env", "path", "known_place")


type Which = Callable[[str], str | None]


def find_exe(
    declared: str | None = None,
    env: Mapping[str, str] | None = None,
    which: Which = shutil.which,
    candidates: Iterable[str | Path] = CANDIDATES,
) -> str | None:
    """Calls `_cerca`, not `where_exe`: the suite's fence replaces both public ones, and one going
    through the other would pick up the stub even when captured on purpose beforehand."""
    return _cerca(declared, env, which, candidates)[0]


def where_exe(
    declared: str | None = None,
    env: Mapping[str, str] | None = None,
    which: Which = shutil.which,
    candidates: Iterable[str | Path] = CANDIDATES,
) -> tuple[str | None, str | None]:
    """The channel is shown because the automatic search is wrong exactly when it finds something
    (an old ASTAP in PATH). The user's choice beats the variable, set by the NAS admin."""
    return _cerca(declared, env, which, candidates)


def _cerca(
    declared: str | None,
    env: Mapping[str, str] | None,
    which: Which,
    candidates: Iterable[str | Path],
) -> tuple[str | None, str | None]:
    env = os.environ if env is None else env
    scritto, canale = (declared, "declared") if declared else (env.get(ENV_EXE), "env")
    if scritto:
        # Windows' *Copy as path* wraps it in quotes: with them inside the file is never found,
        # and the warning would blame the wrong thing.
        scritto = scritto.strip().strip("\"'")
        # A written wrong path, or a folder, stops the search: falling back on PATH would say
        # "found" to whoever wrote it wrong.
        return (scritto, canale) if Path(scritto).is_file() else (None, None)
    for name in EXE_NAMES:
        found = which(name)
        if found:
            return found, "path"
    for candidate in candidates:
        if Path(candidate).is_file():
            return str(candidate), "known_place"
    return None, None


def star_databases(exe: str | Path | None) -> tuple[str, ...]:
    """Only beside the resolved executable, not in known install folders, which would show another
    program's catalogue. Looked at, not asked: asking ASTAP means running it."""
    if exe is None:
        return ()
    with contextlib.suppress(OSError):  # folder gone, disk unplugged, permission denied
        nomi = (DB_NAME.match(f.name) for f in Path(exe).resolve().parent.iterdir())
        return tuple(sorted({m.group(1).lower() for m in nomi if m}))
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


def _reason_of(ini: Mapping[str, str]) -> str:
    message = str(ini.get("ERROR", "")).lower()
    for words, code in _ERROR_WORDS:
        if words in message:
            return code
    return "no_solution"


def command(  # noqa: PLR0913
    fits_path: str | Path,
    out_base: str | Path,
    *,
    exe: str,
    field_deg: float | None = None,
    ra_deg: float | None = None,
    dec_deg: float | None = None,
) -> list[str]:
    """Built without running it, so a test proves the forbidden flags are absent and the units
    are the ones ASTAP wants."""
    cmd = [
        exe,
        "-f",
        str(fits_path),
        "-o",
        str(out_base),
        # The field is the speed lever: where the header lacks focal or pixel size, the blind
        # field search pays for it.
        "-fov",
        f"{field_deg:.3f}" if field_deg else "0",
        "-z",
        "0",
        "-wcs",
    ]
    if ra_deg is not None and dec_deg is not None:
        # ASTAP wants HOURS of right ascension and the distance from the SOUTH pole: getting them
        # wrong gives no error, it gives the sky of another point.
        cmd += ["-ra", f"{ra_deg / 15.0:.5f}", "-spd", f"{dec_deg + 90.0:.4f}", "-r",
                str(SEARCH_RADIUS_DEG)]  # fmt: skip
    else:
        cmd += ["-r", str(BLIND_RADIUS_DEG)]
    return cmd


def solve(  # noqa: PLR0913
    fits_path: str | Path,
    out_base: str | Path,
    *,
    field_deg: float | None = None,
    ra_deg: float | None = None,
    dec_deg: float | None = None,
    exe: str | None = None,
    run: Run | None = None,
    timeout_s: float = TIMEOUT_S,
) -> Solution:
    """Writes `<out_base>.ini` and `.wcs` where we say, never beside the user's FITS. Never raises
    for the solver's fault: a missing or hung ASTAP is a frame without sky and its reason."""
    if not exe:
        return Solution(ok=False, reason="astap_missing")
    cmd = command(fits_path, out_base, exe=exe, field_deg=field_deg, ra_deg=ra_deg, dec_deg=dec_deg)
    try:
        (run or _run)(cmd, timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError):
        log.info("astap: tempo scaduto", extra={"file": str(fits_path)})
        return Solution(ok=False, reason="timeout")
    except OSError as err:
        log.warning("astap: non si e' potuto lanciare", extra={"error": str(err)})
        return Solution(ok=False, reason="astap_missing")

    return from_ini(read_ini(f"{out_base}.ini"))


def from_ini(ini: dict[str, str]) -> Solution:
    """Also the cache's path. A half-written result can say `PLTSOLVD=T` without the numbers: it
    counts as no solution, so the cache reader drops it and solves again."""
    if not solved(ini):
        return Solution(ok=False, reason=_reason_of(ini))
    found = Solution(
        ok=True,
        ra_deg=as_float(ini.get("CRVAL1")),
        dec_deg=as_float(ini.get("CRVAL2")),
        scale_arcsec_px=wcs_scale(ini),
        rotation_deg=wcs_rotation_deg(ini),
    )
    if None in (found.ra_deg, found.dec_deg, found.scale_arcsec_px):
        return Solution(ok=False, reason="no_solution")
    return found


def analyse(
    fits_path: str | Path,
    *,
    exe: str | None = None,
    run: Run | None = None,
    timeout_s: float = TIMEOUT_S,
) -> tuple[float | None, int | None]:
    """`(median HFD, stars)` from a second ASTAP pass: the only way to these two numbers that
    leaves no file in the user's folder, since `-extract` would write a CSV beside the FITS."""
    if not exe:
        return None, None
    try:
        _code, out = (run or _run)([exe, "-f", str(fits_path), "-analyse", "30"], timeout_s)
    except (subprocess.TimeoutExpired, TimeoutError, OSError):
        return None, None
    values = read_ini_text(out)
    stars = _number(values.get("STARS"))
    return _number(values.get("HFD_MEDIAN")), None if stars is None else int(stars)
