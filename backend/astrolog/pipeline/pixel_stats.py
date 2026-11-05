"""Pixel statistics as Image Analysis (ImageAnalysis par. 2.1.2, 2.1.4; ImageWeighting par. 2.8):
median, Sigma, standardized entropy, the noise scaling factors, SNR. Pure: pixels in. software-ok"""

import math
from dataclasses import dataclass

import numpy as np

from .background import EDGE_SHARE
from .cores import MIN_PARALLEL_VALUES, compiled, in_parts, median, middle, side_by_side

BWMV_MADS = 9.0  # [C ImageAnalysis eq. 10: u = (v - M) / (9 MAD); software-ok]
BWMV_NORMAL = 0.990905  # [C ImageAnalysis eq. 9: sqrt BWMV consistent with a normal; software-ok]
ENTROPY_BINS = 16  # [C ImageAnalysis eq. 11: bins of Sigma / 16; software-ok]
SCALE_REJECTION = 4.0  # [C ImageAnalysis par. 2.1.4: farther than four times; software-ok]
SCALE_ROUNDS = 2  # [C ImageAnalysis par. 2.1.4: computed again twice; software-ok]


@dataclass(frozen=True)
class PixelStats:
    median_adu: float  # less the pedestal (ImageAnalysis Median)
    sigma_adu: float  # 0.990905 sqrt BWMV (Sigma)
    entropy_bits: float  # standardized Shannon entropy (Entropy)
    scale_low_adu: float  # spread under the median (PCL:Noise:ScaleLow)
    scale_high_adu: float  # over it (PCL:Noise:ScaleHigh)


def pixel_stats(data: np.ndarray, *, full_scale: float, pedestal: float = 0.0) -> PixelStats:
    """`full_scale`: what [0, 1] maps to (the ceiling, ADR 0041). `pedestal`: PEDESTAL, DN,
    negative accepted. Every value read as float64; float32 kept, not copied (cores.compiled)."""
    flat = np.asarray(data).ravel()
    if flat.dtype != np.float32:
        flat = flat.astype(np.float64)
    valid = _valid(flat, full_scale)
    low, high = middle(valid)
    centre = low if valid.size % 2 else (low + high) / 2
    sigma, low, high = side_by_side(lambda: _sigma(valid, centre),
                                    lambda: _scale(valid, centre, upper=False),
                                    lambda: _scale(valid, centre, upper=True))  # fmt: skip
    return PixelStats(centre - pedestal, sigma, _entropy(valid, sigma), low, high)


def snr(scale_low: float, scale_high: float, noise: float) -> float | None:
    """ImageAnalysis eq. 16: ((sigma_L + sigma_H) / (2 sigma_n))^2; units cancel. software-ok"""
    if noise <= 0:
        return None
    return ((scale_low + scale_high) / (2 * noise)) ** 2


def _valid(flat: np.ndarray, full_scale: float) -> np.ndarray:
    """background.valid_pixels compared in float64: the open range (min + e, max - e)."""
    low, high, edge = float(flat.min()), float(flat.max()), EDGE_SHARE * full_scale
    inside = np.empty(flat.size, dtype=np.bool_)
    in_parts(lambda a, b: _inside(flat, (a, b), low + edge, high - edge, inside), flat.size)
    return flat[inside] if inside.any() else flat


def _sigma(values: np.ndarray, centre: float) -> float:
    """ImageAnalysis eq. 9-10, the biweight midvariance about the median (Wilcox 2017, ch. 3)."""
    away = np.empty(values.size)
    in_parts(lambda a, b: _away(values, (a, b), centre, away), values.size)
    mad = median(away)
    if mad == 0:
        return 0.0
    sums = in_parts(lambda a, b: _biweight(values, (a, b), centre, BWMV_MADS * mad), values.size)
    above, below = (math.fsum(s[k] for s in sums) for k in (0, 1))
    return BWMV_NORMAL * math.sqrt(values.size * above / below**2)


def _entropy(values: np.ndarray, sigma: float) -> float:
    """ImageAnalysis eq. 11: -sum p log2 p over bins of sigma / 16, less log2 16."""
    if sigma <= 0:
        return 0.0
    start, width = float(values.min()), sigma / ENTROPY_BINS
    bins = math.floor((float(values.max()) - start) / width) + 1
    least = max(MIN_PARALLEL_VALUES, bins)  # counters never past one per value, as bincount's
    p = np.sum(in_parts(lambda a, b: _histogram(values, (a, b), start, width, bins), values.size,
                        least=least), axis=0)  # fmt: skip
    p = p[p > 0] / values.size
    return float(-np.sum(p * np.log2(p))) - math.log2(ENTROPY_BINS)


def _scale(values: np.ndarray, centre: float, *, upper: bool) -> float:
    """Std of one side of the median, the median itself on neither (his SNR within 1e-4, sonde
    26.5), then twice more within 4 of it from the median."""
    spread, count = _side_std(values, centre, upper, math.inf)
    if count < 2:
        return 0.0
    reach = math.inf  # each round within the earlier rounds' too
    for _ in range(SCALE_ROUNDS):
        reach = min(reach, SCALE_REJECTION * spread)
        spread, count = _side_std(values, centre, upper, reach)
        if count == 0:
            break  # NaN, as np.std of none
    return spread


def _side_std(values: np.ndarray, centre: float, upper: bool, reach: float) -> tuple[float, int]:
    """np.std of the side's values within `reach` of the centre, two passes; NaN when none."""
    sums = in_parts(lambda a, b: _side(values, (a, b), (centre, reach), upper, 0.0), values.size)
    count = sum(int(s[0]) for s in sums)
    if count == 0:
        return math.nan, 0
    mean = math.fsum(s[1] for s in sums) / count
    sums = in_parts(lambda a, b: _side(values, (a, b), (centre, reach), upper, mean), values.size)
    return math.sqrt(math.fsum(s[2] for s in sums) / count), count


@compiled
def _inside(flat: np.ndarray, span: tuple[int, int], low: float, high: float,
            out: np.ndarray) -> None:  # fmt: skip
    for i in range(*span):
        v = float(flat[i])
        out[i] = low < v < high


@compiled
def _away(values: np.ndarray, span: tuple[int, int], centre: float, out: np.ndarray) -> None:
    for i in range(*span):
        out[i] = abs(float(values[i]) - centre)


@compiled
def _biweight(values: np.ndarray, span: tuple[int, int], centre: float,
              reach: float) -> tuple[float, float]:  # fmt: skip
    above, below = 0.0, 0.0
    for i in range(*span):
        d = float(values[i]) - centre
        u2 = (d / reach) ** 2
        if u2 < 1:
            w = 1 - u2
            above += d**2 * w**4
            below += w * (1 - 5 * u2)
    return above, below


@compiled
def _histogram(values: np.ndarray, span: tuple[int, int], low: float, width: float,
               bins: int) -> np.ndarray:  # fmt: skip
    counts = np.zeros(bins, dtype=np.int64)
    for i in range(*span):
        counts[int(np.floor((float(values[i]) - low) / width))] += 1
    return counts


@compiled
def _side(values: np.ndarray, span: tuple[int, int], around: tuple[float, float], upper: bool,
          mean: float) -> tuple[int, float, float]:  # fmt: skip
    centre, reach = around
    count, total, squares = 0, 0.0, 0.0
    for i in range(*span):
        v = float(values[i])
        if v != centre and (v > centre) == upper and abs(v - centre) <= reach:
            count += 1
            total += v
            squares += (v - mean) ** 2
    return count, total, squares
