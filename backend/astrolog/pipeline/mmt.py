"""The MMT local background at 256 px and its residual R*: M* and N*. software-ok
PixInsight ImageWeighting par. 2.3-2.4, eq. 11-15; Starck, Murtagh & Fadili 2010. software-ok"""

from dataclasses import dataclass

import numpy as np

from ..robust import sn
from .cores import MIN_STRIP_ROWS, compiled, in_parts, median
from .median import median3x3

# Dyadic layers 1, 2, ..., 128 px: the residual left is the model at 256 px.
LAYERS = 8  # [C ImageWeighting par. 2.3: models at the scale of 256 pixels; software-ok]
SN_HALF_NORMAL = 2.054326  # [C ImageWeighting eq. 15, 20: 1 / 0.4867777; software-ok]


@dataclass(frozen=True)
class Background:
    mstar_adu: float  # median of R* (MStar)
    nstar_adu: float  # 2.054326 Sn(R*) (NStar)


def mstar_nstar(data: np.ndarray) -> Background | None:
    """ImageWeighting eq. 13 and 15; None when no pixel lies under the model (an empty frame)."""
    residual = background_residual(data)
    scale = sn(residual)
    if scale is None:
        return None
    return Background(median(residual), SN_HALF_NORMAL * scale)


def background_residual(data: np.ndarray) -> np.ndarray:
    """ImageWeighting eq. 12: R* = {r - x | 0 < x < r}, r the MMT residual layer."""
    image = np.ascontiguousarray(data, dtype=np.float32)
    smooth, cell = _pyramid(image)
    across = (_bilinear(image.shape[0], smooth.shape[0], cell),
              _bilinear(image.shape[1], smooth.shape[1], cell))  # fmt: skip
    parts = in_parts(lambda a, b: _under(image, smooth, across, (a, b)), image.shape[0],
                     least=MIN_STRIP_ROWS)  # fmt: skip
    return np.concatenate(parts)


def background_model(image: np.ndarray) -> np.ndarray:
    """MMT residual at 256 px, as a median pyramid: each dyadic scale a 3x3 median on the plane
    halved by 2x2 means, the last one bilinear back to full size (plan 26.51, misure.md)."""
    smooth, cell = _pyramid(image)
    return _grown(smooth, image.shape, cell)


def _pyramid(image: np.ndarray) -> tuple[np.ndarray, int]:
    """The last scale's plane and its cell, px."""
    smooth, cell = _median(image), 1
    for _ in range(LAYERS - 1):
        rows, cols = smooth.shape[0] // 2 * 2, smooth.shape[1] // 2 * 2
        if rows < 2 or cols < 2:
            break
        halved = smooth[:rows, :cols].reshape(rows // 2, 2, cols // 2, 2).mean(axis=(1, 3))
        smooth, cell = _median(halved), cell * 2
    return smooth.astype(np.float32), cell


def _bilinear(size: int, n: int, cell: int) -> tuple[np.ndarray, np.ndarray]:
    """Each full-size index's left cell and float32 weight, as _grown's."""
    at = (np.arange(size) + 0.5) / cell - 0.5
    left = np.clip(np.floor(at).astype(np.int64), 0, max(n - 2, 0))
    return left, (at - left).astype(np.float32)


@compiled
def _under(image: np.ndarray, small: np.ndarray,
           across: tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]],
           span: tuple[int, int]) -> np.ndarray:  # fmt: skip
    """R* of rows span: model - x where 0 < x < model, the model _grown's, in its order."""
    (left_r, t_r), (left_c, t_c) = across
    start, stop = span
    n_r, n_c = small.shape
    cols = image.shape[1]
    out = np.empty((stop - start) * cols, dtype=np.float32)
    line = np.empty(n_c, dtype=np.float32)
    kept = 0
    for r in range(start, stop):
        a, b = left_r[r], min(left_r[r] + 1, n_r - 1)
        for k in range(n_c):
            line[k] = small[a, k] + (small[b, k] - small[a, k]) * t_r[r]
        for c in range(cols):
            p, q = left_c[c], min(left_c[c] + 1, n_c - 1)
            model = line[p] + (line[q] - line[p]) * t_c[c]
            x = image[r, c]
            if x > 0 and x < model:
                out[kept] = model - x
                kept += 1
    return out[:kept]


def _median(plane: np.ndarray) -> np.ndarray:
    """3x3 median, the border extended odd (2 x0 - x1): a sloped sky stays a plane at the edge,
    where a mirror would bend it a coarse cell deep."""
    padded = np.pad(plane, 1, mode="reflect", reflect_type="odd")
    return median3x3(padded)[1:-1, 1:-1]


def _grown(small: np.ndarray, shape: tuple[int, ...], cell: int) -> np.ndarray:
    """Bilinear from the cells' centres, (k + 1/2) cell - 1/2; past the outer centres the slope
    goes on, so a gradient is followed to the edge."""
    out = small.astype(np.float32)
    for axis in (0, 1):
        n = small.shape[axis]
        at = (np.arange(shape[axis]) + 0.5) / cell - 0.5
        left = np.clip(np.floor(at).astype(np.int64), 0, max(n - 2, 0))
        t = (at - left).astype(np.float32)
        a, b = np.take(out, left, axis), np.take(out, np.minimum(left + 1, n - 1), axis)
        out = a + (b - a) * (t[:, None] if axis == 0 else t[None, :])
    return out
