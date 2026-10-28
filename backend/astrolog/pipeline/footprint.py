"""Frame's rectangle on the sky from ASTAP's solution: scale, mirror, skew, field, corners.
Formulas: Calabretta & Greisen 2002 (WCS Paper II), TAN projection, which ASTAP writes."""

import math
from dataclasses import dataclass

from ..units import field_deg
from .sky import deproject

type Sky = tuple[float, float]  # RA, Dec J2000 degrees


@dataclass(frozen=True)
class Footprint:
    scale_arcsec_px: float
    mirrored: bool
    skew_deg: float
    width_deg: float | None  # frame size unknown: None
    height_deg: float | None
    corners: tuple[Sky, Sky, Sky, Sky] | None  # outer edges of pixels (1,1) (W,1) (W,H) (1,H)


def footprint(
    cd: tuple[float, float, float, float],
    crpix: tuple[float, float],
    centre: Sky,
    size: tuple[int | None, int | None],
    bottom_up: bool,
) -> Footprint:
    """`bottom_up`: ROWORDER holds 'BOT'. Rows from top (N.I.N.A., ASIAIR: measured on mirrored
    copies) give det > 0 on a normal frame; from bottom, rule reversed."""
    cd11, cd12, cd21, cd22 = cd
    det = cd11 * cd22 - cd12 * cd21
    scale = math.sqrt(abs(det)) * 3600.0
    sign = 1.0 if det > 0 else -1.0  # CDELT1's sign in ASTAP's .ini: 27 of 27 measured
    # Paper II eq. 189 angle of each axis; skew: their gap (Paper II wants it zero, no number)
    first_axis = math.atan2(sign * cd21, sign * cd11)
    second_axis = math.atan2(-cd12, cd22)
    width, height = size
    return Footprint(
        scale_arcsec_px=scale,
        mirrored=(det < 0) != bottom_up,
        skew_deg=abs(math.degrees(math.remainder(first_axis - second_axis, math.tau))),
        width_deg=field_deg(width, scale),
        height_deg=field_deg(height, scale),
        corners=_corners(cd, crpix, centre, width, height),
    )


def position_angle(cd: tuple[float, float, float, float], angle_deg: float) -> float:
    """A direction on the file's pixels (from +x toward +y, rows as stored) as a position angle on
    the sky, [0, 360) from North toward East: the CD matrix maps it to (east, north), Paper II."""
    a = math.radians(angle_deg)
    east = cd[0] * math.cos(a) + cd[1] * math.sin(a)
    north = cd[2] * math.cos(a) + cd[3] * math.sin(a)
    turned = math.degrees(math.atan2(east, north)) % 360.0
    return 0.0 if turned >= 360.0 else turned  # -1e-17 % 360 is 360.0


def _corners(
    cd: tuple[float, float, float, float],
    crpix: tuple[float, float],
    centre: Sky,
    width: int | None,
    height: int | None,
) -> tuple[Sky, Sky, Sky, Sky] | None:
    if width is None or height is None:
        return None
    left, right, low, high = 0.5, width + 0.5, 0.5, height + 0.5  # FITS pixel centres at n
    edges = ((left, low), (right, low), (right, high), (left, high))
    return tuple(_tan_inverse(cd, crpix, centre, edge) for edge in edges)  # type: ignore[return-value]


def _tan_inverse(
    cd: tuple[float, float, float, float], crpix: tuple[float, float], centre: Sky, pixel: Sky
) -> Sky:
    """Pixel to sky: intermediate coordinates from CD (Paper II x, y), then deprojection."""
    dx, dy = pixel[0] - crpix[0], pixel[1] - crpix[1]
    east = math.radians(cd[0] * dx + cd[1] * dy)
    north = math.radians(cd[2] * dx + cd[3] * dy)
    return deproject(centre, east, north)
