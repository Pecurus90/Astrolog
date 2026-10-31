"""Stars as Image Analysis finds them (plans 25.15, 26.48, misure.md): from its public docs, probed
black-box on its outputs, never on PCL sources. Pure: pixels in, positions out. software-ok"""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from ..units import sigma_from_mad
from .noise import NOISE_FLOOR_ADU
from .psf_flux import tenth_flux

# Scales up to 2^5 = 32 px: a nebula core or a coma wider than that is no structure of a star.
STRUCTURE_LAYERS = 5  # [C StarDetector structureLayers, SubframeSelector default; software-ok]
# Structure: median copy less its Gaussian blur, kernel 2^L + 1 px cut at 1% of its peak (sigma
# 5.27 px at 5 layers); his map's saturated areas, layers 3 to 6 (misure.md). software-ok
STRUCTURE_REACH = 2 ** (STRUCTURE_LAYERS - 1)  # [D kernel radius: 2^L + 1 px across]
STRUCTURE_CUT = 0.01  # [M plan 26.48.1: sigma doubling per layer, 1.3 / 2.5 / 5 / 10 px]
STRUCTURE_BLUR = STRUCTURE_REACH / np.sqrt(-2 * np.log(STRUCTURE_CUT))  # [D Gaussian at the cut]
# Pixels over this many frame sigmas, closed 3x3: his map on 21 frames, sparse fields. software-ok
STRUCTURE_SIGMA = 2.12  # [M plan 26.48.1: 2.10-2.16 MRS; crowded fields up to 2.44, plan 26.48.2]
# No star of his on fewer pixels, 205 frames, minStructureSize off. software-ok
MIN_PIXELS = 3  # [M plan 26.48.1: his smallest star 3 px in 185 frames, more in the rest]
# A star covers over (1 - maxDistortion) of a disc's pi / 4 of its square: his cut at b/a 0.3-0.4
# (misure.md, 14 synthetic frames) agrees; 0.6 of the square would drop b/a under 0.76.
MAX_DISTORTION = 0.6  # [C StarDetector maxDistortion, SubframeSelector default; software-ok]
MIN_COVERAGE = (1 - MAX_DISTORTION) * np.pi / 4  # [D a disc fills pi / 4 of its square]
# Star: best 2x2 sum on the raw residual over the noise of 4 pixels, its half-found amplitude on
# synthetic stars of known profile, Gaussian sigma 1-4 and Moffat (misure.md); software-ok
APERTURE_SNR = 16.5  # [M plan 26.48.1: 16.2-16.7 per profile, his structures and ring]
# Its threshold on the synthetic frames holds within 1.18x over FWHM 1.5-6; 1 px 1.48x, 3 px 1.64x.
APERTURE_PX = 2  # [M plan 26.45: the aperture whose threshold does not follow the FWHM]
# Saturated: one sensor pixel at the ceiling. [C ASTAP plot_star: a pixel at data_max]
CLIPPED_PIXELS = 1
# One 5x5 local maximum per structure, else a multiple source (allowClusteredSources off); pixels
# over BRIGHT_LEVEL of the ceiling take no part. [C PJSR StarDetector defaults; software-ok]
PEAK_RADIUS = 2  # [C StarDetector localDetectionFilterRadius default; software-ok]
BRIGHT_LEVEL = 0.75  # [C StarDetector localMaximaDetectionLimit default; software-ok]
# (2x2 - 2 b) / n, b and n median and MAD of the box grown by RING_MARGIN less every structure
# grown by RING_GROW (PJSR sensitivity), probed around his structures. software-ok
RING_GROW = 1  # [M plan 26.48: tile and ring probes on his structures]
RING_MARGIN = 6  # [M plan 26.48: as RING_GROW]
MIN_RING = 16  # [T] fewer free sky pixels: the frame's noise, the sky at zero
# Speed: candidates under it never reach the local test. [M plan 26.48: no star of his under it]
PREFILTER_SNR = 8.0
# Moments of the flux ellipse on the star grown by this: Gaussian sigma 1.2-3.5, bright and faint.
FLUX_GROW = 3  # [M plan 26.48.1: flux within 5% of the truth; 2 px 10% short at sigma 3.5]
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
    found = ndimage.label(structure_map(filtered, noise), structure=_EIGHT)
    labels, count = cast(tuple[np.ndarray, int], found)  # stubs say int | tuple
    # Structure pixels only: ndimage's per-label max and centre sweep the frame, 1.5 s at 26 MP.
    rows, cols = np.nonzero(labels)
    owner = labels[rows, cols]
    boxes = ndimage.find_objects(labels)
    box = ndimage.uniform_filter(residual, APERTURE_PX) * APERTURE_PX  # 2x2 mean x 2 = sum / 2
    best = np.full(count + 1, -np.inf)
    np.maximum.at(best, owner, box[rows, cols])
    star = (best >= PREFILTER_SNR * noise) & (_coverage(owner, boxes, count) >= MIN_COVERAGE)
    star &= np.bincount(owner, minlength=count + 1) >= MIN_PIXELS
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
    # Flux ellipse from the star grown FLUX_GROW px: its structure stops short of the wings. A grown
    # sky pixel goes to the nearest star, square distance as the dilation's; no structure's pixel.
    kept = np.where(star[labels], labels, 0)
    far, (near_r, near_c) = cast(
        tuple[np.ndarray, tuple[np.ndarray, np.ndarray]],
        ndimage.distance_transform_cdt(kept == 0, metric="chessboard", return_indices=True),
    )
    grown = (far >= 0) & (far <= FLUX_GROW) & ((labels == 0) | (kept > 0))
    kept = np.where(grown, kept[near_r, near_c], 0)
    del far, near_r, near_c
    rows, cols = np.nonzero(kept)
    owner = np.asarray(kept[rows, cols], dtype=np.intp)
    mine = star[owner]
    pixels = (rows[mine], cols[mine], index[owner[mine]])
    return Detections(x, y, saturated, tenth_flux((residual, filtered), pixels, (x, y)))


def structure_map(filtered: np.ndarray, noise: float) -> np.ndarray:
    """Structure pixels: `filtered` less its blur over STRUCTURE_SIGMA `noise`, closed 3x3."""
    blur = ndimage.gaussian_filter(
        filtered, STRUCTURE_BLUR, mode="mirror", truncate=STRUCTURE_REACH / STRUCTURE_BLUR
    )
    np.subtract(filtered, blur, out=blur)
    return ndimage.binary_closing(blur > STRUCTURE_SIGMA * noise, _EIGHT)


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
