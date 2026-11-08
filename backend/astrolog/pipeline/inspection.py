"""Sensor tilt and off-axis aberration as ASTAP's CCD inspector reads them from the HFDs, and the
sampling class of the FWHM (ADR 0022, ADR 0044, docs/domini/misure.md). Pure. software-ok"""

from dataclasses import dataclass

import numpy as np

from ..levels import SamplingClass, Verdict, sampling_class, tilt_level

__all__ = ["SamplingClass", "sampling_class", "tilt_level"]  # the rules live in levels.py

# The frame in thirds, nine areas; centre the middle one, corners the four outer ones.
THIRDS = 3  # [C ASTAP unit_inspector_plot.pas CCDinspector: the nine areas; software-ok]
# Outer ring: "75% or more distance from centre. (100% is the distance to a corner.)"
OUTER_SHARE = 0.75  # [C ASTAP manual, hnsky.org/astap.htm, Image inspection; software-ok]


@dataclass(frozen=True)
class Inspection:
    tilt_pct: float | None  # 100 (worst - best corner median) / median of every star
    tilt_level: Verdict | None
    off_axis_px: float | None  # outer ring median less the centre's; + wider at the edge
    # corner medians at pixel (1,1) (W,1) (W,H) (1,H), as footprint.py; with the tilt only
    corners_px: tuple[float, float, float, float] | None = None
    centre_px: float | None = None  # the middle area's median, with the corners


def inspect(hfd: np.ndarray, x: np.ndarray, y: np.ndarray, shape: tuple[int, ...]) -> Inspection:
    """`hfd` px at `x` `y` px (0-based, y the row). Tilt needs a star in each of the nine areas,
    the off-axis aberration one in the centre and one in the ring; else None, as ASTAP."""
    rows, cols = shape
    across = _third(x, cols)
    along = _third(y, rows)
    areas = [(i, j) for i in range(THIRDS) for j in range(THIRDS)]
    cells = {(i, j): hfd[(across == i) & (along == j)] for i, j in areas}
    centre = cells[(1, 1)]
    half_x, half_y = cols / 2, rows / 2
    ring = hfd[(x - half_x) ** 2 + (y - half_y) ** 2 > OUTER_SHARE**2 * (half_x**2 + half_y**2)]
    off_axis = None
    if len(centre) and len(ring):
        off_axis = float(np.median(ring) - np.median(centre))
    if not all(len(c) for c in cells.values()):
        return Inspection(None, None, off_axis)
    c1, c2, c3, c4 = (float(np.median(cells[at])) for at in ((0, 0), (2, 0), (2, 2), (0, 2)))
    tilt = 100 * (max(c1, c2, c3, c4) - min(c1, c2, c3, c4)) / float(np.median(hfd))
    return Inspection(tilt, tilt_level(tilt), off_axis, (c1, c2, c3, c4), float(np.median(centre)))


def _third(position: np.ndarray, size: int) -> np.ndarray:
    """0, 1, 2 for each third; -1 on a border, which ASTAP's strict tests leave out."""
    low, high = size / THIRDS, size * 2 / THIRDS
    which = np.full(len(position), -1)
    which[position < low] = 0
    which[(position > low) & (position < high)] = 1
    which[position > high] = 2
    return which
