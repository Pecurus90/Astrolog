"""Star shape (ADR 0042, misure.md Forma): psf_fit.py on each star; the frame's biweight FWHM,
eccentricity, PSF residual, their Qn, a direction. Pure: pixels in, numbers out. software-ok"""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ..robust import biweight_location, qn
from .psf_fit import MAX_FITS, Fitted, folded
from .psf_flux import RING_OUTER

# Doughnut window: a circle of 2 FWHM, never under 3 px, its sky the ring out to RING_OUTER. [T]
WINDOW_FWHM = 2.0
WINDOW_MIN_PX = 3.0  # [T]
# Centre this far under its ring: a doughnut, out of focus.
DOUGHNUT_SIGMA = 3.0  # [C Starck and Murtagh 1998: significance at 3 sigma, as noise.py]
# Fits that hold at least half the stars, else the moments speak: their median is then theirs.
FIT_SHARE = 0.5  # [D the median's breakdown point, one half (Hampel 1971)]
UNMEASURABLE_ECCENTRICITY = 0.99  # [P ADR 0022: eccentricity from 0.99, shape not measurable]
DIRECTION_ECCENTRICITY = 0.4  # [P ADR 0022: direction only from eccentricity 0.4]
# One direction where the axial Rayleigh test rejects a uniform spread at this level.
DIRECTION_ALPHA = 0.05  # [C Zar, Biostatistical Analysis, 27.1: Rayleigh test, alpha 0.05]
SIGMA_TO_FWHM = 2.3548  # [D Gaussian profile: FWHM = 2 sqrt(2 ln 2) sigma]
# Fewer stars: a median (HFD, shape) says nothing. At 5 the lowest and highest hold the median
# with 94% (1 - 2 / 2^5), the first n over 90%. [D order statistics, distribution-free]
MIN_STARS = 5

type Record = np.void | np.ndarray  # one detection of sep's structured array


class ShapeKind(StrEnum):
    FITTED = "fitted"  # the Moffat fit held
    ESTIMATED = "estimated"  # the fit failed: sep's moments, said on the row
    UNMEASURABLE = "unmeasurable"  # doughnuts, or lines (eccentricity from 0.99)


@dataclass(frozen=True)
class Spread:
    """Qn of the stars' values (ImageAnalysis Sigma columns); the residual's only when fitted."""

    fwhm_px: float | None
    eccentricity: float | None
    psf_residual: float | None


@dataclass(frozen=True)
class Shape:
    kind: ShapeKind
    stars: int  # stars the values are the robust mean of; unmeasurable: stars looked at
    fwhm_px: float | None  # geometric mean of the two axes, sensor pixels
    eccentricity: float | None  # sqrt(1 - (b/a)^2)
    angle_deg: float | None  # long axis, [0, 180) from +x (columns) towards +y (rows)
    psf_residual: float | None = None  # ImageAnalysis PSFResidual; only fitted
    spread: Spread | None = None  # None with no values


def shape_of(
    images: tuple[np.ndarray, np.ndarray],
    objects: np.ndarray,
    chosen: np.ndarray,
    noise: float,
    fitted: tuple[Fitted, int],
) -> Shape | None:
    """`images`: the residual and its median copy; `chosen`: indices in sep's `objects`, for
    doughnuts and moments; `fitted`: psf_fit's stars and how many were tried. None: too few."""
    fits, tried = fitted[0].brightest(), min(fitted[1], MAX_FITS)
    doughnuts = sum(_doughnut(images, objects[i], noise) for i in chosen)
    if len(chosen) >= MIN_STARS and doughnuts > len(chosen) / 2:
        return Shape(ShapeKind.UNMEASURABLE, len(chosen), None, None, None)
    if len(fits.fwhm_px) >= max(MIN_STARS, FIT_SHARE * tried):
        return _frame(ShapeKind.FITTED, fits)
    if len(chosen) < MIN_STARS:
        return None
    return _frame(ShapeKind.ESTIMATED, _moments(objects[chosen]))


