"""Oggetto basso (ADR 0039): un esteso sotto 30 gradi, una stella sotto 45, dove il tempo di posa
raddoppia; altezza ignota non si giudica."""

from astrolog.pipeline.frame_rules import LOW_EXTENDED_DEG, LOW_STAR_DEG, low_object


def test_an_extended_object_is_low_under_30_degrees():
    assert (LOW_EXTENDED_DEG, LOW_STAR_DEG) == (30.0, 45.0)
    assert low_object(29.9, star=False) is True
    assert low_object(30.0, star=False) is False
    assert low_object(40.0, star=False) is False


def test_a_star_is_low_under_45_degrees():
    assert low_object(44.9, star=True) is True
    assert low_object(45.0, star=True) is False


def test_an_unknown_altitude_is_not_judged():
    assert low_object(None, star=True) is None
