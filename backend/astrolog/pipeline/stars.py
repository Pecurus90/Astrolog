"""One frame measured on its pixels (ADR 0022, docs/domini/misure.md): sky, noise, stars on a
median-filtered copy, HFD on the raw frame. Pure: pixels in, numbers out."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import sep  # pyright: ignore[reportMissingImports] -- compiled module, no stubs

from ..units import sigma_from_mad

THRESHOLD_SIGMA = 5.0  # [C Siril find_star default: 5 sigma over sky, software-ok]
SATURATED_SHARE = 0.9  # [P ADR 0022: peak under 90% of saturation]
MIN_AXIS_RATIO = 0.5  # [C Siril find_star default roundness, software-ok]
ROOM_HFD = 3.0  # [P ADR 0022: away from the edge and from neighbours more than 3 HFD]
# Aperture radius in estimated HFD: a Moffat beta 2.5 holds 99% of its flux there.
# [D Moffat 1969, enclosed flux 1-(1+r^2/a^2)^(1-b)]
APERTURE_HFD = 3.0
RING_OUTER = 1.5  # [T] ring from the aperture to 1.5 times it: the local sky
RADII = 96  # [T] radii sampled per star; half flux interpolated between two
SUBPIX = 5  # [C sep docs: sum_circle default subpixel sampling]
MIN_STARS = 5  # [T] fewer kept stars: the median HFD says nothing; measured on real frames
# Stars spread over the field, not the brightest: a 3x3 grid, 60 a cell, across the flux ranking.
GRID = 3  # [P ADR 0022]
PER_CELL = 60  # [P ADR 0022]
# Gaussian HFD = FWHM = 2 sqrt(2 ln 2) sigma. [D Gaussian profile]
SIGMA_TO_HFD = 2.3548
BAYER = 2  # [C Bayer pattern: one colour quad is 2x2 sensor pixels]
# Noise never under one ADU step's own: a quantized sky has MAD 0, and then every step is a star.
# [D uniform quantization noise, step/sqrt(12)]
NOISE_FLOOR_ADU = 0.2887


@dataclass(frozen=True)
class Measured:
    stars: int  # every detection on the frame: a relative indicator (ADR 0022)
    kept: int  # stars the HFD is the median of
    hfd_px: float  # sensor pixels
    background_adu: float
    noise_adu: float


@dataclass(frozen=True)
class TooFewStars:
    stars: int
    kept: int
    background_adu: float
    noise_adu: float


def measure_frame(data: np.ndarray, *, saturation: float, bayer: bool) -> Measured | TooFewStars:
    """`bayer`: a colour sensor, measured on its 2x2 superpixel and given back in sensor pixels;
    unknown is mono. `saturation`: the ceiling in the same units as `data`."""
    raw = _quads(data, np.mean) if bayer else np.ascontiguousarray(data, dtype=np.float32)
    ceiling = _quads(data, np.max) if bayer else raw  # a clipped sensor pixel, not its quad
    scale = BAYER if bayer else 1
    sky = sep.Background(raw)
    residual = raw - sky.back()
    spread = sigma_from_mad(float(np.median(np.abs(residual - np.median(residual)))))
    noise = max(spread, NOISE_FLOOR_ADU)
    filtered = median3x3(residual)
    objects = _found(filtered, noise)
    keep = _spread(objects, _kept(ceiling, objects, saturation), raw.shape)
    hfds = _hfd((residual, filtered), objects, keep)
    background, stars = float(sky.globalback), len(objects)
    if len(hfds) < MIN_STARS:
        return TooFewStars(stars, len(hfds), background, noise)
    return Measured(stars, len(hfds), float(np.median(hfds)) * scale, background, noise)


def median3x3(data: np.ndarray) -> np.ndarray:
    """Exact 3x3 median, edges mirrored: vertical triples sorted once, then the median of the
    nine is med3(max of lows, med3 of mids, min of highs) (Paeth, Graphics Gems 1990)."""
    padded = np.pad(data, 1, mode="symmetric")
    a, b, c = padded[:-2], padded[1:-1], padded[2:]
    low, high = np.minimum(a, b), np.maximum(a, b)
    mid = np.maximum(low, np.minimum(high, c))
    low, high = np.minimum(low, c), np.maximum(high, c)
    lows = np.maximum(np.maximum(low[:, :-2], low[:, 1:-1]), low[:, 2:])
    highs = np.minimum(np.minimum(high[:, :-2], high[:, 1:-1]), high[:, 2:])
    mids = _med3(mid[:, :-2], mid[:, 1:-1], mid[:, 2:])
    return _med3(lows, mids, highs)


def _med3(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    return np.maximum(np.minimum(a, b), np.minimum(np.maximum(a, b), c))


def _quads(data: np.ndarray, how: Callable[..., np.ndarray]) -> np.ndarray:
    """One value per 2x2 colour quad: the mean is the superpixel, the pattern gone (ADR 0022)."""
    rows, cols = (data.shape[0] // BAYER) * BAYER, (data.shape[1] // BAYER) * BAYER
    quads = data[:rows, :cols].reshape(rows // BAYER, BAYER, cols // BAYER, BAYER)
    return np.ascontiguousarray(how(quads, axis=(1, 3)), dtype=np.float32)


def _found(filtered: np.ndarray, noise: float) -> np.ndarray:
    """Detections on the filtered copy: hot pixels gone, stars kept (ADR 0022, point 8)."""
    sep.set_extract_pixstack(max(300_000, filtered.size))  # dense fields fill sep's default
    return sep.extract(np.ascontiguousarray(filtered), THRESHOLD_SIGMA, err=noise)


def _estimate(objects: np.ndarray) -> np.ndarray:
    """HFD guessed from sep's second moments, for edges, neighbours and apertures only."""
    return SIGMA_TO_HFD * np.sqrt(np.maximum(objects["a"] * objects["b"], 0.25))


