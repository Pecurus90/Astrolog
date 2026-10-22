"""File card: facts read from one header alone, pure (mappa, passo 4). One function per fact."""

import math
import re
import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from astropy.coordinates import FK5, SkyCoord
from astropy.time import Time

from .fingerprint import frame_size
from .scanner import Program, Value

# DATE-OBS as both programs write it: start of exposure, UTC, no zone (FITS 4.0 sec. 9.1.1).
# fromisoformat alone takes date only (midnight), week dates, compact forms.
_DATE_OBS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?")
_SQLITE_MAX = 2**63 - 1  # largest INTEGER (sqlite.org/datatype3.html)


class FrameType(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    FLAT = "flat"
    BIAS = "bias"
    SNAPSHOT = "snapshot"  # N.I.N.A. test shot: never in hours
    UNKNOWN = "unknown"  # missing, other word, or IMAGETYP and OBJECT disagree: asked later


# What N.I.N.A. and ASIAIR write, casefolded. DARKFLAT: N.I.N.A. < 3.0, "really just DARKs".
_WRITTEN = {
    "light": FrameType.LIGHT,
    "dark": FrameType.DARK,
    "flat": FrameType.FLAT,
    "bias": FrameType.BIAS,
    "darkflat": FrameType.DARK,
}
_SNAPSHOT_NAME = "snapshot"  # N.I.N.A. default target of a snapshot (AnchorableSnapshotVM.cs)


def _word(value: Value | None) -> str | None:
    return value.strip().casefold() if isinstance(value, str) else None


def frame_type(program: Program, values: dict[str, Value]) -> FrameType:
    """N.I.N.A. writes SNAPSHOT as LIGHT (CFitsioFITS.cs): known by its default name only."""
    kind = _WRITTEN.get(_word(values.get("IMAGETYP")) or "", FrameType.UNKNOWN)
    if kind is not FrameType.LIGHT:
        return kind
    name = _word(values.get("OBJECT"))
    if program is Program.NINA and name == _SNAPSHOT_NAME:
        return FrameType.SNAPSHOT
    calibration = _WRITTEN.get(name or "", FrameType.LIGHT) is not FrameType.LIGHT
    return FrameType.UNKNOWN if calibration else kind


def start_utc(values: dict[str, Value]) -> datetime | None:
    """No fallback (MJD-OBS, DATE-AVG, file time): no file lacks DATE-OBS. Past 6 decimals cut."""
    written = values.get("DATE-OBS")
    if not isinstance(written, str) or not _DATE_OBS.fullmatch(written):
        return None
    try:
        return datetime.fromisoformat(written).replace(tzinfo=UTC)
    except ValueError:  # impossible date or time
        return None


def _number(written: Value | None, at_least: float = -math.inf) -> float | None:
    """bool is an int to Python: `T` is not 1. float32 tail cut (_without_float32_tail)."""
    if isinstance(written, bool) or not isinstance(written, int | float):
        return None
    if not math.isfinite(written) or written < at_least:
        return None
    return _without_float32_tail(float(written))


def _count(written: Value | None, at_least: int) -> int | None:
    """Past SQLite INTEGER (64 bit): unknown, else whole scan fails."""
    if isinstance(written, bool) or not isinstance(written, int):
        return None
    return written if at_least <= written <= _SQLITE_MAX else None


def _without_float32_tail(number: float) -> float:
    """Driver float32 printed at 15 digits (DBL_DIG): 3.75999999046326 is 3.76.
    Only when number is that float32; true double untouched."""
    try:
        single = struct.unpack("f", struct.pack("f", number))[0]
    except OverflowError:
        return number
    if f"{single:.15g}" != f"{number:.15g}":
        return number
    for digits in range(1, 10):  # 9 digits round-trip any float32 (IEEE 754 binary32)
        short = float(f"{single:.{digits}g}")
        if struct.unpack("f", struct.pack("f", short))[0] == single:
            return short
    return number


def exposure_s(values: dict[str, Value]) -> float | None:
    """EXPTIME only: EXPOSURE always equal."""
    return _number(values.get("EXPTIME"), at_least=0)


def _name(written: Value | None) -> str | None:
    return written.strip() or None if isinstance(written, str) else None


def _positive(written: Value | None) -> float | None:
    """-0.0 and 0 too: unknown."""
    number = _number(written, at_least=0)
    return number if number else None


def camera(values: dict[str, Value]) -> str | None:
    """INSTRUME as written. CAMERAID no: USB path, changes with port."""
    return _name(values.get("INSTRUME"))


def optics(program: Program, values: dict[str, Value]) -> str | None:
    """TELESCOP as written (SBIG). ASIAIR writes mount there: not known."""
    return None if program is Program.ASIAIR else _name(values.get("TELESCOP"))


def focal_mm(values: dict[str, Value]) -> float | None:
    """Hint on both: N.I.N.A. from profile, ASIAIR from its solve (varies by 1-3 mm)."""
    return _positive(values.get("FOCALLEN"))


def pixel_um(values: dict[str, Value]) -> float | None:
    """XPIXSZ as written, binning included: physical pixel is XPIXSZ / XBINNING."""
    return _positive(values.get("XPIXSZ"))


def bayer(program: Program, values: dict[str, Value]) -> bool | None:
    """Raw frame is Bayer mosaic. N.I.N.A. omits BAYERPAT only for mono or pattern None
    (CFitsioFITS.cs); ASIAIR without it: no case, not known."""
    if "BAYERPAT" not in values:
        return False if program is Program.NINA else None
    written = values["BAYERPAT"]
    return True if isinstance(written, str) and written.strip() else None


def iso(values: dict[str, Value]) -> int | None:
    """ASIAIR with DSLR writes ISO as string: '800'."""
    written = values.get("ISO")
    if isinstance(written, str):
        digits = written.strip()
        written = int(digits) if digits.isascii() and digits.isdigit() else None
    return _count(written, 1)


class PointingSource(StrEnum):
    SOLVE = "solve"  # ASIAIR plate solve, image centre
    MOUNT = "mount"
    TARGET = "target"  # N.I.N.A. planned target: may not be where mount went


def _sky(ra: Value | None, dec: Value | None) -> tuple[float, float] | None:
    """Degrees J2000 in range; RA 360 is 0."""
    ra_deg, dec_deg = _number(ra), _number(dec)
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
    numbers = [n for n in (_number(values.get(k)) for k in keys) if n is not None]
    width, height = _count(values.get("IMAGEW"), 1), _count(values.get("IMAGEH"), 1)
    if len(numbers) < len(keys) or width is None or height is None:
        return None
    ra0, dec0, px, py, cd11, cd12, cd21, cd22 = numbers
    if cd11 * cd22 - cd12 * cd21 == 0:
        return None
    dx, dy = (width + 1) / 2 - px, (height + 1) / 2 - py  # FITS pixels count from 1
    east, north = math.radians(cd11 * dx + cd12 * dy), math.radians(cd21 * dx + cd22 * dy)
    ra0, dec0 = math.radians(ra0), math.radians(dec0)
    across = math.cos(dec0) - north * math.sin(dec0)
    ra = ra0 + math.atan2(east, across)
    dec = math.atan2(math.sin(dec0) + north * math.cos(dec0), math.hypot(east, across))
    return _sky(math.degrees(ra) % 360, math.degrees(dec))


def _asiair_mount(values: dict[str, Value]) -> tuple[float, float] | None:
    """ASIAIR mount is of date (JNow): archive, 1.2' from its solve once precessed, 17.7' not.
    No date, no precession: not known."""
    sky, start = _sky(values.get("RA"), values.get("DEC")), start_utc(values)
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
    program: Program, values: dict[str, Value]
) -> tuple[float, float, PointingSource] | None:
    """Where frame looks, J2000: solve, then mount, then target; each out of range falls to next."""
    mount = (
        _asiair_mount(values)
        if program is Program.ASIAIR
        else _sky(values.get("RA"), values.get("DEC"))
    )  # N.I.N.A.: J2000, EQUINOX 2000 in every file
    for source, sky in (
        (PointingSource.SOLVE, _solve_centre(values) if program is Program.ASIAIR else None),
        (PointingSource.MOUNT, mount),
        (PointingSource.TARGET, _target(values) if program is Program.NINA else None),
    ):
        if sky is not None:
            return (*sky, source)
    return None


