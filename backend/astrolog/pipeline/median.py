"""The exact 3x3 median the measures share (stars.py, mmt.py). Pure: an array in, one out."""

import numpy as np


def median3x3(data: np.ndarray) -> np.ndarray:
    """Exact 3x3 median, edges mirrored: vertical triples sorted once, then the median of the
    nine is med3(max of lows, med3 of mids, min of highs) (Paeth, Graphics Gems 1990)."""
    padded = np.pad(data, 1, mode="symmetric")
    a, b, c = padded[:-2], padded[1:-1], padded[2:]
    low, high = np.minimum(a, b), np.maximum(a, b)
    mid = np.maximum(low, np.minimum(high, c))
    low, high = np.minimum(low, c), np.maximum(high, c)
    lows = np.maximum(np.maximum(low[:, :-2], low[:, 1:-1]), low[:, 2:])
    highs = np.minimum(np.minimum(high[:, :-2], high[:, 1:-1]), high[:, 2:])
    mids = _med3(mid[:, :-2], mid[:, 1:-1], mid[:, 2:])
    return _med3(lows, mids, highs)


def _med3(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    return np.maximum(np.minimum(a, b), np.minimum(np.maximum(a, b), c))