def _frame(kind: ShapeKind, stars: Fitted) -> Shape:
    """Biweight and Qn over the stars, as Image Analysis aggregates them (par. 2.1.6)."""
    eccentricity = biweight_location(stars.eccentricity)
    if eccentricity is None or eccentricity >= UNMEASURABLE_ECCENTRICITY:
        return Shape(ShapeKind.UNMEASURABLE, len(stars.fwhm_px), None, None, None)
    residuals = stars.residual[np.isfinite(stars.residual)]
    angle = None
    if eccentricity >= DIRECTION_ECCENTRICITY:
        angle = _direction(list(stars.angle_deg))
    fitted = kind is ShapeKind.FITTED
    spread = Spread(qn(stars.fwhm_px), qn(stars.eccentricity), qn(residuals) if fitted else None)
    return Shape(kind, len(stars.fwhm_px), biweight_location(stars.fwhm_px), eccentricity, angle,
                 biweight_location(residuals) if fitted else None, spread)  # fmt: skip


def _direction(angles: list[float]) -> float | None:
    """Axial mean: angles doubled on the circle, so 179 and 1 agree [D Mardia 1972, axial data];
    one direction only where the Rayleigh test rejects no direction (Zar eq. 27.4)."""
    mean = np.mean(np.exp(2j * np.radians(angles)))
    n = len(angles)
    resultant = n * float(abs(mean))
    p = math.exp(math.sqrt(1 + 4 * n + 4 * (n * n - resultant**2)) - (1 + 2 * n))
    if p >= DIRECTION_ALPHA:
        return None
    return folded(float(np.degrees(np.angle(mean))) / 2)


def estimated_fwhm(objects: np.ndarray) -> np.ndarray:
    """FWHM guessed from sep's second moments: windows, edges, neighbours, apertures."""
    return SIGMA_TO_FWHM * np.sqrt(np.maximum(objects["a"] * objects["b"], 0.25))


def _moments(stars: np.ndarray) -> Fitted:
    """sep's second moments of the detections, on the median copy: the fallback (ADR 0022)."""
    a, b = stars["a"].astype(np.float64), stars["b"].astype(np.float64)
    eccentricity = np.sqrt(np.maximum(0.0, 1 - (b / np.maximum(a, 1e-12)) ** 2))
    eccentricity[a <= 0] = 0.0
    angles = np.array([folded(math.degrees(float(t))) for t in stars["theta"]])
    nothing = np.full(len(stars), np.nan)
    return Fitted(estimated_fwhm(stars).astype(np.float64), eccentricity, angles, nothing,
                  nothing, nothing, np.arange(len(stars)))  # fmt: skip


def _doughnut(images: tuple[np.ndarray, np.ndarray], star: Record, noise: float) -> bool:
    """Centre darker than the ring around it, on the residual less the ring's median sky; the inner
    disc holds the centre pixel at least."""
    residual, filtered = images
    x, y = float(star["x"]), float(star["y"])
    guess = float(estimated_fwhm(star))  # pyright: ignore[reportArgumentType]
    radius = max(WINDOW_MIN_PX, WINDOW_FWHM * guess)
    rows, cols, reach = *residual.shape, radius * RING_OUTER
    y0, y1 = max(0, int(y - reach)), min(rows, int(y + reach) + 2)
    x0, x1 = max(0, int(x - reach)), min(cols, int(x + reach) + 2)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    distance = np.hypot(xs - x, ys - y)
    sky = float(np.median(filtered[y0:y1, x0:x1][(distance >= radius) & (distance < reach)]))
    values = residual[y0:y1, x0:x1].astype(np.float64) - sky
    inner = max(1.0, guess / 4)
    centre = values[distance < inner]
    ring = values[(distance >= inner) & (distance < max(2.0, guess / 2))]
    if len(centre) == 0 or len(ring) == 0:
        return False
    margin = DOUGHNUT_SIGMA * noise / math.sqrt(len(centre))
    return float(centre.mean()) < float(ring.mean()) - margin
