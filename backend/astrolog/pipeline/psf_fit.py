"""Each star's PSF and PSF flux as Image Analysis fits them (par. 2.1.6; ImageWeighting 2.2): Moffat
beta 4 at pixel centres, sky fitted, median-stabilized square. Pure. software-ok"""

import math
from concurrent.futures import Executor
from dataclasses import dataclass, fields
from functools import partial
from typing import Any

import numpy as np
from scipy.optimize import leastsq  # pyright: ignore[reportMissingTypeStubs]

from . import cores

BETA = 4.0  # [C ImageAnalysis par. 2.1.6: default PSF type Moffat beta 4; software-ok]
# Region grows while its median falls by at least this.
MEDIAN_DROP = 0.01  # [C ImageAnalysis par. 2.1.6; PJSR PSF, Adaptive sampling region; software-ok]
MAX_FITS = 8000  # [C ImageAnalysis Maximum PSF fits default, brightest first; software-ok]
# PSF flux on more: its PSFCount reaches 23263 on the bench. ImageWeighting 3.1.1 says "24K".
MAX_FLUX_FITS = 24576  # [C ImageCalibration maxStars default, read in PJSR; software-ok]
# PSF.signal sums the pixels over B within the tenth ellipse grown by this, each semi-axis.
GROW_PX = 1.0  # [M plan 26.50: signal and count 1.000 in median, PJSR PSF.signal, 3641 stars]
MAX_HALF_PX = 64  # [T] a region still falling past 129 px across sits on a nebula: stops there
# Fit refused with its centre this close to its region's edge, or off its detected structure.
EDGE_PX = 1.0  # [T] ImageWeighting par. 2.2.1 says "too close", no number; software-ok
TENTH = 0.1  # [C ImageAnalysis eq. 24: flux on the FWTM ellipse; software-ok]
# Flux measurement region, in FWTM: the transparency's flux (transparency.py).
APERTURE_FWTM = 1.0  # [C PJSR PSF.fitStar growth default 1.0, in FWTM; software-ok]
WINSOR = 0.1  # [C ImageAnalysis par. 2.1.6: residual a 10% Winsorized mean; software-ok]
EVALUATIONS_PER_PARAMETER = 50  # [T] a star that does not converge stops there
LM_TOLERANCE = 1e-8  # [C scipy least_squares default ftol, xtol, gtol]
CONVERGED = (1, 2, 3, 4)  # [C MINPACK lmder info: 1-4 converged, 5 out of evaluations]
POOL_STARS = 500  # [T] fewer fit in 0.3 s on one core: not worth the processes
CHUNKS_PER_CORE = 4  # [T] uneven stars even out over several chunks a process
_HALF = 2 ** (1 / BETA) - 1  # [D Moffat 1969: half maximum where (1 + q)^-beta = 1/2]
_TENTH = TENTH ** (-1 / BETA) - 1


@dataclass(frozen=True)
class Fitted:
    """Per fitted star, brightest first, the refused left out; residual NaN without signal."""

    fwhm_px: np.ndarray  # 2 sqrt(sx sy) sqrt(2^(1/beta) - 1), ImageAnalysis eq. 22
    eccentricity: np.ndarray  # sqrt(1 - sy^2 / sx^2), eq. 23
    angle_deg: np.ndarray  # long axis, [0, 180) from +x towards +y
    residual: np.ndarray  # eq. 24: Winsorized mean |v - f| over the mean signal 4 S / (pi Wx Wy)
    signal: np.ndarray  # ImageWeighting eq. 7, plane units: S of eq. 24, the PSF flux
    mean_flux: np.ndarray  # eq. 8-10: signal over the tenth ellipse's area
    aperture_flux: np.ndarray  # v - B in the ellipse of semi-axes the FWTM (APERTURE_FWTM)
    star: np.ndarray  # index of the detected star fitted
    rank: np.ndarray  # place in the brightness order: MAX_FITS of them make the shape
    x_px: np.ndarray  # fitted centre, column
    y_px: np.ndarray  # fitted centre, row

    def brightest(self) -> "Fitted":
        """The fits among the MAX_FITS brightest tried, as Image Analysis measures the shape."""
        first = self.rank < MAX_FITS
        return Fitted(*(getattr(self, f.name)[first] for f in fields(self)))


