"""Il giudizio di ogni misura, ora per ora e per la notte: la parola, da che ora e quante ore, la
media sui numeri veri, il picco, e l'ordine in cui la pagina le mostra.

Ogni soglia ha la sua prova di confine: se qualcuno sposta un numero, cade la prova che dice da
dove veniva. Il semaforo lo decidono solo le nuvole; le altre misure pesano accanto.
"""

import pytest

from astrolog.weather import judge, verdict
from test_weather_verdict import notte, ora


def livello(misura, **valori):
    """Il giudizio di un'ora sola con questi valori."""
    return judge.hour_levels(ora("2026-09-25T22:00:00+02:00", **valori)).get(misura)


def misure(ore):
    return {m.code: m for m in judge.measures(ore, verdict.assess(ore))}


@pytest.mark.parametrize(
    ("misura", "campo", "valori"),
    [
        # okta WMO 2700 come classi METAR: FEW fino a 2/8, SCT fino a 4/8
        (
            "cloud_low",
            "cloud_low_pct",
            [(25.0, "go"), (25.1, "marginal"), (50.0, "marginal"), (50.1, "nogo")],
        ),
        # qualunque pioggia
        ("rain", "precip_mm", [(0.0, "go"), (0.1, "nogo")]),
        # Beaufort 5, 29 km/h
        ("gust", "wind_gust_kmh", [(28.9, "go"), (29.0, "nogo")]),
        # Beaufort 4 da 20 km/h, 5 da 29
        (
            "wind",
            "wind_kmh",
            [(19.9, "go"), (20.0, "marginal"), (28.9, "marginal"), (29.0, "nogo")],
        ),
        # meteoblue: oltre 35 m/s (126 km/h) seeing cattivo
        ("jet", "wind_250hpa_kmh", [(125.9, "go"), (126.0, "nogo")]),
        # Canadian Meteorological Centre: fino a 2" discreto, 2-4" moderato, oltre 4" scarso
        (
            "seeing",
            "seeing_arcsec",
            [(2.0, "go"), (2.1, "marginal"), (4.0, "marginal"), (4.1, "nogo")],
        ),
        # NASA Earth Observatory: sotto 0,1 limpido, 1 molto fosco; in mezzo nessuna parola
        (
            "aerosol",
            "aerosol_optical_depth",
            [(0.09, "go"), (0.1, None), (0.99, None), (1.0, "nogo")],
        ),
        # banda larga fino al 25 %; 25-50 al limite; oltre solo banda stretta (il 50 e' di Marco)
        (
            "moon",
            "moon_pct",
            [(25.0, "go"), (25.1, "marginal"), (50.0, "marginal"), (50.1, "nogo")],
        ),
    ],
)
def test_each_measure_judges_an_hour_at_the_edges_of_its_source(misura, campo, valori):
    for valore, atteso in valori:
        assert livello(misura, **{campo: valore}) == atteso, (misura, valore)


def test_condensation_comes_under_three_degrees_between_air_and_dew_point():
    """Regola FAA dei 5 gradi Fahrenheit: sotto i 3 gradi fra aria e rugiada, nebbia."""
    assert livello("condensation", temperature_c=10.0, dew_point_c=7.0) == "go"
    assert livello("condensation", temperature_c=10.0, dew_point_c=7.1) == "nogo"
    assert livello("condensation", temperature_c=10.0, dew_point_c=None) is None


def test_a_missing_value_has_no_judgement_and_a_neutral_measure_never_has_one():
    assert livello("seeing", seeing_arcsec=None) is None
    assert "humidity" not in judge.hour_levels(ora("2026-09-25T22:00:00+02:00"))
    assert "cloud" in judge.hour_levels(ora("2026-09-25T22:00:00+02:00"))


def test_the_moon_down_has_no_judgement():
    """La Luna pesa solo sopra l'orizzonte: sotto, l'ora non porta la sua percentuale."""
    assert livello("moon", moon_pct=None) is None


def test_a_measure_takes_the_worst_hour_of_the_night_and_says_its_hours():
    """Vento incerto alle 20, niente alle 21 e alle 23: la notte e' "niente", dalle 21 alle 24,
    due ore -- quelle con quella parola, e il conto dice che in mezzo ce n'e' una diversa."""
    detto = misure(notte({"wind_kmh": 22.0}, {"wind_kmh": 30.0}, {}, {"wind_kmh": 31.0}))["wind"]
    assert detto.level == "nogo"
    assert (detto.since, detto.until, detto.hours) == (
        "2026-09-25T21:00:00+02:00",
        "2026-09-26T00:00:00+02:00",
        2,
    )
    assert detto.weighs


def test_the_night_value_is_the_mean_of_the_true_numbers_and_rain_is_a_total():
    ore = notte({"wind_kmh": 10.0, "precip_mm": 0.5}, {"wind_kmh": 20.0, "precip_mm": 1.0})
    detto = misure(ore)
    assert detto["wind"].value == 15.0
    assert detto["rain"].value == 1.5


