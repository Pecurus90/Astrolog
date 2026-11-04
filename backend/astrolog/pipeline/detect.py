"""Stars as Image Analysis finds them (plans 25.15, 26.48, misure.md): from its public docs, probed
black-box on its outputs, never on PCL sources. Pure: pixels in, positions out. software-ok"""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from ..units import sigma_from_mad
from .cores import by_strips, compiled, inlined, median_in_place
from .noise import NOISE_FLOOR_ADU
from .psf_flux import tenth_flux

# Scales up to 2^5 = 32 px: a nebula core or a coma wider than that is no structure of a star.
STRUCTURE_LAYERS = 5  # [C StarDetector structureLayers, SubframeSelector default; software-ok]
# Structure: median copy less its Gaussian blur, kernel 2^L + 1 px cut at 1% of its peak (sigma
# 5.27 px at 5 layers); his map's saturated areas, layers 3 to 6 (misure.md). software-ok
STRUCTURE_REACH = 2 ** (STRUCTURE_LAYERS - 1)  # [D kernel radius: 2^L + 1 px across]
STRUCTURE_CUT = 0.01  # [M plan 26.48.1: sigma doubling per layer, 1.3 / 2.5 / 5 / 10 px]
STRUCTURE_BLUR = STRUCTURE_REACH / np.sqrt(-2 * np.log(STRUCTURE_CUT))  # [D Gaussian at the cut]
# Pixels over this many structure-noise sigmas, closed 3x3: his map, sparse fields. software-ok
STRUCTURE_SIGMA = 2.11  # [M plan 26.48.2: 2.09-2.12 on 7 sparse mono; misure.md]
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
    box: np.ndarray  # structure's box, (x0, x1, y0, y1) end exclusive: where the PSF fit starts


def detect(
    residual: np.ndarray,
    filtered: np.ndarray,
    noise: float | tuple[float, float],
    clip: tuple[np.ndarray, float] | None = None,
    level: tuple[np.ndarray, float] | None = None,
) -> Detections:
    """`filtered` the residual's 3x3 median; `noise` MRS and the map's (structure_noise), one for
    both on white noise; `clip` sensor and ceiling, `level` plane and ceiling. One star each."""
    noise, threshold_noise = noise if isinstance(noise, tuple) else (noise, noise)
    found = ndimage.label(structure_map(filtered, threshold_noise), structure=_EIGHT)
    labels, count = cast(tuple[np.ndarray, int], found)  # stubs say int | tuple
    # Structure pixels only: ndimage's per-label max and centre sweep the frame, 1.5 s at 26 MP.
    rows, cols = np.nonzero(labels)
    owner = labels[rows, cols]
    boxes = ndimage.find_objects(labels)
    box = by_strips(lambda rows: ndimage.uniform_filter(rows, APERTURE_PX), residual, APERTURE_PX)
    box *= APERTURE_PX  # 2x2 mean x 2 = sum / 2
    best = np.full(count + 1, -np.inf)
    np.maximum.at(best, owner, box[rows, cols])
    star = (best >= PREFILTER_SNR * noise) & (_coverage(owner, boxes, count) >= MIN_COVERAGE)
    star &= np.bincount(owner, minlength=count + 1) >= MIN_PIXELS
    bright = np.zeros(count + 1, dtype=bool)
    if level is not None:
        plane, top = level
        bright = np.bincount(owner, plane[rows, cols] > BRIGHT_LEVEL * top, count + 1) > 0
    star &= bright | (_peaks(residual, labels, (rows, cols), count) <= 1)
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
    spans = [boxes[k - 1] for k in np.flatnonzero(star)]
    box = np.array([(b[1].start, b[1].stop, b[0].start, b[0].stop) for b in spans], dtype=np.intp)
    box = box.reshape(-1, 4)
    return Detections(x, y, saturated, tenth_flux((residual, filtered), pixels, (x, y)), box)


def structure_map(filtered: np.ndarray, noise: float) -> np.ndarray:
    """Structure pixels: `filtered` less its blur over STRUCTURE_SIGMA `noise`, closed 3x3."""

    def strip(rows: np.ndarray) -> np.ndarray:
        blur = ndimage.gaussian_filter(
            rows, STRUCTURE_BLUR, mode="mirror", truncate=STRUCTURE_REACH / STRUCTURE_BLUR
        )
        np.subtract(rows, blur, out=blur)
        return ndimage.binary_closing(blur > STRUCTURE_SIGMA * noise, _EIGHT)

    return by_strips(strip, filtered, STRUCTURE_REACH + 2)  # closing: one row each way, twice


