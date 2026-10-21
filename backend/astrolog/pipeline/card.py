"""File card: facts read from one header alone, pure (mappa, passo 4). One function per fact."""

from enum import StrEnum

from .scanner import Program, Value


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
