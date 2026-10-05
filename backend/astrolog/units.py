"""Units and numbers in one place. Converted upstream, once: whoever shows or averages receives
the comparable number already."""

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

# The digits a float32 can really assert: `4.29` read back in double precision becomes
# `4.28999996185303`, and that tail is format, not measure.
F32_SIGNIFICANT_DIGITS = 7

# Arcseconds in a radian, divided by a thousand: the micron -> millimetre conversion is inside.
ARCSEC_PER_RAD_PER_1000 = 206.265


def strip_float32_noise(
    value: float | None, *, digits: int = F32_SIGNIFICANT_DIGITS
) -> float | None:
    """Not a convenience rounding: it cuts where the float32 stops saying anything. Shortening a
    number that truly has too many digits is the caller's call, with `round`."""
    if value is None:
        return None
    return float(f"%.{digits}g" % value)


def most_frequent[T](weights: Mapping[T, int]) -> T | None:
    """`None` on a tie: between two values with the same files nothing is chosen at random."""
    top = Counter(weights).most_common(2)
    if not top or (len(top) == 2 and top[0][1] == top[1][1]):
        return None
    return top[0][0]


def physical_pixel_um(pixel_um: float | None, binning: int | None) -> float | None:
    """`XPIXSZ` includes binning by convention (sources in `docs/domini/spina.md`), so it is
    divided, then cleaned like a float32: a header's 11.28 / 3 gives 3.76, not 3.759999910990397."""
    if pixel_um is None or not binning:
        return None
    return strip_float32_noise(pixel_um / binning)


def hundredths(value: float | None) -> float | None:
    """Beyond the second decimal the page would show digits nobody reads as a measure."""
    return None if value is None else round(value, 2)


def median(values: Iterable[float | None]) -> float | None:
    """Median, not mean: from three measures up one bad solve would move the mean and not the
    median; with two, the median is their mean."""
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return None
    half = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[half]
    return (ordered[half - 1] + ordered[half]) / 2


def pixel_um_from_scale(
    scale_arcsec_px: float | None, focal_mm: float | None, binning: int | None
) -> float | None:
    """The inverse of `scale_arcsec_px`, divided by binning because the measured scale is of the
    binned pixels. An unknown binning is not 1."""
    if not scale_arcsec_px or not focal_mm or not binning:
        return None
    return scale_arcsec_px * focal_mm / ARCSEC_PER_RAD_PER_1000 / binning


def scale_arcsec_px(pixel_um: float | None, focal_mm: float | None) -> float | None:
    """The derived scale knows neither binning nor the real optics: the solver's measured one
    always wins, this is the answer until a measure exists."""
    if not pixel_um or not focal_mm or pixel_um <= 0 or focal_mm <= 0:
        return None
    return pixel_um / focal_mm * ARCSEC_PER_RAD_PER_1000


# A focal group spreads <= 5 % (max/min <= 1.05): it absorbs header jitter without chaining
# different optical setups.
FOCAL_TOLERANCE = 0.05


