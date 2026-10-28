"""Measures across the frame (ADR 0022 points 5 and 7, ADR 0037, docs/domini/misure.md): PSF SNR,
the sky gradient, tilt and curvature from five zones. Pure: arrays in, numbers out."""

import math
from dataclasses import dataclass

import numpy as np

# PSF SNR = c3 F^2 / (c4 sigma^2), F the stars' summed flux (psf_flux.py), sigma the noise.
PSF_SNR_C3 = 1.350e-7  # [C PixInsight ImageWeighting, eq. 18-19; software-ok]
PSF_SNR_C4 = 4.987e6  # [C PixInsight ImageWeighting, eq. 18-19; software-ok]
# F times this: at 1 the 10 even mono copies read 0.860 of the SubframeSelector's PSF SNR, so
# 1 / sqrt(0.860); the 10 odd ones then 0.91-1.15, median 0.99 (misure.md). [T] software-ok
PSF_FLUX_SCALE = 1.078
MESH_PX = 64  # [C sep docs: Background bw, bh default] the reduced frame: one value a mesh
PLANE_EXPLAINS = 0.5  # [T] the bright side only when a plane holds half the map's variance
# Stars per zone for tilt and curvature: worst less best of four medians is never under 0, and
# at 5 stars a zone (8% each) a flat sensor read 15%. [T] standard error under 2% at 25.
ZONE_MIN_STARS = 25
GRID = 3  # [P ADR 0037: the 3x3 grid, its corners and centre the five zones]
CORNERS = (0, GRID - 1, GRID * (GRID - 1), GRID * GRID - 1)  # [P ADR 0037]
CENTRE = GRID * GRID // 2  # [P ADR 0037]


@dataclass(frozen=True)
class Gradient:
    pct: float | None  # 100 (max - min) / median of the reduced sky; None: sky at 0 or under
    angle_deg: float | None  # the bright side, [0, 360) from +x towards +y; None: flat


@dataclass(frozen=True)
class Zones:
    tilt_pct: float  # 100 (worst - best corner HFD) / the frame's median HFD
    curvature_pct: float  # 100 (corners' median - centre) / the frame's median; + corners worse


def psf_snr(flux: float, noise: float) -> float | None:
    """ImageWeighting eq. 7 and 18-19: the units cancel, ADU or SubframeSelector's [0, 1] alike."""
    if noise <= 0:
        return None
    return PSF_SNR_C3 * flux * flux / (PSF_SNR_C4 * noise * noise)


def gradient_of(back: np.ndarray) -> Gradient:
    """Sky map at mesh centres: (max - min) / median; bright side from the least-squares plane when
    it explains the map (vignetting: no side). Our convention, no program has one (misure.md)."""
    rows, cols = back.shape
    ys, xs = np.mgrid[MESH_PX // 2 : rows : MESH_PX, MESH_PX // 2 : cols : MESH_PX]
    if ys.size == 0:
        ys, xs = np.mgrid[0:rows, 0:cols]
    values = back[ys, xs].astype(np.float64).ravel()
    median = float(np.median(values))
    spread = float(values.max() - values.min())
    if median <= 0:
        return Gradient(None, None)
    if spread == 0:
        return Gradient(0.0, None)
    pct = 100 * spread / median
    plane = np.column_stack([xs.ravel(), ys.ravel(), np.ones(values.size)]).astype(np.float64)
    fit = np.linalg.lstsq(plane, values, rcond=None)[0]
    left = values - plane @ fit
    explained = 1 - float(left @ left) / float(np.sum((values - values.mean()) ** 2))
    if explained < PLANE_EXPLAINS:
        return Gradient(pct, None)
    angle = math.degrees(math.atan2(fit[1], fit[0])) % 360
    return Gradient(pct, 0.0 if angle >= 360 else angle)


def zones_of(hfd: np.ndarray, x: np.ndarray, y: np.ndarray, shape: tuple[int, ...]) -> Zones | None:
    """Median HFD in the 3x3 grid's corners and centre (ASTAP's 1A 3A 1C 3C and 2B,
    hnsky.org/astap.htm); None when one of the five has under ZONE_MIN_STARS."""
    rows, cols = shape
    cell = np.minimum(y * GRID // rows, GRID - 1) * GRID + np.minimum(x * GRID // cols, GRID - 1)
    medians = {}
    for zone in (*CORNERS, CENTRE):
        here = hfd[cell == zone]
        if len(here) < ZONE_MIN_STARS:
            return None
        medians[zone] = float(np.median(here))
    frame = float(np.median(hfd))
    corners = [medians[zone] for zone in CORNERS]
    tilt = 100 * (max(corners) - min(corners)) / frame
    curvature = 100 * (float(np.median(corners)) - medians[CENTRE]) / frame
    return Zones(tilt, curvature)
