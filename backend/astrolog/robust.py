"""Robust statistics: Qn and its relative bounds between frames (ADR 0039); biweight and robust
Chauvenet as Image Analysis aggregates stars. Pixel noise: units.sigma_from_mad. software-ok"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

# 1/(sqrt 2 Phi^-1(5/8)), 6 digits; 2.2219 of the first papers is a typo (robustbase Qn.Rd)
# [C Rousseeuw & Croux, JASA 88:1273, 1993, p. 1277 after (3.7)]
QN_CONSTANT = 2.21914
# Small-sample factors for n = 2..12, the ones that go with 2.21914; n = 2 is sqrt(pi)/2/2.21914
# [C robustbase 0.99-7 R/qnsn.R, Maechler's simulation, Nsim 2^27]
SMALL_SAMPLE = (
    0.399356, 0.99365, 0.51321, 0.84401, 0.61220,
    0.85877, 0.66993, 0.87344, 0.72014, 0.88906, 0.75743,
)  # fmt: skip
# Over 12, 1/(1 + p(1/n)/n) [C robustbase 0.99-7 R/qnsn.R, Qn.finite.c]
ODD_TERMS = (1.60188, -2.1284, -5.172)
EVEN_TERMS = (3.67561, 1.9654, 6.987, -77.0)  # [C robustbase 0.99-7 R/qnsn.R, Qn.finite.c]
RELATIVE_QN = 2.5  # [D Leys et al. 2013, J. Exp. Soc. Psychol. 49:764; ADR 0039 with Qn]
MIN_VALUES = 10  # [P ADR 0032: at least 10 frames, under that the relative bound is silent]
WINDOW_PER_VALUE = 8  # [T] pairs left per value when the bisection stops and picks among them
# Biweight: values over 6 MAD from the centre weigh nothing, at most 20 steps.
BIWEIGHT_C = 6.0  # [C PixInsight ImageAnalysis par. 2.2, Robust Statistics; software-ok]
BIWEIGHT_ITERATIONS = 20  # [C PixInsight ImageAnalysis par. 2.2, Robust Statistics; software-ok]
BIWEIGHT_TOLERANCE = 1e-10  # [C PixInsight ImageAnalysis par. 2.2, eq. 110; software-ok]
# Robust Chauvenet, two-sided: median and 68.3-percentile deviation, then mean and standard
# deviation; a value goes when N P(>|z|) < 0.5. [C Maples et al. 2018, ApJS 238:2, par. 2-4]
CHAUVENET_EXPECTED = 0.5  # [C Maples et al. 2018, eq. 1: Chauvenet's criterion]
DEVIATION_PERCENTILE = 0.683  # [C Maples et al. 2018, par. 2.2: technique 1]
# Correction factors (1 - a N^-b)^-1: Median-Technique 1, then Mean-Standard Deviation.
MEDIAN_CORRECTION = (1.7198, 1.022)  # [C Maples et al. 2018, Table 3, N > 100]
MEAN_CORRECTION = (0.7240, 0.773)  # [C Maples et al. 2018, Table 3, N > 100]
# Under this many values nothing is rejected: the factors run away (N = 2: 6.5).
CHAUVENET_MIN = 3  # [C Maples et al. 2018, par. 2: at least two distinct values stay]


@dataclass(frozen=True)
class Bounds:
    median: float
    qn: float
    low: float
    high: float


def small_sample_factor(n: int) -> float:
    """c_n of robustbase, so that Qn of a normal sample is sigma on average at every n."""
    if n <= len(SMALL_SAMPLE) + 1:
        return SMALL_SAMPLE[n - 2]
    terms = ODD_TERMS if n % 2 else EVEN_TERMS
    poly = 0.0
    for term in reversed(terms):
        poly = term + poly / n
    return 1 / (1 + poly / n)


def _pair_spans(x: np.ndarray, gap: float) -> tuple[np.ndarray, np.ndarray]:
    """Per value of the sorted x, where its pairs with a difference up to `gap` start and end."""
    first = np.arange(1, len(x))
    ends = np.searchsorted(x, x[:-1] + gap, side="right")
    return first, np.maximum(ends, first)


def _count(x: np.ndarray, gap: float) -> int:
    first, ends = _pair_spans(x, gap)
    return int((ends - first).sum())


def _pick(x: np.ndarray, low: float, high: float, rank: int) -> float:
    """The rank-th smallest difference among the pairs over `low` and up to `high`."""
    _, starts = _pair_spans(x, low)
    _, ends = _pair_spans(x, high)
    lengths = ends - starts
    left = np.repeat(np.arange(len(x) - 1), lengths)
    offsets = np.arange(int(lengths.sum())) - np.repeat(np.cumsum(lengths) - lengths, lengths)
    gaps = x[np.repeat(starts, lengths) + offsets] - x[left]
    return float(np.partition(gaps, rank - 1)[rank - 1])


def _kth_gap(x: np.ndarray, k: int) -> float:
    """k-th smallest |x_i - x_j| without the n^2 matrix: bisection on the value, then a pick."""
    if _count(x, 0.0) >= k:
        return 0.0
    low, high = 0.0, float(x[-1] - x[0])
    while _count(x, high) < k:  # x[0] + span can round below x[-1], the widest pair uncounted
        high *= 2
    below = _count(x, low)
    while True:
        middle = (low + high) / 2
        if _count(x, high) - below <= WINDOW_PER_VALUE * len(x) or middle in (low, high):
            return _pick(x, low, high, k - below)
        at_middle = _count(x, middle)
        if at_middle >= k:
            high = middle
        else:
            low, below = middle, at_middle


def qn(values: Sequence[float] | np.ndarray) -> float | None:
    """Qn = d c_n {|x_i - x_j|; i < j}_(k), k = C(h, 2), h = n // 2 + 1; None under two values."""
    n = len(values)
    if n < 2:
        return None
    x = np.sort(np.asarray(values, dtype=float))
    h = n // 2 + 1
    return QN_CONSTANT * small_sample_factor(n) * _kth_gap(x, math.comb(h, 2))


