"""Reading a saved header (`frames.header_json`) or an ASTAP `.wcs`: the program keys and the typed
getters. The frame's own fields are read by `pipeline/card.py`."""

import math
from typing import Any, Protocol


class HeaderLike(Protocol):
    """The dict read back from the database, or the cards of an ASTAP `.wcs`: only `.get`."""

    def get(self, key: str, default: Any = None, /) -> Any: ...


# Who ACQUIRED the file and who WROTE it: the second is the only trace of a processing program.
# SWMODIFY: *FITS File Header Definitions*, Diffraction Limited (MaxIm DL help). software-ok: source
ACQUISITION_KEYS = ("SWCREATE", "CREATOR")
WRITER_KEYS = ("PROGRAM", "SWMODIFY")


def first(header: HeaderLike, *keys: str) -> Any:
    """The first present, non-blank value among `keys`, raw."""
    for k in keys:
        v = header.get(k)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def text(v: Any) -> str | None:
    """Strips only the quote pair wrapping the value: quotes inside belong to the name, as in
    `Barnard's Loop`."""
    if v is None:
        return None
    cleaned = str(v).strip()
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1] == "'":
        cleaned = cleaned[1:-1].strip()
    return cleaned or None
