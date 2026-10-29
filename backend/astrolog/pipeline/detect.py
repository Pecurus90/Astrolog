"""Stars as the SubframeSelector finds them (plan 25.15, misure.md): from its public docs, tuned
black-box on its outputs, never on PCL sources. Pure: pixels in, positions out. software-ok"""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from .noise import coarse, detail_unit_sigma
from .psf_flux import tenth_flux

# Structure pixels: the median copy's first starlet layers, I - c_5, over this many of their sigma.
# [C Starck and Murtagh 1998, PASP 110:193: significance at 3 sigma, as noise.py's support]
STRUCTURE_SIGMA = 3.0
# Scales up to 2^5 = 32 px: a nebula core or a coma wider than that is no structure of a star.
STRUCTURE_LAYERS = 5  # [C StarDetector structureLayers, SubframeSelector default; software-ok]
STRUCTURE_UNIT = detail_unit_sigma(STRUCTURE_LAYERS)
# A star covers over (1 - maxDistortion) of a disc's pi / 4 of its square: his cut at b/a 0.3-0.4
# (misure.md, 14 synthetic frames) agrees; 0.6 of the square would drop b/a under 0.76.
MAX_DISTORTION = 0.6  # [C StarDetector maxDistortion, SubframeSelector default; software-ok]
MIN_COVERAGE = (1 - MAX_DISTORTION) * np.pi / 4  # [D a disc fills pi / 4 of its square]
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
    detail = filtered - coarse(filtered, STRUCTURE_LAYERS)
    found = ndimage.label(detail > STRUCTURE_SIGMA * STRUCTURE_UNIT * noise, structure=_EIGHT)
    del detail
    labels, count = cast(tuple[np.ndarray, int], found)  # stubs say int | tuple
    # Structure pixels only: ndimage's per-label max and centre sweep the frame, 1.5 s at 26 MP.
    rows, cols = np.nonzero(labels)
    owner = labels[rows, cols]
    box = ndimage.uniform_filter(residual, APERTURE_PX) * APERTURE_PX  # 2x2 mean x 2 = sum / 2
    snr = np.full(count + 1, -np.inf)
    np.maximum.at(snr, owner, box[rows, cols] / noise)
    star = (snr >= APERTURE_SNR) & (_coverage(labels, owner, count) >= MIN_COVERAGE)
    # Barycentre on the median copy's light: on a dark residual a structure pixel can sit at or
    # under zero, and a structure with none above has no position.
    weight = np.maximum(filtered[rows, cols].astype(float), 0.0)
    star &= np.bincount(owner, weight, count + 1) > 0
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


def _coverage(labels: np.ndarray, owner: np.ndarray, count: int) -> np.ndarray:
    """Each structure's pixels over its circumscribed square, the bounding box's longer side."""
    area = np.bincount(owner, minlength=count + 1).astype(float)
    side = np.ones(count + 1)
    for i, box in enumerate(ndimage.find_objects(labels), start=1):
        if box is not None:
            side[i] = max(box[0].stop - box[0].start, box[1].stop - box[1].start)
    return area / side**2
