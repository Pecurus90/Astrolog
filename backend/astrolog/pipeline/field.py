"""Measures across the frame (ADR 0022 point 5, ADR 0042, misure.md): PSF photometry and SNR,
the sky's bright side, FWHM tilt and curvature, elongation. Pure: arrays in, numbers out."""

import math
from dataclasses import dataclass

import numpy as np

from ..robust import biweight_fit, robust_chauvenet, winsorized
from .psf_fit import Fitted, folded

# PSF SNR = c3 F^2 / (c4 sigma^2), F the fitted stars' summed signal (psf_fit.py), sigma the noise.
PSF_SNR_C3 = 1.316e-7  # [C PixInsight ImageWeighting, eq. 23-24; software-ok]
PSF_SNR_C4 = 4.987e6  # [C PixInsight ImageWeighting, eq. 23-24; software-ok]
PSFSW_C1 = 5.326e-6  # [C PixInsight ImageWeighting, eq. 22; software-ok]
PSFSW_C2 = 9.0e6  # [C PixInsight ImageWeighting, eq. 22; software-ok]
MESH_PX = 64  # [C sep docs: Background bw, bh default] the reduced frame: one value a mesh
# The bright side only when a plane holds more of the map's variance than it leaves.
PLANE_EXPLAINS = 0.5  # [D R^2 over one half: the plane explains the larger part]
TILT_MIN_STARS = 32  # [C ImageAnalysis par. 2.1.6: at least 32 fitted stars; software-ok]


@dataclass(frozen=True)
class Tilt:
    tilt: float  # ImageAnalysis FWHMTilt: (|b| W + |c| H) / (R a), eq. 27; software-ok
    curvature: float  # FWHMCurvature: d / a; + stars larger at the corners


@dataclass(frozen=True)
class Elongation:
    angle_deg: float  # ElongationAngle, [0, 180) counterclockwise from +x
    coherence: float  # ElongationCoherence: 0 random, 1 aligned


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


def bright_side(back: np.ndarray) -> float | None:
    """Sky map at mesh centres, its least-squares plane's uphill when it explains the map
    (vignetting: no side). Our convention, no program has one (misure.md)."""
    rows, cols = back.shape
    ys, xs = np.mgrid[MESH_PX // 2 : rows : MESH_PX, MESH_PX // 2 : cols : MESH_PX]
    if ys.size == 0:
        ys, xs = np.mgrid[0:rows, 0:cols]
    values = back[ys, xs].astype(np.float64).ravel()
    spread = float(np.sum((values - values.mean()) ** 2))
    if spread == 0:
        return None
    plane = np.column_stack([xs.ravel(), ys.ravel(), np.ones(values.size)]).astype(np.float64)
    fit = np.linalg.lstsq(plane, values, rcond=None)[0]
    left = values - plane @ fit
    if 1 - float(left @ left) / spread < PLANE_EXPLAINS:
        return None
    angle = math.degrees(math.atan2(fit[1], fit[0])) % 360
    return 0.0 if angle >= 360 else angle


def fwhm_tilt(fits: Fitted, shape: tuple[int, ...]) -> Tilt | None:
    """ImageAnalysis eq. 26-27: every fit's FWHM fitted by Tukey's biweight to a + b u + c v +
    d (u^2 + v^2), u v from the centre over the half diagonal R. None under TILT_MIN_STARS."""
    if len(fits.fwhm_px) < TILT_MIN_STARS:
        return None
    rows, cols = shape
    radius = math.hypot(cols, rows) / 2
    u, v = (fits.x_px - (cols - 1) / 2) / radius, (fits.y_px - (rows - 1) / 2) / radius
    design = np.column_stack([np.ones_like(u), u, v, u * u + v * v])
    a, b, c, d = biweight_fit(design, fits.fwhm_px)
    if a <= 0:
        return None
    return Tilt((abs(b) * cols + abs(c) * rows) / (radius * a), d / a)


def elongation(fits: Fitted) -> Elongation | None:
    """ImageAnalysis eq. 28-29: doubled angles weighted by the eccentricities; his counterclockwise
    from +x, ours towards +y with rows down, so 180 less ours. None: round stars or none."""
    weight = float(fits.eccentricity.sum())
    if weight <= 0:
        return None
    doubled = np.radians(2 * (180 - fits.angle_deg))
    c, s = (
        float((fits.eccentricity * np.cos(doubled)).sum()),
        float((fits.eccentricity * np.sin(doubled)).sum()),
    )
    # min: rounding lifts one fit or aligned fits past 1, the schema CHECK
    coherence = min(math.hypot(c, s) / weight, 1.0)
    return Elongation(folded(math.degrees(math.atan2(s, c)) / 2), coherence)
