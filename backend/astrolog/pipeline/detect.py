"""Stars as Image Analysis finds them (plans 25.15, 26.48, misure.md): from its public docs, probed
black-box on its outputs, never on PCL sources. Pure: pixels in, positions out. software-ok"""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from ..units import sigma_from_mad
from .noise import NOISE_FLOOR_ADU, coarse, detail_unit_sigma
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
# One 5x5 local maximum per structure, else a multiple source (allowClusteredSources off); pixels
# over BRIGHT_LEVEL of the ceiling take no part. [C PJSR StarDetector defaults; software-ok]
PEAK_RADIUS = 2  # [C StarDetector localDetectionFilterRadius default; software-ok]
BRIGHT_LEVEL = 0.75  # [C StarDetector localMaximaDetectionLimit default; software-ok]
# (2x2 - 2 b) / n, b and n median and MAD of the box grown by RING_MARGIN less every structure
# grown by RING_GROW (PJSR sensitivity). His ring is 1 and 6, round structures not ours yet.
RING_GROW = 4  # [M plan 26.48: 7 frames of 205 off 0.95-1.05, 22 with his 1 and 6]
RING_MARGIN = 16  # [M plan 26.48: as RING_GROW]
MIN_RING = 16  # [T] fewer free sky pixels: the frame's noise, the sky at zero
# Speed: candidates under it never reach the local test. [M plan 26.48: no star of his under it]
PREFILTER_SNR = 8.0
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
    level: tuple[np.ndarray, float] | None = None,
) -> Detections:
    """`residual` less sky, `filtered` its 3x3 median, `noise` MRS; `clip` sensor pixels and their
    ceiling, `level` measured plane and ceiling (BRIGHT_LEVEL). One star per structure."""
    detail = filtered - coarse(filtered, STRUCTURE_LAYERS)
    found = ndimage.label(detail > STRUCTURE_SIGMA * STRUCTURE_UNIT * noise, structure=_EIGHT)
    del detail
    labels, count = cast(tuple[np.ndarray, int], found)  # stubs say int | tuple
    # Structure pixels only: ndimage's per-label max and centre sweep the frame, 1.5 s at 26 MP.
    rows, cols = np.nonzero(labels)
    owner = labels[rows, cols]
    boxes = ndimage.find_objects(labels)
    box = ndimage.uniform_filter(residual, APERTURE_PX) * APERTURE_PX  # 2x2 mean x 2 = sum / 2
    best = np.full(count + 1, -np.inf)
    np.maximum.at(best, owner, box[rows, cols])
    star = (best >= PREFILTER_SNR * noise) & (_coverage(owner, boxes, count) >= MIN_COVERAGE)
    bright = np.zeros(count + 1, dtype=bool)
    if level is not None:
        plane, top = level
        bright = np.bincount(owner, plane[rows, cols] > BRIGHT_LEVEL * top, count + 1) > 0
    star &= bright | (_peaks(residual, labels, count) <= 1)
    star &= _over_local_sky(residual, labels, boxes, (best, star), noise)
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


def _coverage(owner: np.ndarray, boxes: list[tuple[slice, slice] | None], count: int) -> np.ndarray:
    """Each structure's pixels over its circumscribed square, the bounding box's longer side."""
    area = np.bincount(owner, minlength=count + 1).astype(float)
    side = np.ones(count + 1)
    for i, box in enumerate(boxes, start=1):
        if box is not None:
            side[i] = max(box[0].stop - box[0].start, box[1].stop - box[1].start)
    return area / side**2


def _peaks(residual: np.ndarray, labels: np.ndarray, count: int) -> np.ndarray:
    """Local maxima of each structure on the residual, its own pixels only; a plateau counts one."""
    inside = np.where(labels > 0, residual, -np.inf).astype(np.float32)
    top = ndimage.maximum_filter(inside, size=2 * PEAK_RADIUS + 1, mode="constant", cval=-np.inf)
    at = (labels > 0) & (inside == top)
    del inside, top
    spots, _ = cast(tuple[np.ndarray, int], ndimage.label(at, structure=_EIGHT))
    owner_of = np.zeros(int(spots.max()) + 1, dtype=np.intp)
    owner_of[spots[at]] = labels[at]  # a spot lies in one structure: both are 8-connected
    return np.bincount(owner_of[1:], minlength=count + 1)


def _over_local_sky(
    residual: np.ndarray,
    labels: np.ndarray,
    boxes: list[tuple[slice, slice] | None],
    candidates: tuple[np.ndarray, np.ndarray],
    noise: float,
) -> np.ndarray:
    """(2x2 - 2 b) / n >= APERTURE_SNR for each candidate, b and n from its ring (RING_GROW)."""
    best, star = candidates
    reach = 2 * RING_GROW + 1  # [D RING_GROW 8-connected dilations make this square]
    free_sky = ndimage.maximum_filter(labels, size=reach) == 0
    rows, cols = residual.shape
    keep = np.zeros(len(star), dtype=bool)
    for i in np.flatnonzero(star):
        r, c = boxes[i - 1] or (slice(0, 0), slice(0, 0))
        ring = (
            slice(max(r.start - RING_MARGIN, 0), min(r.stop + RING_MARGIN, rows)),
            slice(max(c.start - RING_MARGIN, 0), min(c.stop + RING_MARGIN, cols)),
        )
        free = residual[ring][free_sky[ring]]
        sky, spread = 0.0, noise
        if free.size >= MIN_RING:
            sky = float(np.median(free))
            spread = sigma_from_mad(float(np.median(np.abs(free - sky))))
        keep[i] = (best[i] - 2 * sky) / max(spread, NOISE_FLOOR_ADU) >= APERTURE_SNR
    return keep