def _kept(raw: np.ndarray, objects: np.ndarray, saturation: float) -> np.ndarray:
    """Indices of stars fit to measure: whole, unsaturated, round enough, alone, off the edge."""
    if len(objects) == 0:
        return np.array([], dtype=int)
    x, y, guess = objects["x"], objects["y"], _estimate(objects)
    room = ROOM_HFD * guess
    rows, cols = raw.shape
    inside = (x > room) & (y > room) & (x < cols - 1 - room) & (y < rows - 1 - room)
    ratio = objects["b"] / np.maximum(objects["a"], 1e-9)
    ok = (objects["flag"] == 0) & inside & (ratio > MIN_AXIS_RATIO)
    ok &= _peaks(raw, objects, guess) < SATURATED_SHARE * saturation
    candidates = np.flatnonzero(ok)
    return candidates[_alone(x, y, room, candidates)]


def _alone(x: np.ndarray, y: np.ndarray, room: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """No other detection within `room` of each candidate. Neighbours from a strip sorted on x:
    memory linear in the detections, not a table of every pair (dense fields hold 20k+)."""
    order = np.argsort(x)
    xs = x[order]
    low = np.searchsorted(xs, x[candidates] - room[candidates], side="left")
    high = np.searchsorted(xs, x[candidates] + room[candidates], side="right")
    alone = np.ones(len(candidates), dtype=bool)
    for k, (i, start, stop) in enumerate(zip(candidates, low, high, strict=True)):
        near = order[start:stop]
        near = near[near != i]
        alone[k] = bool(np.all(np.hypot(x[near] - x[i], y[near] - y[i]) > room[i]))
    return alone


def _spread(objects: np.ndarray, keep: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    """At most PER_CELL kept stars per grid cell, evenly along the cell's flux ranking."""
    rows, cols = shape
    cell = np.minimum(objects["y"][keep] * GRID // rows, GRID - 1) * GRID + np.minimum(
        objects["x"][keep] * GRID // cols, GRID - 1
    )
    chosen = []
    for number in range(GRID * GRID):
        here = keep[cell == number]
        ranked = here[np.argsort(objects["flux"][here])]
        if len(ranked) > PER_CELL:
            ranked = ranked[np.linspace(0, len(ranked) - 1, PER_CELL).round().astype(int)]
        chosen.append(ranked)
    return np.sort(np.concatenate(chosen)) if chosen else keep


def _ring_sky(
    filtered: np.ndarray, centres: tuple[np.ndarray, np.ndarray], aperture: np.ndarray
) -> np.ndarray:
    """Median of the pixels between the aperture and RING_OUTER times it, star by star."""
    rows, cols = filtered.shape
    sky = np.empty(len(aperture))
    for i, (x, y, inner) in enumerate(zip(*centres, aperture, strict=True)):
        outer = inner * RING_OUTER
        y0, y1 = max(0, int(y - outer)), min(rows, int(y + outer) + 2)
        x0, x1 = max(0, int(x - outer)), min(cols, int(x + outer) + 2)
        dy, dx = np.ogrid[y0 - y : y1 - y, x0 - x : x1 - x]
        distance = np.hypot(dy, dx)
        sky[i] = np.median(filtered[y0:y1, x0:x1][(distance >= inner) & (distance < outer)])
    return sky


def _peaks(raw: np.ndarray, objects: np.ndarray, guess: np.ndarray) -> np.ndarray:
    """Highest raw pixel near each centre: a clipped core stays flat at the ceiling."""
    peaks = np.empty(len(objects))
    rows, cols = raw.shape
    for i, (x, y, size) in enumerate(zip(objects["x"], objects["y"], guess, strict=True)):
        r = max(1, int(np.ceil(size)))
        y0, x0 = int(round(y)), int(round(x))
        peaks[i] = raw[
            max(0, y0 - r) : min(rows, y0 + r + 1), max(0, x0 - r) : min(cols, x0 + r + 1)
        ].max()
    return peaks


def _hfd(
    images: tuple[np.ndarray, np.ndarray], objects: np.ndarray, keep: np.ndarray
) -> np.ndarray:
    """Half-flux diameter on the raw residual, less the ring median on the filtered copy (no hot
    pixels, no neighbours). No segment mask: a masked nebula empties the ring (Rosette)."""
    if len(keep) == 0:
        return np.array([])
    residual, filtered = images
    x, y = objects["x"][keep], objects["y"][keep]
    aperture = APERTURE_HFD * _estimate(objects)[keep]
    sky = _ring_sky(filtered, (x, y), aperture)
    steps = np.linspace(1 / RADII, 1.0, RADII)
    enclosed = np.empty((RADII, len(keep)))
    for i, share in enumerate(steps):
        radius = aperture * share
        flux, _, _ = sep.sum_circle(residual, x, y, radius, subpix=SUBPIX)
        enclosed[i] = flux - sky * np.pi * radius**2
    total = enclosed[-1]
    good = total > 0
    radii = np.empty(len(keep))
    for j in np.flatnonzero(good):
        radii[j] = (
            np.interp(total[j] / 2, np.maximum.accumulate(enclosed[:, j]), steps) * aperture[j]
        )
    return 2 * radii[good]
