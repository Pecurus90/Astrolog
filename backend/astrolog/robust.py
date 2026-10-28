"""Robust scale between frames (ADR 0039): Qn of Rousseeuw and Croux, and the relative bounds it
gives. Noise inside a frame stays the MAD of units.sigma_from_mad, a scale over every pixel."""

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


def qn(values: Sequence[float]) -> float | None:
    """Qn = d c_n {|x_i - x_j|; i < j}_(k), k = C(h, 2), h = n // 2 + 1; None under two values."""
    n = len(values)
    if n < 2:
        return None
    x = np.sort(np.asarray(values, dtype=float))
    h = n // 2 + 1
    return QN_CONSTANT * small_sample_factor(n) * _kth_gap(x, math.comb(h, 2))


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