def fit_stars(
    plane: np.ndarray, x: np.ndarray, y: np.ndarray, box: np.ndarray, flux: np.ndarray
) -> Fitted:
    """`plane` the measured pixels with their sky (the median needs its level); `box` per star
    (x0, x1, y0, y1); the MAX_FLUX_FITS brightest by `flux` fitted."""
    order = np.argsort(-flux, kind="stable")[:MAX_FLUX_FITS]
    stars = [(float(x[i]), float(y[i]), box[i], int(i), rank) for rank, i in enumerate(order)]
    rows = _pooled(stars, plane) if len(stars) >= POOL_STARS else None
    if rows is None:
        rows = _fitted(stars, plane)
    if not rows:
        return Fitted(*(np.empty(0),) * len(fields(Fitted)))
    return Fitted(*(np.array(c, dtype=np.float64) for c in zip(*rows, strict=True)))


def _pooled(stars: list[tuple[Any, ...]], plane: np.ndarray) -> list[tuple[float, ...]] | None:
    """`_fitted` interleaved over the processes, the bright, wide regions shared out; None when
    the shared memory does not fit or a worker died (then a fresh pool next frame)."""
    share = cores.CORES * CHUNKS_PER_CORE

    def work(pool: Executor, ref: Any) -> list[tuple[float, ...]]:
        parts = [pool.submit(cores.attached, ref, partial(_fitted, stars[k::share]))
                 for k in range(share)]  # fmt: skip
        return sorted((r for p in parts for r in p.result()), key=lambda r: r[8])

    return cores.shared_work(plane, work, "star fits")


def _fitted(stars: list[tuple[Any, ...]], plane: np.ndarray) -> list[tuple[float, ...]]:
    """(x, y, box, star, rank) each: the fit's row, star and rank after its first seven."""
    return [(*s[:7], i, rank, *s[7:]) for x, y, box, i, rank in stars
            if (s := _one(plane, x, y, box)) is not None]  # fmt: skip


def region(plane: np.ndarray, cx: int, cy: int, box: np.ndarray) -> tuple[slice, slice]:
    """Square on the star, half side its structure's larger side, a pixel a side per step while
    the median falls by MEDIAN_DROP or more (PJSR PSF, Adaptive sampling region); edges cut it."""
    x0, x1, y0, y1 = (int(v) for v in box)
    half = max(1, x1 - x0, y1 - y0)
    rows, cols = plane.shape

    def window(h: int) -> tuple[slice, slice]:
        return (slice(max(0, cy - h), min(rows, cy + h + 1)),
                slice(max(0, cx - h), min(cols, cx + h + 1)))  # fmt: skip

    median = float(np.median(plane[window(half)]))
    while half < MAX_HALF_PX:
        grown = float(np.median(plane[window(half + 1)]))
        if median - grown < MEDIAN_DROP * abs(median):
            break
        half, median = half + 1, grown
    return window(half)


