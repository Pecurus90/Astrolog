"""Each star's flux for the PSF SNR (ImageWeighting par. 2.2, misure.md): the residual summed in the
ellipse where its profile falls to a tenth of the peak. Pure: pixels in, fluxes out. software-ok"""

import math

import numpy as np
import sep  # pyright: ignore[reportMissingImports] -- compiled module, no stubs

from .shape import RING_OUTER

TENTH = 0.1  # [C PixInsight ImageWeighting par. 2.2: the PSF over a tenth of its peak; software-ok]
TENTH_RADIUS = math.sqrt(2 * math.log(1 / TENTH))  # [D Gaussian: exp(-r^2 / 2) = TENTH]
MIN_AXIS_PX = 0.5  # [D a pixel's own half-width] a lone bright pixel: sep needs axes over 0
SUBPIX = 5  # [C sep docs: sum_ellipse default subpixel sampling]
# Local sky ring, from just past the structure: a median, not sep's mean (neighbours stay out)
LOCAL_SKY_PX = 24  # [C SExtractor BACKPHOTO_THICK default 24]


def ring_sky(
    filtered: np.ndarray,
    centres: tuple[np.ndarray, np.ndarray],
    inner: np.ndarray,
    outer: np.ndarray | None = None,
) -> np.ndarray:
    """Median of the pixels between `inner` and `outer` (RING_OUTER times inner if not given)."""
    rows, cols = filtered.shape
    far_all = inner * RING_OUTER if outer is None else outer
    sky = np.empty(len(inner))
    for i, (x, y, near, far) in enumerate(zip(*centres, inner, far_all, strict=True)):
        y0, y1 = max(0, int(y - far)), min(rows, int(y + far) + 2)
        x0, x1 = max(0, int(x - far)), min(cols, int(x + far) + 2)
        dy, dx = np.ogrid[y0 - y : y1 - y, x0 - x : x1 - x]
        distance = np.hypot(dy, dx)
        sky[i] = np.median(filtered[y0:y1, x0:x1][(distance >= near) & (distance < far)])
    return sky


def tenth_flux(
    images: tuple[np.ndarray, np.ndarray],
    pixels: tuple[np.ndarray, np.ndarray, np.ndarray],
    centres: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    """`pixels`: rows, columns, star of each structure. Ellipse from its second moments (SExtractor
    A, B, THETA); a centre outside its own tenth is no star, 0 (misure.md)."""
    residual, filtered = images
    rows, cols, star = pixels
    x, y = centres
    count = len(x)
    reach = np.zeros(count)
    np.maximum.at(reach, star, np.hypot(cols - x[star], rows - y[star]))
    sky = ring_sky(filtered, centres, reach + 1, reach + 1 + LOCAL_SKY_PX)
    weight = np.maximum(filtered[rows, cols].astype(np.float64) - sky[star], 0.0)
    total = np.maximum(np.bincount(star, weight, count), 1e-12)
    dx, dy = cols - x[star], rows - y[star]
    x2 = np.bincount(star, weight * dx * dx, count) / total
    y2 = np.bincount(star, weight * dy * dy, count) / total
    xy = np.bincount(star, weight * dx * dy, count) / total
    half, root = (x2 + y2) / 2, np.sqrt(((x2 - y2) / 2) ** 2 + xy**2)
    a = np.sqrt(np.maximum(half + root, MIN_AXIS_PX**2))
    b = np.sqrt(np.maximum(half - root, MIN_AXIS_PX**2))
    theta = 0.5 * np.arctan2(2 * xy, x2 - y2)
    data = np.ascontiguousarray(residual, dtype=np.float64)
    flux, _, _ = sep.sum_ellipse(data, x, y, a, b, theta, r=TENTH_RADIUS, subpix=SUBPIX)
    flux = np.asarray(flux, dtype=np.float64) - sky * math.pi * a * b * TENTH_RADIUS**2
    peak = np.zeros(count)
    np.maximum.at(peak, star, filtered[rows, cols] - sky[star])
    rows_at = np.clip(np.rint(y).astype(int), 0, filtered.shape[0] - 1)
    cols_at = np.clip(np.rint(x).astype(int), 0, filtered.shape[1] - 1)
    centred = filtered[rows_at, cols_at] - sky > TENTH * peak
    return np.where(centred, flux, 0.0)