@dataclass(frozen=True, slots=True)
class Card:
    """Fields named and ordered as pipeline_cards columns. None: not known."""

    frame_type: FrameType
    start_utc: datetime | None
    exposure_s: float | None
    camera: str | None
    width: int | None  # frame, after binning and crop
    height: int | None
    bin_x: int | None
    bin_y: int | None
    pixel_um: float | None  # with binning (SBIG; CFitsioFITS.cs; ASIAIR "with binning")
    bayer: bool | None
    gain: int | None
    iso: int | None
    offset: int | None
    ccd_temp_c: float | None
    set_temp_c: float | None
    optics: str | None
    focal_mm: float | None
    filter: str | None  # as written; what it is: filters.resolve
    pointing_ra_deg: float | None  # J2000, every frame type: user filters by type
    pointing_dec_deg: float | None
    pointing_source: PointingSource | None


def read_card(program: Program, values: dict[str, Value]) -> Card:
    width, height = frame_size(values)
    ra, dec, source = pointing(program, values) or (None, None, None)
    return Card(
        frame_type=frame_type(program, values),
        start_utc=start_utc(values),
        exposure_s=exposure_s(values),
        camera=camera(values),
        width=_count(width, 1),
        height=_count(height, 1),
        bin_x=_count(values.get("XBINNING"), 1),
        bin_y=_count(values.get("YBINNING"), 1),
        pixel_um=pixel_um(values),
        bayer=bayer(program, values),
        gain=_count(values.get("GAIN"), 0),
        iso=iso(values),
        offset=_count(values.get("OFFSET"), 0),
        ccd_temp_c=_number(values.get("CCD-TEMP")),
        set_temp_c=_number(values.get("SET-TEMP")),
        optics=optics(program, values),
        focal_mm=focal_mm(values),
        filter=_name(values.get("FILTER")),
        pointing_ra_deg=ra,
        pointing_dec_deg=dec,
        pointing_source=source,
    )
