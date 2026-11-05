"""Rules on a single frame (ADR 0039, docs/domini/misure.md): the low object. Pure; wired at
step 40 with the object's kind."""

# Where exposure time doubles: airmass, sky background and seeing against the CCD equation; a star
# loses faster than an extended object [P ADR 0039: Kasten-Young, Patat 2003, seeing X^0.6]
LOW_EXTENDED_DEG = 30.0
LOW_STAR_DEG = 45.0  # [P ADR 0039]


def low_object(altitude_deg: float | None, *, star: bool) -> bool | None:
    """Under the threshold of its kind; None: altitude unknown."""
    if altitude_deg is None:
        return None
    return altitude_deg < (LOW_STAR_DEG if star else LOW_EXTENDED_DEG)
