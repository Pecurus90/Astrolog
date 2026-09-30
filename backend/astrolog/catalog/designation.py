"""A PARSER, not an existence test: it says a name looks like `NGC 224`, not that the entry
exists. Whoever queries the database checks that."""

import re

_FLAGS = re.IGNORECASE | re.ASCII

# Code -> spellings, tried in order (it matters where one prefixes another). Written out: `Sh2`
# carries a digit, and `Lynds` is left out because it could be LBN or LDN.
_CATALOGS: list[tuple[str, tuple[str, ...]]] = [
    ("M", ("Messier", "M")),
    ("NGC", ("NGC",)),
    ("IC", ("IC",)),
    ("Sh2", ("Sharpless", "Sh2")),
    ("LBN", ("LBN",)),
    ("LDN", ("LDN",)),
    ("vdB", ("van den Bergh", "vdB")),
    ("Arp", ("Arp",)),
    ("HCG", ("HCG",)),
    ("RCW", ("RCW",)),
    ("Caldwell", ("Caldwell",)),
    ("Mel", ("Melotte", "Mel")),
    ("Cl", ("Cl",)),
    ("Barnard", ("Barnard",)),
    ("Abell", ("Abell",)),
    ("WR", ("Wolf-Rayet", "WR")),
    ("Ced", ("Cederblad", "Ced")),
    ("C", ("C",)),
    ("B", ("B",)),
]

# Leading zeros do not count (`NGC 0224`); up to two trailing letters do (`NGC 7331A` is another).
_NUMBER = r"[\s-]*0*(\d+)([A-Za-z]{0,2})$"


def _pattern(forms: tuple[str, ...]) -> re.Pattern[str]:
    """Inside an extended form space and hyphen are the same and may be missing: `Wolf-Rayet`,
    `Wolf Rayet` and `WolfRayet` are one catalogue."""
    alternative = "|".join(r"[\s-]*".join(re.split(r"[\s-]+", f)) for f in forms)
    return re.compile(f"^(?:{alternative}){_NUMBER}", _FLAGS)


_PATTERNS = [(code, _pattern(forms)) for code, forms in _CATALOGS]

# Perek-Kohoutek has no number but a galactic coordinate (`PK 205+14.1`).
_PK = re.compile(r"^(?:Perek[\s-]*Kohoutek|PK)[\s-]*(\d+[+-]\d+(?:\.\d+)?)$", _FLAGS)

# The code the shipped file uses where the user knows the extended spelling.
_AS_WRITTEN = {"Caldwell": "C", "Barnard": "B"}


def parse(raw: str | None) -> tuple[str, str] | None:
    """`(catalogue, number)`: `M31`, `M 31`, `M 031` and `Messier 31` are the same object."""
    if not raw or not str(raw).strip():
        return None
    name = " ".join(str(raw).split())
    pk = _PK.match(name)
    if pk:
        return "PK", pk.group(1)
    for code, pattern in _PATTERNS:
        m = pattern.match(name)
        if m:
            return _AS_WRITTEN.get(code, code), m.group(1) + m.group(2).upper()
    return None


def key(raw: str | None) -> str | None:
    """`NGC 224` -> `NGC|224`: one key written at load and searched here, instead of normalising
    columns inside the query, so the index is really used."""
    parsed = parse(raw)
    return f"{parsed[0].upper()}|{parsed[1]}" if parsed else None
