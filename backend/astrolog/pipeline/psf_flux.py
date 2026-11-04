"""Each star's flux for the PSF SNR (ImageWeighting par. 2.2, misure.md): the residual summed in the
ellipse where its profile falls to a tenth of the peak. Pure: pixels in, fluxes out. software-ok"""

import math

import numpy as np
import sep  # pyright: ignore[reportMissingImports] -- compiled module, no stubs

from .cores import STARS_A_CORE, compiled, in_parts, median_in_place

TENTH = 0.1  # [C PixInsight ImageWeighting par. 2.2: the PSF over a tenth of its peak; software-ok]
TENTH_RADIUS = math.sqrt(2 * math.log(1 / TENTH))  # [D Gaussian: exp(-r^2 / 2) = TENTH]
MIN_AXIS_PX = 0.5  # [D a pixel's own half-width] a lone bright pixel: sep needs axes over 0
SUBPIX = 5  # [C sep docs: sum_ellipse default subpixel sampling]
# Local sky ring, from just past the structure: a median, not sep's mean (neighbours stay out)
LOCAL_SKY_PX = 24  # [C SExtractor BACKPHOTO_THICK default 24]
RING_OUTER = 1.5  # [T] the local sky: the ring from the window (or aperture) to 1.5 times it


def ring_sky(
    filtered: np.ndarray,
    centres: tuple[np.ndarray, np.ndarray],
    inner: np.ndarray,
    outer: np.ndarray | None = None,
) -> np.ndarray:
    """Median of the pixels between `inner` and `outer` (RING_OUTER times inner if not given)."""
    far = inner * RING_OUTER if outer is None else outer
    x, y = (np.asarray(c, dtype=np.float64) for c in centres)
    image, sky = np.ascontiguousarray(filtered), np.empty(len(x))
    radii = (np.asarray(inner, np.float64), np.asarray(far, np.float64))
    in_parts(lambda a, b: _rings(image, (x, y), radii, (a, b), sky), len(x), least=STARS_A_CORE)
    return sky


@compiled
def _rings(
    image: np.ndarray,
    centres: tuple[np.ndarray, np.ndarray],
    radii: tuple[np.ndarray, np.ndarray],
    span: tuple[int, int],
    sky: np.ndarray,
) -> None:
    """The stars of `span`: median of the pixels whose distance from the centre is in [inner,
    outer), into `sky`; offsets start + k as np.ogrid's, the hypotenuse as np.hypot's."""
    rows, cols = image.shape
    xs, ys = centres
    inner, outer = radii
    for i in range(*span):
        x, y, near, far = xs[i], ys[i], inner[i], outer[i]
        y0, y1 = max(0, int(y - far)), min(rows, int(y + far) + 2)
        x0, x1 = max(0, int(x - far)), min(cols, int(x + far) + 2)
        ring = np.empty(max(0, y1 - y0) * max(0, x1 - x0), dtype=image.dtype)
        n = 0
        for r in range(y0, y1):
            dy = (y0 - y) + (r - y0)
            for c in range(x0, x1):
                distance = math.hypot(dy, (x0 - x) + (c - x0))
                if near <= distance < far:
                    ring[n] = image[r, c]
                    n += 1
        sky[i] = median_in_place(ring[:n])


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
    # sep sums in float32 whatever it gets: a float64 copy, 200 MB at 26 MP, buys nothing
    data = np.ascontiguousarray(residual)
    flux, _, _ = sep.sum_ellipse(data, x, y, a, b, theta, r=TENTH_RADIUS, subpix=SUBPIX)
    flux = np.asarray(flux, dtype=np.float64) - sky * math.pi * a * b * TENTH_RADIUS**2
    peak = np.zeros(count)
    np.maximum.at(peak, star, filtered[rows, cols] - sky[star])
    rows_at = np.clip(np.rint(y).astype(int), 0, filtered.shape[0] - 1)
    cols_at = np.clip(np.rint(x).astype(int), 0, filtered.shape[1] - 1)
    centred = filtered[rows_at, cols_at] - sky > TENTH * peak
    return np.where(centred, flux, 0.0)
