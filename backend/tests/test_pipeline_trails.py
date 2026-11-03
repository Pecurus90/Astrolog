"""Trails of satellites, aircraft and meteors as Image Analysis counts them (par. 2.1.3)."""

import numpy as np
from scipy import ndimage  # pyright: ignore[reportMissingTypeStubs]

from astrolog.pipeline.background import valid_pixels
from astrolog.pipeline.detect import Detections
from astrolog.pipeline.trails import MAX_TRAILS, trails

_NOISE = 10.0
_ROWS, _COLS = 600, 900  # under 1500 px: binned by 1
_CEILING = 65535.0


def _sky(seed: int = 1, dense: bool = False) -> np.ndarray:
    """Noise 10 on 1000; dense: unresolved stars under the detection, PSF sigma 1.5, over 7% of
    the pixels, lifting the dispersion to about twice the noise."""
    rng = np.random.default_rng(seed)
    sky = rng.normal(1000.0, _NOISE, (_ROWS, _COLS))
    if dense:
        dots = np.zeros_like(sky)
        n = _ROWS * _COLS // 15
        np.add.at(dots, (rng.integers(0, _ROWS, n), rng.integers(0, _COLS, n)),
                  rng.exponential(300.0, n))  # fmt: skip
        sky += ndimage.gaussian_filter(dots, 1.5)
    return sky


def _no_stars() -> Detections:
    empty = np.array([])
    return Detections(empty, empty, empty.astype(bool), empty, np.zeros((0, 4), dtype=int))


def _stars(sky: np.ndarray, places: list[tuple[float, float]], flux: float) -> Detections:
    """Gaussian stars of sigma 1.5, their structure boxes 11 px across."""
    rows, cols = np.mgrid[0 : sky.shape[0], 0 : sky.shape[1]]
    for x, y in places:
        sky += flux / (2 * np.pi * 2.25) * np.exp(-((cols - x) ** 2 + (rows - y) ** 2) / 4.5)
    x, y = np.array(places, dtype=float).T
    box = np.column_stack([x - 5, x + 6, y - 5, y + 6]).astype(int)
    return Detections(x, y, np.zeros(len(x), dtype=bool), np.full(len(x), flux), box)


def _trail(
    sky: np.ndarray,
    peak: float,
    angle_deg: float,
    *,
    shift: float = 0.0,
    length: float = 0.0,
    width: float = 1.0,
) -> None:
    """A line through the centre moved `shift` px across it, Gaussian profile of sigma `width`;
    `length` px long around the centre, 0 across the frame."""
    rows, cols = np.mgrid[0 : sky.shape[0], 0 : sky.shape[1]]
    t = np.deg2rad(angle_deg)
    x, y = cols - sky.shape[1] / 2, rows - sky.shape[0] / 2
    across = x * np.cos(t) + y * np.sin(t) - shift
    profile = peak * np.exp(-across * across / (2 * width * width))
    if length:
        profile[np.abs(-x * np.sin(t) + y * np.cos(t)) > length / 2] = 0.0
    sky += profile


def _count(sky: np.ndarray, stars: Detections | None = None) -> int:
    return trails(sky, valid_pixels(sky, _CEILING), stars or _no_stars())


def test_a_sky_without_trails_has_none() -> None:
    assert _count(_sky()) == 0
    assert _count(_sky(dense=True)) == 0


def test_a_trail_four_times_the_noise_is_found_in_any_field() -> None:
    """Doc: synthetic trails peaking at four times the noise were detected in all frames."""
    for dense in (False, True):
        for angle in (5.0, 37.0, 90.0, 133.0):
            sky = _sky(dense=dense)
            _trail(sky, 4 * _NOISE, angle)
            assert _count(sky) == 1, (dense, angle)


def test_a_trail_twice_the_noise_is_lost_in_a_dense_field_found_in_a_sparse_one() -> None:
    """Doc: twice the noise lost where unresolved stars lift the dispersion, found where sparse.
    Seed 3: counting flags 1 px beside the line too passed 35% on noise."""
    for seed in (1, 3):
        dense = _sky(seed, dense=True)
        _trail(dense, 2 * _NOISE, 37.0)
        assert _count(dense) == 0, seed
    sparse = _sky()
    _trail(sparse, 2 * _NOISE, 37.0)
    assert _count(sparse) == 1


def test_a_meteor_shorter_than_a_quarter_of_the_short_side_is_not_counted() -> None:
    """Short side 600: a quarter is 150 px."""
    short, long = _sky(), _sky()
    _trail(short, 8 * _NOISE, 20.0, length=120)
    _trail(long, 8 * _NOISE, 20.0, length=200)
    assert _count(short) == 0
    assert _count(long) == 1


def test_a_run_needs_35_percent_flagged_over_its_whole_length() -> None:
    """Dashes of 9 px every 41 px: each 25 px window over 35%, the run 22%."""
    sky = _sky()
    _trail(sky, 8 * _NOISE, 90.0)
    gaps = (np.arange(_COLS) % 41) >= 9
    sky[_ROWS // 2 - 6 : _ROWS // 2 + 7, gaps] = _sky(seed=2)[_ROWS // 2 - 6 : _ROWS // 2 + 7, gaps]
    assert _count(sky) == 0


def test_a_nebula_edge_and_a_wide_filament_are_not_trails() -> None:
    """Doc: the thin profile rejects the edges and filaments of nebulae."""
    edge, filament = _sky(), _sky()
    edge[:, _COLS // 2 :] += 3 * _NOISE
    _trail(filament, 6 * _NOISE, 70.0, width=6.0)
    assert _count(edge) == 0
    assert _count(filament) == 0


def test_two_crossing_trails_are_two() -> None:
    sky = _sky()
    _trail(sky, 5 * _NOISE, 30.0)
    _trail(sky, 5 * _NOISE, 110.0, shift=40)
    assert _count(sky) == 2


def test_no_more_than_sixteen_trails_a_frame() -> None:
    sky = _sky()
    for k in range(20):  # columns 50 to 810
        _trail(sky, 8 * _NOISE, 0.0, shift=-400 + 40 * k)
    assert _count(sky) == MAX_TRAILS


def test_a_trail_through_masked_stars_keeps_its_run() -> None:
    """Stars every 40 px along the line: masked, they neither start nor interrupt the run."""
    sky = _sky()
    places = [(_COLS / 2 + d, _ROWS / 2) for d in range(-400, 401, 40)]
    stars = _stars(sky, places, 50_000.0)
    _trail(sky, 4 * _NOISE, 90.0)
    assert _count(sky, stars) == 1


def test_an_empty_border_is_not_a_trail() -> None:
    """A dark band of a cut frame and its edge: invalid, not a line."""
    sky = _sky()
    sky[:, :60] = 0.0
    assert _count(sky) == 0
