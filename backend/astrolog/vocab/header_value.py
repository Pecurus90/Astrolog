"""A cosmetic, conservative cleanup that never merges two different devices. Idempotent. The same
function normalises what an alias stores and what a frame reads, or they would not compare."""

import re

_WS_RE = re.compile(r"\s+")
_TRAILING_INDEX_RE = re.compile(r"\s*\(\d+\)\s*$")


def normalize_header_value(value: object) -> str:
    """`"ZWO Focuser (1)"` -> `"zwo focuser"`, `"ASCOM.ToupTek.AAF"` -> `"ascom touptek aaf"`,
    None -> "". A value that normalises to "" is not an alias: the writer rejects it."""
    if value is None:
        return ""
    x = str(value).lower()
    x = _TRAILING_INDEX_RE.sub("", x)
    x = x.replace(".", " ")
    x = _WS_RE.sub(" ", x)
    return x.strip()
