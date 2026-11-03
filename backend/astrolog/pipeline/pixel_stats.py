"""Pixel statistics as Image Analysis (ImageAnalysis par. 2.1.2, 2.1.4; ImageWeighting par. 2.8):
median, Sigma, standardized entropy, the noise scaling factors, SNR. Pure: pixels in. software-ok"""

import math
from dataclasses import dataclass

import numpy as np

from .background import valid_pixels

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
    negative accepted."""
    flat = np.asarray(data, dtype=np.float64).ravel()
    valid = flat[valid_pixels(flat, full_scale)]
    centre = float(np.median(valid))
    sigma = _sigma(valid, centre)
    low, high = _scale(valid[valid < centre], centre), _scale(valid[valid >= centre], centre)
    return PixelStats(centre - pedestal, sigma, _entropy(valid, sigma), low, high)


def snr(scale_low: float, scale_high: float, noise: float) -> float | None:
    """ImageAnalysis eq. 16: ((sigma_L + sigma_H) / (2 sigma_n))^2; units cancel. software-ok"""
    if noise <= 0:
        return None
    return ((scale_low + scale_high) / (2 * noise)) ** 2


def _sigma(values: np.ndarray, centre: float) -> float:
    """ImageAnalysis eq. 9-10, the biweight midvariance about the median (Wilcox 2017, ch. 3)."""
    mad = float(np.median(np.abs(values - centre)))
    if mad == 0:
        return 0.0
    u2 = ((values - centre) / (BWMV_MADS * mad)) ** 2
    near = u2 < 1
    d2, w = (values[near] - centre) ** 2, 1 - u2[near]
    bwmv = values.size * float(np.sum(d2 * w**4)) / float(np.sum(w * (1 - 5 * u2[near]))) ** 2
    return BWMV_NORMAL * math.sqrt(bwmv)


def _entropy(values: np.ndarray, sigma: float) -> float:
    """ImageAnalysis eq. 11: -sum p log2 p over bins of sigma / 16, less log2 16."""
    if sigma <= 0:
        return 0.0
    bins = np.floor((values - values.min()) / (sigma / ENTROPY_BINS)).astype(np.int64)
    p = np.bincount(bins)
    p = p[p > 0] / values.size
    return float(-np.sum(p * np.log2(p))) - math.log2(ENTROPY_BINS)


def _scale(side: np.ndarray, centre: float) -> float:
    """Std of one side of the median, then twice more within 4 of it from the median."""
    if side.size < 2:
        return 0.0
    spread = float(np.std(side))
    for _ in range(SCALE_ROUNDS):
        side = side[np.abs(side - centre) <= SCALE_REJECTION * spread]
        spread = float(np.std(side))
    return spread
