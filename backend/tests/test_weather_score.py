"""Il punteggio della notte v4 (ADR 0034): la Trasparenza di ogni ora di buio, la media pesata
sui minuti di buio, il verdetto 70 / 40, le ore di posa.

Ogni prova tiene un confine della regola: chi sposta un numero fa cadere la prova che dice da dove
veniva.
"""

import math

import pytest

from astrolog.weather import score, verdict


def ora(at="2026-09-25T22:00:00+02:00", sky="dark", dark=None, down=None, **campi):
    riga = {
        "cloud_total_pct": 0.0,
        "precip_mm": 0.0,
        "wind_kmh": 5.0,
        "wind_gust_kmh": 10.0,
    }
    riga.update(campi)
    return verdict.Hour(at=at, sky=sky, values=riga, dark=dark, down=down)


def notte(*campi):
    """Ore buie in fila, dalle 20."""
    return [ora(f"2026-09-25T{20 + i:02d}:00:00+02:00", **c) for i, c in enumerate(campi)]


def test_a_clear_hour_without_aerosol_is_fully_transparent():
    assert score.transparency(ora()) == 100.0


def test_the_clouds_take_their_share_of_the_light():
    """La luce persa si moltiplica (Neilsen et al. 2019): 30% di nuvole lasciano il 70%."""
    assert score.transparency(ora(cloud_total_pct=30.0)) == pytest.approx(70.0)


def test_the_aerosol_takes_its_share_above_a_clear_sky():
    """Sotto 0,1 il cielo e' limpido e non toglie niente; sopra, e^(-2 (AOD - 0,1))."""
    assert score.transparency(ora(aerosol_optical_depth=0.05)) == 100.0
    assert score.transparency(ora(aerosol_optical_depth=0.35)) == pytest.approx(
        100 * math.exp(-0.5)
    )


@pytest.mark.parametrize(
    ("campo", "valore"),
    [
        ("precip_mm", 0.1),  # qualunque goccia
        ("visibility_km", 0.9),  # nebbia sotto 1 km
        ("cloud_total_pct", 50.1),  # oltre il 50%
        ("wind_kmh", 29.0),  # Beaufort 5 da 29
        ("wind_gust_kmh", 25.1),  # raffiche oltre 25
    ],
)
def test_an_hour_that_blocks_is_zero(campo, valore):
    assert score.transparency(ora(**{campo: valore})) == 0.0


@pytest.mark.parametrize(
    ("campo", "valore"),
    [
        ("cloud_total_pct", 50.0),
        ("wind_kmh", 28.9),
        ("wind_gust_kmh", 25.0),
        ("visibility_km", 1.0),
        ("wind_250hpa_kmh", 200.0),  # il jet stream dice il seeing, non la luce
        ("seeing_arcsec", 6.0),  # il seeing sta fuori dal voto
    ],
)
def test_an_hour_just_inside_the_rules_is_not_blocked(campo, valore):
    assert score.transparency(ora(**{campo: valore})) > 0.0


def test_without_the_clouds_an_hour_has_no_transparency():
    assert score.transparency(ora(cloud_total_pct=None)) is None


def test_the_verdict_is_good_from_70_and_uncertain_from_40():
    assert score.assess(notte({"cloud_total_pct": 30.0})).verdict == "go"
    assert score.assess(notte({"cloud_total_pct": 30.1})).verdict == "marginal"
    assert score.assess(notte({"cloud_total_pct": 50.0})).verdict == "marginal"
    assert score.assess(notte({"precip_mm": 0.2})).verdict == "nogo"


def test_the_night_is_the_mean_of_its_dark_hours():
    detto = score.assess(notte({"cloud_total_pct": 0.0}, {"cloud_total_pct": 40.0}))
    assert detto.transparency == 80.0


def test_each_hour_weighs_for_its_minutes_of_dark():
    """L'ora del crepuscolo con un quarto d'ora di buio pesa un quarto."""
    detto = score.assess(
        notte({"cloud_total_pct": 0.0, "dark": 0.25}, {"cloud_total_pct": 40.0, "dark": 1.0})
    )
    assert detto.transparency == pytest.approx(round((100 * 0.25 + 60) / 1.25, 1))
    assert detto.dark_hours == 1.2


def test_an_edge_hour_weighs_in_the_score_but_not_in_the_clear_hours():
    """L'ora del crepuscolo col suo pezzo di buio pesa nella Trasparenza; le ore serene e le
    misure restano quelle col buio all'istante, com'erano."""
    ore = [
        ora("2026-09-25T20:00:00+02:00", sky="astronomical", dark=0.4, precip_mm=0.3),
        ora("2026-09-25T21:00:00+02:00", dark=1.0),
    ]
    detto = score.assess(ore)
    assert (detto.window_hours, detto.usable_hours, detto.dark_hours) == (1, 1, 1.4)
    assert detto.transparency == pytest.approx(round(100 / 1.4, 1))


def test_the_exposure_hours_are_the_transparency_times_the_dark():
    """«4,0 ore di posa su 9 di buio»: un'ora limpida e' un'ora di posa, una al 60% e' 0,6."""
    detto = score.assess(notte({}, {"cloud_total_pct": 40.0}, {"precip_mm": 1.0}))
    assert detto.exposure_hours == 1.6
    assert detto.dark_hours == 3.0


def test_a_night_without_aerosol_says_so():
    """Lo storico non porta l'aerosol: la Trasparenza resta quella delle nuvole, e lo si dice."""
    assert score.assess(notte({})).without_aerosol is True
    assert score.assess(notte({"aerosol_optical_depth": 0.05})).without_aerosol is False


def test_a_night_with_a_missing_cloud_hour_has_no_verdict():
    detto = score.assess(notte({"cloud_total_pct": None}, {}))
    assert (detto.verdict, detto.transparency, detto.exposure_hours) == (None, None, None)


def test_without_dark_the_hours_with_the_sun_down_are_judged():
    """D'estate al nord: le ore col Sole sotto l'orizzonte, pesate per i loro minuti."""
    ore = [
        ora("2026-06-21T23:00:00+02:00", sky="nautical", down=1.0),
        ora("2026-06-22T00:00:00+02:00", sky="nautical", down=0.5, cloud_total_pct=40.0),
    ]
    detto = score.assess(ore)
    assert detto.window == "sun_down"
    assert detto.dark_hours == 1.5
    assert detto.exposure_hours == 1.3


def test_where_the_sun_never_sets_there_is_no_score():
    detto = score.assess([ora("2026-06-21T00:00:00+02:00", sky="day")])
    assert (detto.verdict, detto.transparency, detto.dark_hours) == (None, None, 0.0)
