"""Il cielo in quota senza chiave: CAMS (aerosol e polveri), scritto nelle sue righe, per notte,
accanto alla previsione. Nessuna fonte a fasce o ogni tre ore: 7Timer e' uscito (3/10/2026).

Nessuna prova esce di casa: le risposte finte hanno la forma di quelle vere (misurate il 26/9/2026).
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from astrolog.weather import cams, forecast, openmeteo, rounds, sky
from astrolog.weather.fetches import Source
from test_weather_forecast import (  # noqa: F401 - `db` e' una fixture
    ADESSO,
    SITO,
    Finto,
    db,
    righe,
    risposta,
)


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
    return Instradato(**{"/v1/forecast": risposta(), "air-quality": aria(), **cambi})


def test_without_a_key_the_sky_is_asked_only_to_cams():
    """7Timer non si chiede piu': il seeing viene solo da Meteoblue, con la chiave."""
    assert set(sky.SOURCES) == {Source.CAMS}
    assert set(sky.ALL_SOURCES) == {Source.CAMS, Source.METEOBLUE}
    assert "7timer" not in {s.value for s in Source}


def test_the_air_is_read_as_the_service_gives_it():
    tempi, serie = cams.parse(aria(ore=2, aod=0.3, polveri=None))
    assert tempi == [datetime(2026, 9, 24, 0, tzinfo=UTC), datetime(2026, 9, 24, 1, tzinfo=UTC)]
    assert serie == {"aerosol_optical_depth": [0.3, 0.3], "dust_ugm3": [None, None]}


def test_a_series_that_starts_late_still_gives_the_night_that_is_under_way(db):  # noqa: F811
    """Una serie che parte a notte iniziata (qui alle 15 UTC, 17 a Roma): la notte in corso c'e'
    lo stesso, con le ore che la fonte da'. Non si chiede una notte intera al cielo."""
    assert sky.refresh(
        db,
        SITO,
        fetch=tutti(**{"air-quality": aria(inizio="2026-09-25T15:00", ore=48)}),
        now=ADESSO,
    ) == {"cams": "ok"}
    (riga,) = [r for r in righe(db) if r["source"] == "cams" and r["night_date"] == "2026-09-25"]
    ore = json.loads(riga["hourly_json"])
    assert [o["at"][11:16] for o in ore][:2] == ["17:00", "18:00"]


def test_each_source_writes_only_its_rows_and_a_silent_one_keeps_them(db):  # noqa: F811
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    sky.refresh(db, SITO, fetch=tutti(), now=ADESSO)
    prima = {r["source"] for r in righe(db)}
    assert "cams" in prima
    esiti = sky.refresh(db, SITO, fetch=tutti(**{"air-quality": TimeoutError()}), now=ADESSO)
    assert esiti == {"cams": "unreachable"}
    assert {r["source"] for r in righe(db)} == prima
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    assert {r["source"] for r in righe(db)} == prima  # la previsione non tocca le righe del cielo


def test_the_round_asks_the_forecast_and_the_sky_together(db):  # noqa: F811
    assert rounds.refresh(db, SITO, fetch=tutti(), now=ADESSO) == "ok"
    fonti = {r["source"] for r in righe(db)}
    assert {"cams", forecast.source_of("best_match")} <= fonti


def test_the_round_does_not_ask_the_sky_without_a_site_to_ask_for(db):  # noqa: F811
    finto = tutti()
    assert rounds.refresh(db, {**SITO, "timezone": None}, fetch=finto, now=ADESSO) == "no_timezone"
    assert finto.chiesti == []


@pytest.mark.parametrize(
    "storta",
    ["<html/>", aria(inizio="2020-01-01T00:00")],  # la seconda e' vera ma non porta nessuna notte
)
def test_a_source_that_answers_wrong_or_without_nights_keeps_its_rows(db, storta):  # noqa: F811
    sky.refresh(db, SITO, fetch=tutti(), now=ADESSO)
    prima = [tuple(r) for r in righe(db) if r["source"] == "cams"]
    esiti = sky.refresh(db, SITO, fetch=tutti(**{"air-quality": storta}), now=ADESSO)
    assert esiti == {"cams": "bad_answer"}
    assert [tuple(r) for r in righe(db) if r["source"] == "cams"] == prima


@pytest.mark.parametrize(
    "storta",
    ["<html/>", {}, {"hourly": {"time": ["ieri"]}}, {"hourly": {"time": ["2026-09-24T00:00"]}}],
)
def test_an_answer_that_is_not_an_air_series_is_refused(storta):
    with pytest.raises(openmeteo.BadAnswerError):
        cams.parse(storta)
