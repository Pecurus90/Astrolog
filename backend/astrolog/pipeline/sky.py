"""Where frame points, J2000, from one header: solve, mount, or planned target."""

import math
import re
import warnings
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum

import erfa
from erfa import ErfaWarning

from .values import Program, Value, as_count, as_number

_J2000_PRECESSION = erfa.bp06(2451545.0, 0.0)[1]  # IAU 2006 precession at J2000.0 TT


class PointingSource(StrEnum):
    SOLVE = "solve"  # ASIAIR plate solve, image centre
    MOUNT = "mount"  # N.I.N.A. only
    TARGET = "target"  # planned, N.I.N.A. or ASIAIR: may not be where mount went


def _sky(ra: Value | None, dec: Value | None) -> tuple[float, float] | None:
    """Degrees J2000 in range; RA 360 is 0."""
    ra_deg, dec_deg = as_number(ra), as_number(dec)
    if ra_deg is None or dec_deg is None or not 0 <= ra_deg <= 360 or abs(dec_deg) > 90:
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
    # owner's rule, no WCS convention: reference inside solved image (archive: 583 of 583)
    if not (0.5 <= px <= width + 0.5 and 0.5 <= py <= height + 0.5):
        return None
    dx, dy = (width + 1) / 2 - px, (height + 1) / 2 - py  # FITS pixels count from 1
    east, north = math.radians(cd11 * dx + cd12 * dy), math.radians(cd21 * dx + cd22 * dy)
    if not (math.isfinite(east) and math.isfinite(north)):  # overflow: atan2 would fake a place
        return None
    return _sky(*deproject((ra0, dec0), east, north))


def deproject(centre: tuple[float, float], east: float, north: float) -> tuple[float, float]:
    """Gnomonic (TAN) inverse, Calabretta & Greisen 2002 sec. 5.1.3: radians off centre to
    RA, Dec degrees, RA in [0, 360)."""
    ra0, dec0 = math.radians(centre[0]), math.radians(centre[1])
    across = math.cos(dec0) - north * math.sin(dec0)
    ra = math.degrees(ra0 + math.atan2(east, across)) % 360.0
    dec = math.atan2(math.sin(dec0) + north * math.cos(dec0), math.hypot(east, across))
    return (0.0 if ra == 360.0 else ra), math.degrees(dec)  # -1e-17 % 360 is 360.0


def _asiair_target(values: dict[str, Value], start: datetime | None) -> tuple[float, float] | None:
    """ASIAIR RA/DEC: 'Object Right Ascension', of date (JNow): 1.2' from its solve once
    precessed, 17.7' not. No date, no precession: not known."""
    sky = _written(values)
    if sky is None or start is None:
        return None
    seconds = start.second + start.microsecond / 1e6
    with warnings.catch_warnings():  # year past leap-second table: 'dubious year', precession fine
        warnings.simplefilter("ignore", ErfaWarning)
        day = (start.year, start.month, start.day, start.hour, start.minute, seconds)
        tt = erfa.taitt(*erfa.utctai(*erfa.dtf2d("UTC", *day)))
    # astropy FK5 to FK5 (fk5._precession_matrix), without SkyCoord: 30x faster, same to 1e-9"
    of_date_to_j2000 = _J2000_PRECESSION @ erfa.bp06(*tt)[1].swapaxes(-2, -1)
    ra, dec = erfa.c2s(of_date_to_j2000 @ erfa.s2c(math.radians(sky[0]), math.radians(sky[1])))
    return _sky(math.degrees(erfa.anp(ra)), math.degrees(dec))


def _written(values: dict[str, Value]) -> tuple[float, float] | None:
    """RA/DEC as written; both zero: placeholder, as for target and site (archive: never)."""
    sky = _sky(values.get("RA"), values.get("DEC"))
    return None if sky == (0, 0) else sky


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
    if int(minutes) >= 60 or float(seconds) >= 60:
        return None
    value = int(whole) + int(minutes) / 60 + float(seconds) / 3600
    return -value if sign == "-" else value


def pointing(
    program: Program, values: dict[str, Value], start: datetime | None
) -> tuple[float, float, PointingSource] | None:
    """Where frame looks, J2000: solve, then mount, then target; each out of range falls to next.
    Computed in order, first found wins: target precession never paid for nothing."""
    asiair = program is Program.ASIAIR
    sources: tuple[tuple[PointingSource, Callable[[], tuple[float, float] | None]], ...] = (
        (PointingSource.SOLVE, lambda: _solve_centre(values) if asiair else None),
        # N.I.N.A.: J2000, EQUINOX 2000 in every file
        (PointingSource.MOUNT, lambda: None if asiair else _written(values)),
        (PointingSource.TARGET,
         lambda: _asiair_target(values, start) if asiair else _target(values)),
    )  # fmt: skip
    for source, compute in sources:
        sky = compute()
        if sky is not None:
            return (*sky, source)
    return None
