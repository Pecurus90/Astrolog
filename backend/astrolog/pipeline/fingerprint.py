"""Frame identity: dimensions, exposure start, 64 KB from data block centre; stable across
header rewrites and moves. Without DATE-OBS, same as fits/header_read.py (ADR 0030)."""

# jscpd:ignore-start  # noqa: ERA001
import hashlib
import math
import os
import warnings
from dataclasses import dataclass
from typing import Any

from astropy.io import fits

from .walk import long_path

FINGERPRINT_BYTES = 65536
BLOCK = 2880  # header and data fill whole blocks
CARD = 80
_CLEAN_END = b"END" + b" " * (CARD - 3)
_KEY_CHARS = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
_BYTES_PER_PIXEL = {8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}
_STRUCTURAL = frozenset({b"SIMPLE", b"BITPIX", b"GROUPS", b"PCOUNT", b"GCOUNT"})  # and NAXISn


@dataclass(frozen=True)
class FrameIdentity:
    fingerprint: str
    complete: bool  # file holds every byte its header announces


def data_block(path: str | os.PathLike[str]) -> tuple[int, int]:
    """(start, length) of pixels. Fast path reads primary's blocks; compressed (empty primary) or
    other shape: astropy, which reads every page."""
    fast = _primary_data_block(path)
    return fast if fast is not None else _data_block_astropy(path)


def _primary_data_block(path: str | os.PathLike[str]) -> tuple[int, int] | None:
    """Common case (primary with pixels, no groups, clean END) without astropy. Else None:
    withdraws, never guesses."""
    values, start = {}, 0
    with open(long_path(path), "rb") as f:
        while True:
            block = f.read(BLOCK)
            if len(block) < BLOCK:
                return None  # header without END: astropy decides
            start += BLOCK
            for i in range(0, BLOCK, CARD):
                card = block[i : i + CARD]
                # END alone, not start of key like ENDTIME
                if card[:3] == b"END" and card[3] not in _KEY_CHARS:
                    return _span(values, start) if card == _CLEAN_END else None
                key = card[:8].rstrip()
                if (key in _STRUCTURAL or key.startswith(b"NAXIS")) and card[8:10] == b"= ":
                    values[key] = card[10:].split(b"/")[0].strip()


def _span(values: dict[bytes, bytes], start: int) -> tuple[int, int] | None:
    try:
        if values.get(b"SIMPLE") != b"T" or b"GROUPS" in values:
            return None
        if int(values.get(b"PCOUNT", 0)) != 0 or int(values.get(b"GCOUNT", 1)) != 1:
            return None  # astropy adds them to length: rare case, it decides
        pixel = _BYTES_PER_PIXEL.get(int(values[b"BITPIX"]))
        axes = int(values[b"NAXIS"])
        if pixel is None or axes <= 0:
            return None
        size = pixel * math.prod(int(values[b"NAXIS%d" % n]) for n in range(1, axes + 1))
    except (KeyError, ValueError):
        return None
    return start, size + (-size % BLOCK)


def _has_pixels(hdu: Any) -> bool:
    return isinstance(hdu, fits.CompImageHDU) or bool(hdu.header.get("NAXIS", 0))


def _data_block_astropy(path: str | os.PathLike[str]) -> tuple[int, int]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # notes on odd cards: only block matters here
        return _astropy_block(path)


def _astropy_block(path: str | os.PathLike[str]) -> tuple[int, int]:
    with fits.open(
        long_path(path),
        output_verify="silently",
        ignore_missing_end=True,
        memmap=False,
        lazy_load_hdus=False,
    ) as hdul:
        for i, hdu in enumerate(hdul):
            info = hdul.fileinfo(i)
            if info and _has_pixels(hdu):
                return info["datLoc"], info["datSpan"]
    return 0, 0


def _primary_cards(path: str | os.PathLike[str]) -> bytes:
    """No pixels: primary's cards as astropy writes them, as today."""
    with (
        warnings.catch_warnings(),
        fits.open(long_path(path), output_verify="silently", ignore_missing_end=True) as hdul,
    ):
        warnings.simplefilter("ignore")
        primary: Any = hdul[0]  # astropy stubs type int index as slice: HDUList
        return primary.header.tostring().encode("ascii", "replace")


def frame_size(cards: dict[str, Any]) -> tuple[Any, Any]:
    """(width, height) as written. Compressed: ZNAXISn (FITS 4.0 sec. 10)."""
    return cards.get("NAXIS1", cards.get("ZNAXIS1")), cards.get("NAXIS2", cards.get("ZNAXIS2"))


def frame_identity(path: str | os.PathLike[str], cards: dict[str, Any]) -> FrameIdentity:
    """sha256 of dimensions, DATE-OBS if written, FINGERPRINT_BYTES from data block centre, away
    from registration borders and overscan; no pixels: cards."""
    start, span = data_block(path)
    chunk = b""
    if span:
        with open(long_path(path), "rb") as f:
            f.seek(start + max(0, (span - FINGERPRINT_BYTES) // 2))
            chunk = f.read(FINGERPRINT_BYTES)
    width, height = frame_size(cards)
    shape = f"{width}x{height}:{cards.get('BITPIX')}"
    exposure_start = cards.get("DATE-OBS")  # same pixels, other instant: other frame
    digest = hashlib.sha256(
        f"{shape}:{exposure_start}".encode() if isinstance(exposure_start, str) else shape.encode()
    )
    digest.update(chunk or _primary_cards(path))
    complete = os.path.getsize(long_path(path)) >= start + span
    return FrameIdentity(digest.hexdigest(), complete)


# jscpd:ignore-end  # noqa: ERA001
