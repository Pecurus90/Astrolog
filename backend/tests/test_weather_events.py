"""Gli eventi della notte del Meteo (passo 13.1): dal tramonto all'alba, uno per riga, come la
tavola v82 (Meteo.dc.html:460-499). Ore e fasce costruite qui: la regola, non l'effemeride."""

from collections.abc import Mapping
from datetime import datetime, timedelta

from astrolog.ephemeris.moon import MoonNight, TrackPoint
from astrolog.ephemeris.planets import Planet, PlanetNight
from astrolog.ephemeris.sun import Sky, SkyBand
from astrolog.levels import MoonRule, Verdict
from astrolog.weather import events
from astrolog.weather.events import Group, Kind
from astrolog.weather.verdict import Hour

ZONA = "+01:00"
INIZIO = datetime.fromisoformat(f"2026-11-24T17:00{ZONA}")


def ora(n: int) -> datetime:
    return INIZIO + timedelta(hours=n)


def iso(n: float) -> str:
    return (INIZIO + timedelta(hours=n)).isoformat(timespec="minutes")


# 17-18 giorno, 18-21 crepuscoli, 21-05 buio, 05-06 crepuscolo, 06-07 giorno; tramonto 17:40,
# alba 06:20. Il buio va dalle 21 (ora 4) alle 05 (ora 12).
FASCE = [
    SkyBand(ora(0), ora(0) + timedelta(minutes=40), Sky.DAY),
    SkyBand(ora(0) + timedelta(minutes=40), ora(4), Sky.NAUTICAL),
    SkyBand(ora(4), ora(12), Sky.DARK),
    SkyBand(ora(12), ora(13) + timedelta(minutes=20), Sky.NAUTICAL),
    SkyBand(ora(13) + timedelta(minutes=20), ora(14), Sky.DAY),
]


def cielo(n: int) -> Sky:
    if n == 0 or n >= 14:
        return Sky.DAY
    return Sky.DARK if 4 <= n < 12 else Sky.NAUTICAL


def ore(**per_ora: Mapping[int, float | None]) -> list[Hour]:
    """Quindici ore, nuvole a zero dove non dette; ogni campo per ora."""
    out = []
    for n in range(15):
        valori: dict[str, float | None] = {"cloud_total_pct": 0.0}
        for campo, serie in per_ora.items():
            if n in serie:
                valori[campo] = serie[n]
        out.append(Hour(at=iso(n), sky=cielo(n), values=valori))
    return out


def eventi(hours=None, moon=None, lit=None, planets=(), rule=MoonRule()):
    sky = events.NightSky(FASCE, moon, list(planets), lit)
    return events.night_events(hours or ore(), sky, rule)


def di(kind: Kind, lista):
    return [e for e in lista if e.kind == kind]


def test_the_sun_and_the_dark_come_to_the_minute_from_the_sky_bands():
    lista = eventi()
    assert [(e.kind, e.at) for e in lista if e.group in (Group.SUN, Group.SKY)] == [
        (Kind.SUNSET, "2026-11-24T17:40+01:00"),
        (Kind.DARK_START, iso(4)),
        (Kind.DARK_END, iso(12)),
        (Kind.SUNRISE, "2026-11-25T06:20+01:00"),
    ]
    assert di(Kind.DARK_START, lista)[0].until == iso(12)


def test_a_sunset_with_seconds_is_said_to_the_minute_and_stays_in():
    secondi = timedelta(minutes=40, seconds=32)
    fasce = [
        SkyBand(ora(0), ora(0) + secondi, Sky.DAY),
        SkyBand(ora(0) + secondi, ora(4), Sky.NAUTICAL),
        *FASCE[2:],
    ]
    lista = events.night_events(ore(), events.NightSky(fasce, None, [], None), MoonRule())
    assert lista[0].kind == Kind.SUNSET and lista[0].at == "2026-11-24T17:40+01:00"


