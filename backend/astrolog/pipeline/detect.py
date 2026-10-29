"""Stars as the SubframeSelector finds them (plan 25.15, misure.md): from its public docs, tuned
black-box on its outputs, never on PCL sources. Pure: pixels in, positions out. software-ok"""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from .psf_flux import tenth_flux

# Structure pixels: the median copy over this many sigma.
# [C Starck and Murtagh 1998, PASP 110:193: significance at 3 sigma, as noise.py's support]
STRUCTURE_SIGMA = 3.0
# Star: best 2x2 sum on the raw residual over the noise of 4 pixels, the SubframeSelector's own
# threshold on synthetic frames of known truth, FWHM 1.5-6 px (misure.md); software-ok
APERTURE_SNR = 16.85  # [M plan 26.45: half its stars found there, median of five FWHM]
# Its threshold on the synthetic frames holds within 1.18x over FWHM 1.5-6; 1 px 1.48x, 3 px 1.64x.
APERTURE_PX = 2  # [M plan 26.45: the aperture whose threshold does not follow the FWHM]
# Saturated: one sensor pixel at the ceiling. [C ASTAP plot_star: a pixel at data_max]
CLIPPED_PIXELS = 1
_EIGHT = np.ones((3, 3), dtype=bool)  # [D 8-connected: diagonal pixels of a star join it]


@dataclass(frozen=True)
class Detections:
    x: np.ndarray  # barycentre on the median copy, columns
    y: np.ndarray  # rows
    saturated: np.ndarray  # bool: CLIPPED_PIXELS sensor pixels at the ceiling; all False unasked
    flux: np.ndarray  # as the PSF SNR sums it (psf_flux.py)


def detect(
    residual: np.ndarray,
    filtered: np.ndarray,
    noise: float,
    clip: tuple[np.ndarray, float] | None = None,
) -> Detections:
    """`residual`: frame less sky; `filtered`: its 3x3 median; `clip`: sensor pixels (colour: the
    mosaic) and their ceiling. One star per structure: touching stars count once."""
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
    saturated = np.zeros(len(x), dtype=bool)
    if clip is not None:
        sensor, top = clip
        at_top = np.bincount(owner, sensor[rows, cols] >= top, count + 1)[star]
        saturated = at_top >= CLIPPED_PIXELS
    index = np.cumsum(star) - 1  # label to star number
    mine = star[owner]
    pixels = (rows[mine], cols[mine], index[owner[mine]])
    return Detections(x, y, saturated, tenth_flux((residual, filtered), pixels, (x, y)))
