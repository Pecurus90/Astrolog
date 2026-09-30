"""Comets and asteroids recognised by name, since by coordinates they get a confident wrong answer.
The full designation is required: calling a fixed object moving hides it for good."""

import re

# Each branch closes a real false positive: no digit after the comet letter (`3C 273`), and a
# provisional form needs the year (`C 109`) and the end anchor (`2022 IC 1396`).
_MOVING = re.compile(
    r"^\s*("
    # numbered comet: 12P/Pons-Brooks, 12P Pons-Brooks, 12P_Pons-Brooks, 73P-C, 12P
    r"\d{1,4}[PDCI](?:/|[\s_-]+[A-Z][a-z]|-[A-Z](?![0-9A-Za-z])|\s*$)"
    r"|[PDCXAI]/\s*\d{3,4}\b"  # provisional with the slash: C/2023, P/2010
    # without it (illegal in folder names): half-month B, C, M left out, `C 2023 M31` is a folder
    r"|[PDCXAI][\s_-]\s*(?:1[89]|20)\d{2}[\s_-]+[ADEFGHJKLNOPQRSTUVWXY]\d"
    r"|\(\d{1,7}\)"  # numbered asteroid in brackets: (4) Vesta
    r"|\d{4}\s+[A-Z]{2}\d*\s*$"  # asteroid provisional: 2023 DZ2
    r")",
    re.IGNORECASE,
)


def is_moving_designation(name: str | None) -> bool:
    """A bare-numbered asteroid (`433 Eros`) is not recognised: it has the shape of a Flamsteed name
    (`104 Herculis`) and of working names (`600 Second Darks`)."""
    return bool(name) and bool(_MOVING.match(name.strip()))
