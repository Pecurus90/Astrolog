"""**Skyfield contro astropy**: le effemeridi dell'app (Skyfield, DE421 del JPL) e un'altra
implementazione indipendente (astropy, modello incorporato) dicono lo stesso cielo, entro
tolleranze scritte qui (ADR 0046).

Le tolleranze nascono dalla misura del 20/11/2026 (2 mesi a 3 minuti, 4 siti): Sole entro 3,1",
Luna entro 9,7" (l'errore del modello di astropy, non di DE421); orari del Sole entro 0,23 s,
della Luna entro 2,4 s (a 64 gradi nord, dove sale piu' radente). La soglia degli orari e' **5 s**,
quella del passo del piano: sotto il minuto a cui si arrotondano a schermo, sopra lo scarto vero.

astropy resta per i test (i FITS di prova), quindi l'oracolo costa zero; il suo download dei dati
della Terra lo disarma `conftest.py`: la suite gira senza rete.
"""

import datetime as dt

import numpy as np
import pytest
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    GeocentricMeanEcliptic,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time

from astrolog.ephemeris import RISESET_DEG, bodies, moon
from astrolog.ephemeris.frames import moon_and_sun
from astrolog.ephemeris.grid import first_crossing, night_grid

# Oltre i dati di rotazione della Terra di astropy: l'avviso e' il prezzo detto dell'oracolo.
pytestmark = pytest.mark.filterwarnings("ignore:Tried to get polar motions:")

ORARI_S = 5.0
ALTEZZA_ARCSEC = 30.0
CASA = (45.5455, 11.5354)  # Vicenza
SITI = [CASA, (-33.87, 151.21), (64.1, -21.9), (19.8, -155.5)]  # Sydney, Reykjavik, Mauna Kea
INIZIO = dt.datetime(2027, 3, 14, 12, tzinfo=dt.UTC)


def _astropy(
    corpo: bodies.Body, istanti: list[dt.datetime], dove: tuple[float, float]
) -> np.ndarray:
    sito = EarthLocation(lat=dove[0], lon=dove[1])
    tempi = Time(istanti)
    visto = get_sun(tempi) if corpo == "sun" else get_body(corpo, tempi, sito)
    return np.asarray(visto.transform_to(AltAz(obstime=tempi, location=sito)).alt.deg)  # pyright: ignore[reportOptionalMemberAccess]


def _scarti_orari(corpo: bodies.Body, dove: tuple[float, float], giorni: int) -> list[float]:
    """Sorgere e tramonto giorno per giorno, sulla stessa griglia e con la stessa soglia."""
    istanti = night_grid(INIZIO, hours=24 * giorni, step_min=3)
    nostre = bodies.body_altitudes(corpo, istanti, *dove)
    loro = list(_astropy(corpo, istanti, dove))
    giorno = 24 * 60 // 3
    scarti = []
    for k in range(0, len(istanti) - giorno, giorno):
        fetta = slice(k, k + giorno + 1)
        for verso in ("up", "down"):
            a = first_crossing(istanti[fetta], nostre[fetta], RISESET_DEG, verso)
            b = first_crossing(istanti[fetta], loro[fetta], RISESET_DEG, verso)
            assert (a is None) == (b is None), (corpo, dove, istanti[k], verso)
            if a and b:
                scarti.append(abs((a - b).total_seconds()))
    return scarti


@pytest.mark.parametrize("corpo", ["sun", "moon"])
def test_rise_and_set_agree_with_astropy_within_five_seconds(corpo):
    scarti = _scarti_orari(corpo, CASA, giorni=7)
    assert len(scarti) >= 12
    assert max(scarti) < ORARI_S, max(scarti)


@pytest.mark.lento
@pytest.mark.parametrize("dove", SITI)
@pytest.mark.parametrize("corpo", ["sun", "moon"])
def test_rise_and_set_agree_with_astropy_on_four_sites_for_two_months(corpo, dove):
    scarti = _scarti_orari(corpo, dove, giorni=60)
    assert max(scarti) < ORARI_S, max(scarti)


