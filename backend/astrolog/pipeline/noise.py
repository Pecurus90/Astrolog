"""The frame's noise by the multiresolution support (Starck & Murtagh 1998, PASP 110:193; as
PixInsight ImageWeighting par. 2.4, 3.1.2: software-ok). Pure: pixels in, a sigma out."""

from collections.abc import Callable

import numpy as np

from ..units import sigma_from_mad

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
    planes, smooth = [], np.asarray(image, dtype=np.float32)
    for j in range(layers):
        coarser = _smoother(smooth, j)
        planes.append(smooth - coarser)
        smooth = coarser
    return planes, smooth


def _smoother(smooth: np.ndarray, j: int) -> np.ndarray:
    return _taps(_taps(smooth, 2**j, 0), 2**j, 1)


def _taps(image: np.ndarray, step: int, axis: int) -> np.ndarray:
    """B3 along one axis, its five taps `step` apart: the zeros between them never multiplied.
    Borders mirrored without repeating the edge, as ndimage's mirror."""
    reach, size = 2 * step, image.shape[axis]
    padded = np.pad(image, [(reach, reach) if a == axis else (0, 0) for a in (0, 1)], "reflect")

    def shifted(offset: int) -> np.ndarray:
        window = [slice(None), slice(None)]
        window[axis] = slice(reach + offset, reach + offset + size)
        return padded[tuple(window)]

    out = shifted(-reach) + shifted(reach)
    out *= np.float32(B3[0])
    out += (shifted(-step) + shifted(step)) * np.float32(B3[1])
    out += shifted(0) * np.float32(B3[2])
    return out


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
    centre = float(np.median(layer))
    start = sigma_from_mad(float(np.median(np.abs(layer - centre))))
    away = np.abs(layer - centre)
    return _fixed_point(start, lambda sigma: layer[away < K_SIGMA * sigma]) / MEDIAN_LAYER2_GAIN


def _fixed_point(sigma: float, quiet_of: Callable[[float], np.ndarray]) -> float:
    """Std of the pixels quiet at k sigma, again on the new sigma, until it settles."""
    for _ in range(MAX_ROUNDS):
        quiet = quiet_of(sigma)
        if quiet.size < 2:
            break
        new = float(np.std(quiet))
        settled = abs(new - sigma) <= TOLERANCE * new
        sigma = new
        if settled:
            break
    return sigma


def mrs_noise(image: np.ndarray) -> float:
    """Sigma of I - c_p over the pixels in no layer's support (|w_j| >= k sigma sigma_j), iterated
    to a fixed point, over 0.974. The start, which the paper leaves open: the first layer's MAD."""
    planes, smooth = starlet(image, LAYERS)
    first = planes[0]
    sigma = sigma_from_mad(float(np.median(np.abs(first - np.median(first))))) / UNIT_SIGMAS[0]
    strongest = np.abs(planes.pop(0)) / UNIT_SIGMAS[0]  # layer by layer: one plane at a time
    for unit in UNIT_SIGMAS[1:]:
        np.maximum(strongest, np.abs(planes.pop(0)) / unit, out=strongest)
    detail = np.asarray(image, dtype=np.float32) - smooth
    del smooth
    return _fixed_point(sigma, lambda s: detail[strongest < K_SIGMA * s]) / BIAS
