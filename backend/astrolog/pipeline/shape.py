"""Star shape (ADR 0022 point 4, docs/domini/misure.md): elliptical Moffat by Levenberg-Marquardt,
integrated on the pixel; the frame's FWHM, eccentricity, direction. Pure: pixels in, numbers out."""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from scipy.optimize import least_squares  # pyright: ignore[reportMissingTypeStubs]

# Window: a circle of 2 FWHM, never under 3 px; neighbours are kept 3 FWHM away (stars.py). [T]
WINDOW_FWHM = 2.0
WINDOW_MIN_PX = 3.0  # [T]
RING_OUTER = 1.5  # [T] the local sky: the ring from the window (or aperture) to 1.5 times it
# Beta over 1, else the flux is infinite [D Moffat 1969]. At most 100, a Gaussian for the fit:
# capped at 10 a Gaussian star read 3% narrow, at 100 within 0.1%. [T] synthetic stars
BETA_MIN = 1.01
BETA_MAX = 100.0  # [T]
START_BETA = 2.5  # [M misure.md: HFD/FWHM 1.36 on the 24 real frames, a Moffat of beta 2.5]
EVALUATIONS_PER_PARAMETER = 50  # [T] a star that does not converge stops there
HOT_SIGMA = 5.0  # [T] raw over its median copy by this much off the core: a hot pixel, masked
DOUGHNUT_SIGMA = 3.0  # [T] centre this far under its ring: a doughnut, out of focus
FIT_SHARE = 0.5  # [T] fits that hold at least half the stars, else the moments speak
UNMEASURABLE_ECCENTRICITY = 0.99  # [P ADR 0022: eccentricity from 0.99, shape not measurable]
DIRECTION_ECCENTRICITY = 0.4  # [P ADR 0022: direction only from eccentricity 0.4]
DIRECTION_AGREEMENT = 0.5  # [T] length of the mean of 2 theta: under it no one direction
SIGMA_TO_FWHM = 2.3548  # [D Gaussian profile: FWHM = 2 sqrt(2 ln 2) sigma]
MIN_STARS = 5  # [T] fewer stars: a median (HFD, shape) says nothing; measured on real frames

type Record = np.void | np.ndarray  # one detection of sep's structured array


class ShapeKind(StrEnum):
    FITTED = "fitted"  # the Moffat fit held
    ESTIMATED = "estimated"  # the fit failed: sep's moments, said on the row
    UNMEASURABLE = "unmeasurable"  # doughnuts, or lines (eccentricity from 0.99)


@dataclass(frozen=True)
class Shape:
    kind: ShapeKind
    stars: int  # stars the values are the median of; unmeasurable: stars looked at
    fwhm_px: float | None  # geometric mean of the two axes, sensor pixels
    eccentricity: float | None  # sqrt(1 - (b/a)^2)
    angle_deg: float | None  # long axis, [0, 180) from +x (columns) towards +y (rows)


@dataclass(frozen=True)
class Star:
    fwhm_px: float
    eccentricity: float
    angle_deg: float


@dataclass(frozen=True)
class Window:
    """Pixels of one star, values over its peak, and the sky-free start of its fit."""

    xs: np.ndarray
    ys: np.ndarray
    values: np.ndarray
    start: np.ndarray
    offsets: np.ndarray  # sub-pixel sample positions, the model integrated on the pixel


def shape_of(
    images: tuple[np.ndarray, np.ndarray], objects: np.ndarray, chosen: np.ndarray, noise: float
) -> Shape | None:
    """`images`: the residual (raw less sky) and its median copy; `chosen`: indices in sep's
    `objects`. None with fewer than MIN_STARS: too few stars, the shape is not a shape fault."""
    if len(chosen) < MIN_STARS:
        return None
    stars, doughnuts = [], 0
    for i in chosen:
        window = _window(images, objects[i], noise)
        if window is None:
            doughnuts += 1
            continue
        star = _fitted(window)
        if star is not None:
            stars.append(star)
    if doughnuts > len(chosen) / 2:
        return Shape(ShapeKind.UNMEASURABLE, len(chosen), None, None, None)
    if len(stars) >= max(MIN_STARS, FIT_SHARE * len(chosen)):
        return _frame(ShapeKind.FITTED, stars)
    return _frame(ShapeKind.ESTIMATED, [_moments(objects[i]) for i in chosen])


