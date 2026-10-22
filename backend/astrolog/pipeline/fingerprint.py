"""Frame identity from header: camera, exposure start, size, exposure time (ADR 0030).
Pixels only without them; same file handle, never reopened, no astropy."""

import hashlib
import math
from dataclasses import dataclass
from typing import Any, BinaryIO

from .card import exposure_s, start_utc
from .values import as_name, frame_size

FINGERPRINT_BYTES = 65536
BLOCK = 2880  # header and data fill whole blocks
CARD = 80
_BYTES = {8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}  # FITS 4.0 table 8: BITPIX
_MAX_AXES = 999  # FITS 4.0 sec. 4.4.1.1
_MAX_BYTES = 2**62  # past any file system; keeps seek offsets in a signed 64-bit integer


@dataclass(frozen=True)
class Header:
    cards: dict[str, Any]
    data_start: int  # first byte of frame's data block (page 2 when compressed)
    data_length: int | None  # padded to BLOCK; None: header does not say


@dataclass(frozen=True)
class FrameIdentity:
    fingerprint: str
    complete: bool  # file holds every byte its header announces


def data_length(raw: dict[str, Any]) -> int | None:
    """FITS 4.0 sec. 4.4.1.1: |BITPIX|/8 * GCOUNT * (PCOUNT + prod NAXISn), whole blocks; also
    tile-compressed table (heap in PCOUNT). No NAXIS: no data. Broken: None."""
    naxis = raw.get("NAXIS", 0)
    if naxis == 0:
        return 0
    if not _count(naxis) or naxis > _MAX_AXES:  # bound before any list: never huge allocation
        return None
    written = [raw.get(f"NAXIS{n}") for n in range(1, naxis + 1)]
    counts = [raw.get("PCOUNT", 0), raw.get("GCOUNT", 1), *written]
    if raw.get("BITPIX") not in _BYTES or not written or not all(_count(v) for v in counts):
        return None
    axes = [int(axis) for axis in written if axis is not None]
    if raw.get("GROUPS") is True and axes[0] == 0:  # random groups: NAXIS1 = 0 is no axis
        axes = axes[1:]
    size = _BYTES[raw["BITPIX"]] * raw.get("GCOUNT", 1) * (raw.get("PCOUNT", 0) + math.prod(axes))
    if size > _MAX_BYTES:  # beyond any file: seek would overflow
        return None
    return size + (-size % BLOCK)


def _count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def frame_identity(header: Header, size: int, fh: BinaryIO) -> FrameIdentity:
    """Same shot is same frame: .fits and fpack copy, ':00' and ':00.000'. Shot incomplete:
    size, BITPIX, start and FINGERPRINT_BYTES from data centre (as before); no data: header."""
    length = header.data_length or 0
    shot = _shot(header.cards)
    if shot is not None:
        digest = hashlib.sha256(shot.encode())
    else:
        digest = hashlib.sha256(_shape(header.cards).encode())
        if length:
            fh.seek(header.data_start + max(0, (length - FINGERPRINT_BYTES) // 2))
            digest.update(fh.read(FINGERPRINT_BYTES))
        else:
            fh.seek(0)
            digest.update(fh.read(header.data_start))
    return FrameIdentity(digest.hexdigest(), size >= header.data_start + length)


def _shot(cards: dict[str, Any]) -> str | None:
    camera, start, exposure = as_name(cards.get("INSTRUME")), start_utc(cards), exposure_s(cards)
    width, height = frame_size(cards)
    if camera is None or start is None or exposure is None or not _count(width):
        return None
    if not _count(height):
        return None
    when = start.isoformat(timespec="microseconds")
    return f"v2|{camera}|{when}|{width}x{height}|{exposure!r}"


def _shape(cards: dict[str, Any]) -> str:
    width, height = frame_size(cards)
    shape = f"{width}x{height}:{cards.get('BITPIX')}"
    start = cards.get("DATE-OBS")
    return f"{shape}:{start}" if isinstance(start, str) else shape