def biweight_location(values: Sequence[float] | np.ndarray) -> float | None:
    """Tukey's biweight from the median, weights (1 - u^2)^2 with u the distance over BIWEIGHT_C
    MADs, until it moves less than BIWEIGHT_TOLERANCE MAD or BIWEIGHT_ITERATIONS; None if empty."""
    x = np.asarray(values, dtype=float)
    if len(x) == 0:
        return None
    centre = float(np.median(x))
    mad = float(np.median(np.abs(x - centre)))
    if mad == 0:
        return centre
    for _ in range(BIWEIGHT_ITERATIONS):
        u = (x - centre) / (BIWEIGHT_C * mad)
        w = np.where(np.abs(u) < 1, (1 - u * u) ** 2, 0.0)
        moved = float((w * x).sum() / w.sum())
        done = abs(moved - centre) < BIWEIGHT_TOLERANCE * mad
        centre = moved
        if done:
            break
    return centre


def robust_chauvenet(values: np.ndarray) -> np.ndarray:
    """Which values stay: one rejected per pass, the farthest, each stage until none goes; the
    factors' table for N <= 100 is not in the text, the N > 100 law serves there too."""
    x = np.asarray(values, dtype=float)
    kept = np.ones(len(x), dtype=bool)
    for centre, scale, (a, b) in (
        (np.median, _deviation_683, MEDIAN_CORRECTION),
        (np.mean, _standard_deviation, MEAN_CORRECTION),
    ):
        while (n := int(kept.sum())) > CHAUVENET_MIN:
            here = x[kept]
            mu = float(centre(here))
            sigma = scale(here - mu) / (1 - a * n**-b)
            if sigma <= 0:
                break
            z = np.where(kept, np.abs(x - mu) / sigma, -1.0)
            worst = int(np.argmax(z))
            if n * math.erfc(z[worst] / math.sqrt(2)) >= CHAUVENET_EXPECTED:
                break
            kept[worst] = False
    return kept


def _deviation_683(deviations: np.ndarray) -> float:
    ordered = np.sort(np.abs(deviations))
    return float(ordered[math.ceil(DEVIATION_PERCENTILE * len(ordered)) - 1])


def _standard_deviation(deviations: np.ndarray) -> float:
    return float(np.sqrt((deviations**2).sum() / (len(deviations) - 1)))


def winsorized(values: np.ndarray, kept: np.ndarray) -> np.ndarray:
    """Rejected values replaced with the nearest kept one (ImageWeighting par. 2.2.1)."""
    if not kept.any():
        return values.copy()
    return np.clip(values, values[kept].min(), values[kept].max())


def relative_bounds(values: Sequence[float]) -> Bounds | None:
    """Median +- 2.5 Qn (ADR 0039); None, the bound silent, under 10 values or at Qn zero (half the
    pairs tied: the bound would be the median itself)."""
    if len(values) < MIN_VALUES:
        return None
    scale = qn(values)
    if not scale:
        return None
    median = statistics.median(values)
    return Bounds(median, scale, median - RELATIVE_QN * scale, median + RELATIVE_QN * scale)