def _frame(kind: ShapeKind, stars: list[Star]) -> Shape:
    eccentricity = float(np.median([s.eccentricity for s in stars]))
    if eccentricity >= UNMEASURABLE_ECCENTRICITY:
        return Shape(ShapeKind.UNMEASURABLE, len(stars), None, None, None)
    fwhm = float(np.median([s.fwhm_px for s in stars]))
    angle = None
    if eccentricity >= DIRECTION_ECCENTRICITY:
        angle = _direction([s.angle_deg for s in stars])
    return Shape(kind, len(stars), fwhm, eccentricity, angle)


def _direction(angles: list[float]) -> float | None:
    """Axial mean: angles doubled on the circle, so 179 and 1 agree [D Mardia 1972, axial data]."""
    mean = np.mean(np.exp(2j * np.radians(angles)))
    if abs(mean) < DIRECTION_AGREEMENT:
        return None
    return _folded(float(np.degrees(np.angle(mean))) / 2)


def _folded(degrees: float) -> float:
    """Into [0, 180): -1e-15 % 180 rounds to 180.0, which the schema refuses."""
    folded = degrees % 180
    return 0.0 if folded >= 180 else folded


def estimated_fwhm(objects: np.ndarray) -> np.ndarray:
    """FWHM guessed from sep's second moments: windows, edges, neighbours, apertures."""
    return SIGMA_TO_FWHM * np.sqrt(np.maximum(objects["a"] * objects["b"], 0.25))


def _moments(star: Record) -> Star:
    """sep's second moments of the detection, on the median copy: the fallback (ADR 0022)."""
    a, b = float(star["a"]), float(star["b"])
    return Star(
        _guess(star),
        math.sqrt(max(0.0, 1 - (b / a) ** 2)) if a > 0 else 0.0,
        _folded(math.degrees(float(star["theta"]))),
    )


def _guess(star: Record) -> float:
    return float(estimated_fwhm(star))  # pyright: ignore[reportArgumentType]


def _window(images: tuple[np.ndarray, np.ndarray], star: Record, noise: float) -> Window | None:
    """The star's circle less the ring's median sky, hot pixels masked off the core; None when
    it is a doughnut. A free sky in the fit ate the wings: FWHM +4% at beta 2.5. [T]"""
    residual, filtered = images
    x, y, guess = float(star["x"]), float(star["y"]), _guess(star)
    radius = max(WINDOW_MIN_PX, WINDOW_FWHM * guess)
    rows, cols, reach = *residual.shape, radius * RING_OUTER
    y0, y1 = max(0, int(y - reach)), min(rows, int(y + reach) + 2)
    x0, x1 = max(0, int(x - reach)), min(cols, int(x + reach) + 2)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    distance = np.hypot(xs - x, ys - y)
    smooth = filtered[y0:y1, x0:x1]
    sky = float(np.median(smooth[(distance >= radius) & (distance < reach)]))
    values = residual[y0:y1, x0:x1].astype(np.float64) - sky
    if _doughnut(values, distance, guess, noise):
        return None
    hot = (values + sky - smooth > HOT_SIGMA * noise) & (distance > guess / 2)
    use = (distance <= radius) & ~hot
    peak = max(float(values[use].max()), noise)
    alpha = math.log(guess / (2 * math.sqrt(2 ** (1 / START_BETA) - 1)))
    shape = _logit((START_BETA - BETA_MIN) / (BETA_MAX - BETA_MIN))
    start = np.array([x, y, 1.0, alpha, alpha, float(star["theta"]), shape])
    return Window(xs[use].astype(np.float64), ys[use].astype(np.float64), values[use] / peak,
                  start, _offsets(guess))  # fmt: skip


def _doughnut(values: np.ndarray, distance: np.ndarray, guess: float, noise: float) -> bool:
    """Centre darker than the ring around it; the inner disc holds the centre pixel at least."""
    inner = max(1.0, guess / 4)
    centre = values[distance < inner]
    ring = values[(distance >= inner) & (distance < max(2.0, guess / 2))]
    if len(centre) == 0 or len(ring) == 0:
        return False
    margin = DOUGHNUT_SIGMA * noise / math.sqrt(len(centre))
    return float(centre.mean()) < float(ring.mean()) - margin


def _offsets(guess: float) -> np.ndarray:
    """Samples per pixel side on sep's guess, about 1.6 times the true FWHM: 5 under 3, 3 under
    6, else 1. One sample at FWHM 2.8 px read it 4% wide. [T] measured on synthetic stars."""
    side = 5 if guess < 3 else 3 if guess < 6 else 1
    steps = (np.arange(side) + 0.5) / side - 0.5
    dy, dx = np.meshgrid(steps, steps, indexing="ij")
    return np.stack([dx.ravel(), dy.ravel()])


def _logit(share: float) -> float:
    return math.log(share / (1 - share))


