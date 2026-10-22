"""Header values read as numbers, counts, names: broken or out of range is None."""

import math
import struct
import unicodedata

from .scanner import Value

_SQLITE_MAX = 2**63 - 1  # largest INTEGER (sqlite.org/datatype3.html)


def as_number(written: Value | None, at_least: float = -math.inf) -> float | None:
    """bool is an int to Python: `T` is not 1. float32 tail cut (_without_float32_tail)."""
    if isinstance(written, bool) or not isinstance(written, int | float):
        return None
    if not math.isfinite(written) or written < at_least:
        return None
    return _without_float32_tail(float(written))


def as_count(written: Value | None, at_least: int) -> int | None:
    """Past SQLite INTEGER (64 bit): unknown, else whole scan fails."""
    if isinstance(written, bool) or not isinstance(written, int):
        return None
    return written if at_least <= written <= _SQLITE_MAX else None


def _without_float32_tail(number: float) -> float:
    """Driver float32 printed at 15 digits (DBL_DIG): 3.75999999046326 is 3.76.
    Only when number is that float32; true double untouched."""
    try:
        single = struct.unpack("f", struct.pack("f", number))[0]
    except OverflowError:
        return number
    if f"{single:.15g}" != f"{number:.15g}":
        return number
    for digits in range(1, 10):  # 9 digits round-trip any float32 (IEEE 754 binary32)
        short = float(f"{single:.{digits}g}")
        if struct.unpack("f", struct.pack("f", short))[0] == single:
            return short
    return number


def as_name(written: Value | None) -> str | None:
    """Stripped, non-empty, no control character (Unicode Cc: NUL, tab): else broken value."""
    if not isinstance(written, str):
        return None
    name = written.strip()
    if any(unicodedata.category(ch) == "Cc" for ch in name):
        return None
    return name or None


def as_positive(written: Value | None) -> float | None:
    """-0.0 and 0 too: unknown."""
    number = as_number(written, at_least=0)
    return number if number else None


def as_percent(written: Value | None) -> float | None:
    """ASCOM ObservingConditions: 0.0 - 100.0."""
    number = as_number(written, at_least=0)
    return number if number is not None and number <= 100 else None  # noqa: PLR2004


COLDEST_C = -273.15  # SI: below it a temperature is a broken value


def as_celsius(written: Value | None) -> float | None:
    return as_number(written, at_least=COLDEST_C)