@pytest.mark.parametrize("corpo", ["sun", "moon", "jupiter", "venus"])
def test_the_altitude_agrees_with_astropy_within_thirty_arcseconds(corpo):
    istanti = night_grid(INIZIO, hours=48, step_min=30)
    nostre = np.array(bodies.body_altitudes(corpo, istanti, *CASA))
    assert np.max(np.abs(nostre - _astropy(corpo, istanti, CASA))) * 3600 < ALTEZZA_ARCSEC


def test_the_light_and_the_distance_of_the_moon_agree_with_astropy():
    """Geocentriche tutte e due: frazione illuminata entro un decimo di punto, distanza entro
    15 km (su 384 mila: l'errore del modello incorporato di astropy, misurato 10,0 km su
    2026-2027 ogni sei ore)."""
    istanti = [INIZIO + dt.timedelta(days=g) for g in range(30)]
    tempi = Time(istanti)
    sole, luna = get_sun(tempi), get_body("moon", tempi)
    loro = (1 - np.cos(np.radians(np.asarray(sole.separation(luna).deg)))) / 2  # pyright: ignore[reportArgumentType]
    nostre = np.array(moon.lit_fractions(istanti))
    assert np.max(np.abs(nostre - loro)) * 100 < 0.1
    for quando, km in zip(istanti, np.asarray(luna.distance.km), strict=True):  # pyright: ignore[reportOptionalMemberAccess]
        assert abs(moon.distance_km(quando) - km) < 15


def _fasi_di_astropy(istanti):
    """La stessa grandezza di `moon._offsets_and_elongations`, calcolata da astropy."""
    tempi = Time(istanti)
    sole, luna = get_sun(tempi), get_body("moon", tempi)
    eclittica = GeocentricMeanEcliptic(obstime=tempi)
    lon = [np.asarray(c.transform_to(eclittica).lon.deg) for c in (luna, sole)]  # pyright: ignore[reportOptionalMemberAccess]
    return lon[0] - lon[1], np.asarray(sole.separation(luna).deg)  # pyright: ignore[reportArgumentType]


def test_new_and_full_moons_agree_with_astropy_within_twenty_seconds(monkeypatch):
    """Le lune nuove e piene del calendario: misurato fino a 11,7 s su 13 eventi del 2026
    (l'errore del modello incorporato di astropy), soglia 20 s."""
    inizio, fine = dt.datetime(2026, 1, 1, tzinfo=dt.UTC), dt.datetime(2026, 7, 1, tzinfo=dt.UTC)
    nostre = moon.main_phases(inizio, fine)
    monkeypatch.setattr(moon, "_offsets_and_elongations", _fasi_di_astropy)
    loro = moon.main_phases(inizio, fine)
    assert [e.kind for e in nostre] == [e.kind for e in loro] and len(nostre) >= 12
    scarti = [abs((a.at - b.at).total_seconds()) for a, b in zip(nostre, loro, strict=True)]
    assert max(scarti) < 20, max(scarti)


def test_the_moon_off_a_frame_centre_agrees_with_astropy_within_a_minute():
    """Distanza Luna-centro del frame, dal sito: misurato fino a 25" (qui senza aberrazione da
    tutte e due le parti, astropy con), soglia un minuto d'arco."""
    istanti = [INIZIO + dt.timedelta(hours=7 * k) for k in range(40)]
    centri = [((37.0 * k) % 360, -60 + 3.0 * k) for k in range(40)]
    trovate = moon_and_sun(istanti, [CASA] * 40, centri)
    sito, tempi = EarthLocation(lat=CASA[0], lon=CASA[1]), Time(istanti)
    stelle = SkyCoord([c[0] for c in centri], [c[1] for c in centri], unit="deg")
    loro = np.asarray(get_body("moon", tempi, sito).separation(stelle).deg)  # pyright: ignore[reportArgumentType]
    nostre = np.array([t.moon_separation_deg for t in trovate if t is not None], dtype=float)
    assert len(nostre) == 40
    assert np.max(np.abs(nostre - loro)) * 3600 < 60
