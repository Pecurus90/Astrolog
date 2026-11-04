"""The exact 3x3 median the measures share (stars.py, mmt.py). Pure: an array in, one out."""

import numpy as np

from .cores import MIN_STRIP_ROWS, compiled, in_parts


def median3x3(data: np.ndarray) -> np.ndarray:
    """Exact 3x3 median, edges mirrored: vertical triples sorted once, then the median of the
    nine is med3(max of lows, med3 of mids, min of highs) (Paeth, Graphics Gems 1990)."""
    image = np.ascontiguousarray(data, dtype=data.dtype.newbyteorder("="))  # FITS: big-endian
    out = np.empty_like(image)
    if image.size:
        in_parts(lambda a, b: _median3x3(image, (a, b), out), image.shape[0], least=MIN_STRIP_ROWS)
    return out


@compiled
def _median3x3(image: np.ndarray, span: tuple[int, int], out: np.ndarray) -> None:
    """Rows span; the edge pixel repeated (numpy pad 'symmetric'). NaN as np.minimum's."""
    start, stop = span
    rows, cols = image.shape
    low, mid, high = np.empty((3, cols + 2), dtype=image.dtype)
    for r in range(start, stop):
        above, below = max(r - 1, 0), min(r + 1, rows - 1)
        for k in range(cols + 2):
            c = min(max(k - 1, 0), cols - 1)
            a, b, d = image[above, c], image[r, c], image[below, c]
            lo, hi = _min(a, b), _max(a, b)
            mid[k] = _max(lo, _min(hi, d))
            low[k], high[k] = _min(lo, d), _max(hi, d)
        for c in range(cols):
            lows = _max(_max(low[c], low[c + 1]), low[c + 2])
            highs = _min(_min(high[c], high[c + 1]), high[c + 2])
            out[r, c] = _med3(lows, _med3(mid[c], mid[c + 1], mid[c + 2]), highs)


@compiled
def _min(a: float, b: float) -> float:
    return a if a < b or a != a else b  # a NaN either side wins, as np.minimum


@compiled
def _max(a: float, b: float) -> float:
    return a if a > b or a != a else b


@compiled
def _med3(a: float, b: float, c: float) -> float:
    return _max(_min(a, b), _min(_max(a, b), c))
