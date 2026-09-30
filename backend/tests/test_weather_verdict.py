"""Il verdetto di una notte e i fattori che lo decidono, dalle sue ore.

Le soglie vengono da convenzioni pubbliche, e ogni prova qui tiene il confine della sua: se
qualcuno sposta un numero, cade la prova che dice da dove veniva.
"""

from astrolog.weather import verdict


def ora(at, sky="dark", **campi):
    riga = {
        "at": at,
        "sky": sky,
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
    return riga


def notte(*buie, prima=("day", "civil")):
    """Una notte con qualche ora di luce prima, e poi le ore buie date."""
    ore = [ora(f"2026-09-25T{18 + i:02d}:00:00+02:00", sky=s) for i, s in enumerate(prima)]
    for i, campi in enumerate(buie):
        ore.append(ora(f"2026-09-25T{20 + i:02d}:00:00+02:00", **campi))
    return ore


def test_the_verdict_follows_the_okta_classes_of_the_total_cloud():
    """FEW fino a 2 okta (25%) si fa; SCT fino a 4 (50%) e' incerta; da BKN in su no."""
    assert verdict.assess(notte({"cloud_total_pct": 25.0}))["verdict"] == "go"
    assert verdict.assess(notte({"cloud_total_pct": 25.1}))["verdict"] == "marginal"
    assert verdict.assess(notte({"cloud_total_pct": 50.0}))["verdict"] == "marginal"
    assert verdict.assess(notte({"cloud_total_pct": 50.1}))["verdict"] == "nogo"


def test_the_verdict_looks_only_at_the_dark_hours():
    """Le nuvole del pomeriggio non tolgono la notte: conta il buio."""
    ore = notte({"cloud_total_pct": 0.0}, {"cloud_total_pct": 10.0})
    ore[0]["cloud_total_pct"] = 100.0
    ore[1]["cloud_total_pct"] = 100.0
    detto = verdict.assess(ore)
    assert detto["verdict"] == "go"
    assert detto["cloud_total_pct"] == 5.0
    assert detto["window"] == "dark"
    assert detto["window_hours"] == 2


def test_without_dark_the_night_is_the_hours_with_the_sun_down():
    """D'estate al nord il buio astronomico non arriva: la notte e' quella col Sole sotto
    l'orizzonte, e lo si dice."""
    ore = [ora("2026-06-21T22:00:00+02:00", sky="nautical", cloud_total_pct=80.0)]
    ore.append(ora("2026-06-21T12:00:00+02:00", sky="day", cloud_total_pct=0.0))
    detto = verdict.assess(ore)
    assert detto["window"] == "sun_down"
    assert detto["verdict"] == "nogo"


def test_where_the_sun_never_sets_there_is_no_verdict():
    detto = verdict.assess([ora("2026-06-21T00:00:00+02:00", sky="day")])
    assert detto["verdict"] is None
    assert detto["window"] is None
    assert detto["usable_hours"] is None


def test_without_the_total_cloud_there_is_no_verdict_and_no_usable_hours():
    detto = verdict.assess(notte({"cloud_total_pct": None}, {"cloud_total_pct": 0.0}))
    assert detto["verdict"] is None
    assert detto["usable_hours"] is None


def test_the_usable_hours_are_the_dark_hours_the_verdict_would_call_clear():
    detto = verdict.assess(
        notte({"cloud_total_pct": 25.0}, {"cloud_total_pct": 26.0}, {"cloud_total_pct": 0.0})
    )
    assert detto["usable_hours"] == 2


def codici(detto):
    return [f["code"] for f in detto["factors"]]


def test_a_clear_calm_dry_night_has_no_factors():
    assert verdict.assess(notte({}, {}))["factors"] == []


def test_the_gust_counts_from_beaufort_five():
    """Forza 5 comincia a 29 km/h, e 29 e' gia' forza 5."""
    assert "gust" not in codici(verdict.assess(notte({"wind_gust_kmh": 28.9})))
    detto = verdict.assess(notte({"wind_gust_kmh": 29.0}, {"wind_gust_kmh": 12.0}))
    (raffica,) = [f for f in detto["factors"] if f["code"] == "gust"]
    assert raffica["value"] == 29.0
    assert raffica["threshold"] == 29.0
    assert raffica["hours"] == 1


def test_condensation_comes_when_the_air_is_less_than_three_degrees_from_the_dew_point():
    assert "condensation" not in codici(
        verdict.assess(notte({"temperature_c": 10.0, "dew_point_c": 7.0}))
    )
    detto = verdict.assess(notte({"temperature_c": 10.0, "dew_point_c": 7.1}))
    (condensa,) = [f for f in detto["factors"] if f["code"] == "condensation"]
    assert condensa["value"] == 2.9
    assert condensa["threshold"] == 3.0


def test_any_rain_in_the_dark_is_a_factor():
    detto = verdict.assess(notte({"precip_mm": 0.1}, {"precip_mm": 0.3}))
    (pioggia,) = [f for f in detto["factors"] if f["code"] == "rain"]
    assert pioggia["value"] == 0.4
    assert pioggia["hours"] == 2


def test_low_clouds_are_a_factor_of_their_own_beyond_two_oktas():
    assert "cloud_low" not in codici(verdict.assess(notte({"cloud_low_pct": 25.0})))
    assert "cloud_low" in codici(verdict.assess(notte({"cloud_low_pct": 25.1})))


def test_the_cloud_factor_exists_exactly_when_the_night_is_not_a_go():
    assert "cloud" not in codici(verdict.assess(notte({"cloud_total_pct": 25.0})))
    assert "cloud" in codici(verdict.assess(notte({"cloud_total_pct": 25.1})))


def test_the_factors_come_in_order_of_gravity():
    """La pioggia chiude la serata; le nuvole basse bloccano; il totale vela; la raffica fa
    vibrare; la condensa si combatte con una fascia."""
    detto = verdict.assess(
        notte(
            {
                "precip_mm": 1.0,
                "cloud_low_pct": 90.0,
                "cloud_total_pct": 90.0,
                "wind_gust_kmh": 40.0,
                "temperature_c": 5.0,
                "dew_point_c": 5.0,
            }
        )
    )
    assert codici(detto) == ["rain", "cloud_low", "cloud", "gust", "condensation"]


def test_a_factor_says_when_it_bites_without_inventing_a_continuous_window():
    """Morde alle 20 e alle 22, non alle 21: dalle 20 alle 23, due ore e non tre -- la fine e'
    quella dell'ultima ora colpita, e il conteggio dice che in mezzo ce n'e' una libera."""
    detto = verdict.assess(notte({"wind_gust_kmh": 35.0}, {}, {"wind_gust_kmh": 31.0}))
    (raffica,) = [f for f in detto["factors"] if f["code"] == "gust"]
    assert raffica["since"] == "2026-09-25T20:00:00+02:00"
    assert raffica["until"] == "2026-09-25T23:00:00+02:00"
    assert raffica["hours"] == 2
    assert raffica["value"] == 35.0


def test_the_end_of_a_factor_is_the_next_hour_of_the_night_even_when_the_clocks_change():
    """La notte del cambio d'ora l'ora dopo le 02:00+02:00 e' le 02:00+01:00: la fine si legge
    dall'ora che viene dopo, non aggiungendo sessanta minuti all'orologio a muro."""
    ore = [
        ora("2026-10-25T02:00:00+02:00", wind_gust_kmh=40.0),
        ora("2026-10-25T02:00:00+01:00"),
    ]
    (raffica,) = verdict.assess(ore)["factors"]
    assert raffica["until"] == "2026-10-25T02:00:00+01:00"


def test_the_clouds_bite_only_in_the_hours_beyond_two_oktas():
    detto = verdict.assess(
        notte({"cloud_total_pct": 80.0}, {"cloud_total_pct": 25.0}, {"cloud_total_pct": 30.0})
    )
    (nuvole,) = [f for f in detto["factors"] if f["code"] == "cloud"]
    assert (nuvole["since"], nuvole["hours"]) == ("2026-09-25T20:00:00+02:00", 2)


def test_condensation_bites_only_in_the_hours_near_the_dew_point_and_says_nothing_without_it():
    detto = verdict.assess(
        notte(
            {"temperature_c": 10.0, "dew_point_c": 9.5},
            {"temperature_c": 10.0, "dew_point_c": 6.0},
            {"temperature_c": 10.0, "dew_point_c": None},
        )
    )
    (condensa,) = [f for f in detto["factors"] if f["code"] == "condensation"]
    assert (condensa["since"], condensa["hours"]) == ("2026-09-25T20:00:00+02:00", 1)


def test_the_wind_aloft_is_told_but_does_not_change_the_verdict():
    """Il vento in quota si confronta col solito, non pesa: stessa notte, stesso verdetto."""
    calmo = verdict.assess(notte({"wind_700hpa_kmh": 0.0}))
    tempesta = verdict.assess(notte({"wind_700hpa_kmh": 300.0}))
    assert tempesta["wind_700hpa_kmh"] == 300.0
    assert {**tempesta, "wind_700hpa_kmh": 0.0} == calmo
