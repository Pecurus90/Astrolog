"""Stars as the SubframeSelector finds them (plan 25.15, misure.md): from its public docs, tuned
black-box on its outputs, never on PCL sources. Pure: pixels in, positions out. software-ok"""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

# Structure pixels: the median copy over this many sigma. The SubframeSelector's structure map on
# the 24 real frames starts at 2.3-2.5; counts move under 0.2% from 2.0 to 2.4. [T]
STRUCTURE_SIGMA = 2.4
# Star: best 2x2 sum on the raw residual over the noise of 4 pixels. Tuned on the 12 even frames
# to the SubframeSelector's count; the 12 odd ones: median 1.00, 0.98 to 1.12 (misure.md). [T]
APERTURE_SNR = 17.25
# Count ratio against the frame's FWHM: correlation -0.80 at 1 px, 0.78 at 3, -0.25 at 2. [T]
APERTURE_PX = 2
_EIGHT = np.ones((3, 3), dtype=bool)  # [D 8-connected: diagonal pixels of a star join it]


@dataclass(frozen=True)
class Detections:
    x: np.ndarray  # barycentre on the median copy, columns
    y: np.ndarray  # rows


def detect(residual: np.ndarray, filtered: np.ndarray, noise: float) -> Detections:
    """`residual`: the frame less its sky; `filtered`: its 3x3 median copy (hot pixels gone);
    `noise`: the sky's sigma. One star per structure: touching stars count once."""
    found = ndimage.label(filtered > STRUCTURE_SIGMA * noise, structure=_EIGHT)
    labels, count = cast(tuple[np.ndarray, int], found)  # stubs say int | tuple
    # Structure pixels only: ndimage's per-label max and centre sweep the frame, 1.5 s at 26 MP.
    rows, cols = np.nonzero(labels)
    owner = labels[rows, cols]
    box = ndimage.uniform_filter(residual, APERTURE_PX) * APERTURE_PX  # 2x2 mean x 2 = sum / 2
    snr = np.full(count + 1, -np.inf)
    np.maximum.at(snr, owner, box[rows, cols] / noise)
    star = snr >= APERTURE_SNR
    # On the median copy: over the threshold in every pixel of a structure, so never a zero sum.
    weight = filtered[rows, cols].astype(float)
    total = np.bincount(owner, weight, count + 1)[star]
    x = np.bincount(owner, weight * cols, count + 1)[star] / total
    y = np.bincount(owner, weight * rows, count + 1)[star] / total
    return Detections(x, y)
