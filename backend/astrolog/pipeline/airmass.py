"""Air mass and values at the zenith (ADR 0022 point 5): pure, degrees and numbers in."""

import math

# Seeing at the zenith = measured / airmass^0.6 (Kolmogorov).
SEEING_POWER = 0.6  # [C ESO La Silla seeing, eso.org/sci/facilities/lasilla/astclim/seeing.html]


def apparent_altitude(true_deg: float) -> float:
    """Raised by the refraction, Saemundsson at 1010 hPa and 10 C [C Meeus 1998 eq. 16.4, plus
    0.0019279 for zero at the zenith]; under -1 degree no lift: the formula bends, all is set."""
    h = true_deg
    if h < -1.0:
        return h
    lift_arcmin = 1.02 / math.tan(math.radians(h + 10.3 / (h + 5.11))) + 0.0019279
    return h + lift_arcmin / 60.0


def airmass_of(altitude_deg: float) -> float | None:
    """Pickering 2002 on the apparent altitude [C DIO 12(1) 20-39: X = 1 / sin(h + 244 /
    (165 + 47 h^1.1))]; finite at the horizon, None under it."""
    h = altitude_deg
    if h < 0:
        return None
    return 1.0 / math.sin(math.radians(h + 244.0 / (165.0 + 47.0 * h**1.1)))


def at_zenith(value: float | None, airmass: float | None) -> float | None:
    """FWHM or HFD as at the zenith: value / X^0.6."""
    if value is None or airmass is None:
        return None
    return value / airmass**SEEING_POWER