def _one(plane: np.ndarray, x: float, y: float, box: np.ndarray) -> tuple[float, ...] | None:
    cx, cy = round(x), round(y)
    rs, cs = region(plane, cx, cy, box)
    values = plane[rs, cs].astype(np.float64)
    ys, xs = np.mgrid[rs, cs]
    xs, ys, values = xs.ravel().astype(np.float64), ys.ravel().astype(np.float64), values.ravel()
    sky = float(np.median(values))
    peak = float(values.max()) - sky
    if peak <= 0:
        return None
    width = max(1.0, (box[1] - box[0] + box[3] - box[2]) / 8)
    start = np.array([0.0, 1.0, x, y, math.log(width), math.log(width), 0.0])
    scaled = (values - sky) / peak
    if len(values) < len(start):  # MINPACK fits no fewer residuals than parameters
        return None
    try:
        with np.errstate(divide="raise", over="raise", invalid="raise", under="ignore"):
            # least_squares(method="lm", x_scale="jac")'s own MINPACK call, without its wrappers
            fitted, _, _, _, status = leastsq(  # pyright: ignore[reportAssignmentType]
                _residuals, start, args=(xs, ys, scaled), Dfun=_jacobian, full_output=True,
                ftol=LM_TOLERANCE, xtol=LM_TOLERANCE, gtol=LM_TOLERANCE,
                maxfev=EVALUATIONS_PER_PARAMETER * (len(start) + 1))  # fmt: skip
    except (ValueError, ArithmeticError):
        return None
    b, a, x0, y0, log_sx, log_sy, theta = fitted
    if status not in CONVERGED or not np.all(np.isfinite(fitted)) or a <= 0:
        return None
    if not _placed(x0, y0, (xs, ys), box):
        return None
    sx, sy = math.exp(log_sx), math.exp(log_sy)
    signal = _signal(scaled, (xs - x0, ys - y0), (sx, sy, theta), b)
    tenth_x, tenth_y = sx * math.sqrt(_TENTH), sy * math.sqrt(_TENTH)
    residual = _residual(scaled, _model(fitted, xs, ys), signal, (2 * tenth_x, 2 * tenth_y))
    long_axis, short_axis = max(sx, sy), min(sx, sy)
    angle = math.degrees(theta) + (0 if sx >= sy else 90)
    fwhm = 2 * math.sqrt(sx * sy) * math.sqrt(_HALF)
    eccentricity = math.sqrt(1 - (short_axis / long_axis) ** 2)
    flux = signal * peak  # back to the plane's units
    mean_flux = flux / (math.pi * tenth_x * tenth_y)
    aperture = _aperture(plane, (x0, y0), (2 * tenth_x, 2 * tenth_y, theta), sky + b * peak)
    return fwhm, eccentricity, folded(angle), residual, flux, mean_flux, aperture, x0, y0


def _aperture(
    plane: np.ndarray, centre: tuple[float, float], axes: tuple[float, float, float], sky: float
) -> float:
    """Sum of v - B over the ellipse of semi-axes APERTURE_FWTM times the FWTM, past the
    sampling region if it reaches further; the frame's edge cuts it."""
    x0, y0 = centre
    ax, ay, theta = APERTURE_FWTM * axes[0], APERTURE_FWTM * axes[1], axes[2]
    reach = math.ceil(max(ax, ay))
    rows, cols = plane.shape
    r0, r1 = max(0, round(y0) - reach), min(rows, round(y0) + reach + 1)
    c0, c1 = max(0, round(x0) - reach), min(cols, round(x0) + reach + 1)
    ys, xs = np.mgrid[r0:r1, c0:c1]
    c, s = math.cos(theta), math.sin(theta)
    u, v = c * (xs - x0) + s * (ys - y0), -s * (xs - x0) + c * (ys - y0)
    inside = (u / ax) ** 2 + (v / ay) ** 2 <= 1
    return float((plane[r0:r1, c0:c1][inside].astype(np.float64) - sky).sum())


def _placed(x0: float, y0: float, pixels: tuple[np.ndarray, np.ndarray], box: np.ndarray) -> bool:
    """Centre inside the detected structure and EDGE_PX inside the region (ImageWeighting 2.2.1)."""
    xs, ys = pixels
    inside_box = box[0] - 0.5 <= x0 <= box[1] - 0.5 and box[2] - 0.5 <= y0 <= box[3] - 0.5
    off_edge = (xs.min() + EDGE_PX <= x0 <= xs.max() - EDGE_PX
                and ys.min() + EDGE_PX <= y0 <= ys.max() - EDGE_PX)  # fmt: skip
    return bool(inside_box and off_edge)


