"""Altezza di un punto fisso del cielo con erfa, senza astropy nella pipeline (ADR 0030); astropy
qui fa solo da oracolo."""

import datetime as dt

import pytest
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from astrolog.pipeline.altitude import true_altitudes

_SITE = (45.494, 11.5218)


@pytest.mark.parametrize(
    ("sky", "when"),
    [
        ((241.25, 17.73), dt.datetime(2025, 6, 29, 21, 32, 30, tzinfo=dt.UTC)),
        ((0.0, -44.0), dt.datetime(2026, 10, 15, 22, 0, tzinfo=dt.UTC)),  # radente
        (
            (83.8, -5.4),
            dt.datetime(2031, 1, 5, 23, 0, tzinfo=dt.UTC),
        ),  # oltre i secondi intercalari
    ],
)
@pytest.mark.filterwarnings("ignore::erfa.ErfaWarning")  # l'oracolo, oltre la tabella dei secondi
def test_the_altitude_agrees_with_astropy(sky, when):
    """Geometrica: astropy senza pressione; UT1 come UTC sbaglia meno di un centesimo di grado."""
    frame = AltAz(obstime=Time(when), location=EarthLocation(lat=_SITE[0], lon=_SITE[1]))
    expected = SkyCoord(ra=sky[0], dec=sky[1], unit="deg").transform_to(frame).alt.deg  # pyright: ignore[reportOptionalMemberAccess]
    [found] = true_altitudes([sky], [when], [_SITE])
    assert found == pytest.approx(float(expected), abs=0.01)  # pyright: ignore[reportArgumentType]


def test_many_points_go_in_one_call_each_with_its_own_instant_and_site():
    """Il polo sta alla latitudine del sito, piu' o meno la precessione dal J2000."""
    when = dt.datetime(2026, 10, 15, 22, 0, tzinfo=dt.UTC)
    found = true_altitudes([(0.0, 90.0)] * 2, [when] * 2, [(45.0, 11.5), (-45.0, 11.5)])
    assert found == pytest.approx([45.0, -45.0], abs=0.5)


def test_no_point_no_call():
    assert true_altitudes([], [], []) == []


def test_an_instant_without_zone_is_refused():
    with pytest.raises(ValueError, match="fuso"):
        true_altitudes([(0.0, 0.0)], [dt.datetime(2026, 1, 1)], [_SITE])