def known_focal(value: Any) -> float | None:
    """`True` in JSON is an integer, and a zero or negative focal is not a focal: unknown, never
    invented."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return None
    return float(value)


def same_focal(known: float | None, focal_mm: float | None) -> bool:
    """Unknown on one side only is not the same; unknown on both, it is."""
    if known is None or focal_mm is None:
        return known is None and focal_mm is None
    return abs(known - focal_mm) <= FOCAL_TOLERANCE * abs(known)


def focal_buckets(focals: Iterable[Any], tol: float = FOCAL_TOLERANCE) -> dict[float, float]:
    """Each group is anchored to its smallest value, so the result does not depend on order and
    560 -> 570 -> 580 -> ... cannot chain two different optics. Representative: the median."""
    distinct = sorted({f for f in map(known_focal, focals) if f is not None})
    mapping = {}
    i = 0
    while i < len(distinct):
        anchor = distinct[i]
        j = i + 1
        while j < len(distinct) and distinct[j] <= anchor * (1 + tol):
            j += 1
        cluster = distinct[i:j]
        representative = cluster[len(cluster) // 2]
        for value in cluster:
            mapping[value] = representative
        i = j
    return mapping


# The natural night-sky background, 174 microcandela per square metre: without adding it a
# perfect site would have infinite brightness.
NATURAL_SKY_CD_M2 = 174e-6
# The constant linking candela per square metre and magnitudes per square arcsecond.
CD_M2_PER_MAG0 = 1.08e5

# Bortle gave no numeric bounds: the floors of Wikipedia's *Bortle scale* (docs/domini/sito.md),
# its 4.5 read as 5; it merges 8 and 9 below 18.00, split at 17.00 for the inner city.
BORTLE_FLOORS = ((1, 21.76), (2, 21.60), (3, 21.30), (4, 20.80), (5, 19.25), (6, 18.50),
                 (7, 18.00), (8, 17.00))  # fmt: skip
# Class 1 is open above and 9 below: two convenience ends for the reverse direction.
BORTLE_TOP, BORTLE_BOTTOM = 22.00, 16.00


def sqm_from_brightness(artificial_mcd_m2: float | None) -> float | None:
    """From artificial light in millicandela per square metre, as the services give it, to
    magnitudes per square arcsecond. A negative value is not a brightness."""
    if artificial_mcd_m2 is None or artificial_mcd_m2 < 0:
        return None
    total = artificial_mcd_m2 / 1000.0 + NATURAL_SKY_CD_M2
    return hundredths(-2.5 * math.log10(total / CD_M2_PER_MAG0))


# Below is a lit car park, above is no place on Earth: an answer outside is a fault, not a sky.
# `schema.sql` repeats the numbers in a CHECK, the guard for whoever writes without passing here.
SQM_MIN, SQM_MAX = 10.0, 23.0


def believable_sqm(sqm: float | None) -> float | None:
    """An absurd estimate is neither saved nor shown: it is treated as no answer."""
    if sqm is None or not (SQM_MIN <= sqm <= SQM_MAX):
        return None
    return sqm


def bortle_of(sqm: float | None) -> int | None:
    if sqm is None:
        return None
    for classe, floor in BORTLE_FLOORS:
        if sqm >= floor:
            return classe
    return 9


def sqm_of_bortle(classe: int) -> float | None:
    """The centre of the class, so reading it back gives the same class."""
    floors = dict(BORTLE_FLOORS)
    low = floors.get(classe, BORTLE_BOTTOM)
    high = floors.get(classe - 1, BORTLE_TOP)
    return hundredths((low + high) / 2)


def field_deg(pixels: int | None, scale_arcsec_px_: float | None) -> float | None:
    """An unknown field is not invented: the solver would rather search by itself than search
    the wrong field."""
    if not pixels or not scale_arcsec_px_ or pixels <= 0 or scale_arcsec_px_ <= 0:
        return None
    return pixels * scale_arcsec_px_ / 3600.0


def radius_deg(size_major_arcmin: float | None) -> float:
    """Without a size the object is a point."""
    return size_major_arcmin / 120.0 if size_major_arcmin else 0.0


def separation_deg_from_cosine(cos_sep: float) -> float:
    """The clamp is not caution: two parallel unit vectors give a dot product like
    `1.0000000000000002`, and `acos` of that raises."""
    return math.degrees(math.acos(min(1.0, max(-1.0, cos_sep))))


def angular_separation_deg(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    """Through unit vectors rather than right-ascension differences, so the 0/360 wrap is not a
    case to remember."""
    ra1, dec1, ra2, dec2 = map(math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg))
    cos_sep = math.sin(dec1) * math.sin(dec2) + math.cos(dec1) * math.cos(dec2) * math.cos(
        ra1 - ra2
    )
    return separation_deg_from_cosine(cos_sep)
