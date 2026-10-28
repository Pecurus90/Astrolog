"""Rules against the setup (ADR 0039, docs/domini/misure.md): eccentricity out on one tail, the
"elongated stars" warning, the gust limits learnt from the setup's FWHM. Pure; wired at step 40."""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from ..robust import MIN_VALUES, relative_bounds

ELONGATED_ECCENTRICITY = 0.6  # [U ADR 0039: b/a 0.8, forum usage; sqrt(1 - 0.8^2) = 0.6]
# Time doubles where wind adds the calm FWHM^2 once (FWHM x sqrt 2), the frame is lost where it
# adds it three times (FWHM x 2): the seeing rule against the setup floor [P ADR 0039]
UNCERTAIN_SHARE = 1.0
UNUSABLE_SHARE = 3.0  # [P ADR 0039]


@dataclass(frozen=True)
class GustLimits:
    calm_fwhm: float  # FWHM with no wind, in the unit of the points
    uncertain_kmh: float
    unusable_kmh: float | None  # None: past the strongest gust measured, not extrapolated


def eccentricity_outliers(values: Sequence[float]) -> set[int]:
    """Indexes over median + 2.5 Qn of the setup; rounder stars are never out. Empty under 10."""
    bounds = relative_bounds(values)
    if bounds is None:
        return set()
    return {i for i, value in enumerate(values) if value > bounds.high}


def elongated_stars(values: Sequence[float]) -> bool | None:
    """The setup's median eccentricity over 0.6; None under 10 frames."""
    if len(values) < MIN_VALUES:
        return None
    return statistics.median(values) > ELONGATED_ECCENTRICITY


def _theil_sen(x: np.ndarray, y: np.ndarray) -> tuple[float, float] | None:
    """Median of the pairwise slopes, then the median intercept: a cloudy frame does not tilt it.
    [D Sen 1968, JASA 63:1379]"""
    i, j = np.triu_indices(len(x), k=1)
    apart = x[j] != x[i]
    if not apart.any():
        return None
    slope = float(np.median((y[j] - y[i])[apart] / (x[j] - x[i])[apart]))
    return slope, float(np.median(y - slope * x))


def gust_limits(points: Sequence[tuple[float, float]]) -> GustLimits | None:
    """FWHM^2 = calm^2 + c v^4 fitted on (gust km/h, FWHM) points, one per weather hour (the gust
    is hourly). None, and 25 km/h stays: under 10 points, no growth, or past the strongest gust."""
    if len(points) < MIN_VALUES:
        return None
    gust = np.array([p[0] for p in points], dtype=float)
    fwhm = np.array([p[1] for p in points], dtype=float)
    fit = _theil_sen(gust**4, fwhm**2)
    if fit is None:
        return None
    c, calm_sq = fit
    if c <= 0 or calm_sq <= 0:
        return None
    uncertain = (UNCERTAIN_SHARE * calm_sq / c) ** 0.25
    unusable = (UNUSABLE_SHARE * calm_sq / c) ** 0.25
    strongest = float(gust.max())
    if uncertain > strongest:
        return None
    return GustLimits(math.sqrt(calm_sq), uncertain, unusable if unusable <= strongest else None)
