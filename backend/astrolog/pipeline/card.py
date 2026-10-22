"""File card: facts read from one header alone, pure (mappa, passo 4). One function per fact."""

import math
import re
import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

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


def camera(values: dict[str, Value]) -> str | None:
    """INSTRUME as written. CAMERAID no: USB path, changes with port."""
    written = values.get("INSTRUME")
    return written.strip() or None if isinstance(written, str) else None


def pixel_um(values: dict[str, Value]) -> float | None:
    """XPIXSZ as written, binning included: physical pixel is XPIXSZ / XBINNING."""
    written = _number(values.get("XPIXSZ"), at_least=0)
    return written if written else None


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


def read_card(program: Program, values: dict[str, Value]) -> Card:
    width, height = frame_size(values)
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
    )
