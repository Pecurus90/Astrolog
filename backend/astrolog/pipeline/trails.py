"""Trails of satellites, aircraft and meteors as Image Analysis counts them (par. 2.1.3), from its
public docs, never on PCL sources. Pure: pixels in, a count out. software-ok"""

import functools
from dataclasses import dataclass

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from ..units import sigma_from_mad
from .detect import Detections

BINNED_SIDE = 1500  # [C ImageAnalysis par. 2.1.3: about 1500 px on the largest side; software-ok]
TILE_PX = 32  # [C ImageAnalysis par. 2.1.3: tile medians of 32 x 32 binned px; software-ok]
INVALID_REACH = 3  # [C ImageAnalysis par. 2.1.3: and those within three binned px; software-ok]
FLAG_SIGMA = 2.0  # [C ImageAnalysis par. 2.1.3: two standard deviations over; software-ok]
# Disks proportional to the stars, three times larger for the brightest 2% (spikes).
BRIGHT_SHARE = 0.02  # [C ImageAnalysis par. 2.1.3; software-ok]
BRIGHT_SCALE = 3.0  # [C ImageAnalysis par. 2.1.3; software-ok]
STAR_PAD = 1.0  # [T] binned px past half the structure box's larger side
ANGLE_STEP_DEG = 0.25  # [C ImageAnalysis par. 2.1.3: Hough in steps of 0.25 degrees; software-ok]
NEAR_PX = 1  # [C ImageAnalysis par. 2.1.3: flagged pixels within one binned px; software-ok]
RUN_SIDE_SHARE = 0.25  # [C ImageAnalysis par. 2.1.3: a quarter of the smallest side; software-ok]
FLAGGED_SHARE = 0.35  # [C ImageAnalysis par. 2.1.3: at least 35% of the samples; software-ok]
# Share over a sliding window: one over the whole run grows it twice its length on noise flags.
RUN_WINDOW = 25  # [T]
PEAK_SIGMA = 1.0  # [C ImageAnalysis par. 2.1.3: one standard deviation over each side; software-ok]
SHOULDERS = (2, 3)  # [C ImageAnalysis par. 2.1.3: two and three binned px away; software-ok]
SIDES = (4, 6)  # [T] a side: the mean profile from 4 to 6 binned px away
MAX_TRAILS = 16  # [C ImageAnalysis par. 2.1.3: up to 16 trails per frame; software-ok]
MAX_CANDIDATES = 100  # [T] examined, accepted or not
REMOVED_PX = 2  # [T] an accepted trail's flagged pixels this near go
FINE_ANGLE_DEG = 0.05  # [T] refinement steps over one Hough step each way
FINE_SHIFT_PX = 0.1  # [T] over 1.5 binned px each way
EXAMINED_REACH = (1.0, 3)  # [T] degrees, px: one candidate's neighbours are not examined again
CHORD_SHAPES = 4  # [T] frame shapes whose chords stay kept, 17 MB each at 26 MP
_EIGHT = np.ones((3, 3), dtype=np.int8)  # [D 8-connected: diagonal pixels touch]


@dataclass(frozen=True)
class _Frame:
    residual: np.ndarray  # binned, background off
    flagged: np.ndarray
    open: np.ndarray  # usable and off the stars
    sigma: float
    min_run: float  # binned px


@dataclass(frozen=True)
class _Line:
    angle: float  # radians, of the normal
    distance: float  # binned px from the origin


@dataclass(frozen=True)
class BinnedSky:
    """The binned copy with its tile background off: all the count needs but the stars."""

    factor: int  # sensor px a binned px
    residual: np.ndarray  # binned, background off
    usable: np.ndarray  # every sample valid, off the invalid ones
    sigma: float  # MAD of the usable residual


def trails(plane: np.ndarray, valid: np.ndarray, stars: Detections) -> int:
    """Count on a binned copy: tile background off, pixels over 2 sigma flagged off the stars,
    Hough candidates by significance, accepted on a long run and a thin profile."""
    return counted(binned_sky(plane, valid), stars)


