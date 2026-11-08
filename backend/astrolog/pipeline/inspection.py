"""Sensor tilt and off-axis aberration as ASTAP's CCD inspector reads them from the HFDs, and the
sampling class of the FWHM (ADR 0022, ADR 0044, docs/domini/misure.md). Pure. software-ok"""

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ..levels import Verdict

# The frame in thirds, nine areas; centre the middle one, corners the four outer ones.
THIRDS = 3  # [C ASTAP unit_inspector_plot.pas CCDinspector: the nine areas; software-ok]
# Outer ring: "75% or more distance from centre. (100% is the distance to a corner.)"
OUTER_SHARE = 0.75  # [C ASTAP manual, hnsky.org/astap.htm, Image inspection; software-ok]
TILT_GOOD_PCT = 10.0  # [C ASTAP manual: "equal or less than 10% ... good"; software-ok]
TILT_PROBLEM_PCT = 20.0  # [C ASTAP manual: "equal or more than 20% ... tilt problem"; software-ok]
# FWHM in pixels: under 1.5 badly undersampled, 2-3 ideal, past 3 oversampled
SEVERE_UNDER_PX = 1.5  # [C Howell et al. 1996, PASP 108:1074]
IDEAL_LOW_PX = 2.0  # [C AAVSO CCD Photometry Guide; Diffraction Limited]
IDEAL_HIGH_PX = 3.0  # [C AAVSO CCD Photometry Guide; Diffraction Limited]


class SamplingClass(StrEnum):
    SEVERE_UNDER = "severe_under"
    UNDER = "under"
    IDEAL = "ideal"
    OVER = "over"


@dataclass(frozen=True)
class Inspection:
    tilt_pct: float | None  # 100 (worst - best corner median) / median of every star
    tilt_level: Verdict | None
    off_axis_px: float | None  # outer ring median less the centre's; + wider at the edge


def inspect(hfd: np.ndarray, x: np.ndarray, y: np.ndarray, shape: tuple[int, ...]) -> Inspection:
    """`hfd` px at `x` `y` px. Tilt needs a star in each of the nine areas, the off-axis
    aberration one in the centre and one in the ring; else None, as ASTAP."""
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
    corners = [float(np.median(cells[(i, j)])) for i in (0, 2) for j in (0, 2)]
    tilt = 100 * (max(corners) - min(corners)) / float(np.median(hfd))
    return Inspection(tilt, tilt_level(tilt), off_axis)


def sampling_class(fwhm_px: float | None) -> SamplingClass | None:
    if fwhm_px is None:
        return None
    if fwhm_px < SEVERE_UNDER_PX:
        return SamplingClass.SEVERE_UNDER
    if fwhm_px < IDEAL_LOW_PX:
        return SamplingClass.UNDER
    return SamplingClass.IDEAL if fwhm_px <= IDEAL_HIGH_PX else SamplingClass.OVER


def _third(position: np.ndarray, size: int) -> np.ndarray:
    """0, 1, 2 for each third; -1 on a border, which ASTAP's strict tests leave out."""
    low, high = size / THIRDS, size * 2 / THIRDS
    which = np.full(len(position), -1)
    which[position < low] = 0
    which[(position > low) & (position < high)] = 1
    which[position > high] = 2
    return which


def tilt_level(tilt_pct: float) -> Verdict:
    if tilt_pct <= TILT_GOOD_PCT:
        return Verdict.GO
    return Verdict.MARGINAL if tilt_pct < TILT_PROBLEM_PCT else Verdict.NOGO