def test_a_hazy_hour_without_a_word_is_worse_than_a_clear_one():
    """Aerosol 0,5 alle 20 e alle 21, 0,09 alle 22: la notte non e' "limpida" per un'ora sola."""
    ore = notte(
        {"aerosol_optical_depth": 0.5},
        {"aerosol_optical_depth": 0.5},
        {"aerosol_optical_depth": 0.09},
    )
    assert misure(ore)["aerosol"].level is None


def test_the_peak_is_the_worst_hour_and_says_when():
    ore = notte({"wind_gust_kmh": 12.0}, {"wind_gust_kmh": 35.0}, {"wind_gust_kmh": 20.0})
    raffica = misure(ore)["gust"]
    assert (raffica.peak, raffica.peak_at) == (35.0, "2026-09-25T21:00:00+02:00")
    freddo = misure(notte({"temperature_c": 8.0}, {"temperature_c": 3.0}))["temperature"]
    assert (freddo.peak, freddo.peak_at) == (3.0, "2026-09-25T21:00:00+02:00")


def test_a_measure_known_only_in_part_of_the_night_says_which_part():
    """Seeing fino alle 22: la media e' di quelle ore, e la pagina dice "media fino alle 22"."""
    ore = notte({"seeing_arcsec": 1.0}, {"seeing_arcsec": 2.0}, {"seeing_arcsec": None})
    seeing = misure(ore)["seeing"]
    assert seeing.value == 1.5
    assert (seeing.known_hours, seeing.known_since, seeing.known_until) == (
        2,
        "2026-09-25T20:00:00+02:00",
        "2026-09-25T22:00:00+02:00",
    )


def test_only_the_dark_is_judged_for_the_night():
    """Le raffiche del pomeriggio non pesano sulla notte."""
    ore = notte({}, prima=("day", "civil"))
    ore[0].values["wind_gust_kmh"] = 60.0
    assert misure(ore)["gust"].level == "go"


def test_the_clouds_are_the_verdict_and_never_weigh():
    """Il totale delle nuvole e' il semaforo: la sua parola e' il verdetto, e non sta fra cio' che
    pesa."""
    nuvole = misure(notte({"cloud_total_pct": 40.0}))["cloud"]
    assert nuvole.level == "marginal"
    assert not nuvole.weighs


def test_the_clouds_count_the_hours_as_bad_as_the_verdict_or_worse():
    """Nuvole 0, 0, 100, 60: media 40, incerta; nessuna ora e' incerta, ma due sono peggio: sono
    quelle le ore che il verdetto ha visto."""
    ore = notte(*({"cloud_total_pct": c} for c in (0.0, 0.0, 100.0, 60.0)))
    nuvole = misure(ore)["cloud"]
    assert (nuvole.level, nuvole.since, nuvole.hours) == (
        "marginal",
        "2026-09-25T22:00:00+02:00",
        2,
    )


def test_good_and_neutral_measures_do_not_weigh():
    detto = misure(notte({"aerosol_optical_depth": 0.05, "humidity_pct": 99.0}))
    assert detto["aerosol"].level == "go"
    assert not detto["aerosol"].weighs
    assert detto["humidity"].level is None
    assert not detto["humidity"].weighs


def test_the_moon_is_left_out_when_it_is_never_up_in_the_dark():
    assert "moon" not in misure(notte({}, {}))
    assert misure(notte({}, {"moon_pct": 60.0}))["moon"].weighs


def test_the_order_is_clouds_then_nogo_then_marginal_then_go_earliest_first_then_neutral():
    ore = notte(
        {"wind_kmh": 22.0},
        {"wind_gust_kmh": 30.0, "seeing_arcsec": 1.0},
        {"precip_mm": 0.2, "seeing_arcsec": 1.0},
    )
    codici = [m.code for m in judge.measures(ore, verdict.assess(ore))]
    assert codici[0] == "cloud"
    assert codici[1:4] == ["gust", "rain", "wind"]
    giudicate = [c for c in codici if c in judge.SCALES]
    neutre = [c for c in codici if c not in judge.SCALES]
    assert codici == giudicate + neutre
    assert neutre == [c for c in judge.NEUTRAL if c in neutre]


def test_every_scale_is_sent_with_its_steps():
    """Le soglie arrivano dal backend, le stesse del giudizio: la scala a destra le disegna."""
    passi = {s.code: s.steps for s in judge.scales()}
    assert passi["wind"] == [
        judge.Step("nogo", 29.0, strict=False),
        judge.Step("marginal", 20.0, strict=False),
    ]
    assert passi["aerosol"] == [
        judge.Step("nogo", 1.0, strict=False),
        judge.Step(None, 0.1, strict=False),
    ]
    assert set(passi) == set(judge.SCALES)
