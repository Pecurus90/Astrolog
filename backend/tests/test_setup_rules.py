"""Regole rispetto al setup (ADR 0039): eccentricita' scartata da una coda sola, l'avviso "stelle
allungate", e la soglia delle raffiche tarata sulla FWHM dei frame del setup."""

import math

import pytest

from astrolog.pipeline.setup_rules import (
    ELONGATED_ECCENTRICITY,
    eccentricity_outliers,
    elongated_stars,
    gust_limits,
)
from astrolog.robust import qn


def test_elongated_is_b_over_a_08():
    """b/a 0,8 e' eccentricita' 0,6: sqrt(1 - 0,8^2)."""
    assert pytest.approx(math.sqrt(1 - 0.8**2)) == ELONGATED_ECCENTRICITY


def test_only_the_long_tail_is_out():
    """Una coda: stelle piu' tonde del solito non sono uno scarto."""
    values = [0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.05, 0.90]
    assert eccentricity_outliers(values) == {11}


def test_the_outliers_need_ten_frames():
    assert eccentricity_outliers([0.4] * 8 + [0.9]) == set()


def test_elongated_from_the_setup_median():
    """La mediana del setup oltre 0,6 accende l'avviso; sotto 10 frame non si dice."""
    assert elongated_stars([0.65] * 10) is True
    assert elongated_stars([0.55] * 10) is False
    assert elongated_stars([0.65] * 9) is None


def _frames(calm: float, c: float, gusts: list[float]) -> list[tuple[float, float]]:
    return [(v, math.sqrt(calm**2 + c * v**4)) for v in gusts]


def test_the_gust_limits_where_the_time_doubles_and_quadruples():
    """FWHM^2 = calma^2 + c v^4: incerto dove la FWHM e' sqrt2 volte la calma (tempo x2), niente
    dove e' doppia, come il seeing rispetto al pavimento del setup."""
    calm, c = 2.0, 4e-5
    limits = gust_limits(_frames(calm, c, [float(v) for v in range(0, 60, 4)]))
    assert limits is not None
    assert limits.calm_fwhm == pytest.approx(calm)
    assert limits.uncertain_kmh == pytest.approx((calm**2 / c) ** 0.25)
    assert limits.unusable_kmh == pytest.approx((3 * calm**2 / c) ** 0.25)


def test_the_gust_limits_are_not_extrapolated():
    """Se il vento misurato non arriva alla soglia, i frame non bastano: resta il 25 km/h."""
    assert gust_limits(_frames(2.0, 4e-5, [float(v) for v in range(0, 16, 2)])) is None
    short = gust_limits(_frames(2.0, 4e-5, [float(v) for v in range(0, 20, 2)]))
    assert short is not None
    assert short.unusable_kmh is None


def test_the_gust_limits_need_ten_frames_and_a_growth():
    assert gust_limits(_frames(2.0, 4e-5, [0, 10, 20, 30, 40, 50, 55, 60, 65])) is None
    assert gust_limits([(float(v), 2.0) for v in range(0, 60, 5)]) is None


def test_the_gust_fit_ignores_a_bad_frame():
    """Un frame con le nuvole non sposta la soglia: il fit e' robusto (Theil-Sen)."""
    frames = _frames(2.0, 4e-5, [float(v) for v in range(0, 60, 4)])
    frames[1] = (frames[1][0], 9.0)
    limits = gust_limits(frames)
    assert limits is not None
    assert limits.uncertain_kmh == pytest.approx((2.0**2 / 4e-5) ** 0.25, rel=0.05)


def test_qn_is_the_scale_of_the_setup():
    """La soglia dell'eccentricita' e' mediana + 2,5 Qn, la stessa dello scarto dei frame."""
    values = [0.40 + 0.01 * i for i in range(10)] + [0.70]
    scale = qn(values)
    assert scale is not None
    assert (10 in eccentricity_outliers(values)) == (0.45 + 2.5 * scale < 0.70)
