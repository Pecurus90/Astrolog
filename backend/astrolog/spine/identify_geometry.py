"""Field geometry: how much sky to query, and what is really in the frame. Pure."""

import math
from typing import Any, Literal

from ..units import radius_deg

# At least `identify_score.SCALE_CAP_DEG`: an entry whose ranking scale reaches the pointing must
# be in the cone.
MIN_SEARCH_RADIUS_DEG = 3.0


def search_radius_deg(frame_radius_deg: float | None) -> float:
    """Never below the floor: on a narrow field a large, off-center subject would otherwise fall
    outside the search."""
    if frame_radius_deg is None:
        return MIN_SEARCH_RADIUS_DEG
    return max(frame_radius_deg, MIN_SEARCH_RADIUS_DEG)


def frame_radius_deg(wcs: dict[str, Any]) -> float | None:
    """Half-diagonal of the stored rectangle, not recomputed from the sensor's pixels."""
    width, height = wcs.get("width_deg"), wcs.get("height_deg")
    if not width or not height:
        return None
    return math.hypot(width, height) / 2.0


def tangent_offset_deg(
    center_ra_deg: float, center_dec_deg: float, ra_deg: float, dec_deg: float
) -> tuple[float, float] | None:
    """`(east, north)` on the tangent plane at the center, `None` on the opposite side of the sky.
    True gnomonic projection, not the cos(dec) shortcut."""
    ra0, dec0 = math.radians(center_ra_deg), math.radians(center_dec_deg)
    ra1, dec1 = math.radians(ra_deg), math.radians(dec_deg)
    d_ra = ra1 - ra0
    cos_c = math.sin(dec0) * math.sin(dec1) + math.cos(dec0) * math.cos(dec1) * math.cos(d_ra)
    if cos_c <= 0:
        return None
    east = math.cos(dec1) * math.sin(d_ra) / cos_c
    north = (
        math.cos(dec0) * math.sin(dec1) - math.sin(dec0) * math.cos(dec1) * math.cos(d_ra)
    ) / cos_c
    return math.degrees(east), math.degrees(north)


def frame_shape(wcs: dict[str, Any]) -> Literal["rectangle", "circle"] | None:
    if wcs.get("ra_deg") is None or wcs.get("dec_deg") is None:
        return None
    whole = wcs.get("width_deg") and wcs.get("height_deg") and wcs.get("rotation_deg") is not None
    return "rectangle" if whole else "circle"


def in_frame(
    wcs: dict[str, Any], ra_deg: float, dec_deg: float, size_major_arcmin: float | None = None
) -> bool | None:
    """`None` without sky; the object's own radius widens the frame."""
    shape = frame_shape(wcs)
    if shape is None:
        return None
    offset = tangent_offset_deg(wcs["ra_deg"], wcs["dec_deg"], ra_deg, dec_deg)
    if offset is None:
        return False
    east, north = offset
    radius = radius_deg(size_major_arcmin)
    if shape == "circle":
        circle = frame_radius_deg(wcs)
        return True if circle is None else math.hypot(east, north) <= circle + radius
    x, y = in_axes(offset, wcs["rotation_deg"])
    return abs(x) <= wcs["width_deg"] / 2.0 + radius and abs(y) <= wcs["height_deg"] / 2.0 + radius


def in_axes(offset: tuple[float, float], rotation_deg: float) -> tuple[float, float]:
    """`(east, north)` in the axes of a field rotated by `rotation_deg`."""
    east, north = offset
    t = math.radians(rotation_deg)
    return east * math.cos(t) + north * math.sin(t), -east * math.sin(t) + north * math.cos(t)


def reach_deg(fov_radius_deg: float, size_major_arcmin: float | None) -> float:
    """Largest center separation at which the object still touches the frame."""
    return fov_radius_deg + radius_deg(size_major_arcmin)


def overlaps_frame(
    separation_deg: float, size_major_arcmin: float | None, fov_radius_deg: float | None
) -> bool:
    """False only for a real miss: a missing size or field keeps the candidate."""
    if fov_radius_deg is None or size_major_arcmin is None:
        return True
    return separation_deg <= reach_deg(fov_radius_deg, size_major_arcmin)
