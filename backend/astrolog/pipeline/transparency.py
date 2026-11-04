"""Transparency of one field and filter as Image Analysis (par. 2.1.7, misure.md Trasparenza):
each frame's brightness ladder; relative and cloud extinction over the series. Pure. software-ok"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from ..robust import biweight_fit

# Windows of 50 consecutive ranks by decreasing flux, from these ranks.
STARTS = (1, 51, 101, 201, 401, 801, 1601, 3201, 6401)  # [C ImageAnalysis par. 2.1.7; software-ok]
WIDTH = 50  # [C ImageAnalysis par. 2.1.7; software-ok]
# Saturated: peak at 3/4 of the frame's highest pixel or more.
SATURATED_SHARE = 0.75  # [C ImageAnalysis par. 2.1.7; software-ok]
# The median holds the same stars while under 40% of its window saturate.
MAX_SATURATED = 0.4  # [C ImageAnalysis par. 2.1.7; software-ok]
MIN_FIT_FRAMES = 5  # [C ImageAnalysis par. 2.1.7: five frames with air masses; software-ok]
MIN_SPAN = 0.05  # [C ImageAnalysis par. 2.1.7: air masses closer, only the constant; software-ok]
MAG = 2.5  # [D Pogson 1856: 5 magnitudes a factor 100]


@dataclass(frozen=True)
class SeriesFrame:
    ladder: Mapping[int, float]  # window start -> median log10 flux, ADU; missing: not available
    exposure_s: float | None
    airmass: float | None


@dataclass(frozen=True)
class Extinction:
    relative_mag: float | None  # RelativeExtinction; None: the window not available in it
    cloud_mag: float | None  # CloudExtinction; None: no air mass, or under MIN_FIT_FRAMES


@dataclass(frozen=True)
class Transparency:
    window: int | None  # rank the window starts at; None: no frame has one
    coefficient: (
        float | None
    )  # k of Bouguer's law, mag per air mass; None: constant only, or no fit
    frames: list[Extinction]  # in the order given


def brightness_ladder(flux: np.ndarray, saturated: np.ndarray) -> dict[int, float]:
    """Per star its flux (NaN or <= 0: no rank) and saturation. The windows the frame holds, each
    the median log10 flux, saturated stars over every other of their window."""
    ranked = np.flatnonzero(np.isfinite(flux) & (flux > 0))
    ranked = ranked[np.argsort(-flux[ranked], kind="stable")]
    ladder = {}
    for start in STARTS:
        window = ranked[start - 1 : start - 1 + WIDTH]
        if len(window) < WIDTH or saturated[window].mean() >= MAX_SATURATED:
            continue
        logs = np.where(saturated[window], np.inf, np.log10(flux[window]))
        ladder[start] = float(np.median(logs))
    return ladder


def transparency(frames: Sequence[SeriesFrame]) -> Transparency:
    """ImageAnalysis eq. 30-31: one window for the series, the one most frames have, the
    brightest on a tie; fluxes per second when every frame has its exposure. software-ok"""
    counts = {s: sum(s in f.ladder for f in frames) for s in STARTS}
    if not frames or not max(counts.values()):
        return Transparency(None, None, [Extinction(None, None) for _ in frames])
    window = max(STARTS, key=lambda s: (counts[s], -s))
    timed = all(f.exposure_s and f.exposure_s > 0 for f in frames)
    level = [-MAG * (f.ladder[window] - (math.log10(f.exposure_s) if timed and f.exposure_s else 0))
             if window in f.ladder else None for f in frames]  # fmt: skip
    clearest = min(v for v in level if v is not None)
    relative = [None if v is None else v - clearest for v in level]
    coefficient, clouds = _bouguer(relative, [f.airmass for f in frames])
    return Transparency(
        window, coefficient, [Extinction(r, c) for r, c in zip(relative, clouds, strict=True)]
    )


def _bouguer(
    relative: list[float | None], airmass: list[float | None]
) -> tuple[float | None, list[float | None]]:
    """Delta m = a + k X on the frames with both, residuals the clouds (eq. 31)."""
    known = [i for i, (r, x) in enumerate(zip(relative, airmass, strict=True))
             if r is not None and x is not None]  # fmt: skip
    clouds: list[float | None] = [None] * len(relative)
    if len(known) < MIN_FIT_FRAMES:
        return None, clouds
    x = np.array([airmass[i] for i in known], dtype=float)
    y = np.array([relative[i] for i in known], dtype=float)
    sloped = float(np.ptp(x)) >= MIN_SPAN
    design = np.column_stack([np.ones_like(x), x]) if sloped else np.ones((len(x), 1))
    fit = biweight_fit(design, y, upper=True)
    for i, left in zip(known, y - design @ fit, strict=True):
        clouds[i] = float(left)
    return (float(fit[1]) if sloped else None), clouds
