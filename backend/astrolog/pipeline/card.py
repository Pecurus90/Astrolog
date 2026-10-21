"""File card: facts read from one header alone, pure (mappa, passo 4). One function per fact."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from .scanner import Program, Value

# DATE-OBS as both programs write it: start of exposure, UTC, no zone (FITS 4.0 sec. 9.1.1).
# fromisoformat alone takes date only (midnight), week dates, compact forms.
_DATE_OBS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?")


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


def exposure_s(values: dict[str, Value]) -> float | None:
    """EXPTIME only: EXPOSURE always equal. bool is an int to Python: `T` is not 1 s."""
    written = values.get("EXPTIME")
    if isinstance(written, bool) or not isinstance(written, int | float) or written < 0:
        return None
    return float(written)


@dataclass(frozen=True, slots=True)
class Card:
    frame_type: FrameType
    start_utc: datetime | None  # None: not known
    exposure_s: float | None


def read_card(program: Program, values: dict[str, Value]) -> Card:
    return Card(frame_type(program, values), start_utc(values), exposure_s(values))
