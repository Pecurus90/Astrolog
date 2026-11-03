"""Measures across the frame (ADR 0022 points 5 and 7, ADR 0037, misure.md): PSF photometry and
SNR, sky gradient, tilt and curvature from five zones. Pure: arrays in, numbers out."""

import math
from dataclasses import dataclass

import numpy as np

from ..robust import robust_chauvenet, winsorized
from ..units import sigma_from_mad
from .psf_fit import Fitted
from .shape import MIN_STARS

# PSF SNR = c3 F^2 / (c4 sigma^2), F the fitted stars' summed signal (psf_fit.py), sigma the noise.
PSF_SNR_C3 = 1.316e-7  # [C PixInsight ImageWeighting, eq. 23-24; software-ok]
PSF_SNR_C4 = 4.987e6  # [C PixInsight ImageWeighting, eq. 23-24; software-ok]
PSFSW_C1 = 5.326e-6  # [C PixInsight ImageWeighting, eq. 22; software-ok]
PSFSW_C2 = 9.0e6  # [C PixInsight ImageWeighting, eq. 22; software-ok]
MESH_PX = 64  # [C sep docs: Background bw, bh default] the reduced frame: one value a mesh
# The bright side only when a plane holds more of the map's variance than it leaves.
PLANE_EXPLAINS = 0.5  # [D R^2 over one half: the plane explains the larger part]
# Stars a zone needs: on a flat sensor the range of the four corner medians, d2(4) sqrt(pi/2)
# s / sqrt(n) for a relative HFD spread s, stays inside ASTAP's first tilt band.
TILT_BAND_PCT = 5.0  # [C ASTAP astap.htm, CCD inspector: tilt 0-5% "none"]
D2_FOUR = 2.059  # [C Montgomery, Statistical Quality Control: d2 for subgroups of 4]
MEDIAN_SE = math.sqrt(math.pi / 2)  # [D asymptotic standard error of the median, normal]
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


@dataclass(frozen=True)
class Photometry:
    """ImageAnalysis PSFFlux, PSFTotalMeanFlux, PSFCount, in the plane's units. software-ok"""

    flux: float  # sum of the stars' signal (ImageWeighting eq. 7)
    mean_flux: float  # sum of their mean fluxes (eq. 8), rejected ones winsorized (par. 2.2.1)
    count: int  # valid fits


def photometry(fits: Fitted) -> Photometry | None:
    """None without a fit: no flux to sum."""
    if len(fits.signal) == 0:
        return None
    mean = winsorized(fits.mean_flux, robust_chauvenet(fits.mean_flux))
    return Photometry(float(fits.signal.sum()), float(mean.sum()), len(fits.signal))


def psf_snr(flux: float, noise: float) -> float | None:
    """ImageWeighting eq. 7 and 23-24: the units cancel, ADU or SubframeSelector's [0, 1] alike."""
    if noise <= 0:
        return None
    return PSF_SNR_C3 * flux * flux / (PSF_SNR_C4 * noise * noise)


def psf_signal_weight(found: Photometry, noise: float, mstar: float) -> float | None:
    """ImageWeighting eq. 21-22: c1 sum f sum f-bar / (c2 sigma_n M*); the units cancel."""
    if noise <= 0 or mstar <= 0:
        return None
    return PSFSW_C1 * found.flux * found.mean_flux / (PSFSW_C2 * noise * mstar)


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


def zone_min_stars(hfd: np.ndarray) -> int:
    """From the frame's own HFD spread (MAD as sigma, over the median); never under MIN_STARS."""
    centre = float(np.median(hfd))
    spread = sigma_from_mad(float(np.median(np.abs(hfd - centre)))) / centre
    need = math.ceil((D2_FOUR * MEDIAN_SE * spread * 100 / TILT_BAND_PCT) ** 2)
    return max(MIN_STARS, need)


def zones_of(hfd: np.ndarray, x: np.ndarray, y: np.ndarray, shape: tuple[int, ...]) -> Zones | None:
    """Median HFD in the 3x3 grid's corners and centre (ASTAP's 1A 3A 1C 3C and 2B,
    hnsky.org/astap.htm); None when one of the five has under zone_min_stars(hfd)."""
    rows, cols = shape
    cell = np.minimum(y * GRID // rows, GRID - 1) * GRID + np.minimum(x * GRID // cols, GRID - 1)
    need = zone_min_stars(hfd)
    medians = {}
    for zone in (*CORNERS, CENTRE):
        here = hfd[cell == zone]
        if len(here) < need:
            return None
        medians[zone] = float(np.median(here))
    frame = float(np.median(hfd))
    corners = [medians[zone] for zone in CORNERS]
    tilt = 100 * (max(corners) - min(corners)) / frame
    curvature = 100 * (float(np.median(corners)) - medians[CENTRE]) / frame
    return Zones(tilt, curvature)
