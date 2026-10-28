"""Massa d'aria e valori allo zenit: Pickering 2002 e la potenza 0,6 dell'ESO, su numeri noti."""

import math

import pytest

from astrolog.pipeline.airmass import airmass_of, apparent_altitude, at_zenith


@pytest.mark.parametrize(
    ("altitude", "expected"),
    [(90.0, 1.0), (30.0, 1.9932), (10.0, 5.5807), (0.0, 38.749)],
)
def test_the_airmass_is_pickering_on_the_apparent_altitude(altitude, expected):
    """Allo zenit 1; a 30 gradi poco sotto 2 (1/sin darebbe 2 esatto); all'orizzonte finita."""
    assert airmass_of(altitude) == pytest.approx(expected, abs=1e-3)
    assert (airmass_of(30.0) or 0) < 1 / math.sin(math.radians(30.0))


@pytest.mark.parametrize(
    ("true", "lift_arcmin"), [(90.0, 0.0), (45.0, 1.01), (10.0, 5.41), (0.0, 28.98)]
)
def test_the_refraction_lifts_a_low_star_saemundsson(true, lift_arcmin):
    """Meeus 1998 eq. 16.4, aria a 1010 hPa e 10 C: 29' all'orizzonte, 1' a 45 gradi."""
    assert (apparent_altitude(true) - true) * 60 == pytest.approx(lift_arcmin, abs=0.02)


def test_well_under_the_horizon_the_refraction_stops():
    """Sotto -1 grado la formula si piega (a -5 tornerebbe a zero): niente alzata, e' tramontata."""
    assert apparent_altitude(-3.0) == -3.0
    assert airmass_of(apparent_altitude(-1.0)) is None


@pytest.mark.parametrize("altitude", [-0.5, -30.0])
def test_under_the_horizon_there_is_no_airmass(altitude):
    assert airmass_of(altitude) is None


def test_a_value_at_the_zenith_is_divided_by_the_airmass_to_the_three_fifths():
    """ESO: seeing(zenit) = seeing(misurato) / airmass^0,6."""
    assert at_zenith(3.0, 2.0) == pytest.approx(3.0 / 2.0**0.6)
    assert at_zenith(3.0, 1.0) == 3.0


@pytest.mark.parametrize(("value", "airmass"), [(None, 1.5), (3.0, None), (None, None)])
def test_without_value_or_airmass_there_is_no_zenith(value, airmass):
    assert at_zenith(value, airmass) is None
