"""Where frame points, J2000, from one header: solve, mount, or planned target."""

import math
import re
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any

from astropy.coordinates import FK5, SkyCoord
from astropy.time import Time

from .values import Program, Value, as_count, as_number


class PointingSource(StrEnum):
    SOLVE = "solve"  # ASIAIR plate solve, image centre
    MOUNT = "mount"
    TARGET = "target"  # N.I.N.A. planned target: may not be where mount went


def _sky(ra: Value | None, dec: Value | None) -> tuple[float, float] | None:
    """Degrees J2000 in range; RA 360 is 0."""
    ra_deg, dec_deg = as_number(ra), as_number(dec)
    if ra_deg is None or dec_deg is None or not 0 <= ra_deg <= 360 or abs(dec_deg) > 90:  # noqa: PLR2004
        return None
    return ra_deg % 360, dec_deg


def _solve_centre(values: dict[str, Value]) -> tuple[float, float] | None:
    """Linear TAN at centre of solved image (Calabretta & Greisen 2002, sec. 5.1.3).
    SIP left out: few pixels, hint only. Solved image may be smaller than saved one."""
    if not (str(values.get("CTYPE1", "")).startswith("RA---TAN")):
        return None
    if not (str(values.get("CTYPE2", "")).startswith("DEC--TAN")):
        return None
    keys = ("CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CD1_1", "CD1_2", "CD2_1", "CD2_2")
    numbers = [n for n in (as_number(values.get(k)) for k in keys) if n is not None]
    width, height = as_count(values.get("IMAGEW"), 1), as_count(values.get("IMAGEH"), 1)
    if len(numbers) < len(keys) or width is None or height is None:
        return None
    ra0, dec0, px, py, cd11, cd12, cd21, cd22 = numbers
    det = cd11 * cd22 - cd12 * cd21
    if not math.isfinite(det) or det == 0:
        return None
    # reference pixel inside solved image (archive: 583 of 583); outside: degenerate solve
    if not (0.5 <= px <= width + 0.5 and 0.5 <= py <= height + 0.5):  # noqa: PLR2004
        return None
    dx, dy = (width + 1) / 2 - px, (height + 1) / 2 - py  # FITS pixels count from 1
    east, north = math.radians(cd11 * dx + cd12 * dy), math.radians(cd21 * dx + cd22 * dy)
    if not (math.isfinite(east) and math.isfinite(north)):  # overflow: atan2 would fake a place
        return None
    ra0, dec0 = math.radians(ra0), math.radians(dec0)
    across = math.cos(dec0) - north * math.sin(dec0)
    ra = ra0 + math.atan2(east, across)
    dec = math.atan2(math.sin(dec0) + north * math.cos(dec0), math.hypot(east, across))
    return _sky(math.degrees(ra) % 360, math.degrees(dec))


def _asiair_mount(values: dict[str, Value], start: datetime | None) -> tuple[float, float] | None:
    """ASIAIR mount is of date (JNow): archive, 1.2' from its solve once precessed, 17.7' not.
    No date, no precession: not known."""
    sky = _sky(values.get("RA"), values.get("DEC"))
    if sky is None or start is None:
        return None
    of_date = SkyCoord(*sky, unit="deg", frame=FK5(equinox=Time(start)))
    j2000: Any = of_date.transform_to(FK5(equinox="J2000"))  # astropy stubs: Any
    return _sky(float(j2000.ra.deg), float(j2000.dec.deg))


def _target(values: dict[str, Value]) -> tuple[float, float] | None:
    """OBJCTRA 'HH MM SS', OBJCTDEC '+DD MM SS'; both zero: N.I.N.A. placeholder."""
    ra, dec = _sexagesimal(values.get("OBJCTRA")), _sexagesimal(values.get("OBJCTDEC"))
    if ra is None or dec is None or ra == dec == 0:
        return None
    return _sky(ra * 15, dec)


_SEXAGESIMAL = re.compile(r"([+-]?)(\d{1,3}) (\d{1,2}) (\d{1,2}(?:\.\d+)?)")


def _sexagesimal(written: Value | None) -> float | None:
    """Sign on whole value: '-00 30 00' is -0.5."""
    found = _SEXAGESIMAL.fullmatch(written.strip()) if isinstance(written, str) else None
    if found is None:
        return None
    sign, whole, minutes, seconds = found.groups()
    if int(minutes) >= 60 or float(seconds) >= 60:  # noqa: PLR2004 - malformed: not a place
        return None
    value = int(whole) + int(minutes) / 60 + float(seconds) / 3600
    return -value if sign == "-" else value


def pointing(
    program: Program, values: dict[str, Value], start: datetime | None
) -> tuple[float, float, PointingSource] | None:
    """Where frame looks, J2000: solve, then mount, then target; each out of range falls to next.
    Computed in order, first found wins: mount precession never paid for nothing."""
    asiair = program is Program.ASIAIR
    ra, dec = values.get("RA"), values.get("DEC")
    sources: tuple[tuple[PointingSource, Callable[[], tuple[float, float] | None]], ...] = (
        (PointingSource.SOLVE, lambda: _solve_centre(values) if asiair else None),
        # N.I.N.A.: J2000, EQUINOX 2000 in every file
        (PointingSource.MOUNT, lambda: _asiair_mount(values, start) if asiair else _sky(ra, dec)),
        (PointingSource.TARGET, lambda: _target(values) if program is Program.NINA else None),
    )  # fmt: skip
    for source, compute in sources:
        sky = compute()
        if sky is not None:
            return (*sky, source)
    return None
