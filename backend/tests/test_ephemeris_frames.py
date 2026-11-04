"""**La Luna e il Sole su una posa** (Image Analysis par. 2.1.1): altezze topocentriche senza
rifrazione, distanza della Luna dal centro, frazione illuminata; tutte le pose in una chiamata
per sito. Le date sono nel futuro, come negli altri file delle effemeridi."""

import datetime as dt

import pytest
from astropy.coordinates import EarthLocation, get_body
from astropy.time import Time

from astrolog.ephemeris import moon, sun
from astrolog.ephemeris.frames import moon_and_sun

pytestmark = pytest.mark.filterwarnings("ignore:Tried to get polar motions:")

CASA = (45.5455, 11.5354)  # Vicenza
SUD = (-33.87, 151.21)  # Sydney
QUANDO = [
    dt.datetime(2027, 3, 14, 21, 0, tzinfo=dt.UTC),
    dt.datetime(2027, 3, 22, 2, 0, tzinfo=dt.UTC),
]


def test_the_altitudes_are_the_ones_of_the_night_chart():
    """Stesse effemeridi della curva della notte: un fatto, una casa."""
    found = moon_and_sun(QUANDO, [CASA] * 2, [None, None])
    assert [f.moon_altitude_deg for f in found] == pytest.approx(moon.altitudes(QUANDO, *CASA))
    assert [f.sun_altitude_deg for f in found] == pytest.approx(sun.altitudes(QUANDO, *CASA))


def test_the_illumination_is_the_phase_unrounded():
    """Frazione 0-1, la stessa luce della fase (che la porta in percento intero)."""
    found = moon_and_sun(QUANDO, [CASA] * 2, [None, None])
    for f, p in zip(found, moon.phases(QUANDO), strict=True):
        assert 0 <= f.moon_illumination <= 1
        assert f.moon_illumination * 100 == pytest.approx(p.illumination_pct, abs=0.5)


def test_a_frame_on_the_moon_is_at_no_distance_from_it():
    """Il centro messo dove si vede la Luna dal sito: separazione zero (l'aberrazione, secondi
    d'arco); senza centro, nessuna."""
    when = QUANDO[0]
    seen = get_body("moon", Time(when), EarthLocation(lat=CASA[0], lon=CASA[1]))
    centre = (float(seen.ra.deg), float(seen.dec.deg))  # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]
    [on, away] = moon_and_sun([when] * 2, [CASA] * 2, [centre, None])
    assert on.moon_separation_deg is not None and on.moon_separation_deg < 0.05
    assert away.moon_separation_deg is None


def test_the_parallax_of_the_moon_counts():
    """Topocentrica: lo stesso centro dista dalla Luna fino a un grado in piu' o in meno da un
    altro sito della Terra (Image Analysis par. 2.1.1)."""
    when = QUANDO[0]
    centre = (0.0, 0.0)
    [here, there] = moon_and_sun([when] * 2, [CASA, SUD], [centre] * 2)
    assert here.moon_separation_deg is not None and there.moon_separation_deg is not None
    assert 0.1 < abs(here.moon_separation_deg - there.moon_separation_deg) < 2.0


def test_each_site_keeps_its_own_frames_in_order():
    found = moon_and_sun(QUANDO + QUANDO, [CASA, SUD, SUD, CASA], [None] * 4)
    alone = moon_and_sun(QUANDO, [CASA, SUD], [None] * 2)
    assert found[0] == alone[0]
    assert found[1] == alone[1]
    assert found[3].moon_altitude_deg == pytest.approx(moon.altitudes([QUANDO[1]], *CASA)[0])


def test_no_frame_no_call():
    assert moon_and_sun([], [], []) == []
