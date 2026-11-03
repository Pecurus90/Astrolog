"""Star shape on synthetic stars of known shape (ADR 0042, misure.md Forma): FWHM, eccentricity,
PSF residual, their spread and the direction, through measure_frame as the pipeline calls it."""

import math

import numpy as np
import pytest

from astrolog.pipeline import shape, stars
from astrolog.pipeline.psf_fit import Fitted
from astrolog.pipeline.shape import Shape, ShapeKind
from astrolog.pipeline.stars import Measured, TooFewStars, measure_frame

_SIDE = 600
_BACKGROUND = 1000.0
_NOISE = 10.0
_SUB = 5  # samples per pixel side: the star integrated on the pixel


def _moffat_fwhm(alpha: float, beta: float) -> float:
    return 2 * alpha * math.sqrt(2 ** (1 / beta) - 1)


def _stamp(radius: int, profile) -> np.ndarray:
    side = 2 * radius + 1
    fine = (np.arange(side * _SUB) + 0.5) / _SUB - 0.5 - radius
    yy, xx = np.meshgrid(fine, fine, indexing="ij")
    binned = profile(xx, yy).reshape(side, _SUB, side, _SUB).sum(axis=(1, 3))
    return binned / binned.sum()


def _moffat(major: float, ratio: float, angle_deg: float, beta: float):
    """Elliptical Moffat, `major` the alpha of the long axis at `angle_deg` from +x towards +y."""
    c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    minor = major * ratio

    def profile(xx: np.ndarray, yy: np.ndarray) -> np.ndarray:
        along, across = c * xx + s * yy, -s * xx + c * yy
        return (1 + (along / major) ** 2 + (across / minor) ** 2) ** -beta

    return profile


def _gauss(sigma: float):
    return lambda xx, yy: np.exp(-(xx**2 + yy**2) / (2 * sigma**2))


def _doughnut(radius: float, width: float):
    return lambda xx, yy: np.exp(-((np.hypot(xx, yy) - radius) ** 2) / (2 * width**2))