def binned_sky(plane: np.ndarray, valid: np.ndarray) -> BinnedSky | None:
    """trails' first half, before the stars; None: nothing usable, or a flat sky (no trail)."""
    factor = max(1, round(max(plane.shape) / BINNED_SIDE))
    binned, usable = _binned(plane, valid, factor)
    if not usable.any():
        return None
    residual = binned - _background(binned, usable)
    sigma = sigma_from_mad(float(np.median(np.abs(residual[usable] - np.median(residual[usable])))))
    if sigma <= 0:
        return None
    _chords(*binned.shape)  # the Hough's lines, ready for the count
    return BinnedSky(factor, residual, usable, sigma)


def counted(sky: BinnedSky | None, stars: Detections) -> int:
    """trails' second half: the stars masked, the trails counted."""
    if sky is None:
        return 0
    free = sky.usable & ~_star_mask(sky.residual.shape, sky.factor, stars)
    flagged = free & (sky.residual > FLAG_SIGMA * sky.sigma)
    flagged &= ndimage.convolve(flagged.astype(np.int8), _EIGHT, mode="constant") > 1  # not alone
    frame = _Frame(sky.residual, flagged, free, sky.sigma, RUN_SIDE_SHARE * min(free.shape))
    return _count(frame)


def _binned(plane: np.ndarray, valid: np.ndarray, factor: int) -> tuple[np.ndarray, np.ndarray]:
    """Means of factor x factor blocks; usable: every sample valid, 3 binned px from any not."""
    rows, cols = plane.shape[0] // factor * factor, plane.shape[1] // factor * factor
    shape = (rows // factor, factor, cols // factor, factor)
    binned = plane[:rows, :cols].reshape(shape).mean(axis=(1, 3), dtype=np.float64)
    good = np.asarray(valid[:rows, :cols].reshape(shape).all(axis=(1, 3)))
    if good.all():
        return binned, good
    near = ndimage.binary_dilation(~good, np.ones((3, 3), bool), iterations=INVALID_REACH)
    return binned, np.logical_not(near)


def _background(binned: np.ndarray, usable: np.ndarray) -> np.ndarray:
    """Tile medians, bilinear between the tile centres, flat past the outer ones."""
    rows, cols = binned.shape
    ny, nx = -(-rows // TILE_PX), -(-cols // TILE_PX)
    medians = np.full((ny, nx), np.nan)
    for i in range(ny):
        for j in range(nx):
            tile = np.s_[i * TILE_PX : (i + 1) * TILE_PX, j * TILE_PX : (j + 1) * TILE_PX]
            here = binned[tile][usable[tile]]
            if here.size:
                medians[i, j] = np.median(here)
    empty = np.isnan(medians)
    if empty.any():  # a tile of invalid pixels takes its nearest
        nearest = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
        medians = medians[tuple(np.asarray(nearest))]
    at_y = np.interp(np.arange(rows), np.minimum(np.arange(ny) * TILE_PX + TILE_PX / 2 - 0.5,
                                                 rows - 1), np.arange(ny))  # fmt: skip
    at_x = np.interp(np.arange(cols), np.minimum(np.arange(nx) * TILE_PX + TILE_PX / 2 - 0.5,
                                                 cols - 1), np.arange(nx))  # fmt: skip
    grid = np.meshgrid(at_y, at_x, indexing="ij")
    return ndimage.map_coordinates(medians, grid, order=1, mode="nearest")


def _star_mask(shape: tuple[int, ...], factor: int, stars: Detections) -> np.ndarray:
    """Disks of half the box's larger side plus STAR_PAD, BRIGHT_SCALE times the brightest."""
    mask = np.zeros(shape, dtype=bool)
    if len(stars.x) == 0:
        return mask
    box = stars.box
    radius = np.maximum(box[:, 1] - box[:, 0], box[:, 3] - box[:, 2]) / (2 * factor) + STAR_PAD
    radius = np.where(stars.flux >= np.quantile(stars.flux, 1 - BRIGHT_SHARE),
                      radius * BRIGHT_SCALE, radius)  # fmt: skip
    centres_x, centres_y = (stars.x + 0.5) / factor - 0.5, (stars.y + 0.5) / factor - 0.5
    rows, cols = shape
    for x, y, r in zip(centres_x, centres_y, radius, strict=True):
        reach = int(np.ceil(r))
        y0, y1 = max(0, int(y) - reach), min(rows, int(y) + reach + 2)
        x0, x1 = max(0, int(x) - reach), min(cols, int(x) + reach + 2)
        if y0 < y1 and x0 < x1:
            yy, xx = np.ogrid[y0:y1, x0:x1]
            mask[y0:y1, x0:x1] |= (yy - y) ** 2 + (xx - x) ** 2 <= r * r
    return mask


class _Hough:
    """Votes of the flagged pixels per (angle, distance), summed over distance +-NEAR_PX, and how
    many a line of the flagged density would get."""

    def __init__(self, frame: _Frame) -> None:
        rows, cols = frame.flagged.shape
        self.angles, self.offset, self.size = _lines(rows, cols)
        ys, xs = np.nonzero(frame.flagged)
        self.band = self._votes(ys, xs)
        density = len(ys) / max(1, int(frame.open.sum())) * float(frame.open.mean())
        self.expected = density * (2 * NEAR_PX + 1) * _chords(rows, cols)
        # Fewer votes: no run can pass, its open samples the frame's open share of it
        self.least = FLAGGED_SHARE * frame.min_run * float(frame.open.mean())
        self.score = self._score()

    def _score(self) -> np.ndarray:
        """(n - e) / sqrt(e), Poisson on the expected count; -inf where no run can pass."""
        excess = (self.band - self.expected) / np.sqrt(np.maximum(self.expected, 1.0))
        return np.where(self.band >= self.least, excess, -np.inf)

    def _votes(self, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
        votes = np.zeros((len(self.angles), self.size))
        cos, sin = np.cos(self.angles), np.sin(self.angles)
        for a0 in range(0, len(self.angles), 48):  # 48 angles at a time: memory
            a1 = min(len(self.angles), a0 + 48)
            distance = np.rint(np.outer(cos[a0:a1], xs) + np.outer(sin[a0:a1], ys)).astype(np.int64)
            flat = (np.arange(a1 - a0)[:, None] * self.size + distance + self.offset).ravel()
            votes[a0:a1] = np.bincount(flat, minlength=(a1 - a0) * self.size).reshape(a1 - a0, -1)
        band = votes.copy()
        for shift in range(1, NEAR_PX + 1):
            band[:, shift:] += votes[:, :-shift]
            band[:, :-shift] += votes[:, shift:]
        return band

    def best(self) -> tuple[_Line, tuple[int, int]] | None:
        """The most significant line not examined yet; None: none could pass."""
        a, r = np.unravel_index(int(np.argmax(self.score)), self.score.shape)
        if self.score[a, r] == -np.inf:
            return None
        return _Line(float(self.angles[a]), float(r - self.offset)), (int(a), int(r))

    def examined(self, at: tuple[int, int]) -> None:
        """Neighbours of a candidate are the same line; across 0 / 180 degrees distance flips."""
        a, r = at
        angle_reach, shift_reach = round(EXAMINED_REACH[0] / ANGLE_STEP_DEG), EXAMINED_REACH[1]
        self.score[
            max(0, a - angle_reach) : a + angle_reach + 1,
            max(0, r - shift_reach) : r + shift_reach + 1,
        ] = -np.inf
        past = a + angle_reach - (len(self.angles) - 1)
        rows = np.s_[a - angle_reach :] if a < angle_reach else np.s_[:past] if past > 0 else None
        if rows is not None:
            flipped = self.size - 1 - r
            self.score[rows, max(0, flipped - shift_reach) : flipped + shift_reach + 1] = -np.inf

    def remove(self, ys: np.ndarray, xs: np.ndarray) -> None:
        """An accepted trail's votes out; what was examined stays examined."""
        self.band -= self._votes(ys, xs)
        self.score = np.where(self.score == -np.inf, -np.inf, self._score())


def _lines(rows: int, cols: int) -> tuple[np.ndarray, int, int]:
    """The Hough's normal angles, and the offset and count of its distances, for a frame's shape."""
    diagonal = int(np.ceil(np.hypot(rows, cols)))
    return np.deg2rad(np.arange(0.0, 180.0, ANGLE_STEP_DEG)), diagonal + 1, 2 * diagonal + 3


@functools.lru_cache(maxsize=CHORD_SHAPES)
def _chords(rows: int, cols: int) -> np.ndarray:
    """_chord on every Hough line of a shape: the same for every frame of it, kept, read only."""
    angles, offset, size = _lines(rows, cols)
    chords = _chord(angles, np.arange(size, dtype=float) - offset, rows, cols)
    chords.flags.writeable = False
    return chords


def _chord(angles: np.ndarray, distances: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Length of x cos a + y sin a = distance inside [0, cols - 1] x [0, rows - 1]."""
    cos, sin = np.cos(angles)[:, None], np.sin(angles)[:, None]
    low = np.full((len(angles), len(distances)), -np.inf)
    high = np.full_like(low, np.inf)
    for start, step, top in ((distances * cos, -sin, cols - 1), (distances * sin, cos, rows - 1)):
        start, step = np.broadcast_to(start, low.shape), np.broadcast_to(step, low.shape)
        moving = np.abs(step) > 1e-12
        safe = np.where(moving, step, 1.0)
        t0, t1 = -start / safe, (top - start) / safe
        inside = np.where((start >= 0) & (start <= top), np.inf, -np.inf)  # parallel: in or out
        low = np.maximum(low, np.where(moving, np.minimum(t0, t1), -inside))
        high = np.minimum(high, np.where(moving, np.maximum(t0, t1), inside))
    return np.maximum(high - low, 0.0)


def _count(frame: _Frame) -> int:
    hough = _Hough(frame)
    ys, xs = np.nonzero(frame.flagged)
    flagged = frame.flagged.copy()
    found = 0
    for _ in range(MAX_CANDIDATES):
        if found == MAX_TRAILS:
            break
        candidate = hough.best()
        if candidate is None:
            break
        line, at = candidate
        hough.examined(at)
        line = _refined(ys, xs, line)
        if not _accepted(frame, flagged, line):
            continue
        found += 1
        gone = (
            np.abs(xs * np.cos(line.angle) + ys * np.sin(line.angle) - line.distance) <= REMOVED_PX
        )
        flagged[ys[gone], xs[gone]] = False
        hough.remove(ys[gone], xs[gone])
        ys, xs = ys[~gone], xs[~gone]
    return found


def _refined(ys: np.ndarray, xs: np.ndarray, line: _Line) -> _Line:
    """The angle and distance with the most flagged pixels within NEAR_PX; ties: the nearest."""
    near = np.abs(xs * np.cos(line.angle) + ys * np.sin(line.angle) - line.distance) <= 4 * NEAR_PX
    ys, xs = ys[near], xs[near]
    shifts = np.arange(-15, 16) * FINE_SHIFT_PX
    best, chosen = (-1, 0.0), line
    for step in np.arange(-5, 6) * FINE_ANGLE_DEG:
        angle = line.angle + np.deg2rad(step)
        across = np.sort(xs * np.cos(angle) + ys * np.sin(angle))
        centres = line.distance + shifts
        counts = np.searchsorted(across, centres + NEAR_PX, "right") - np.searchsorted(
            across, centres - NEAR_PX, "left"
        )
        for count, shift in zip(counts, shifts, strict=True):
            key = (int(count), -abs(step) - abs(shift))
            if key > best:
                best, chosen = key, _Line(angle, line.distance + float(shift))
    return chosen


def _accepted(frame: _Frame, flagged: np.ndarray, line: _Line) -> bool:
    samples = _run(frame, flagged, line)
    return samples is not None and _thin(frame, line, samples)


def _run(frame: _Frame, flagged: np.ndarray, line: _Line) -> np.ndarray | None:
    """Positions along the line of the longest run, open samples only; None: under min_run."""
    rows, cols = flagged.shape
    cos, sin = np.cos(line.angle), np.sin(line.angle)
    reach = np.hypot(rows, cols)
    t = np.arange(-np.ceil(reach), np.ceil(reach) + 1)
    x, y = line.distance * cos - t * sin, line.distance * sin + t * cos
    inside = (x >= 0) & (x <= cols - 1) & (y >= 0) & (y <= rows - 1)
    t, x, y = t[inside], x[inside], y[inside]
    at = np.rint(y).astype(int), np.rint(x).astype(int)
    keep = frame.open[at]
    t = t[keep]
    if len(t) < RUN_WINDOW:
        return None
    # The sample on the line only: one across too lifts a dense field's noise flags over 35%
    hit = flagged[at][keep]
    dense = np.convolve(hit, np.ones(RUN_WINDOW), "valid") >= FLAGGED_SHARE * RUN_WINDOW
    covered = np.zeros(len(t), dtype=bool)
    for start in np.flatnonzero(dense):
        covered[start : start + RUN_WINDOW] = True
    best: tuple[float, int, int] | None = None
    edges = np.flatnonzero(np.diff(np.concatenate(([0], covered.astype(int), [0]))))
    for a, z in zip(edges[::2], edges[1::2], strict=True):
        hits = a + np.flatnonzero(hit[a:z])
        if len(hits) < FLAGGED_SHARE * (hits[-1] - hits[0] + 1 if len(hits) else 1):
            continue  # windows over 35% overlapping into a run under it: dashes far apart
        if best is None or t[hits[-1]] - t[hits[0]] + 1 > best[0]:
            best = (float(t[hits[-1]] - t[hits[0]] + 1), int(hits[0]), int(hits[-1]))
    if best is None or best[0] < frame.min_run:
        return None
    return t[best[1] : best[2] + 1]


def _thin(frame: _Frame, line: _Line, along: np.ndarray) -> bool:
    """Mean profile across the run: peak on the line PEAK_SIGMA over both sides, the shoulders
    nearer their side than the peak."""
    rows, cols = frame.residual.shape
    cos, sin = np.cos(line.angle), np.sin(line.angle)
    offsets = np.arange(-SIDES[1], SIDES[1] + 1)
    profile = np.full(len(offsets), np.nan)
    for i, k in enumerate(offsets):
        x = np.rint((line.distance + k) * cos - along * sin).astype(int)
        y = np.rint((line.distance + k) * sin + along * cos).astype(int)
        inside = (x >= 0) & (x < cols) & (y >= 0) & (y < rows)
        x, y = x[inside], y[inside]
        free = frame.open[y, x]
        if free.any():
            profile[i] = frame.residual[y[free], x[free]].mean()
    centre = SIDES[1]
    peak = profile[centre]
    sides = (np.nanmean(profile[: SIDES[1] - SIDES[0] + 1]),
             np.nanmean(profile[centre + SIDES[0] :]))  # fmt: skip
    if np.isnan(peak) or np.isnan(sides).any() or int(np.nanargmax(profile)) != centre:
        return False
    if min(peak - sides[0], peak - sides[1]) < PEAK_SIGMA * frame.sigma:
        return False
    shoulders = [(profile[centre + s * d], sides[d > 0]) for d in (-1, 1) for s in SHOULDERS]
    return all(value - side < peak - value for value, side in shoulders)
