"""Tilt and off-axis aberration as ASTAP's CCD inspector reads them from the HFDs, and the
sampling class of the FWHM (ADR 0022, ADR 0044, docs/domini/misure.md). software-ok"""

import numpy as np
import pytest

from astrolog.levels import Verdict
from astrolog.pipeline.inspection import SamplingClass, inspect, sampling_class

_COLS, _ROWS = 1200, 900


def _grid(per_side: int = 12) -> tuple[np.ndarray, np.ndarray]:
    """Stars evenly over the frame, none on a third's border."""
    xs = (np.arange(per_side) + 0.5) * _COLS / per_side
    ys = (np.arange(per_side) + 0.5) * _ROWS / per_side
    x, y = np.meshgrid(xs, ys)
    return x.ravel(), y.ravel()


def _corner(x: np.ndarray, y: np.ndarray, right: bool, top: bool) -> np.ndarray:
    across = x > _COLS * 2 / 3 if right else x < _COLS / 3
    along = y > _ROWS * 2 / 3 if top else y < _ROWS / 3
    return across & along


def test_tilt_is_worst_less_best_corner_over_the_frame_median() -> None:
    """One corner wider: 100 (worst - best) / median of every star's HFD."""
    x, y = _grid()
    hfd = np.full(len(x), 3.0)
    hfd[_corner(x, y, right=True, top=True)] = 3.45
    found = inspect(hfd, x, y, (_ROWS, _COLS))
    assert found.tilt_pct == pytest.approx(100 * 0.45 / 3.0)
    assert found.tilt_level is Verdict.MARGINAL


def test_off_axis_is_the_outer_ring_less_the_centre() -> None:
    """Outer ring: past 75% of the way from the centre to a corner; centre: the middle third."""
    x, y = _grid()
    hfd = np.full(len(x), 3.0)
    smx, smy = _COLS / 2, _ROWS / 2
    outer = (x - smx) ** 2 + (y - smy) ** 2 > 0.75**2 * (smx**2 + smy**2)
    hfd[outer] = 4.0
    found = inspect(hfd, x, y, (_ROWS, _COLS))
    assert found.off_axis_px == pytest.approx(1.0)
    assert found.tilt_pct == pytest.approx(0.0)
    assert found.tilt_level is Verdict.GO


def test_stars_smaller_at_the_edge_give_a_negative_off_axis() -> None:
    x, y = _grid()
    hfd = np.where(np.abs(x - _COLS / 2) < _COLS / 6, 3.0, 2.5)
    assert inspect(hfd, x, y, (_ROWS, _COLS)).off_axis_px == pytest.approx(-0.5)


@pytest.mark.parametrize(
    ("pct", "level"),
    [(10.0, Verdict.GO), (10.5, Verdict.MARGINAL), (19.9, Verdict.MARGINAL), (20.0, Verdict.NOGO)],
)
def test_the_tilt_levels_are_the_manuals(pct: float, level: Verdict) -> None:
    """ASTAP: equal or less than 10% good, equal or more than 20% a tilt problem. HFD 2.5: the
    borders come out exact in binary."""
    x, y = _grid()
    hfd = np.full(len(x), 2.5)
    hfd[_corner(x, y, right=False, top=False)] = 2.5 + pct / 40
    found = inspect(hfd, x, y, (_ROWS, _COLS))
    assert found.tilt_pct == pytest.approx(pct)
    assert found.tilt_level is level


def test_an_empty_edge_cell_silences_the_tilt_not_the_off_axis() -> None:
    """ASTAP wants a star in each of the nine areas for the tilt, the centre and ring only for
    the off-axis aberration."""
    x, y = _grid()
    edge = (x > _COLS / 3) & (x < _COLS * 2 / 3) & (y < _ROWS / 3)
    x, y = x[~edge], y[~edge]
    found = inspect(np.full(len(x), 3.0), x, y, (_ROWS, _COLS))
    assert found.tilt_pct is None
    assert found.tilt_level is None
    assert found.off_axis_px == pytest.approx(0.0)


def test_an_empty_centre_silences_both() -> None:
    x, y = _grid()
    centre = (np.abs(x - _COLS / 2) < _COLS / 6) & (np.abs(y - _ROWS / 2) < _ROWS / 6)
    x, y = x[~centre], y[~centre]
    found = inspect(np.full(len(x), 3.0), x, y, (_ROWS, _COLS))
    assert (found.tilt_pct, found.off_axis_px) == (None, None)


def test_no_stars_no_inspection() -> None:
    empty = np.array([])
    found = inspect(empty, empty, empty, (_ROWS, _COLS))
    assert (found.tilt_pct, found.tilt_level, found.off_axis_px) == (None, None, None)


@pytest.mark.parametrize(
    ("fwhm_px", "sampled"),
    [
        (1.4, SamplingClass.SEVERE_UNDER),
        (1.5, SamplingClass.UNDER),
        (1.99, SamplingClass.UNDER),
        (2.0, SamplingClass.IDEAL),
        (3.0, SamplingClass.IDEAL),
        (3.01, SamplingClass.OVER),
    ],
)
def test_the_sampling_classes_of_adr_0022(fwhm_px: float, sampled: SamplingClass) -> None:
    assert sampling_class(fwhm_px) is sampled


def test_no_fwhm_no_sampling_class() -> None:
    assert sampling_class(None) is None
