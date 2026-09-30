"""The header's object name without palette words ("M31 LRGB final" -> "M31"). Designations are not
recognised here but by identify against the catalogue: an unrecognised name stays as it is."""

PALETTE_NOISE = frozenset(
    {"rgb", "lrgb", "hargb", "rgbha", "lrgbha", "sho", "hoo", "hso", "final", "crop", "reprocessed"}
)


def _strip_palette_suffix(s: str) -> str:
    tokens = s.split()
    if len(tokens) <= 1:
        return s
    removed = False
    while len(tokens) > 1 and tokens[-1].lower() in PALETTE_NOISE:
        tokens.pop()
        removed = True
    return " ".join(tokens) if removed else s


def clean_object_name(raw: str | None) -> str | None:
    """Empty or None comes back as is; a non-string raises, since it is not a name."""
    if not raw:
        return raw
    return _strip_palette_suffix(raw.strip())
