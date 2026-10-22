"""Finds FITS files, extracts header of those N.I.N.A. and ASIAIR wrote (ADR 0029)."""

import math
import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

from .fingerprint import BLOCK, CARD, Header, data_length, frame_identity
from .values import Program, Value, as_count
from .walk import long_path

MAX_HEADER_BLOCKS = 100  # owner's cap, no convention: 288 KB; real files use 2-4
_COMMENTARY = frozenset({"COMMENT", "HISTORY"})  # FITS 4.0 4.4.2.4 free text; format notes, dropped

_STRUCTURE = ("SIMPLE", "BITPIX", "NAXIS", "NAXIS1", "NAXIS2", "BZERO", "EXTEND")

# Complete for uncompressed: writers FITS/FITSHeader.cs, FITS/CFitsioFITS.cs (BSCALE, checksums
# via cfitsio); user-defined keys not N.I.N.A.'s own.
NINA_KEYS = frozenset({
    *_STRUCTURE,
    "IMAGETYP", "EXPOSURE", "EXPTIME", "DATE-LOC", "DATE-OBS", "MJD-OBS", "DATE-AVG", "MJD-AVG",
    "XBINNING", "YBINNING", "GAIN", "OFFSET", "EGAIN", "XPIXSZ", "YPIXSZ", "INSTRUME", "CAMERAID",
    "SET-TEMP", "CCD-TEMP", "READOUTM", "BAYERPAT", "XBAYROFF", "YBAYROFF", "USBLIMIT",
    "TELESCOP", "FOCALLEN", "FOCRATIO", "RA", "DEC", "CENTALT", "CENTAZ", "AIRMASS", "PIERSIDE",
    "SITEELEV", "SITELAT", "SITELONG", "OBSERVER", "OBSERVAT", "SITENAME",
    "FWHEEL", "FILTER", "OBJECT", "OBJCTRA", "OBJCTDEC", "OBJCTROT",
    "FOCNAME", "FOCPOS", "FOCUSPOS", "FOCUSSZ", "FOCTEMP", "FOCUSTEM",
    "ROTNAME", "ROTATOR", "ROTATANG", "ROTSTPSZ",
    "CLOUDCVR", "DEWPOINT", "HUMIDITY", "PRESSURE", "SKYBRGHT", "MPSAS", "SKYTEMP", "STARFWHM",
    "AMBTEMP", "WINDDIR", "WINDGUST", "WINDSPD",
    "ROWORDER", "EQUINOX", "SWCREATE", "BSCALE", "CHECKSUM", "DATASUM",
})  # fmt: skip

# Partial: ZWO publishes no list; keys of 696 real ASIAIR files.
ASIAIR_KEYS = frozenset({
    *_STRUCTURE, "BSCALE",
    "CREATOR", "IMAGETYP", "EXPOSURE", "EXPTIME", "DATE-OBS",
    "XBINNING", "YBINNING", "CCDXBIN", "CCDYBIN", "XPIXSZ", "YPIXSZ", "XORGSUBF", "YORGSUBF",
    "GAIN", "OFFSET", "EGAIN", "ISO", "INSTRUME", "SET-TEMP", "CCD-TEMP", "BAYERPAT", "GUIDECAM",
    "TELESCOP", "FOCALLEN", "FOCUSPOS", "ROTATOR", "RA", "DEC", "OBJECT", "SITELAT", "SITELONG",
    "CTYPE1", "CTYPE2", "CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CD1_1", "CD1_2", "CD2_1", "CD2_2",
    "IMAGEW", "IMAGEH",
})  # fmt: skip

# FITS 4.0 sec. 4.1.2.1 keyword; HIERARCH name: same words, blank-separated.
_KEY = re.compile(r"[A-Z0-9_-]{1,8}")
_HIERARCH_NAME = re.compile(r"[A-Z0-9_-]+( +[A-Z0-9_-]+)*")
# FITS 4.0 sec. 4.2.3-4.2.4: Python also takes NaN, inf, 1_000; FITS does not.
_INTEGER = re.compile(r"[+-]?\d+")
_REAL = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([EeD][+-]?\d+)?")  # lower e: Python read it already
# SIP distortion terms of ASIAIR plate solve: A_ORDER, A_0_2, AP_1_0, ...
_SIP = re.compile(r"^(A|B|AP|BP)_(ORDER|\d_\d)$")
_AXIS = re.compile(r"Z?NAXIS\d*")  # frame axes, plain or tile-compressed
# Keys neither program writes, left by processing program that rewrote file.
_REWRITE_MARKS = frozenset({"PROGRAM", "STACKCNT"})
# Tile-compressed image page (FITS 4.0 sec. 10): its Z keys and table columns.
_COMPRESSION_KEYS = frozenset({"XTENSION", "EXTNAME", "PCOUNT", "GCOUNT", "TFIELDS", "THEAP"})
_TABLE_GEOMETRY = frozenset({"BITPIX", "NAXIS", "NAXIS1", "NAXIS2"})
_COMPRESSION = re.compile(
    r"^(ZIMAGE|ZCMPTYPE|ZBITPIX|ZNAXIS\d*|ZTILE\d+|ZNAME\d+|ZVAL\d+|ZMASKCMP|ZQUANTIZ|ZDITHER0"
    r"|ZSIMPLE|ZEXTEND|ZBLOCKED|ZTENSION|ZPCOUNT|ZGCOUNT|ZHECKSUM|ZDATASUM|ZBLANK|ZSCALE|ZZERO"
    r"|T(TYPE|FORM|UNIT)\d+)$"
)


