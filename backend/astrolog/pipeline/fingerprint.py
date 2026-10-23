"""Frame identity from header: camera, start to fraction of second, size, exposure (ADR 0030).
Pixels only without them; same file handle, never reopened, no astropy."""

import hashlib
import math
from dataclasses import dataclass
from typing import BinaryIO

from .card import camera, exposure_s, start_utc
from .values import Value, as_count, frame_size

FINGERPRINT_BYTES = 65536
BLOCK = 2880  # header and data fill whole blocks
CARD = 80
_BYTES = {8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}  # FITS 4.0 table 8: BITPIX
_MAX_AXES = 999  # FITS 4.0 sec. 4.4.1.1
_MAX_BYTES = 2**62  # past any file system; keeps seek offsets in a signed 64-bit integer


@dataclass(frozen=True)
class Header:
    cards: dict[str, Value]
    data_start: int  # first byte of frame's data block (page 2 when compressed)
    data_length: int | None  # padded to BLOCK; None: header does not say


@dataclass(frozen=True)
class FrameIdentity:
    fingerprint: str
    complete: bool  # file holds every byte its header announces


def data_length(raw: dict[str, Value]) -> int | None:
    """FITS 4.0 sec. 4.4.1.1: |BITPIX|/8 * GCOUNT * (PCOUNT + prod NAXISn), whole blocks; also
    tile-compressed table (heap in PCOUNT). No NAXIS: no data. Broken: None."""
    if raw.get("NAXIS", 0) == 0:
        return 0
    naxis = as_count(raw.get("NAXIS"), 0)
    if naxis is None or naxis > _MAX_AXES:  # bound before any list: never huge allocation
        return None
    written = [as_count(raw.get(f"NAXIS{n}"), 0) for n in range(1, naxis + 1)]
    pcount, gcount = as_count(raw.get("PCOUNT", 0), 0), as_count(raw.get("GCOUNT", 1), 0)
    bitpix = raw.get("BITPIX")
    width = _BYTES.get(bitpix) if isinstance(bitpix, int) else None
    if width is None or pcount is None or gcount is None or not written or None in written:
        return None
    axes = [axis for axis in written if axis is not None]
    if raw.get("GROUPS") is True and axes[0] == 0:  # random groups: NAXIS1 = 0 is no axis
        axes = axes[1:]
    size = width * gcount * (pcount + math.prod(axes))
    if size > _MAX_BYTES:  # beyond any file: seek would overflow
        return None
    return size + (-size % BLOCK)


def _side(value: Value | None) -> bool:
    """Side 0 unknown, as on card."""
    return as_count(value, 1) is not None


def frame_identity(header: Header, size: int, fh: BinaryIO) -> FrameIdentity:
    """Same shot is same frame: .fits and fpack copy, ':00.4' and ':00.400'. Shot incomplete:
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


def _shot(cards: dict[str, Value]) -> str | None:
    """Start without fraction of second: short shots share it, pixels decide (archive: none)."""
    if "." not in str(cards.get("DATE-OBS", "")):
        return None
    name, start, exposure = camera(cards), start_utc(cards), exposure_s(cards)
    width, height = frame_size(cards)
    if name is None or start is None or exposure is None or not _side(width):
        return None
    if not _side(height):
        return None
    when = start.isoformat(timespec="microseconds")
    return f"v2|{name}|{when}|{width}x{height}|{exposure!r}"


def _shape(cards: dict[str, Value]) -> str:
    width, height = frame_size(cards)
    shape = f"{width}x{height}:{cards.get('BITPIX')}"
    start = cards.get("DATE-OBS")
    return f"{shape}:{start}" if isinstance(start, str) else shape
