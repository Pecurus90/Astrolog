"""Sky gradient and banding as Image Analysis measures them (par. 2.1.3, eq. 13-15), in units of
the noise, on the valid pixels of the whole frame. Pure: pixels in, numbers out. software-ok"""

import math
from dataclasses import dataclass

import numpy as np

from ..robust import biweight_fit
from ..units import sigma_from_mad

# Valid pixels: the open range (min + e, max - e), e this share of the full scale: no empty
# border, no saturation; one DN at 16 bit.
EDGE_SHARE = 1 / 65535  # [C ImageAnalysis par. 2.1.2: e = 1/65535 of [0, 1]; software-ok]
MAX_TILES = 16  # [C ImageAnalysis par. 2.1.3: a grid of up to 16 x 16 tiles; software-ok]
MIN_TILE_PX = 32  # [C ImageAnalysis par. 2.1.3: tiles of at least 32 x 32 pixels; software-ok]
SURFACE_SAMPLES = 257  # [T] the surface's extremes read on 257 x 257 points of [-1, 1]
# Row medians detrended by the median of the same parity's within this many rows.
BANDING_REACH = 50  # [C ImageAnalysis par. 2.1.3: within fifty rows; software-ok]
# Standard deviation of the median of n normal values, sqrt(pi / 2) sigma / sqrt(n).
MEDIAN_SE = 1.2533  # [C ImageAnalysis eq. 15; Kenney & Keeping 1962; software-ok]


@dataclass(frozen=True)
class Banding:
    row: float  # RowBanding, noise units
    column: float  # ColumnBanding


def valid_pixels(data: np.ndarray, full_scale: float) -> np.ndarray:
    """Mask of the open range (min + e, max - e); all of them when none is inside it."""
    low, high, edge = float(data.min()), float(data.max()), EDGE_SHARE * full_scale
    valid = (data > low + edge) & (data < high - edge)
    return valid if valid.any() else np.ones(data.shape, dtype=bool)


def gradient(plane: np.ndarray, valid: np.ndarray, noise: float) -> float | None:
    """Eq. 13-14: quadratic surface by Tukey's biweight on tile medians, centres over [-1, 1];
    peak-to-peak over the noise. None: noise zero, or under six tiles with valid pixels."""
    if noise <= 0:
        return None
    rows, cols = plane.shape
    edges_y = _edges(rows)
    edges_x = _edges(cols)
    us, vs, medians = [], [], []
    for y0, y1 in zip(edges_y[:-1], edges_y[1:], strict=True):
        for x0, x1 in zip(edges_x[:-1], edges_x[1:], strict=True):
            here = plane[y0:y1, x0:x1][valid[y0:y1, x0:x1]]
            if here.size:
                us.append((x0 + x1) / cols - 1)
                vs.append((y0 + y1) / rows - 1)
                medians.append(float(np.median(here)))
    u, v = np.array(us), np.array(vs)
    if len(medians) < 6:  # six coefficients: not measured, not flat
        return None
    c = biweight_fit(
        np.column_stack([np.ones_like(u), u, v, u * u, u * v, v * v]), np.array(medians)
    )
    q = np.linspace(-1, 1, SURFACE_SAMPLES)
    v, u = np.meshgrid(q, q, indexing="ij")
    surface = c[1] * u + c[2] * v + c[3] * u * u + c[4] * u * v + c[5] * v * v
    return float(surface.max() - surface.min()) / noise


def _edges(side: int) -> np.ndarray:
    tiles = max(1, min(MAX_TILES, side // MIN_TILE_PX))
    return np.linspace(0, side, tiles + 1).round().astype(int)


def banding(plane: np.ndarray, valid: np.ndarray, noise: float) -> Banding | None:
    """Eq. 15 on the rows, then the columns. None: noise zero."""
    if noise <= 0:
        return None
    return Banding(_excess(plane, valid, noise), _excess(plane.T, valid.T, noise))


def _excess(plane: np.ndarray, valid: np.ndarray, noise: float) -> float:
    """Each row's valid median less the median of its parity's within BANDING_REACH rows; their
    MAD as sigma less what the noise gives a median of n, n the mean valid pixels a row."""
    counts = valid.sum(axis=1)
    medians = np.array([np.median(r[k]) if n else np.nan
                        for r, k, n in zip(plane, valid, counts, strict=True)])  # fmt: skip
    left = []
    for i, m in enumerate(medians):
        if np.isnan(m):
            continue
        near = medians[max(0, i - BANDING_REACH) + (max(0, i - BANDING_REACH) - i) % 2 :
                       i + BANDING_REACH + 1 : 2]  # fmt: skip
        left.append(m - float(np.nanmedian(near)))
    left_a = np.array(left)
    s = sigma_from_mad(float(np.median(np.abs(left_a - np.median(left_a)))))
    expected = MEDIAN_SE * noise / math.sqrt(float(counts[counts > 0].mean()))
    return math.sqrt(max(0.0, s * s - expected * expected)) / noise
