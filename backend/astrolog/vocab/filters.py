"""Filter names from the header spelling to a canonical name, and from there to a passband. The
model catalogue answers first: a product is more specific than a generic word."""

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

_DATA = json.loads(Path(__file__).with_name("filters.json").read_text(encoding="utf-8"))

FILTER_MAP = dict(_DATA["words"])
NARROWBAND_CLIP = frozenset(_DATA["clip"])
PASSBANDS = frozenset(_DATA["passbands"])
# On a colour camera broad bands do not exist: the matrix is the filter (they become OSC).
BROADBAND = frozenset({"L", "R", "G", "B"}) & PASSBANDS
_PASSBAND_OF = dict(_DATA["passband_of"])
WIDTH_RE = re.compile(r"\b\d+(?:\.\d+)?\s*nm\b", re.IGNORECASE | re.ASCII)
JUNK_RE = re.compile(r"^(?:\d+|-+|dslr)$", re.IGNORECASE | re.ASCII)

_MODELS: list[dict[str, Any]] = sorted(
    (
        {
            "id": m["id"],
            "brand": m["brand"],
            "name": m["name"],
            "passband": m["passband"],
            "aliases": list(m.get("aliases") or ()),
        }
        for m in _DATA["models"]
    ),
    key=lambda m: (m["brand"].lower(), m["name"].lower()),
)
# Stripped before the map: the catalogue's brands, plus wheel-only brands with no screw-on models.
BRAND_PREFIXES = frozenset({m["brand"].lower() for m in _MODELS} | {"astrodon", "chroma"})

# Deciders compare against these, not against a string written by hand elsewhere.
NO_FILTER = "NONE"
UNKNOWN = "UNKNOWN"
# As in the data: the "no filter" row is born with it, and translating it is the page's job.
NO_FILTER_NAME = FILTER_MAP["none"]
_BY_NAME: dict[str, dict[str, Any] | None] = {}
for _m in _MODELS:
    for _n in [_m["name"], *_m["aliases"]]:
        _key = _n.strip().lower()
        # already seen from another model -> contested, and contested for good
        _BY_NAME[_key] = None if _key in _BY_NAME and _BY_NAME[_key] is not _m else _m


def models() -> list[dict[str, Any]]:
    """Sorted by brand and name: the order of the dropdown search."""
    return list(_MODELS)


def model_by_id(model_id: str) -> dict[str, Any] | None:
    return next((m for m in _MODELS if m["id"] == model_id), None)


def model_of(name: str | None) -> dict[str, Any] | None:
    """Case and edge spaces ignored; None also when two models share the name."""
    if not name:
        return None
    return _BY_NAME.get(str(name).strip().lower())


def passband_of(canonical: str | None) -> str:
    if canonical in _PASSBAND_OF:
        return _PASSBAND_OF[canonical]
    m = model_of(canonical)
    return m["passband"] if m is not None else UNKNOWN


# The PHYSICAL bands a filter lets through, the only ones declared: the other PASSBANDS (duo, tri,
# OSC, no filter) are labels derived from these.
BANDS = ("L", "R", "G", "B", "HA", "HB", "OIII", "SII")
_NARROW = frozenset({"HA", "HB", "OIII", "SII"})
# Pairs with a name of their own in the closed domain; any other pair is MULTI_NB.
_DUO = {frozenset({"HA", "OIII"}): "DUO_HAOIII", frozenset({"SII", "OIII"}): "DUO_SIIOIII"}


def passband_from_bands(bands: Iterable[str]) -> str:
    """The only road from bands to a passband, for whoever declares a filter and whoever reads it
    back, so a duo is not named two ways. Words that are not physical bands are ignored."""
    chosen = [b for b in dict.fromkeys(bands) if b in BANDS]
    if not chosen:
        return UNKNOWN
    if len(chosen) == 1:
        return chosen[0]
    if not set(chosen) <= _NARROW:
        # MULTI_NB and TRI_NB mean NARROW bands: L, R and G together have no label in the domain.
        return UNKNOWN
    if len(chosen) == 2:
        return _DUO.get(frozenset(chosen), "MULTI_NB")
    return "TRI_NB" if len(chosen) == 3 else "MULTI_NB"


def _strip_brand_and_width(value: str) -> str:
    s = WIDTH_RE.sub(" ", value)
    tokens = [t for t in s.split() if t not in BRAND_PREFIXES]
    return " ".join(tokens).strip()


def normalize_filter(raw: str | None, *, bayer: object) -> str | None:
    """`bayer`: the header declared a colour matrix, so a broadband word becomes OSC while a
    screw-on model stays itself. An unknown word comes back capitalised; junk is None."""
    canonical = None
    if raw:
        low = raw.lower().strip()
        model = model_of(low)
        if model is not None:
            return model["name"]
        core = _strip_brand_and_width(low)
        canonical = FILTER_MAP.get(core) or FILTER_MAP.get(low)
        if not canonical:
            canonical = None if JUNK_RE.match(low) else raw[0].upper() + raw[1:]
    if bayer:
        if canonical and model_of(canonical) is not None:
            return canonical
        if not canonical or canonical not in NARROWBAND_CLIP:
            return "OSC"
    return canonical


def is_broadband_word(raw: str | None) -> bool:
    """A word the vocabulary knows as a broad band (`L`, `Lum`, `B`)."""
    return passband_of(normalize_filter(raw, bayer=False)) in BROADBAND
