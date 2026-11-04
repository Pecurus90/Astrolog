"""Altezza, azimut e angolo orario di un punto fisso del cielo con erfa (ADR 0030); astropy qui
fa solo da oracolo."""

import datetime as dt
from typing import Any

import pytest
from astropy.coordinates import TETE, AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from astrolog.pipeline.altitude import observed

_SITE = (45.494, 11.5218)
_SKIES = [
    ((241.25, 17.73), dt.datetime(2025, 6, 29, 21, 32, 30, tzinfo=dt.UTC)),
    ((0.0, -44.0), dt.datetime(2026, 10, 15, 22, 0, tzinfo=dt.UTC)),  # radente
    ((83.8, -5.4), dt.datetime(2031, 1, 5, 23, 0, tzinfo=dt.UTC)),  # oltre i secondi intercalari
]


def _oracle(sky, when) -> SkyCoord:
    frame = AltAz(obstime=Time(when), location=EarthLocation(lat=_SITE[0], lon=_SITE[1]))
    return SkyCoord(ra=sky[0], dec=sky[1], unit="deg").transform_to(frame)


@pytest.mark.parametrize(("sky", "when"), _SKIES)
@pytest.mark.filterwarnings("ignore::erfa.ErfaWarning")  # l'oracolo, oltre la tabella dei secondi
def test_the_altitude_and_azimuth_agree_with_astropy(sky, when):
    """Geometriche: astropy senza pressione; UT1 come UTC sbaglia meno di un centesimo di grado."""
    expected = _oracle(sky, when)
    [found] = observed([sky], [when], [_SITE])
    assert found.altitude_deg == pytest.approx(float(expected.alt.deg), abs=0.01)  # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]
    assert found.azimuth_deg == pytest.approx(float(expected.az.deg), abs=0.01)  # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]


@pytest.mark.parametrize(("sky", "when"), _SKIES)
@pytest.mark.filterwarnings("ignore::erfa.ErfaWarning")
def test_the_hour_angle_is_the_apparent_sidereal_time_less_the_place_of_date(sky, when):
    """Image Analysis par. 2.1.1: H = tempo siderale apparente + longitudine - AR di data, in ore
    fra -12 e +12."""
    t = Time(when)
    tete = SkyCoord(ra=sky[0], dec=sky[1], unit="deg").transform_to(TETE(obstime=t))
    local: Any = t.sidereal_time("apparent", longitude=_SITE[1]).hour
    place: Any = tete.ra.hour  # pyright: ignore[reportOptionalMemberAccess]
    expected = (local - place + 12) % 24 - 12
    [found] = observed([sky], [when], [_SITE])
    assert -12 <= found.hour_angle_h < 12
    assert found.hour_angle_h == pytest.approx(float(expected), abs=0.001)


def test_before_the_transit_the_hour_angle_is_negative_and_the_azimuth_east():
    """Un'ora prima del transito: H -1, l'oggetto a Est del meridiano (azimut sotto 180)."""
    when = dt.datetime(2026, 10, 15, 22, 0, tzinfo=dt.UTC)
    [now] = observed([(0.0, 30.0)], [when], [_SITE])
    ra = (now.hour_angle_h + 1) * 15 % 360  # H = sidereal time - RA
    [found] = observed([(ra, 30.0)], [when], [_SITE])
    assert found.hour_angle_h == pytest.approx(-1.0, abs=0.01)
    assert 0 < found.azimuth_deg < 180


def test_many_points_go_in_one_call_each_with_its_own_instant_and_site():
    """Il polo sta alla latitudine del sito, piu' o meno la precessione dal J2000."""
    when = dt.datetime(2026, 10, 15, 22, 0, tzinfo=dt.UTC)
    found = observed([(0.0, 90.0)] * 2, [when] * 2, [(45.0, 11.5), (-45.0, 11.5)])
    assert [f.altitude_deg for f in found] == pytest.approx([45.0, -45.0], abs=0.5)


def test_no_point_no_call():
    assert observed([], [], []) == []


def test_an_instant_without_zone_is_refused():
    with pytest.raises(ValueError, match="fuso"):
        observed([(0.0, 0.0)], [dt.datetime(2026, 1, 1)], [_SITE])