class Skip(StrEnum):
    NOT_SUPPORTED = "not_supported"
    REWRITTEN = "rewritten"
    UNREADABLE = "unreadable"  # disk error (locked, NAS hiccup): passing, read again
    INCOMPLETE = "incomplete"  # shorter than header says: copy still running or broken
    BROKEN = "broken"  # header wrong for good (no END, bad axes): read again only once changed


@dataclass(frozen=True)
class Extracted:
    """Every key of file; `unknown`: those outside program's known list."""

    path: Path
    program: Program
    values: dict[str, Value]
    unknown: frozenset[str]
    fingerprint: str  # frame identity (pipeline/fingerprint.py)


@dataclass(frozen=True)
class Skipped:
    path: Path
    reason: Skip


def read_header(fh: BinaryIO) -> Header | None:
    """Frame header (primary, plus image page if compressed) and where its data lies, from one
    open file. Latin-1 or UTF-8 text; CONTINUE joins strings. None without END."""
    primary = _card_images(fh)
    if primary is None:
        return None
    cards = _parse(primary)
    start, length = fh.tell(), data_length(cards)
    if cards.get("NAXIS") == 0 and program_of(cards) is None:
        # tile-compressed (FITS 4.0 sec. 10): empty primary, frame's keys and data in page 2
        page = _card_images(fh)
        image = _parse(page) if page is not None else {}
        if image.get("ZIMAGE") is True:
            # page's NAXISn, BITPIX describe table; frame's are ZNAXISn, ZBITPIX
            page_keys = {k: v for k, v in image.items() if k not in _TABLE_GEOMETRY}
            cards = {**page_keys, **cards}
            start, length = fh.tell(), data_length(image)
    return Header({key: _utf8(value) for key, value in cards.items()}, start, length)


def _utf8(value: Value) -> Value:
    """Text read latin-1 whose bytes are valid UTF-8 (ASIAIR on Linux): read as UTF-8. Else
    latin-1 stays (N.I.N.A. on Windows). FITS 4.0 wants ASCII: nothing lost either way."""
    if not isinstance(value, str) or value.isascii():
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return value


def _parse(images: list[str]) -> dict[str, Value]:
    """CONTINUE pieces gathered, joined once at chain end: linear, not quadratic."""
    cards: dict[str, Value] = {}
    last: str | None = None
    pieces: list[str] = []
    for image in images:
        key = image[:8].rstrip()
        if key == "CONTINUE":  # reserved word, never a key; joins quoted strings only
            if last is not None and _continues(pieces[-1]) and _quoted(image[8:]):
                pieces[-1] = pieces[-1][:-1]
                pieces.append(_string(image[8:]))
            else:
                last = _close(cards, last, pieces)  # unquoted or stray: chain ends here
            continue
        last = _close(cards, last, pieces)
        key, field = _key_and_field(image)
        if key is None or key in cards:
            continue
        cards[key] = _value(field)
        if isinstance(cards[key], str) and _quoted(field):
            last, pieces = key, [str(cards[key])]
    _close(cards, last, pieces)
    return cards


def _close(cards: dict[str, Value], last: str | None, pieces: list[str]) -> None:
    """Chain ends: its string is the joined pieces."""
    if last is not None:
        cards[last] = "".join(pieces)


def _key_and_field(image: str) -> tuple[str | None, str]:
    """Keyword and value field of card; None for commentary, valueless or malformed key."""
    key = image[:8].rstrip()
    if key == "HIERARCH" and "=" in image:
        name, field = image[9:].split("=", 1)
        name = name.strip()
        return (name, field) if _HIERARCH_NAME.fullmatch(name) else (None, "")
    if key in _COMMENTARY or image[8:10] != "= " or not _KEY.fullmatch(key):
        return None, ""
    return key, image[10:]