def _beta(s: float) -> tuple[float, float]:
    """Beta and its derivative in the fitted parameter: a logistic between the two bounds."""
    share = 1 / (1 + math.exp(-s)) if s >= 0 else math.exp(s) / (1 + math.exp(s))  # no overflow
    return BETA_MIN + (BETA_MAX - BETA_MIN) * share, (BETA_MAX - BETA_MIN) * share * (1 - share)


class _Moffat:
    """A (1 + (x'/ax)^2 + (y'/ay)^2)^-beta averaged on each pixel's samples, analytic Jacobian
    (MINPACK lmder). Parameters: x0, y0, A, ln ax, ln ay, theta, s; beta = _beta(s)."""

    def __init__(self, window: Window) -> None:
        self.window = window
        self._at: bytes = b""
        self._model = np.empty(0)
        self._jac = np.empty((0, 7))

    def residuals(self, p: np.ndarray) -> np.ndarray:
        self._evaluate(p)
        return self._model - self.window.values

    def jacobian(self, p: np.ndarray) -> np.ndarray:
        self._evaluate(p)
        return self._jac

    def _evaluate(self, p: np.ndarray) -> None:
        if p.tobytes() == self._at:
            return
        w = self.window
        x0, y0, amp, log_ax, log_ay, theta, s = p
        beta, beta_slope = _beta(s)
        ax2, ay2 = math.exp(2 * log_ax), math.exp(2 * log_ay)
        c, n = math.cos(theta), math.sin(theta)
        dx = w.xs[:, None] + w.offsets[0][None, :] - x0
        dy = w.ys[:, None] + w.offsets[1][None, :] - y0
        u, v = c * dx + n * dy, -n * dx + c * dy
        base = 1 + u * u / ax2 + v * v / ay2
        g = base**-beta
        dg = -beta * g / base  # d g / d q
        jac = np.empty((len(w.values), 7))
        jac[:, 0] = amp * np.mean(dg * (-2 * c * u / ax2 + 2 * n * v / ay2), axis=1)
        jac[:, 1] = amp * np.mean(dg * (-2 * n * u / ax2 - 2 * c * v / ay2), axis=1)
        jac[:, 2] = np.mean(g, axis=1)
        jac[:, 3] = amp * np.mean(dg * (-2 * u * u / ax2), axis=1)
        jac[:, 4] = amp * np.mean(dg * (-2 * v * v / ay2), axis=1)
        jac[:, 5] = amp * np.mean(dg * 2 * u * v * (1 / ax2 - 1 / ay2), axis=1)
        jac[:, 6] = amp * np.mean(-np.log(base) * g, axis=1) * beta_slope
        self._model = amp * jac[:, 2]
        self._jac = jac
        self._at = p.tobytes()


def _fitted(window: Window) -> Star | None:
    """None when the fit fails: no convergence, a value not finite, a centre that wandered."""
    model = _Moffat(window)
    budget = EVALUATIONS_PER_PARAMETER * (len(window.start) + 1)
    try:
        with np.errstate(divide="raise", over="raise", invalid="raise", under="ignore"):
            fit = least_squares(model.residuals, window.start,
                                jac=model.jacobian,  # pyright: ignore[reportArgumentType] -- stub types jac as str only
                                method="lm", x_scale="jac", max_nfev=budget)  # fmt: skip
    except (ValueError, ArithmeticError):  # axes or beta pushed off any star: a failed fit
        return None
    x0, y0, amp, log_ax, log_ay, theta, s = fit.x
    moved = math.hypot(x0 - window.start[0], y0 - window.start[1])
    lost = moved > math.exp(window.start[3]) or not np.all(np.isfinite(fit.x))
    if fit.status <= 0 or lost or amp <= 0:
        return None
    return _star(log_ax, log_ay, theta, _beta(s)[0])


def _star(log_ax: float, log_ay: float, theta: float, beta: float) -> Star:
    """FWHM 2 a sqrt(2^(1/beta) - 1), a the axes' geometric mean [C PCL PSFFit.h; software-ok];
    the long axis named, so b <= a."""
    long_axis, short_axis = (log_ax, log_ay) if log_ax >= log_ay else (log_ay, log_ax)
    angle = math.degrees(theta) + (0 if log_ax >= log_ay else 90)
    fwhm = 2 * math.exp((log_ax + log_ay) / 2) * math.sqrt(2 ** (1 / beta) - 1)
    eccentricity = math.sqrt(1 - math.exp(2 * (short_axis - long_axis)))
    return Star(fwhm, eccentricity, _folded(angle))
