"""Pixels of a frame for measure: uncompressed FITS, primary image, read by us (no astropy in the
new pipeline). Values as written times BSCALE plus BZERO, in float32; read only, never written."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np

from .scanner import read_header
from .values import as_count
from .walk import long_path

# Below this side an image has no surface for a pixel statistic: not measured. [T]
MIN_IMAGE_SIDE_PX = 20
# BITPIX -> big-endian type; floats never reach here (scanner skips them as rewritten).
_TYPES = {8: ">u1", 16: ">i2", 32: ">i4"}  # [C FITS 4.0 table 8: BITPIX]


class Why(StrEnum):
    NOT_SUPPORTED = "not_supported"  # not one 2D image: cube, sliver, float
    UNREADABLE = "unreadable"  # cut, missing, not FITS: a later pass may read it
    FZ_UNSUPPORTED = "fz_unsupported"  # tile-compressed: not decompressed yet


@dataclass(frozen=True)
class Pixels:
    data: np.ndarray  # float32, rows = NAXIS2, columns = NAXIS1
    saturation: float  # DATAMAX if written, else the type's top after BZERO and BSCALE


@dataclass(frozen=True)
class Unmeasurable:
    why: Why


def read_pixels(path: Path) -> Pixels | Unmeasurable:
    if path.name.lower().endswith(".fz"):
        return Unmeasurable(Why.FZ_UNSUPPORTED)
    try:
        with open(long_path(path), "rb") as fh:
            header = read_header(fh)
            if header is None:
                return Unmeasurable(Why.UNREADABLE)
            cards = header.cards
            shape = _shape(cards)
            kind = _TYPES.get(cards.get("BITPIX"))  # type: ignore[arg-type]
            if shape is None or kind is None:
                return Unmeasurable(Why.NOT_SUPPORTED)
            fh.seek(header.data_start)
            wanted = shape[0] * shape[1] * np.dtype(kind).itemsize
            raw = fh.read(wanted)
    except (OSError, ValueError):
        return Unmeasurable(Why.UNREADABLE)
    if len(raw) < wanted:
        return Unmeasurable(Why.UNREADABLE)
    scale, offset = _number(cards.get("BSCALE"), 1.0), _number(cards.get("BZERO"), 0.0)
    data = np.frombuffer(raw, dtype=kind).reshape(shape).astype(np.float64) * scale + offset
    top = float(np.iinfo(np.dtype(kind)).max) * scale + offset
    return Pixels(data.astype(np.float32), _number(cards.get("DATAMAX"), top))


def _shape(cards: Mapping[str, object]) -> tuple[int, int] | None:
    """(rows, columns) of a 2D image at least MIN_IMAGE_SIDE_PX a side; else None."""
    if cards.get("NAXIS") != 2:
        return None
    width, height = as_count(cards.get("NAXIS1"), 0), as_count(cards.get("NAXIS2"), 0)  # type: ignore[arg-type]
    if width is None or height is None or min(width, height) < MIN_IMAGE_SIDE_PX:
        return None
    return height, width


def _number(written: object, otherwise: float) -> float:
    if isinstance(written, bool) or not isinstance(written, int | float):
        return otherwise
    return float(written)