def _field(profiles: list, *, reach: int = 30, flux: float = 60000.0, seed: int = 1) -> np.ndarray:
    """One star per profile on a grid, `reach` px of room each, flat sky with Gaussian noise."""
    rng = np.random.default_rng(seed)
    data = np.full((_SIDE, _SIDE), _BACKGROUND)
    per_side = math.ceil(math.sqrt(len(profiles)))
    step = (_SIDE - 2 * (reach + 20)) // max(per_side - 1, 1)
    for k, profile in enumerate(profiles):
        y, x = reach + 20 + (k // per_side) * step, reach + 20 + (k % per_side) * step
        data[y - reach : y + reach + 1, x - reach : x + reach + 1] += flux * _stamp(reach, profile)
    data += rng.normal(0, _NOISE, data.shape)
    return data.astype(np.float32)


def _shape(data: np.ndarray, pattern: str | None = None) -> Shape:
    found = measure_frame(data, saturation=65535.0, pattern=pattern)
    assert found.shape is not None, found
    return found.shape


@pytest.mark.parametrize(("alpha", "wider"), [(3.0, 0.05), (6.0, 0.02)])
def test_round_moffat_stars_give_their_fwhm(alpha: float, wider: float) -> None:
    """Beta 4, the fitted function. Fitted at the pixel centres, as Image Analysis: a star binned
    on its pixels reads wider by the pixel, +4% at FWHM 2.6 px, +1% at 5.2. software-ok"""
    found = _shape(_field([_moffat(alpha, 1.0, 0, 4.0)] * 49))
    assert found.kind is ShapeKind.FITTED
    truth = _moffat_fwhm(alpha, 4.0)
    assert found.fwhm_px is not None and truth < found.fwhm_px < (1 + wider) * truth
    assert found.eccentricity is not None and found.eccentricity < 0.15
    assert found.angle_deg is None
    assert found.psf_residual is not None and found.psf_residual < 0.02


@pytest.mark.parametrize(
    ("star", "low", "high"), [("moffat 2.5", 1.05, 1.12), ("gauss", 0.92, 0.97)]
)
def test_other_profiles_read_as_a_moffat_4_reads_them(star: str, low: float, high: float) -> None:
    """Wider wings than beta 4 widen the fit, a Gaussian narrows it, and the residual says the
    function does not follow the star: as Image Analysis with its default PSF type."""
    profile, truth = _moffat(2.5, 1.0, 0, 2.5), _moffat_fwhm(2.5, 2.5)
    if star == "gauss":
        profile, truth = _gauss(1.8), 2.3548 * 1.8
    found = _shape(_field([profile] * 49))
    exact = _shape(_field([_moffat(3.0, 1.0, 0, 4.0)] * 49))
    assert found.fwhm_px is not None and low * truth < found.fwhm_px < high * truth
    assert found.psf_residual is not None and exact.psf_residual is not None
    assert found.psf_residual > 2 * exact.psf_residual


def test_the_spread_is_the_qn_of_the_stars() -> None:
    """FWHM from 2.6 to 4.4 px across the field: a spread; one FWHM: next to none."""
    varied = _shape(_field([_moffat(3.0 + 2.0 * k / 48, 1.0, 0, 4.0) for k in range(49)]))
    same = _shape(_field([_moffat(4.0, 1.0, 0, 4.0)] * 49))
    assert varied.spread is not None and same.spread is not None
    assert varied.spread.fwhm_px is not None and same.spread.fwhm_px is not None
    assert varied.spread.fwhm_px > 0.3 > 10 * same.spread.fwhm_px


@pytest.mark.parametrize(("ratio", "angle"), [(0.866, 30.0), (0.6, 120.0), (0.6, 0.0)])
def test_elongated_stars_give_eccentricity_and_direction(ratio: float, angle: float) -> None:
    found = _shape(_field([_moffat(4.0, ratio, angle, 4.0)] * 49))
    assert found.kind is ShapeKind.FITTED
    assert found.eccentricity == pytest.approx(math.sqrt(1 - ratio**2), abs=0.03)
    assert found.fwhm_px == pytest.approx(_moffat_fwhm(4.0 * math.sqrt(ratio), 4.0), rel=0.05)
    assert found.angle_deg is not None
    gap = abs(found.angle_deg - angle) % 180
    assert min(gap, 180 - gap) < 3.0


def test_trailed_stars_have_a_shape_even_with_too_few_round_ones() -> None:
    """b/a 0.25: none round enough for the HFD (sep's b/a 0.5), the shape says how long."""
    data = _field([_moffat(5.0, 0.25, 45, 4.0)] * 49, flux=200000.0)
    found = measure_frame(data, saturation=65535.0, pattern=None)
    assert isinstance(found, TooFewStars)
    assert found.shape is not None and found.shape.kind is ShapeKind.FITTED
    assert found.shape.eccentricity == pytest.approx(math.sqrt(1 - 0.25**2), abs=0.03)


def test_lines_instead_of_stars_are_an_unmeasurable_shape() -> None:
    """From eccentricity 0.99. Real lines rarely get here: the detector drops them."""
    lines = Fitted(np.full(9, 3.0), np.full(9, 0.995), np.full(9, 10.0), np.full(9, 0.01),
                   np.ones(9), np.ones(9), np.arange(9))  # fmt: skip
    found = shape._frame(ShapeKind.FITTED, lines)
    assert found == Shape(ShapeKind.UNMEASURABLE, 9, None, None, None)


def test_doughnuts_are_an_unmeasurable_shape() -> None:
    found = _shape(_field([_doughnut(8.0, 1.5)] * 36, flux=300000.0))
    assert found.kind is ShapeKind.UNMEASURABLE
    assert found.fwhm_px is None


def test_directions_that_disagree_give_no_direction() -> None:
    """Half the stars long in x, half in y (coma, tilt): elongated, but no one direction."""
    profiles = [_moffat(3.0, 0.6, 0 if k % 2 else 90, 3.0) for k in range(50)]
    found = _shape(_field(profiles))
    assert found.eccentricity is not None and found.eccentricity > 0.4
    assert found.angle_deg is None


def test_a_direction_is_one_the_rayleigh_test_holds_at_five_percent() -> None:
    """Axial Rayleigh test (Zar 27.1): 21 of 30 stars at 10 degrees, 9 at 100, mean length 0.4,
    p 0.008: a direction. 4 of 5 at 10, 1 at 100, length 0.6, p 0.17: none."""
    many = shape._direction([10.0] * 21 + [100.0] * 9)
    assert many is not None and many == pytest.approx(10.0, abs=0.01)
    assert shape._direction([10.0] * 4 + [100.0]) is None


@pytest.mark.parametrize("degrees", [-1e-15, 180.0, 360.0 - 1e-13, -180.0])
def test_an_angle_folds_into_0_to_180_never_180_itself(degrees: float) -> None:
    """-1e-15 % 180 is 180.0 in floats, and the schema refuses 180."""
    assert 0.0 <= shape.folded(degrees) < 180.0
    direction = shape._direction([degrees] * 5)
    assert direction is not None and 0.0 <= direction < 180.0


def test_a_fit_that_fails_falls_back_on_the_moments_and_says_so(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """sep's moments on the median copy read the wings: a Moffat beta 3 comes out 1.5 times
    its FWHM. Estimated, and said so."""
    monkeypatch.setattr(stars, "fit_stars", lambda *_: Fitted(*(np.empty(0),) * 7))
    found = _shape(_field([_moffat(3.0, 0.7, 60, 3.0)] * 49))
    assert found.kind is ShapeKind.ESTIMATED
    assert found.psf_residual is None and found.spread is not None
    truth = _moffat_fwhm(3.0 * math.sqrt(0.7), 3.0)
    assert found.fwhm_px is not None and truth < found.fwhm_px < 1.7 * truth
    assert found.eccentricity == pytest.approx(math.sqrt(1 - 0.7**2), abs=0.1)


def _mosaic(r: float, g: float, b: float) -> np.ndarray:
    return np.tile(np.array([[r, g], [g, b]], dtype=np.float32), (_SIDE // 2, _SIDE // 2))


@pytest.mark.parametrize(("alpha", "wider"), [(4.0, 0.05), (2.0, 0.3)])
def test_round_colour_stars_stay_round_after_vng(alpha: float, wider: float) -> None:
    """VNG widens small stars, as WBPP sees them: FWHM 3.5 px +4%, 1.8 px +28%. software-ok"""
    data = _field([_moffat(alpha, 1.0, 0, 4.0)] * 49) * _mosaic(0.82, 1.0, 0.83)
    found = _shape(data, pattern="RGGB")
    assert found.eccentricity is not None and found.eccentricity < 0.15
    truth = _moffat_fwhm(alpha, 4.0)
    assert found.fwhm_px is not None and truth < found.fwhm_px < (1 + wider) * truth


def test_an_eight_bit_frame_is_fitted_on_its_steps() -> None:
    data = np.round(_field([_moffat(3.0, 1.0, 0, 4.0)] * 49, flux=3000.0) / 40)
    found = measure_frame(data.astype(np.float32), saturation=255.0, pattern=None)
    assert isinstance(found, Measured) and found.shape is not None
    assert found.shape.fwhm_px == pytest.approx(_moffat_fwhm(3.0, 4.0), rel=0.05)
