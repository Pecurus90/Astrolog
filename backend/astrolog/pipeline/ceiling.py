"""The saturation ceiling from the histogram (ADR 0022 point 7): a clipped sensor piles its
brightest pixels on one value, maybe under the declared top. Pure: pixels in, a value out."""

import numpy as np

# Piles looked for in the top of the histogram: a clip sits over the sky, a few stars' cores. [T]
TOP_SHARE = 0.999
# Their neighbours from a wider top: values just under a pile, never cut off at its edge. [T]
NEIGHBOUR_SHARE = 0.99
# A pile: at least this many pixels on one value... [T] a clipped core of 2x2; 24 copies: 64-4050
SPIKE_MIN = 4
# ...and this many times the typical count of the values just under it. [T] 24 copies: piles
# 100-4000 times their neighbours (1-4 pixels a value), a nebula's values about 1 time.
SPIKE_RATIO = 10.0
# "Just under": this many values present below, whatever the step (8 bits, 12 in 16). [T]
NEIGHBOURS = 8
# Values this close are one pile: Canon 700D clips at 61208 and 61212. [M misure.md]
SAME_PILE = 0.001


def ceiling_of(sensor: np.ndarray, declared: float) -> float:
    """The lowest value of the highest pile at the top; no pile: `declared` (DATAMAX or the type's
    top). Never over `declared`. A frame divided by a flat has no pile: the declared one stays."""
    flat = sensor.ravel()
    last = flat.size - 1
    start, wide = min(int(TOP_SHARE * flat.size), last), min(int(NEIGHBOUR_SHARE * flat.size), last)
    cut, floor = (float(v) for v in np.partition(flat, (wide, start))[[start, wide]])
    values, counts = np.unique(flat[flat >= floor], return_counts=True)
    wanted = np.flatnonzero((counts >= SPIKE_MIN) & (values >= cut) & (values > 0))
    piles = [i for i in wanted.tolist() if _is_pile(values, counts, i)]
    if not piles:
        return float(declared)
    top = values[piles[-1]]
    lowest = min(values[i] for i in piles if values[i] >= top * (1 - SAME_PILE))
    return float(min(lowest, declared))


def _is_pile(values: np.ndarray, counts: np.ndarray, i: int) -> bool:
    high = int(np.searchsorted(values, values[i] * (1 - SAME_PILE), side="left"))
    under = counts[max(0, high - NEIGHBOURS) : high]
    typical = float(np.median(under)) if len(under) else 1.0
    return bool(counts[i] >= SPIKE_RATIO * typical)
