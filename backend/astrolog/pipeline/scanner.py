"""Finds FITS files and extracts the header of those N.I.N.A. and ASIAIR wrote (ADR 0029)."""

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

FITS_SUFFIXES = frozenset({".fits", ".fit", ".fts"})
BLOCK = 2880
CARD = 80
MAX_HEADER_BLOCKS = 1000
_COMMENTARY = frozenset({"COMMENT", "HISTORY"})  # free text after column 9 (FITS 4.0 4.4.2.4)
Value = str | int | float | bool

_STRUCTURE = ("SIMPLE", "BITPIX", "NAXIS", "NAXIS1", "NAXIS2", "BZERO", "EXTEND")

# Complete: the writer NINA.Image/FileFormat/FITS/FITSHeader.cs; user-defined keys are not its own.
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
    "ROWORDER", "EQUINOX", "SWCREATE",
})  # fmt: skip

# Partial: ZWO publishes no list; these are the keys of 696 real ASIAIR files.
ASIAIR_KEYS = frozenset({
    *_STRUCTURE, "BSCALE",
    "CREATOR", "IMAGETYP", "EXPOSURE", "EXPTIME", "DATE-OBS",
    "XBINNING", "YBINNING", "CCDXBIN", "CCDYBIN", "XPIXSZ", "YPIXSZ", "XORGSUBF", "YORGSUBF",
    "GAIN", "OFFSET", "EGAIN", "ISO", "INSTRUME", "SET-TEMP", "CCD-TEMP", "BAYERPAT", "GUIDECAM",
    "TELESCOP", "FOCALLEN", "FOCUSPOS", "ROTATOR", "RA", "DEC", "OBJECT", "SITELAT", "SITELONG",
    "CTYPE1", "CTYPE2", "CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CD1_1", "CD1_2", "CD2_1", "CD2_2",
    "IMAGEW", "IMAGEH",
})  # fmt: skip

# SIP distortion terms of the ASIAIR plate solve: A_ORDER, A_0_2, AP_1_0, ...
_SIP = re.compile(r"^(A|B|AP|BP)_(ORDER|\d_\d)$")
# Keys neither program writes, left by a processing program that rewrote the file.
_REWRITE_MARKS = frozenset({"PROGRAM", "STACKCNT"})


class Program(StrEnum):
    NINA = "N.I.N.A."
    ASIAIR = "ASIAIR"


class Skip(StrEnum):
    NOT_SUPPORTED = "not_supported"
    REWRITTEN = "rewritten"
    UNREADABLE = "unreadable"
    FOLDER_UNREADABLE = "folder_unreadable"


@dataclass(frozen=True)
class Extracted:
    """Every key of the file; `unknown` are those outside the program's known list."""

    path: Path
    program: Program
    values: dict[str, Value]
    unknown: frozenset[str]


@dataclass(frozen=True)
class Skipped:
    path: Path
    reason: Skip


def _walk(root: Path) -> Iterator[Path | Skipped]:
    """FITS files under `root`, and the folders that could not be opened (NAS unplugged, rights)."""
    seen: set[str] = set()
    failed: list[OSError] = []
    for folder, dirs, files in os.walk(root, onerror=failed.append, followlinks=True):
        yield from (Skipped(Path(e.filename), Skip.FOLDER_UNREADABLE) for e in failed)
        failed.clear()
        real = os.path.realpath(folder)
        if real in seen:
            dirs.clear()
            continue
        seen.add(real)
        dirs.sort()
        for name in sorted(files):
            if Path(name).suffix.lower() in FITS_SUFFIXES:
                yield Path(folder, name)
    yield from (Skipped(Path(e.filename), Skip.FOLDER_UNREADABLE) for e in failed)


def find_fits(root: Path) -> Iterator[Path]:
    """FITS files under `root`, following linked folders; a folder reached twice is walked once."""
    return (item for item in _walk(root) if isinstance(item, Path))


def read_cards(path: Path) -> dict[str, Value] | None:
    """Keyword -> value of the primary header, first occurrence wins; None without END or on a
    read error. Latin-1: N.I.N.A. writes the header in ISO-8859-1. CONTINUE joins strings."""
    try:
        with path.open("rb") as fh:
            images = _card_images(fh)
    except OSError:
        return None
    if images is None:
        return None
    cards: dict[str, Value] = {}
    last: str | None = None
    for image in images:
        key = image[:8].rstrip()
        if key == "CONTINUE" and last is not None and _continues(cards[last]):
            cards[last] = str(cards[last])[:-1] + _string(image[8:])
            continue
        last = None
        key, field = _key_and_field(image)
        if key is None or key in cards:
            continue
        cards[key] = _value(field)
        last = key if isinstance(cards[key], str) else None
    return cards


def _key_and_field(image: str) -> tuple[str | None, str]:
    """Keyword and value field of a card; None for commentary and cards without a value."""
    key = image[:8].rstrip()
    if key == "HIERARCH" and "=" in image:
        name, field = image[9:].split("=", 1)
        return name.strip(), field
    if key in _COMMENTARY or image[8:10] != "= ":
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


def _continues(value: Value) -> bool:
    return isinstance(value, str) and value.endswith("&")


def _string(field: str) -> str:
    """A quoted FITS string: '' is a quote, trailing blanks do not count; unquoted, its text."""
    match = re.match(r"\s*'((?:[^']|'')*)'", field)
    if match is None:
        return field.split("/", 1)[0].strip().strip("'").strip()
    return match.group(1).replace("''", "'").rstrip()


def _value(field: str) -> Value:
    """String, logical, integer or real as FITS writes them; anything else keeps its text."""
    if field.lstrip().startswith("'"):
        return _string(field)
    text = field.split("/", 1)[0].strip()
    if text in ("T", "F"):
        return text == "T"
    for parse in (int, float):
        try:
            return parse(text.replace("D", "E"))
        except ValueError:
            pass
    return text


def program_of(cards: dict[str, Value]) -> Program | None:
    if str(cards.get("SWCREATE", "")).startswith("N.I.N.A."):
        return Program.NINA
    if str(cards.get("CREATOR", "")).startswith("ZWO ASIAIR"):
        return Program.ASIAIR
    return None


def _writes(program: Program, key: str) -> bool:
    if program is Program.NINA:
        return key in NINA_KEYS
    return key in ASIAIR_KEYS or bool(_SIP.match(key))


def scan_file(path: Path) -> Extracted | Skipped:
    try:
        cards = read_cards(path)
    except OSError:
        cards = None
    if cards is None:
        return Skipped(path, Skip.UNREADABLE)
    if _REWRITE_MARKS & cards.keys():
        return Skipped(path, Skip.REWRITTEN)
    program = program_of(cards)
    if program is None:
        return Skipped(path, Skip.NOT_SUPPORTED)
    unknown = frozenset(k for k in cards if not _writes(program, k))
    return Extracted(path, program, cards, unknown)


def scan(root: Path) -> Iterator[Extracted | Skipped]:
    for item in _walk(root):
        yield scan_file(item) if isinstance(item, Path) else item