def _coverage(owner: np.ndarray, boxes: list[tuple[slice, slice] | None], count: int) -> np.ndarray:
    """Each structure's pixels over its circumscribed square, the bounding box's longer side."""
    area = np.bincount(owner, minlength=count + 1).astype(float)
    side = np.ones(count + 1)
    for i, box in enumerate(boxes, start=1):
        if box is not None:
            side[i] = max(box[0].stop - box[0].start, box[1].stop - box[1].start)
    return area / side**2


def _peaks(
    residual: np.ndarray, labels: np.ndarray, pixels: tuple[np.ndarray, np.ndarray], count: int
) -> np.ndarray:
    """Structure pixels (`pixels`, rows and columns) at the top of their 5x5 on the whole residual,
    sky pixels too (plan 26.48.3, probe on his singles); a plateau counts one."""
    rows, cols = pixels
    at = np.zeros(labels.shape, dtype=bool)
    at[rows, cols] = _tops(residual, rows, cols, PEAK_RADIUS)
    spots, _ = cast(tuple[np.ndarray, int], ndimage.label(at, structure=_EIGHT))
    owner_of = np.zeros(int(spots.max()) + 1, dtype=np.intp)
    owner_of[spots[at]] = labels[at]  # a spot lies in one structure: both are 8-connected
    return np.bincount(owner_of[1:], minlength=count + 1)


@compiled
def _tops(image: np.ndarray, rows: np.ndarray, cols: np.ndarray, reach: int) -> np.ndarray:
    """Each pixel no lower than any within `reach` (a square), the frame's edge cutting it: the
    pixel equal to its maximum filter, outside -inf."""
    height, width = image.shape
    top = np.ones(len(rows), dtype=np.bool_)
    for k in range(len(rows)):
        r, c = rows[k], cols[k]
        value = image[r, c]
        for i in range(max(0, r - reach), min(height, r + reach + 1)):
            for j in range(max(0, c - reach), min(width, c + reach + 1)):
                if image[i, j] > value:
                    top[k] = False
    return top


def _over_local_sky(
    residual: np.ndarray,
    labels: np.ndarray,
    boxes: list[tuple[slice, slice] | None],
    candidates: tuple[np.ndarray, np.ndarray],
    noise: float,
) -> np.ndarray:
    """(2x2 - 2 b) / n >= APERTURE_SNR for each candidate, b and n from its ring (RING_GROW)."""
    best, star = candidates
    rows, cols = residual.shape
    tried = np.flatnonzero(star)
    windows = np.zeros((len(tried), 4), dtype=np.intp)
    for k, i in enumerate(tried):
        r, c = boxes[i - 1] or (slice(0, 0), slice(0, 0))
        windows[k] = (max(r.start - RING_MARGIN, 0), min(r.stop + RING_MARGIN, rows),
                      max(c.start - RING_MARGIN, 0), min(c.stop + RING_MARGIN, cols))  # fmt: skip
    skies, mads, counts = _rings(residual, labels, windows, RING_GROW)
    keep = np.zeros(len(star), dtype=bool)
    for i, sky, mad, count in zip(tried, skies, mads, counts, strict=True):
        if count < MIN_RING:
            sky, spread = 0.0, noise
        else:
            sky, spread = float(sky), sigma_from_mad(float(mad))
        keep[i] = (best[i] - 2 * sky) / max(spread, NOISE_FLOOR_ADU) >= APERTURE_SNR
    return keep


@compiled
def _rings(
    image: np.ndarray, labels: np.ndarray, windows: np.ndarray, grow: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per window (r0, r1, c0, c1), its pixels with no label within `grow` (labels' maximum filter
    zero, edges mirrored): their median, median absolute deviation from it, and count."""
    skies, mads = np.zeros(len(windows), np.float32), np.zeros(len(windows), np.float32)
    counts = np.zeros(len(windows), np.intp)
    for k in range(len(windows)):
        r0, r1, c0, c1 = windows[k]
        free = np.empty((r1 - r0) * (c1 - c0), dtype=image.dtype)
        n = 0
        for r in range(r0, r1):
            for c in range(c0, c1):
                if _clear(labels, r, c, grow):
                    free[n] = image[r, c]
                    n += 1
        counts[k] = n
        if n:
            skies[k] = median_in_place(free[:n])
            mads[k] = median_in_place(np.abs(free[:n] - skies[k]))
    return skies, mads, counts


@inlined
def _clear(labels: np.ndarray, r: int, c: int, grow: int) -> bool:
    height, width = labels.shape
    for i in range(max(0, r - grow), min(height, r + grow + 1)):
        for j in range(max(0, c - grow), min(width, c + grow + 1)):
            if labels[i, j]:
                return False
    return True
