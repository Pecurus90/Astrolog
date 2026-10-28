"""Each star's flux for the PSF SNR (ImageWeighting par. 2.2, misure.md): its pixels over a tenth
of its peak, less its local sky. Pure: pixels in, fluxes out. software-ok"""

import numpy as np

from .shape import RING_OUTER

# The region over a tenth of the peak [C PixInsight ImageWeighting par. 2.2; software-ok]; each
# star's own: one PSF a zone lost the wide saturated stars, 0.12-0.48 of the PSF SNR (misure.md)
TENTH = 0.1


def ring_sky(
    filtered: np.ndarray, centres: tuple[np.ndarray, np.ndarray], inner: np.ndarray
) -> np.ndarray:
    """Median of the pixels between `inner` and RING_OUTER times it, star by star."""
    rows, cols = filtered.shape
    sky = np.empty(len(inner))
    for i, (x, y, near) in enumerate(zip(*centres, inner, strict=True)):
        outer = near * RING_OUTER
        y0, y1 = max(0, int(y - outer)), min(rows, int(y + outer) + 2)
        x0, x1 = max(0, int(x - outer)), min(cols, int(x + outer) + 2)
        dy, dx = np.ogrid[y0 - y : y1 - y, x0 - x : x1 - x]
        distance = np.hypot(dy, dx)
        sky[i] = np.median(filtered[y0:y1, x0:x1][(distance >= near) & (distance < outer)])
    return sky


def tenth_flux(
    images: tuple[np.ndarray, np.ndarray],
    pixels: tuple[np.ndarray, np.ndarray, np.ndarray],
    centres: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    """`pixels`: rows, columns, star index of each structure. Peak and region on the median copy,
    sum on the residual; a centre outside its own region is no star, 0 (misure.md)."""
    residual, filtered = images
    rows, cols, star = pixels
    x, y = centres
    reach = np.zeros(len(x))
    np.maximum.at(reach, star, np.hypot(cols - x[star], rows - y[star]))
    sky = ring_sky(filtered, centres, reach + 1)
    level = filtered[rows, cols] - sky[star]
    peak = np.zeros(len(x))
    np.maximum.at(peak, star, level)
    inside = level > TENTH * peak[star]
    flux = np.bincount(star, (residual[rows, cols] - sky[star]) * inside, len(x))
    rows_at = np.clip(np.rint(y).astype(int), 0, filtered.shape[0] - 1)
    cols_at = np.clip(np.rint(x).astype(int), 0, filtered.shape[1] - 1)
    centred = filtered[rows_at, cols_at] - sky > TENTH * peak
    return np.where(centred, flux, 0.0)
