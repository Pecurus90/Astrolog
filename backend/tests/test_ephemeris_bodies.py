"""Dove sta un corpo del cielo: le regole di `ephemeris/bodies.py`, che Luna, Sole e pianeti
dividono.

Le prove del conto vero stanno nei file dei corpi e nel confronto con astropy; qui c'e' cio' che
vale per tutti.

test-tolto: test_a_conversion_that_does_not_happen_is_said_not_ignored -- difendeva il `None`
che la conversione di astropy puo' rendere; Skyfield non lo dichiara, e la funzione non c'e' piu'.
"""

import datetime as dt

import pytest

from astrolog.ephemeris import bodies


def test_an_instant_without_a_zone_is_refused_not_read_as_utc():
    """Un'ora senza fuso letta come UTC sposterebbe il cielo di tante ore quante il fuso."""
    with pytest.raises(ValueError, match="fuso"):
        bodies.body_altitudes("sun", [dt.datetime(2027, 3, 14, 21)], 45.5, 11.5)


def test_the_same_instant_in_two_zones_is_the_same_sky():
    utc = dt.datetime(2027, 3, 14, 21, tzinfo=dt.UTC)
    roma = utc.astimezone(dt.timezone(dt.timedelta(hours=1)))
    assert bodies.body_altitudes("moon", [utc, roma], 45.5, 11.5) == pytest.approx(
        [bodies.body_altitudes("moon", [utc], 45.5, 11.5)[0]] * 2
    )


def test_the_altitude_has_no_refraction_in_it():
    """Geometrica: la rifrazione vive nella soglia `RISESET_DEG`, non nell'altezza. Con la
    rifrazione anche dentro l'altezza, l'alba verrebbe corretta due volte. Si prende il Sole
    vicino all'orizzonte, dove l'aria lo alza di mezzo grado: l'altezza data e' quella senza
    aria."""
    quando = [dt.datetime(2027, 3, 20, 5, 25, tzinfo=dt.UTC)]  # un grado sopra l'orizzonte
    alba = bodies.observed("sun", quando, (45.5, 11.5))
    senza, _, _ = alba.altaz()
    con, _, _ = alba.altaz(temperature_C=10.0, pressure_mbar=1010.0)
    assert float(senza.degrees[0]) == pytest.approx(
        bodies.body_altitudes("sun", quando, 45.5, 11.5)[0]
    )
    assert float(con.degrees[0]) - float(senza.degrees[0]) > 0.05


def test_a_date_outside_de421_is_said_before_it_is_asked():
    """DE421 copre dal 1899 al 2053; un header con l'orologio sbagliato dice 1850 o 2099.
    Fuori, il conto solleva: chi chiama guarda prima `covers` e risponde "non so"."""
    assert bodies.covers(dt.datetime(2027, 3, 14, tzinfo=dt.UTC))
    assert bodies.covers(dt.datetime(1970, 1, 1, tzinfo=dt.UTC))
    assert not bodies.covers(dt.datetime(2099, 1, 1, tzinfo=dt.UTC))
    assert not bodies.covers(dt.datetime(1850, 1, 1, tzinfo=dt.UTC))
    start, end = bodies.covered()
    assert bodies.body_altitudes("moon", [start, end], 45.5, 11.5)  # i bordi si calcolano


def test_the_kernel_is_opened_once_for_the_whole_process():
    """Aprire la DE421 costa: chi la riaprisse a ogni chiamata pagherebbe a ogni rotta."""
    assert bodies.kernel() is bodies.kernel()
