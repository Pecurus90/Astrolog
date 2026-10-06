"""Two solved fields compared: overlapping, nested or apart. Pure: whether they are panels is the
contract's call (`docs/domini/mosaico.md`). Symmetric, or it would depend on the run's order."""

import math
from enum import StrEnum
from typing import Any

from .identify_geometry import frame_radius_deg, frame_shape, in_axes, tangent_offset_deg


class Relation(StrEnum):
    DISJOINT = "disjoint"
    PARTIAL = "partial"
    NESTED = "nested"


# Half-diagonal fraction: degrees would fit one focal length. N.I.N.A.'s dithering example is 1.2%,
# the narrowest panel step (half a field) 83%: a quarter leaves 20x margin one side, 3x the other.
SAME_POINTING_FRACTION = 0.25


def overlap(a: dict[str, Any], b: dict[str, Any]) -> Relation | None:
    """`None` without a sky. `nested` is the same shot redone, or dithering, and not a mosaic.
    On the true tangent plane: near the pole the cosine approximation is far off."""
    if frame_shape(a) is None or frame_shape(b) is None:
        return None
    offset = tangent_offset_deg(a["ra_deg"], a["dec_deg"], b["ra_deg"], b["dec_deg"])
    if offset is None:
        return Relation.DISJOINT  # on the other side of the sky
    if frame_shape(a) == "circle" or frame_shape(b) == "circle":
        return _between_circles(a, b, offset)
    return _between_rectangles(a, b, offset)


def same_pointing(a: dict[str, Any], b: dict[str, Any]) -> bool | None:
    """Rectangles cannot tell dithering from adjacent panels. Without sides never the same, as a
    silent merge is the worst harm; the smaller field decides, where an offset weighs most."""
    if frame_shape(a) is None or frame_shape(b) is None:
        return None
    offset = tangent_offset_deg(a["ra_deg"], a["dec_deg"], b["ra_deg"], b["dec_deg"])
    if offset is None:
        return False  # on the other side of the sky
    raggi = [r for r in (frame_radius_deg(a), frame_radius_deg(b)) if r]
    if len(raggi) < 2:
        return False
    return math.hypot(*offset) < min(raggi) * SAME_POINTING_FRACTION


def _between_circles(a: dict[str, Any], b: dict[str, Any], offset: tuple[float, float]) -> Relation:
    """Without even the sides the radius is unknown, and it overlaps: a wrong proposal costs a
    click, a lost panel goes unseen."""
    ra, rb = frame_radius_deg(a), frame_radius_deg(b)
    if ra is None or rb is None:
        return Relation.PARTIAL
    distance = math.hypot(*offset)
    if distance > ra + rb:
        return Relation.DISJOINT
    if distance + min(ra, rb) <= max(ra, rb):
        return Relation.NESTED
    return Relation.PARTIAL


def _between_rectangles(
    a: dict[str, Any], b: dict[str, Any], offset: tuple[float, float]
) -> Relation:
    """Separating axis theorem on oriented rectangles: rotation alone changes the answer. In A's
    sensor axes, so B keeps only its relative rotation; four axes are enough."""
    ax, ay = a["width_deg"] / 2.0, a["height_deg"] / 2.0
    bx, by = b["width_deg"] / 2.0, b["height_deg"] / 2.0
    cx, cy = in_axes(offset, a["rotation_deg"])
    t = math.radians(b["rotation_deg"] - a["rotation_deg"])
    cos_t, sin_t = abs(math.cos(t)), abs(math.sin(t))

    # how far B reaches along A's axes, and A along B's
    b_su_a = (bx * cos_t + by * sin_t, bx * sin_t + by * cos_t)
    a_su_b = (ax * cos_t + ay * sin_t, ax * sin_t + ay * cos_t)
    # only magnitudes count here, so the offset is not reversed: a sign no test could tell apart
    ux, uy = in_axes((cx, cy), math.degrees(t))

    if abs(cx) > ax + b_su_a[0] or abs(cy) > ay + b_su_a[1]:
        return Relation.DISJOINT
    if abs(ux) > bx + a_su_b[0] or abs(uy) > by + a_su_b[1]:
        return Relation.DISJOINT
    if abs(cx) + b_su_a[0] <= ax and abs(cy) + b_su_a[1] <= ay:
        return Relation.NESTED  # B entirely inside A
    if abs(ux) + a_su_b[0] <= bx and abs(uy) + a_su_b[1] <= by:
        return Relation.NESTED
    return Relation.PARTIAL
