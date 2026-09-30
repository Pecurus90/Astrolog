"""Il cielo in quota: 7Timer (seeing e trasparenza in fasce) e CAMS (aerosol e polveri), scritti
ognuno nelle sue righe, per notte, accanto alla previsione.

Nessuna prova esce di casa: le risposte finte hanno la forma di quelle vere (misurate il 26/9/2026).
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from astrolog.weather import cams, forecast, openmeteo, rounds, seventimer, sky
from test_weather_forecast import (  # noqa: F401 - `db` e' una fixture
    ADESSO,
    SITO,
    Finto,
    db,
    righe,
    risposta,
)


def settetimer(init="2026092512", passi=24, seeing=5, trasparenza=6):
    """Una risposta ASTRO: `init` e' il run in UTC, e ogni voce dice a quante ore da li' cade."""
    return {
        "product": "astro",
        "init": init,
        "dataseries": [
            {"timepoint": 3 * (i + 1), "seeing": seeing, "transparency": trasparenza}
            for i in range(passi)
        ],
    }


def aria(inizio="2026-09-24T00:00", ore=8 * 24, aod=0.12, polveri: float | None = 3.0):
    t0 = datetime.fromisoformat(inizio)
    return {
        "hourly": {
            "time": [(t0 + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(ore)],
            "aerosol_optical_depth": [aod] * ore,
            "dust": [polveri] * ore,
        }
    }


class Instradato:
    """Una chiamata finta che risponde secondo il servizio chiesto."""

    def __init__(self, **per_servizio):
        self.per_servizio = per_servizio
        self.chiesti = []

    def __call__(self, url):
        self.chiesti.append(url)
        for pezzo, risposta_ in self.per_servizio.items():
            if pezzo in url:
                if isinstance(risposta_, Exception):
                    raise risposta_
                return risposta_
        raise AssertionError(f"servizio non previsto: {url}")


def tutti(**cambi):
    """Tutti i servizi rispondono; `cambi` ne sostituisce qualcuno, col pezzo del suo indirizzo."""
    return Instradato(
        **{"/v1/forecast": risposta(), "7timer": settetimer(), "air-quality": aria(), **cambi}
    )


def test_the_seeing_bands_become_the_ranges_the_service_documents():
    """Fascia 1 = sotto 0,5", 5 = da 1,25" a 1,5", 8 = sopra 2,5": un intervallo, mai un numero
    inventato in mezzo. Fonte: https://www.7timer.info/doc.php?lang=en"""
    tempi, serie = seventimer.parse(
        {"init": "2026092512", "dataseries": [
            {"timepoint": 3, "seeing": 1, "transparency": 1},
            {"timepoint": 6, "seeing": 5, "transparency": 6},
            {"timepoint": 9, "seeing": 8, "transparency": 8},
            {"timepoint": 12, "seeing": 9, "transparency": -9999},
            "una voce che non e' una voce",
            {"seeing": 3},
        ]}
    )  # fmt: skip
    assert tempi[0] == datetime(2026, 9, 25, 15, tzinfo=UTC)
    assert list(zip(serie["seeing_from"], serie["seeing_to"], strict=True)) == [
        (None, 0.5), (1.25, 1.5), (2.5, None), (None, None)
    ]  # fmt: skip
    assert list(zip(serie["transparency_from"], serie["transparency_to"], strict=True)) == [
        (None, 0.3), (0.7, 0.85), (1.0, None), (None, None)
    ]  # fmt: skip


@pytest.mark.parametrize("storta", ["<html/>", {}, {"init": "ieri", "dataseries": []}, [1]])
def test_an_answer_that_is_not_an_astro_forecast_is_refused(storta):
    with pytest.raises(seventimer.BadAnswerError):
        seventimer.parse(storta)


def test_the_air_is_read_as_the_service_gives_it():
    tempi, serie = cams.parse(aria(ore=2, aod=0.3, polveri=None))
    assert tempi == [datetime(2026, 9, 24, 0, tzinfo=UTC), datetime(2026, 9, 24, 1, tzinfo=UTC)]
    assert serie == {"aerosol_optical_depth": [0.3, 0.3], "dust_ugm3": [None, None]}


def test_a_source_every_three_hours_still_gives_the_night_that_is_under_way(db):  # noqa: F811
    """7Timer comincia tre ore dopo il suo run: la notte in corso c'e' lo stesso, con le ore che la
    fonte da'. Non si chiede una notte intera a chi campiona ogni tre ore."""
    sky.refresh(db, SITO, fetch=tutti(), now=ADESSO)
    (riga,) = [r for r in righe(db) if r["source"] == "7timer" and r["night_date"] == "2026-09-25"]
    ore = json.loads(riga["hourly_json"])
    assert [o["at"][11:16] for o in ore][:3] == ["17:00", "20:00", "23:00"]
    assert ore[0]["seeing_from"] == 1.25


def test_each_source_writes_only_its_rows_and_a_silent_one_keeps_them(db):  # noqa: F811
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    sky.refresh(db, SITO, fetch=tutti(), now=ADESSO)
    prima = {r["source"] for r in righe(db)}
    assert {"7timer", "cams"} <= prima
    esiti = sky.refresh(db, SITO, fetch=tutti(**{"7timer": TimeoutError()}), now=ADESSO)
    assert esiti == {"7timer": "unreachable", "cams": "ok"}
    assert {r["source"] for r in righe(db)} == prima
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    assert {r["source"] for r in righe(db)} == prima  # la previsione non tocca le righe del cielo


def test_the_round_asks_the_forecast_and_the_sky_together(db):  # noqa: F811
    assert rounds.refresh(db, SITO, fetch=tutti(), now=ADESSO) == "ok"
    fonti = {r["source"] for r in righe(db)}
    assert {"7timer", "cams", forecast.source_of("best_match")} <= fonti


def test_the_round_does_not_ask_the_sky_without_a_site_to_ask_for(db):  # noqa: F811
    finto = tutti()
    assert rounds.refresh(db, {**SITO, "timezone": None}, fetch=finto, now=ADESSO) == "no_timezone"
    assert finto.chiesti == []


@pytest.mark.parametrize(
    "storta",
    ["<html/>", settetimer(init="2020010100")],  # la seconda e' vera ma non porta nessuna notte
)
def test_a_source_that_answers_wrong_or_without_nights_keeps_its_rows(db, storta):  # noqa: F811
    sky.refresh(db, SITO, fetch=tutti(), now=ADESSO)
    prima = [tuple(r) for r in righe(db) if r["source"] == "7timer"]
    esiti = sky.refresh(db, SITO, fetch=tutti(**{"7timer": storta}), now=ADESSO)
    assert esiti == {"7timer": "bad_answer", "cams": "ok"}
    assert [tuple(r) for r in righe(db) if r["source"] == "7timer"] == prima


@pytest.mark.parametrize(
    "storta",
    ["<html/>", {}, {"hourly": {"time": ["ieri"]}}, {"hourly": {"time": ["2026-09-24T00:00"]}}],
)
def test_an_answer_that_is_not_an_air_series_is_refused(storta):
    with pytest.raises(openmeteo.BadAnswerError):
        cams.parse(storta)
