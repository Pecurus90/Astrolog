"""Only the four supported programs get a canonical name; anything else stays in `software_raw`.
Substring search in order: "nina" and "n.i.n.a" before anything that contains them."""

from enum import StrEnum


# One member per name: a rule elsewhere names it instead of repeating the string.
class Software(StrEnum):
    NINA = "N.I.N.A."
    ASIAIR = "ASIAIR"
    VOYAGER = "Voyager"
    SGP = "Sequence Generator Pro"


SOFTWARE_PATTERNS = (
    ("nina", Software.NINA),
    ("n.i.n.a", Software.NINA),
    ("asiair", Software.ASIAIR),
    ("voyager", Software.VOYAGER),
    ("sequence generator", Software.SGP),
    ("sgpro", Software.SGP),
    ("sgp", Software.SGP),
)


def telescope_is_mount(software: str | None) -> bool:
    """The ASIAIR writes the mount in `TELESCOP` and the optics nowhere: whoever reads `TELESCOP`
    asks here, or one place takes it for optics and another for a mount."""
    return software == Software.ASIAIR


def normalize_software(raw: str | None) -> Software | None:
    if not raw:
        return None
    low = str(raw).lower()
    for needle, canonical in SOFTWARE_PATTERNS:
        if needle in low:
            return canonical
    return None
