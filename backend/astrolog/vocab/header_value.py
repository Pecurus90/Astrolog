"""A cosmetic, conservative cleanup that never merges two different devices. Idempotent. The same
function normalises what an alias stores and what a frame reads, or they would not compare."""

import re

_WS_RE = re.compile(r"\s+")


def _strip_trailing_indexes(x: str) -> str:
    """`"efw (1) (2)"` -> `"efw"`. A loop, not a regex: `(\\s*\\(\\d+\\))+$` is quadratic."""
    while x.endswith(")"):
        i = x.rfind("(")
        if i < 0 or not x[i + 1 : -1].isdecimal():
            break
        x = x[:i].rstrip()
    return x


def normalize_header_value(value: object) -> str:
    """`"ZWO Focuser (1)"` -> `"zwo focuser"`, `"ASCOM.ToupTek.AAF"` -> `"ascom touptek aaf"`,
    None -> "". A value that normalises to "" is not an alias: the writer rejects it."""
    if value is None:
        return ""
    # dots and spaces first, then every ASCOM index at the end: what is left has none to strip
    x = _WS_RE.sub(" ", str(value).lower().replace(".", " ")).strip()
    return _strip_trailing_indexes(x)
