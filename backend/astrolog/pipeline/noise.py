"""The frame's noise by the multiresolution support (Starck & Murtagh 1998, PASP 110:193; as
PixInsight ImageWeighting par. 2.4, 3.1.2: software-ok). Pure: pixels in, a sigma out."""

import math
from dataclasses import dataclass

import numpy as np

from ..units import sigma_from_mad
from .cores import MIN_STRIP_ROWS, compiled, in_parts, inlined, median

B3 = np.array([1, 4, 6, 4, 1]) / 16  # [C Starck & Murtagh, starlet B3 spline kernel]
LAYERS = 4  # [C PixInsight ImageWeighting par. 3.1.2: the first four wavelet layers; software-ok]
K_SIGMA = 3.0  # [C Starck & Murtagh 1998 par. 2.2: k "often" 3]
BIAS = 0.974  # [C Starck & Murtagh 1998 par. 3: sigma divided by 0.974]
TOLERANCE = 1e-4  # [T] relative change that stops the iteration; the paper gives none
MAX_ROUNDS = 20  # [T] a frame that has not converged by then keeps the last sigma
# Noise never under one ADU step's own: a quantized sky has MAD 0, and then every step is a star.
# [D uniform quantization noise, step/sqrt(12)]
NOISE_FLOOR_ADU = 0.2887


def starlet(image: np.ndarray, layers: int) -> tuple[list[np.ndarray], np.ndarray]:
    """A trous B3 transform, borders mirrored: w_j = c_{j-1} - c_j, the kernel's taps 2^j apart."""
    planes, smooth = [], np.ascontiguousarray(image, dtype=np.float32)
    for j in range(layers):
        coarser, plane = _smoother(smooth, 2**j)
        planes.append(plane)
        smooth = coarser
    return planes, smooth


def _smoother(smooth: np.ndarray, step: int) -> tuple[np.ndarray, np.ndarray]:
    """B3 down the columns, then along the rows; and smooth less it, the layer."""
    across, coarser, plane = (np.empty_like(smooth) for _ in range(3))
    rows = smooth.shape[0]
    in_parts(lambda a, b: _down(smooth, step, (a, b), across, TAPS), rows, least=MIN_STRIP_ROWS)
    in_parts(lambda a, b: _along(across, step, (a, b), (smooth, coarser, plane), TAPS), rows,
             least=MIN_STRIP_ROWS)  # fmt: skip
    return coarser, plane


# B3's three distinct taps in float32: the sums as numpy's on float32 planes, to the bit.
TAPS = (np.float32(B3[0]), np.float32(B3[1]), np.float32(B3[2]))  # [C Starck & Murtagh, B3]


@inlined
def _mirror(i: int, size: int) -> int:
    """Index reflected without repeating the edge (numpy pad 'reflect', ndimage 'mirror')."""
    if size == 1:
        return 0
    while i < 0 or i >= size:
        i = -i if i < 0 else 2 * (size - 1) - i
    return i


@compiled
def _down(image: np.ndarray, step: int, span: tuple[int, int], out: np.ndarray,
          taps: tuple[np.float32, np.float32, np.float32]) -> None:  # fmt: skip
    """B3 along axis 0 on the rows of `span`, its five taps `step` apart."""
    rows, cols = image.shape
    for r in range(*span):
        r0, r1 = _mirror(r - 2 * step, rows), _mirror(r - step, rows)
        r3, r4 = _mirror(r + step, rows), _mirror(r + 2 * step, rows)
        for c in range(cols):
            value = (image[r0, c] + image[r4, c]) * taps[0]
            value += (image[r1, c] + image[r3, c]) * taps[1]
            out[r, c] = value + image[r, c] * taps[2]


@compiled
def _along(image: np.ndarray, step: int, span: tuple[int, int],
           out: tuple[np.ndarray, np.ndarray, np.ndarray],
           taps: tuple[np.float32, np.float32, np.float32]) -> None:  # fmt: skip
    """B3 along axis 1 on the rows of `span` into out[1]; out[0] less it into out[2]."""
    smooth, coarser, plane = out
    cols = image.shape[1]
    for r in range(*span):
        for c in range(cols):
            c0, c1 = _mirror(c - 2 * step, cols), _mirror(c - step, cols)
            c3, c4 = _mirror(c + step, cols), _mirror(c + 2 * step, cols)
            value = (image[r, c0] + image[r, c4]) * taps[0]
            value += (image[r, c1] + image[r, c3]) * taps[1]
            value = value + image[r, c] * taps[2]
            coarser[r, c] = value
            plane[r, c] = smooth[r, c] - value


