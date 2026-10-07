"""Il verdetto di una notte, le sue ore serene e la finestra da mostrare, dalle sue ore.

Le soglie vengono da convenzioni pubbliche, e ogni prova qui tiene il confine della sua: se
qualcuno sposta un numero, cade la prova che dice da dove veniva.
"""

import dataclasses

from astrolog.weather import verdict


def ora(at, sky="dark", **campi):
    riga = {
        "cloud_total_pct": 0.0,
        "cloud_low_pct": 0.0,
        "cloud_mid_pct": 0.0,
        "cloud_high_pct": 0.0,
        "temperature_c": 12.0,
        "humidity_pct": 60.0,
        "dew_point_c": 4.0,
        "wind_kmh": 5.0,
        "wind_gust_kmh": 10.0,
        "precip_mm": 0.0,
    }
    riga.update(campi)
    return verdict.Hour(at=at, sky=sky, values=riga)


def notte(*buie, prima=("day", "civil")):
    """Una notte con qualche ora di luce prima, e poi le ore buie date."""
    ore = [ora(f"2026-09-25T{18 + i:02d}:00:00+02:00", sky=s) for i, s in enumerate(prima)]
    for i, campi in enumerate(buie):
        ore.append(ora(f"2026-09-25T{20 + i:02d}:00:00+02:00", **campi))
    return ore


def test_the_verdict_follows_the_okta_classes_of_the_total_cloud():
    """FEW fino a 2 okta (25%) si fa; SCT fino a 4 (50%) e' incerta; da BKN in su no."""
    assert verdict.assess(notte({"cloud_total_pct": 25.0})).verdict == "go"
    assert verdict.assess(notte({"cloud_total_pct": 25.1})).verdict == "marginal"
    assert verdict.assess(notte({"cloud_total_pct": 50.0})).verdict == "marginal"
    assert verdict.assess(notte({"cloud_total_pct": 50.1})).verdict == "nogo"


def test_the_verdict_looks_only_at_the_dark_hours():
    """Le nuvole del pomeriggio non tolgono la notte: conta il buio."""
    ore = notte({"cloud_total_pct": 0.0}, {"cloud_total_pct": 10.0})
    ore[0].values["cloud_total_pct"] = 100.0
    ore[1].values["cloud_total_pct"] = 100.0
    detto = verdict.assess(ore)
    assert detto.verdict == "go"
    assert detto.cloud_total_pct == 5.0
    assert detto.window == "dark"
    assert detto.window_hours == 2


def test_without_dark_the_night_is_the_hours_with_the_sun_down():
    """D'estate al nord il buio astronomico non arriva: la notte e' quella col Sole sotto
    l'orizzonte, e lo si dice."""
    ore = [ora("2026-06-21T22:00:00+02:00", sky="nautical", cloud_total_pct=80.0)]
    ore.append(ora("2026-06-21T12:00:00+02:00", sky="day", cloud_total_pct=0.0))
    detto = verdict.assess(ore)
    assert detto.window == "sun_down"
    assert detto.verdict == "nogo"


def test_where_the_sun_never_sets_there_is_no_verdict():
    detto = verdict.assess([ora("2026-06-21T00:00:00+02:00", sky="day")])
    assert detto.verdict is None
    assert detto.window is None
    assert detto.usable_hours is None


def test_without_the_total_cloud_there_is_no_verdict_and_no_usable_hours():
    detto = verdict.assess(notte({"cloud_total_pct": None}, {"cloud_total_pct": 0.0}))
    assert detto.verdict is None
    assert detto.usable_hours is None


def test_the_usable_hours_are_the_dark_hours_the_verdict_would_call_clear():
    detto = verdict.assess(
        notte({"cloud_total_pct": 25.0}, {"cloud_total_pct": 26.0}, {"cloud_total_pct": 0.0})
    )
    assert detto.usable_hours == 2


def test_the_usable_hours_are_said_as_an_interval_and_a_count():
    """ "Dalle 20 alle 23, 2 ore": l'intervallo va dalla prima ora serena alla fine dell'ultima, e
    il conto dice che in mezzo ce n'e' una coperta."""
    detto = verdict.assess(
        notte({"cloud_total_pct": 0.0}, {"cloud_total_pct": 80.0}, {"cloud_total_pct": 10.0})
    )
    assert (detto.usable_since, detto.usable_until, detto.usable_hours) == (
        "2026-09-25T20:00:00+02:00",
        "2026-09-25T23:00:00+02:00",
        2,
    )


def test_a_night_without_clear_hours_has_no_interval():
    detto = verdict.assess(notte({"cloud_total_pct": 90.0}))
    assert (detto.usable_since, detto.usable_until, detto.usable_hours) == (None, None, 0)


def test_the_end_of_an_interval_is_the_next_hour_of_the_night_even_when_the_clocks_change():
    """La notte del cambio d'ora l'ora dopo le 02:00+02:00 e' le 02:00+01:00: la fine si legge
    dall'ora che viene dopo, non aggiungendo sessanta minuti all'orologio a muro."""
    ore = [
        ora("2026-10-25T02:00:00+02:00"),
        ora("2026-10-25T02:00:00+01:00", cloud_total_pct=90.0),
    ]
    assert verdict.assess(ore).usable_until == "2026-10-25T02:00:00+01:00"


def test_the_page_shows_from_the_last_hour_of_day_to_the_first_after_dawn():
    """A ottobre 18-08: l'ultima ora di giorno prima del crepuscolo e la prima dopo l'alba."""
    cieli = ["day", "day", "civil", "dark", "dark", "civil", "day", "day"]
    ore = [ora(f"2026-09-25T{17 + i:02d}:00:00+02:00", sky=s) for i, s in enumerate(cieli)]
    detto = verdict.assess(ore)
    assert (detto.shown_from, detto.shown_until) == (
        "2026-09-25T18:00:00+02:00",
        "2026-09-25T23:00:00+02:00",
    )


def test_where_the_sun_never_sets_nothing_is_shown():
    detto = verdict.assess([ora("2026-06-21T00:00:00+02:00", sky="day")])
    assert (detto.shown_from, detto.shown_until) == (None, None)


def test_the_wind_aloft_is_told_but_does_not_change_the_verdict():
    """Il vento in quota si confronta col solito, non pesa: stessa notte, stesso verdetto."""
    calmo = verdict.assess(notte({"wind_700hpa_kmh": 0.0}))
    tempesta = verdict.assess(notte({"wind_700hpa_kmh": 300.0}))
    assert tempesta.wind_700hpa_kmh == 300.0
    assert dataclasses.replace(tempesta, wind_700hpa_kmh=0.0) == calmo