def test_a_night_without_dark_has_no_dark_events():
    senza = [
        SkyBand(b.starts_at, b.ends_at, Sky.ASTRONOMICAL if b.kind == Sky.DARK else b.kind)
        for b in FASCE
    ]
    lista = events.night_events(ore(), events.NightSky(senza, None, [], None), MoonRule())
    assert not di(Kind.DARK_START, lista) and not di(Kind.DARK_END, lista)
    assert di(Kind.SUNSET, lista) and di(Kind.SUNRISE, lista)


def test_the_verdict_tells_each_stretch_of_the_dark_with_its_lowest_transparency():
    nuvole = {n: 0.0 for n in range(15)} | {7: 40.0, 8: 35.0}
    lista = di(Kind.VERDICT, eventi(ore(cloud_total_pct=nuvole)))
    assert [(e.at, e.level, e.value) for e in lista] == [
        (iso(4), Verdict.GO, 100.0),
        (iso(7), Verdict.MARGINAL, 60.0),
        (iso(9), Verdict.GO, 100.0),
    ]


def test_an_hour_without_clouds_is_a_stretch_that_does_not_know_until_the_next_known():
    nuvole = {n: 0.0 for n in range(15)} | {5: None, 6: None}
    lista = eventi(ore(cloud_total_pct=nuvole))
    ignoto = di(Kind.SKY_UNKNOWN, lista)
    assert [(e.at, e.until, e.level) for e in ignoto] == [(iso(5), iso(7), None)]
    assert [e.at for e in di(Kind.VERDICT, lista)] == [iso(4), iso(7)]


def test_the_clouds_crossing_a_class_say_over_or_under_its_bound():
    nuvole = {n: 0.0 for n in range(15)} | {6: 30.0, 7: 60.0, 8: 10.0}
    lista = eventi(ore(cloud_total_pct=nuvole))
    assert [
        (e.kind, e.at, e.bound, e.value)
        for e in lista
        if e.kind in (Kind.CLOUDS_OVER, Kind.CLOUDS_UNDER)
    ] == [
        (Kind.CLOUDS_OVER, iso(6), 25.0, 30.0),
        (Kind.CLOUDS_OVER, iso(7), 50.0, 60.0),
        (Kind.CLOUDS_UNDER, iso(8), 50.0, 10.0),
    ]


def test_the_clouds_outside_the_dark_tell_nothing():
    nuvole = {n: 0.0 for n in range(15)} | {2: 80.0}
    assert not di(Kind.CLOUDS_OVER, eventi(ore(cloud_total_pct=nuvole)))


def test_the_rain_starts_and_ends_with_its_amount():
    lista = eventi(ore(precip_mm={6: 0.4, 7: 0.2, 8: 0.0}))
    assert [
        (e.kind, e.at, e.value) for e in lista if e.group == Group.MEASURE and "rain" in e.kind
    ] == [
        (Kind.RAIN_START, iso(6), 0.4),
        (Kind.RAIN_END, iso(8), None),
    ]


def test_the_condensation_is_the_first_hour_under_its_hours_dew_threshold():
    """Alle 9 lo scarto 2,0 sta sotto la soglia 2,43: l'evento dice la soglia di quell'ora,
    scritta per eccesso (2,5) perche' lo scarto resti sotto anche scritto."""
    caldo = {n: 10.0 for n in range(15)}
    rugiada = {n: 5.0 for n in range(15)} | {9: 8.0, 10: 8.5}
    soglia = {n: 4.0 for n in range(15)} | {8: 2.43, 9: 2.43}
    lista = di(
        Kind.CONDENSATION,
        eventi(ore(temperature_c=caldo, dew_point_c=rugiada, dew_threshold_c=soglia)),
    )
    assert [(e.at, e.value, e.bound) for e in lista] == [(iso(9), 2.0, 2.5)]


def test_the_gusts_peak_inside_the_dark():
    lista = di(Kind.GUST_PEAK, eventi(ore(wind_gust_kmh={2: 60.0, 5: 20.0, 9: 31.0})))
    assert [(e.at, e.value) for e in lista] == [(iso(9), 31.0)]


def test_the_best_seeing_is_the_lowest_inside_the_dark_and_absent_without_a_number():
    assert [
        (e.at, e.value)
        for e in di(Kind.SEEING_BEST, eventi(ore(seeing_arcsec={5: 1.8, 8: 1.2, 2: 0.9})))
    ] == [(iso(8), 1.2)]
    assert not di(Kind.SEEING_BEST, eventi())