def _signal(
    values: np.ndarray,
    offsets: tuple[np.ndarray, np.ndarray],
    axes: tuple[float, float, float],
    sky: float,
) -> float:
    """ImageWeighting eq. 7: sum of v - B over the pixels with v > B, in the tenth ellipse grown
    by GROW_PX (PSF.signal, misure.md)."""
    sx, sy, theta = axes
    dx, dy = offsets
    c, s = math.cos(theta), math.sin(theta)
    u, v = c * dx + s * dy, -s * dx + c * dy
    rx, ry = sx * math.sqrt(_TENTH) + GROW_PX, sy * math.sqrt(_TENTH) + GROW_PX
    above = values[(u / rx) ** 2 + (v / ry) ** 2 <= 1] - sky
    return float(above[above > 0].sum())


def _residual(
    values: np.ndarray, model: np.ndarray, signal: float, fwtm: tuple[float, float]
) -> float:
    """ImageAnalysis eq. 24 on values scaled alike: the ratio does not see the scale."""
    if signal <= 0:
        return math.nan
    wx, wy = fwtm
    return winsorized_mean(np.abs(values - model)) / (4 * signal / (math.pi * wx * wy))


def winsorized_mean(values: np.ndarray, share: float = WINSOR) -> float:
    """Mean with the lowest and highest `share` set to the nearest kept value."""
    ordered = np.sort(values)
    cut = int(share * len(ordered))
    if cut:
        ordered[:cut] = ordered[cut]
        ordered[-cut:] = ordered[-cut - 1]
    return float(ordered.mean())


def folded(degrees: float) -> float:
    """Into [0, 180): -1e-15 % 180 rounds to 180.0, which the schema refuses."""
    turned = degrees % 180
    return 0.0 if turned >= 180 else turned


@cores.inlined
def _widths(p: np.ndarray) -> tuple[float, float]:
    """sx^2, sy^2; FloatingPointError where numpy's errstate would raise: exp overflowing, or
    flushed to zero and divided by."""
    sx2, sy2 = math.exp(2 * p[4]), math.exp(2 * p[5])
    if not (math.isfinite(sx2) and math.isfinite(sy2)) or sx2 == 0 or sy2 == 0:
        raise FloatingPointError("PSF width out of range")
    return sx2, sy2


@cores.inlined
def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise FloatingPointError("PSF model out of range")
    return value


@cores.compiled
def _model(p: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """B + A (1 + u^2/sx^2 + v^2/sy^2)^-beta, u v the pixel's offset turned by theta."""
    sx2, sy2 = _widths(p)
    c, s = math.cos(p[6]), math.sin(p[6])
    out = np.empty(len(xs))
    for i in range(len(xs)):
        dx, dy = xs[i] - p[2], ys[i] - p[3]
        u, v = c * dx + s * dy, -s * dx + c * dy
        out[i] = _finite(p[0] + p[1] * (1 + u * u / sx2 + v * v / sy2) ** -BETA)
    return out


@cores.compiled
def _residuals(p: np.ndarray, xs: np.ndarray, ys: np.ndarray, values: np.ndarray) -> np.ndarray:
    return _model(p, xs, ys) - values


@cores.compiled
def _jacobian(p: np.ndarray, xs: np.ndarray, ys: np.ndarray, _values: np.ndarray) -> np.ndarray:
    """_model's, analytic (MINPACK lmder)."""
    a, (sx2, sy2) = p[1], _widths(p)
    c, s = math.cos(p[6]), math.sin(p[6])
    jac = np.empty((len(xs), 7))
    for i in range(len(xs)):
        dx, dy = xs[i] - p[2], ys[i] - p[3]
        u, v = c * dx + s * dy, -s * dx + c * dy
        base = 1 + u * u / sx2 + v * v / sy2
        g = base**-BETA
        dg = -BETA * g / base * a  # d model / d base
        jac[i, 0] = 1.0
        jac[i, 1] = g
        jac[i, 2] = _finite(dg * (-2 * c * u / sx2 + 2 * s * v / sy2))
        jac[i, 3] = _finite(dg * (-2 * s * u / sx2 - 2 * c * v / sy2))
        jac[i, 4] = _finite(dg * (-2 * u * u / sx2))
        jac[i, 5] = _finite(dg * (-2 * v * v / sy2))
        jac[i, 6] = _finite(dg * 2 * u * v * (1 / sx2 - 1 / sy2))
    return jac
