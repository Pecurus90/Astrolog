"""La rugiada su un vetro esposto: Beysens 2016, Atmos. Res. 167:146, Eq. 25 (copia d'autore
hal-04005956, p. 12). La soglia e' lo scarto aria-rugiada sotto cui l'Eq. 25 da' resa positiva."""

import math

import pytest

from astrolog.weather import dew


def resa(td: float, ta: float, n_oktas: float, v_ms: float, h_km: float) -> float:
    """L'Eq. 25 scritta come sta stampata, in mm/giorno, per confronto col modulo."""
    p = (
        1
        + 0.204323 * h_km
        - 0.0238893 * h_km**2
        - (18.0132 - 1.04963 * h_km + 0.21891 * h_km**2) * 1e-3 * td
    )
    c = 1 + 100 * (1 - math.exp(-((v_ms / 4.4) ** 20)))
    return 0.37 * p * ((td + 273.15) / 285) ** 4 * (1 - n_oktas / 8) + 0.06 * (td - ta) * c


def test_clear_and_calm_at_sea_level_with_the_dew_point_at_285_kelvin():
    """Td = 11,85 gradi: il fattore (Td+273,15)/285 vale 1 e resta il conto a mano
    0,37 x (1 - 18,0132e-3 x 11,85) / 0,06 = 4,850 gradi."""
    soglia = dew.threshold_c(dew_point_c=11.85, cloud_pct=0.0, wind_kmh=0.0, elevation_m=0.0)
    assert soglia == pytest.approx(0.37 * (1 - 18.0132e-3 * 11.85) / 0.06, abs=1e-9)
    assert soglia == pytest.approx(4.850, abs=1e-3)


@pytest.mark.parametrize(
    ("td", "nuvole", "vento_kmh", "quota_m"),
    [
        (11.85, 0.0, 0.0, 0.0),
        (5.0, 37.5, 7.2, 400.0),
        (-3.0, 0.0, 10.8, 1800.0),
        (15.0, 75.0, 3.6, 2600.0),
    ],
)
def test_at_the_threshold_the_printed_equation_gives_no_dew_and_just_under_it_gives_some(
    td, nuvole, vento_kmh, quota_m
):
    soglia = dew.threshold_c(td, nuvole, vento_kmh, quota_m)
    oktas, v, h = nuvole * 8 / 100, vento_kmh / 3.6, quota_m / 1000
    assert resa(td, td + soglia, oktas, v, h) == pytest.approx(0.0, abs=1e-12)
    assert resa(td, td + soglia - 0.01, oktas, v, h) > 0
    assert resa(td, td + soglia + 0.01, oktas, v, h) < 0


def test_the_elevation_enters_linearly_where_the_paper_prints_h_not_h_squared():
    """Eq. 25: "(18.0132 - 1.04963H + 0.21891H^2)". NREL pvdeg (humidity.dew_yield) scrive
    1.04963 * H**2: a 2 km la differenza si vede, e vale la stampa."""
    td, h = 10.0, 2.0
    stampata = 1 + 0.204323 * h - 0.0238893 * h**2 - (18.0132 - 1.04963 * h + 0.21891 * h**2) * 1e-2
    pvdeg = 1 + 0.204323 * h - 0.0238893 * h**2 - (18.0132 - 1.04963 * h**2 + 0.21891 * h**2) * 1e-2
    soglia = dew.threshold_c(td, 0.0, 0.0, 2000.0)
    radiativo = 0.37 * ((td + 273.15) / 285) ** 4 / 0.06
    assert soglia == pytest.approx(radiativo * stampata, abs=1e-9)
    assert soglia != pytest.approx(radiativo * pvdeg, abs=1e-3)


def test_overcast_or_wind_over_4_4_metres_a_second_leave_almost_no_room():
    """Eq. 23: sopra V0 = 4,4 m/s lo scambio col vento e' 101 volte; con 8 okta niente
    raffreddamento."""
    assert dew.threshold_c(10.0, 100.0, 0.0, 0.0) == 0.0
    calma = dew.threshold_c(10.0, 0.0, 0.0, 0.0)
    ventosa = dew.threshold_c(10.0, 0.0, 5.0 * 3.6, 0.0)
    assert ventosa == pytest.approx(calma / 101, rel=1e-3)


def test_a_missing_input_gives_no_threshold():
    assert dew.threshold_c(None, 0.0, 0.0, 0.0) is None
    assert dew.threshold_c(10.0, None, 0.0, 0.0) is None
    assert dew.threshold_c(10.0, 0.0, None, 0.0) is None


def test_without_the_site_elevation_the_threshold_is_at_sea_level():
    assert dew.threshold_c(10.0, 0.0, 0.0, None) == dew.threshold_c(10.0, 0.0, 0.0, 0.0)


def test_the_shown_threshold_stays_on_the_side_of_the_spread():
    """Uno scarto di 4,9 con soglia 4,93 e' rugiada: la soglia si scrive 5,0, mai 4,9."""
    assert dew.shown_threshold(4.9, 4.93) == 5.0
    assert dew.shown_threshold(5.0, 4.97) == 4.9
    assert dew.shown_threshold(None, 4.97) == 5.0
    assert dew.shown_threshold(3.0, None) is None