def luna(rise=None, set_=None) -> MoonNight:
    punto = TrackPoint(ora(5), 30.0)
    return MoonNight(rise=rise, set=set_, highest=punto, track=[punto], grid=[punto])


def test_the_moon_rises_with_its_lit_part_and_sets():
    lista = eventi(moon=luna(rise=ora(6) + timedelta(minutes=12), set_=None), lit=48)
    assert [(e.kind, e.at, e.value) for e in lista if e.group == Group.MOON] == [
        (Kind.MOON_RISE, "2026-11-24T23:12+01:00", 48.0)
    ]


def test_the_moon_weighs_from_where_it_climbs_over_the_rule_and_says_the_band():
    # sopra la soglia dalle 23 alle 02 al 70%: oltre il limite della regola, banda stretta
    lista = eventi(ore(moon_pct={6: 70, 7: 70, 8: 70}))
    assert [(e.kind, e.at, e.level, e.value) for e in lista if e.group == Group.SHOOTING] == [
        (Kind.MOON_ABOVE, iso(6), Verdict.NOGO, 0.0),
        (Kind.MOON_BELOW, iso(9), Verdict.NOGO, 0.0),
    ]


def test_the_moon_says_nothing_when_it_weighs_the_whole_dark_or_never():
    tutta = {n: 70 for n in range(15)}
    assert not [e for e in eventi(ore(moon_pct=tutta)) if e.group == Group.SHOOTING]
    poca = {6: 10, 7: 10}
    assert not [e for e in eventi(ore(moon_pct=poca)) if e.group == Group.SHOOTING]


def test_the_moon_threshold_says_the_degrees_of_the_setting():
    lista = eventi(ore(moon_pct={6: 70}), rule=MoonRule(floor_deg=10.0))
    assert di(Kind.MOON_ABOVE, lista)[0].value == 10.0


def pianeta(alt_per_quarto: list[float]) -> PlanetNight:
    return PlanetNight(
        key=Planet.JUPITER,
        track=[
            TrackPoint(INIZIO + timedelta(minutes=15 * i), a) for i, a in enumerate(alt_per_quarto)
        ],
    )


def test_a_planet_rises_culminates_over_thirty_degrees_and_sets():
    salita = [-10.0 + 2.0 * i for i in range(28)]  # da -10 a 44, culmina alle 00:00
    curva = salita + salita[-2::-1]
    lista = [e for e in eventi(planets=[pianeta(curva)]) if e.group == Group.PLANET]
    assert [e.kind for e in lista] == [Kind.PLANET_RISE, Kind.PLANET_TOP, Kind.PLANET_SET]
    assert lista[1].value == 44.0 and lista[1].body == Planet.JUPITER


def test_a_planet_that_stays_low_does_not_culminate():
    curva = [5.0 + i * 0.1 for i in range(28)] + [7.7 - i * 0.1 for i in range(28)]
    assert not di(Kind.PLANET_TOP, eventi(planets=[pianeta(curva)]))


def test_the_events_run_from_sunset_to_sunrise_in_order_sun_first_then_the_verdict():
    lista = eventi(ore(precip_mm={0: 1.0}))
    assert not di(Kind.RAIN_START, lista)  # alle 17:00, prima del tramonto
    a_pari = [e for e in lista if e.at == iso(4)]
    assert [e.group for e in a_pari] == [Group.SKY, Group.VERDICT]
    istanti = [datetime.fromisoformat(e.at) for e in lista]
    assert istanti == sorted(istanti)


def test_the_moments_that_matter_are_the_sky_the_verdict_the_moon_and_the_shooting():
    lista = eventi(ore(moon_pct={6: 70}, wind_gust_kmh={6: 20.0}), moon=luna(rise=ora(6)), lit=50)
    contano = {e.group for e in lista if e.key_moment}
    assert contano == {Group.SKY, Group.VERDICT, Group.MOON, Group.SHOOTING}