def _card_images(fh: BinaryIO) -> list[str] | None:
    images: list[str] = []
    for _ in range(MAX_HEADER_BLOCKS):
        block = fh.read(BLOCK)
        if len(block) < BLOCK:
            return None
        for start in range(0, BLOCK, CARD):
            image = block[start : start + CARD].decode("latin-1")
            if image[:8].rstrip() == "END":
                return images
            images.append(image)
    return None


def _quoted(field: str) -> bool:
    """Long string convention (FITS 4.0 sec. 4.2.1.2): quoted text only."""
    return field.lstrip().startswith("'")


def _continues(value: Value) -> bool:
    return isinstance(value, str) and value.endswith("&")


def _string(field: str) -> str:
    """Quoted FITS string: '' is a quote, trailing blanks don't count; unquoted: its text."""
    match = re.match(r"\s*'((?:[^']|'')*)'", field)
    if match is None:
        return field.split("/", 1)[0].strip().strip("'").strip()
    return match.group(1).replace("''", "'").rstrip()


def _value(field: str) -> Value:
    """String, logical, integer or real as FITS writes them; else keeps its text."""
    if _quoted(field):
        return _string(field)
    text = field.split("/", 1)[0].strip()
    if text in ("T", "F"):
        return text == "T"
    if _INTEGER.fullmatch(text):
        return int(text)
    if _REAL.fullmatch(text):
        real = float(text.replace("D", "E"))
        if math.isfinite(real):  # beyond a double: JSON has no inf
            return real
    return text


def program_of(cards: dict[str, Value]) -> Program | None:
    if str(cards.get("SWCREATE", "")).startswith("N.I.N.A."):
        return Program.NINA
    if str(cards.get("CREATOR", "")).startswith("ZWO ASIAIR"):
        return Program.ASIAIR
    return None


def _writes(program: Program, key: str, compressed: bool) -> bool:
    if compressed and (key in _COMPRESSION_KEYS or _COMPRESSION.match(key)):
        return True
    if program is Program.NINA:
        return key in NINA_KEYS
    return key in ASIAIR_KEYS or bool(_SIP.match(key))


def _floating(cards: dict[str, Value]) -> bool:
    """Floating-point pixels: N.I.N.A. saves integers (BaseImageData.SaveFits), ASIAIR 16 bit;
    so calibrated or registered elsewhere, header kept. Compressed: frame's is ZBITPIX."""
    bitpix = cards.get("ZBITPIX") if cards.get("ZIMAGE") is True else cards.get("BITPIX")
    return bitpix in (-32, -64)


def _axes_are_counts(cards: dict[str, Value]) -> bool:
    """FITS 4.0 sec. 4.4.1.1: NAXIS, NAXISn written are non-negative integers; else no image.
    Compressed frame: same for ZNAXIS, ZNAXISn (sec. 10)."""
    return all(
        as_count(value, 0) is not None for key, value in cards.items() if _AXIS.fullmatch(key)
    )


def scan_file(path: Path, size: int | None = None) -> Extracted | Skipped:
    """One open per file. `size`: from walk's stat (no extra access); else asked to open file."""
    try:
        with open(long_path(path), "rb") as fh:  # noqa: PTH123 - the `\\?\` form is a str
            return _extract(path, fh, size)
    except OSError:  # this file, never whole scan
        return Skipped(path, Skip.UNREADABLE)
    except (ValueError, OverflowError):
        return Skipped(path, Skip.BROKEN)


def _extract(path: Path, fh: BinaryIO, size: int | None) -> Extracted | Skipped:
    """No END: copy cut in header changes size or date once done, read then."""
    header = read_header(fh)
    if header is None:
        return Skipped(path, Skip.BROKEN)
    cards = header.cards
    if _REWRITE_MARKS & cards.keys() or _floating(cards):
        return Skipped(path, Skip.REWRITTEN)
    program = program_of(cards)
    if program is None:
        return Skipped(path, Skip.NOT_SUPPORTED)
    if not _axes_are_counts(cards) or header.data_length is None:
        return Skipped(path, Skip.BROKEN)
    known = size if size is not None else os.fstat(fh.fileno()).st_size
    identity = frame_identity(header, known, fh)
    if not identity.complete:
        return Skipped(path, Skip.INCOMPLETE)
    compressed = cards.get("ZIMAGE") is True
    unknown = frozenset(k for k in cards if not _writes(program, k, compressed))
    return Extracted(path, program, cards, unknown, identity.fingerprint)