def _unit_sigmas(layers: int) -> np.ndarray:
    """Each layer's sigma for unit Gaussian noise: the L2 norm of its impulse response (as Duchamp
    app-waveletNoise; 0.8908 at the first layer)."""
    side = 4 * 2**layers + 1
    impulse = np.zeros((side, side), dtype=np.float32)
    impulse[side // 2, side // 2] = 1
    planes, _ = starlet(impulse, layers)
    return np.array([float(np.sqrt(np.sum(p.astype(np.float64) ** 2))) for p in planes])


UNIT_SIGMAS = _unit_sigmas(LAYERS)


# Structure noise: the median copy's second layer, k-sigma clipped, over its spread on white noise.
# Sees noise correlated at the structures' scale (Debayer), which MRS's first layer misses.
MEDIAN_LAYER2_GAIN = 0.1492  # [M plan 26.48.2: 3x3 median of Gaussian noise, 4 x 4 MP, +-0.0001]


def structure_noise(filtered: np.ndarray) -> float:
    """The frame's sigma as the structure map sees it: `filtered` the 3x3 median copy (plan 26.48.2;
    his threshold over it and over MRS on 21 frames: misure.md, Stelle)."""
    layer = starlet(filtered, 2)[0][1].ravel()
    centre = median(layer)
    away = np.abs(layer - centre)
    start = sigma_from_mad(median(away))
    sigma, _ = _fixed_point(start, layer, away)
    return sigma / MEDIAN_LAYER2_GAIN


def _fixed_point(sigma: float, values: np.ndarray, key: np.ndarray) -> tuple[float, int]:
    """Std of the values whose key is under k sigma, again on the new sigma, until it settles;
    and how many values the last one took. Summed in float64 (np.std of float32: float32)."""
    used = 0
    flat, keys = values.ravel(), key.ravel()
    for _ in range(MAX_ROUNDS):
        under = key.dtype.type(K_SIGMA * sigma)  # compared in the key's type, as numpy's
        sums = in_parts(lambda a, b, u=under: _quiet(flat, keys, u, (a, b), math.nan), flat.size)
        count = sum(s[0] for s in sums)
        if count < 2:
            break
        mean = math.fsum(s[1] for s in sums) / count
        sums = in_parts(lambda a, b, u=under, m=mean: _quiet(flat, keys, u, (a, b), m), flat.size)
        new, used = math.sqrt(math.fsum(s[2] for s in sums) / count), count
        settled = abs(new - sigma) <= TOLERANCE * new
        sigma = new
        if settled:
            break
    return sigma, used


@compiled
def _quiet(values: np.ndarray, key: np.ndarray, under: float, span: tuple[int, int],
           mean: float) -> tuple[int, float, float]:  # fmt: skip
    """Count, sum and squares about `mean` (NaN: skipped) of the values in `span` keyed under."""
    count, total, squares = 0, 0.0, 0.0
    for i in range(*span):
        if key[i] < under:
            v = float(values[i])
            count += 1
            total += v
            if mean == mean:
                squares += (v - mean) ** 2
    return count, total, squares


@dataclass(frozen=True)
class Mrs:
    sigma: float  # the noise, ADU
    ratio: float  # share of the frame's pixels it was taken on (ImageAnalysis NoiseRatio)


def mrs(image: np.ndarray) -> Mrs:
    """Sigma of I - c_p over the pixels in no layer's support (|w_j| >= k sigma sigma_j), iterated
    to a fixed point, over 0.974. The start, which the paper leaves open: the first layer's MAD."""
    planes, smooth = starlet(image, LAYERS)
    first = planes[0]
    sigma = sigma_from_mad(median(np.abs(first - median(first)))) / UNIT_SIGMAS[0]
    strongest = np.abs(planes.pop(0)) / UNIT_SIGMAS[0]  # layer by layer: one plane at a time
    for unit in UNIT_SIGMAS[1:]:
        np.maximum(strongest, np.abs(planes.pop(0)) / unit, out=strongest)
    detail = np.asarray(image, dtype=np.float32) - smooth
    del smooth
    sigma, used = _fixed_point(sigma, detail, strongest)
    return Mrs(sigma / BIAS, used / detail.size)
