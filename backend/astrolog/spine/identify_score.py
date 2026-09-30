"""Which object in the field is the subject, by weight, not nearest-first: the closest candidate
is often a smaller piece or companion inside the subject. Pure."""

import math
from typing import Any

from ..catalog import designation
from ..units import radius_deg
from .identify_geometry import reach_deg

# Magnitude weighs slightly more than containment: it flips the faint clutter nearby.
W_CONTAINMENT = 1.0
W_MAGNITUDE = 1.4
W_SIZE = 0.6
W_CATALOG = 1.0
W_CENTERING = 1.2

# Floor: the solver's error, below which two candidates can't be told apart.
# Ceiling: a huge object need not "contain" half a constellation.
SEP_FLOOR_DEG = 0.05
SCALE_CAP_DEG = 3.0

# Curated, well-known catalogs beat obscure ones.
CATALOG_PRIORITY = {
    "M": 1.0, "C": 0.9, "NGC": 0.7, "IC": 0.55,
    "Sh2": 0.4, "LBN": 0.3, "LDN": 0.3, "vdB": 0.3, "Ced": 0.3,
    "B": 0.3, "Abell": 0.3, "RCW": 0.3,
}  # fmt: skip
CATALOG_PRIORITY_DEFAULT = 0.2

# Ambiguity needs both: a competitive score AND an object distinct from the best.
AMBIGUOUS_SCORE_RATIO = 0.6
# Fallback, only when neither candidate carries a size.
AMBIGUOUS_SEPARATION_DEG = 0.4


def _magnitude_term(magnitude: float | None) -> float:
    """0..1, brighter is higher; missing is 0: unmeasured clutter earns no bonus."""
    if magnitude is None:
        return 0.0
    return (12.0 - min(12.0, max(3.0, magnitude))) / 9.0


def _size_term(size_major_arcmin: float | None) -> float:
    """0..1 on the log of the size."""
    if size_major_arcmin is None:
        return 0.0
    return min(1.0, math.log10(max(size_major_arcmin, 1.0)) / 2.5)


def catalog_priority(name: str | None) -> float:
    parsed = designation.parse(name)
    return (
        CATALOG_PRIORITY.get(parsed[0], CATALOG_PRIORITY_DEFAULT)
        if parsed
        else (CATALOG_PRIORITY_DEFAULT)
    )


def ranking_scale_deg(size_major_arcmin: float | None) -> float:
    """The clamped own radius: a scale that ranks candidates, not an acceptance tolerance."""
    return min(SCALE_CAP_DEG, max(radius_deg(size_major_arcmin), SEP_FLOOR_DEG))


def centering_term(
    separation_deg: float, fov_radius_deg: float | None, size_major_arcmin: float | None = None
) -> float:
    """How present the candidate is: 1 centered, 0 at the edge of reach, neutral if unknown."""
    if fov_radius_deg is None or fov_radius_deg <= 0:
        return 0.5
    return max(0.0, 1.0 - separation_deg / reach_deg(fov_radius_deg, size_major_arcmin))


def score_candidate(entry: dict[str, Any], fov_radius_deg: float | None = None) -> float:
    """`entry` as `catalog.lookup.in_cone` returns it."""
    sep = entry["sep_deg"]
    size = entry.get("size_major_arcmin")
    sep_norm = min(1.0, sep / ranking_scale_deg(size))
    centering = centering_term(sep, fov_radius_deg, size)
    known_field = fov_radius_deg is not None and fov_radius_deg > 0
    return (
        W_CONTAINMENT * (1.0 - sep_norm)
        + (W_CENTERING * centering if known_field else 0.0)
        + W_MAGNITUDE * _magnitude_term(entry.get("magnitude")) * centering
        + W_SIZE * _size_term(size)
        + W_CATALOG * catalog_priority(entry.get("name"))
    )


def _is_inside(
    first: dict[str, Any],
    second: dict[str, Any],
    separation_deg: float,
    fov_radius_deg: float | None = None,
) -> bool:
    """Same subject: closer than the larger radius (or the fallback) and within the frame radius,
    beyond which asking beats linking silently; an unknown field sets no bound."""
    sizes = [x.get("size_major_arcmin") for x in (first, second)]
    largest = max((s for s in sizes if s and s > 0), default=None)
    near_in_frame = fov_radius_deg is None or separation_deg <= fov_radius_deg
    if not largest:
        return separation_deg < AMBIGUOUS_SEPARATION_DEG and near_in_frame
    return separation_deg <= radius_deg(largest) and near_in_frame


def is_ambiguous(
    first: dict[str, Any],
    second: dict[str, Any] | None,
    *,
    separation_deg: float | None,
    fov_radius_deg: float | None = None,
) -> bool:
    """Does the second really contend? Score alone would send a nebula and its own cluster to
    confirmation."""
    if second is None or separation_deg is None:
        return False
    if _is_inside(first, second, separation_deg, fov_radius_deg):
        return False
    best = score_candidate(first, fov_radius_deg)
    return score_candidate(second, fov_radius_deg) >= AMBIGUOUS_SCORE_RATIO * best
