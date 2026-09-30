"""A file with an empty primary page (MEF, Rice) keeps its metadata in the first page with data,
merged with the primary. Every read error is a typed `HeaderReadError` the caller counts."""

import hashlib
import json
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

from astropy.io import fits

# Structural keys describe the container, not the frame.
STRUCTURAL_KEYS = frozenset(
    {"SIMPLE", "XTENSION", "EXTEND", "BITPIX", "NAXIS", "PCOUNT", "GCOUNT", "EXTNAME"}
)


class HeaderReadError(Exception):
    """Missing, unreadable, corrupt or non-FITS file."""

    def __init__(self, path: str | Path, cause: Exception) -> None:
        super().__init__(f"lettura header fallita per {path}: {cause}")
        self.path = path
        self.cause = cause


def _has_pixels(hdu: Any) -> bool:
    return isinstance(hdu, fits.CompImageHDU) or bool(hdu.header.get("NAXIS", 0))


def _with_data_page(primary: fits.Header, data_hdr: fits.Header) -> fits.Header:
    combined = primary.copy()
    for card in data_hdr.cards:
        kw = card.keyword
        if not kw or kw in ("COMMENT", "HISTORY") or kw in STRUCTURAL_KEYS:
            continue
        try:
            combined[kw] = (card.value, card.comment)
        except (ValueError, TypeError):
            continue  # odd card: skipped, never a crash
    return combined


def read_frame(path: str | Path) -> tuple[fits.Header, tuple[int, int] | None]:
    """The whole header and, if reading it already reached a page with pixels after the primary,
    that page's `(start, length)` for the fingerprint; None otherwise. Raises `HeaderReadError`."""
    try:
        with fits.open(path, output_verify="silently", ignore_missing_end=True) as hdul:
            # one page at a time up to the first with pixels: `len(hdul)` and `hdul.fileinfo` would
            # make astropy read every page. `fits.open` already refuses a file with no pages.
            primary: Any = None
            # astropy's types say iterating an HDUList yields HDULists: it yields pages
            pages = cast("Iterator[Any]", iter(hdul))
            for hdu in pages:
                if primary is None:
                    primary = hdu.header
                    if primary.get("NAXIS", 0):
                        return primary, None
                elif _has_pixels(hdu):
                    info = hdu.fileinfo()
                    block = (info["datLoc"], info["datSpan"]) if info else None
                    return _with_data_page(primary, hdu.header), block
            return primary, None  # `_data_block` decides the block, fast path first
    except Exception as e:  # noqa: BLE001 - any failure is a typed domain error
        raise HeaderReadError(path, e) from e


def read_header(path: str | Path) -> fits.Header:
    """Raises `HeaderReadError`."""
    return read_frame(path)[0]


FINGERPRINT_BYTES = 65536


BLOCK = 2880  # the FITS block: header and data fill a whole number of them
_CARD = 80
_CLEAN_END = b"END" + b" " * (_CARD - 3)
_KEY_CHARS = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
_BYTES_PER_PIXEL = {8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}
_STRUCTURAL = frozenset({b"SIMPLE", b"BITPIX", b"GROUPS", b"PCOUNT", b"GCOUNT"})  # and NAXISn


def _data_block(path: str | Path, known: tuple[int, int] | None = None) -> tuple[int, int]:
    """Read from the file: the merged header is not the one on disk. The fast path goes first, so
    the block never depends on who asks; `known` (from `read_frame`) spares astropy's reread."""
    fast = _primary_data_block(path)
    if fast is not None:
        return fast
    return known if known is not None else _data_block_astropy(path)


def _primary_data_block(path: str | Path) -> tuple[int, int] | None:
    """The common case (primary page with pixels, no groups, clean END) without astropy, which
    reads every page. None otherwise: it withdraws rather than guess."""
    values, start = {}, 0
    with open(path, "rb") as f:
        while True:
            block = f.read(BLOCK)
            if len(block) < BLOCK:
                return None  # a header without END: astropy decides
            start += BLOCK
            for i in range(0, BLOCK, _CARD):
                card = block[i : i + _CARD]
                # END alone, not the start of a key like ENDTIME
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
            return None  # astropy adds them to the length: the rare case, it decides
        pixel = _BYTES_PER_PIXEL.get(int(values[b"BITPIX"]))
        axes = int(values[b"NAXIS"])
        if pixel is None or axes <= 0:
            return None
        size = pixel * math.prod(int(values[b"NAXIS%d" % n]) for n in range(1, axes + 1))
    except (KeyError, ValueError):
        return None
    return start, size + (-size % BLOCK)


def _data_block_astropy(path: str | Path) -> tuple[int, int]:
    with fits.open(
        path, output_verify="silently", ignore_missing_end=True, memmap=False, lazy_load_hdus=False
    ) as hdul:
        for i, hdu in enumerate(hdul):
            info = hdul.fileinfo(i)
            if info and _has_pixels(hdu):
                return info["datLoc"], info["datSpan"]
    return 0, 0


def frame_fingerprint(
    path: str | Path, header: fits.Header, block: tuple[int, int] | None = None
) -> str:
    """sha256 of the dimensions and `FINGERPRINT_BYTES` from the CENTRE of the data block, away from
    registration borders and overscan: stable across header rewrites. Truncated file: the cards."""
    try:
        # The FILE says where the pixels are, never the header in hand: a reread header may differ
        # in length from the one on disk (astropy adds a missing END).
        start, span = _data_block(path, block)
    except Exception as e:  # noqa: BLE001 - same umbrella as read_frame: counted per file
        raise HeaderReadError(path, e) from e
    chunk = b""
    if span:
        with open(path, "rb") as f:
            f.seek(start + max(0, (span - FINGERPRINT_BYTES) // 2))
            chunk = f.read(FINGERPRINT_BYTES)
    dims = f"{header.get('NAXIS1')}x{header.get('NAXIS2')}:{header.get('BITPIX')}".encode()
    h = hashlib.sha256(dims)
    h.update(chunk if chunk else header.tostring().encode("ascii", "replace"))
    return h.hexdigest()


def header_from_json(header_json: str | None) -> dict[str, Any]:
    """The inverse of `header_to_json`, beside it so readers need not know the format. Repeated keys
    (`HISTORY`, `COMMENT`) collapse on the last."""
    return dict(json.loads(header_json or "[]"))


def header_to_json(header: fits.Header) -> str:
    """A list of `[key, value]` pairs; a value that does not serialise becomes text, so the JSON is
    always valid."""
    pairs = []
    for k, v in header.items():
        if v is None or isinstance(v, (str, int, bool)):
            pairs.append([k, v])
        elif isinstance(v, float):
            pairs.append([k, v if math.isfinite(v) else str(v)])
        else:
            pairs.append([k, str(v)])
    return json.dumps(pairs, ensure_ascii=False)
