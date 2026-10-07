"""Il vento in quota tipico del sito: un anno di notti, il vento a 700 hPa di ognuna sulle ore su
cui la si giudica, e dove cade stanotte rispetto a loro. Nessuna soglia: una posizione.

Le risposte finte hanno la forma di quelle vere (misurate il 26/9/2026 sull'archivio delle
previsioni: un anno intero in una chiamata, ore UTC senza fuso).
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from astrolog.weather import climate, forecast, position, view
from test_weather_forecast import (  # noqa: F401 - `db` e' una fixture
    SITO,
    Finto,
    db,
    righe,
    risposta,
)

ADESSO = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)


def anno(valore=lambda i: float(i % 50), giorni=366):
    """Un anno di vento a 700 hPa: di fabbrica cresce e ricomincia ogni 50 ore."""
    t0 = datetime(2025, 9, 25)
    ore = giorni * 24
    return {
        "hourly": {
            "time": [(t0 + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(ore)],
            "wind_speed_700hPa": [valore(i) for i in range(ore)],
        }
    }


def _di_giorno(i):
    """Vento forte dalle 9 alle 15 UTC, mai notte a 45 gradi nord; debole il resto."""
    return 100.0 if 9 <= i % 24 <= 15 else 5.0


def mese(valore=lambda i: float(i % 50)):
    """Un mese di vento: basta alle prove che non contano le notti, e costa meno cielo."""
    return anno(valore=valore, giorni=31)


@pytest.fixture
def minimo_di_un_mese(monkeypatch):
    monkeypatch.setattr(climate, "MIN_NIGHTS", 20)


def test_the_climate_of_a_site_is_a_year_of_nights_seen_in_their_own_hours(db):  # noqa: F811
    """Una voce per notte, fatta solo delle sue ore: il vento del giorno non entra."""
    assert climate.step(db, SITO, fetch=Finto(anno(valore=_di_giorno)), now=ADESSO) == "ok"
    riga = db.execute(
        "SELECT nights, percentiles_json FROM weather_climate WHERE site_id = 1"
    ).fetchone()
    assert riga["nights"] == 365  # le notti intere di 366 giorni, non le loro ore
    assert json.loads(riga["percentiles_json"]) == [5.0] * 101


def test_where_the_dark_never_comes_the_climate_uses_the_hours_the_verdict_uses(db):  # noqa: F811
    """A Tromso d'estate il buio pieno non arriva: il solito si misura, come il verdetto, sulle ore
    col Sole sotto l'orizzonte. Solo sul buio mancherebbero i mesi chiari."""
    tromso = {"id": 1, "latitude": 69.65, "longitude": 18.96, "timezone": "Europe/Oslo"}
    assert climate.step(db, tromso, fetch=Finto(anno()), now=ADESSO) == "ok"
    notti = db.execute("SELECT nights FROM weather_climate").fetchone()[0]
    assert 290 < notti < 330  # fuori restano solo le notti del Sole di mezzanotte


def test_the_archive_is_asked_for_the_last_year_up_to_yesterday(db, minimo_di_un_mese):  # noqa: F811
    finto = Finto(mese())
    climate.step(db, SITO, fetch=finto, now=ADESSO)
    assert "historical-forecast-api" in finto.chiesti[0]
    assert "start_date=2025-09-25" in finto.chiesti[0]
    assert "end_date=2026-09-25" in finto.chiesti[0]


def test_the_climate_is_asked_once_a_year(db, minimo_di_un_mese):  # noqa: F811
    finto = Finto(mese())
    climate.step(db, SITO, fetch=finto, now=ADESSO)
    assert climate.step(db, SITO, fetch=finto, now=ADESSO + timedelta(days=364)) is None
    assert climate.step(db, SITO, fetch=finto, now=ADESSO + timedelta(days=366)) == "ok"
    assert len(finto.chiesti) == 2


def test_a_silent_archive_waits_before_trying_again_and_writes_nothing(db, minimo_di_un_mese):  # noqa: F811
    muto = Finto(TimeoutError())
    assert climate.step(db, SITO, fetch=muto, now=ADESSO) == "unreachable"
    assert climate.step(db, SITO, fetch=muto, now=ADESSO + timedelta(minutes=10)) is None
    assert db.execute("SELECT COUNT(*) FROM weather_climate").fetchone()[0] == 0
    assert climate.step(db, SITO, fetch=Finto(mese()), now=ADESSO + timedelta(minutes=16)) == "ok"


def test_too_few_nights_make_no_climate(db, monkeypatch):  # noqa: F811
    """Sotto il minimo di notti il solito sarebbe di una stagione sola: non si scrive."""
    assert climate.step(db, SITO, fetch=Finto(anno(giorni=60)), now=ADESSO) == "bad_answer"
    assert db.execute("SELECT COUNT(*) FROM weather_climate").fetchone()[0] == 0
    # al bordo: 59 notti intere in 60 giorni
    monkeypatch.setattr(climate, "MIN_NIGHTS", 60)
    assert (
        climate.step(db, SITO, fetch=Finto(anno(giorni=60)), now=ADESSO + timedelta(days=1))
        == "bad_answer"
    )
    monkeypatch.setattr(climate, "MIN_NIGHTS", 59)
    assert (
        climate.step(db, SITO, fetch=Finto(anno(giorni=60)), now=ADESSO + timedelta(days=2)) == "ok"
    )


def test_a_year_too_short_is_not_asked_again_every_quarter_of_an_hour(db):  # noqa: F811
    """Un anno corto torna corto: si riprova il giorno dopo, non a ogni giro."""
    corto = Finto(anno(giorni=60))
    climate.step(db, SITO, fetch=corto, now=ADESSO)
    assert climate.step(db, SITO, fetch=corto, now=ADESSO + timedelta(hours=23)) is None
    assert climate.step(db, SITO, fetch=corto, now=ADESSO + timedelta(days=1)) == "bad_answer"
    assert len(corto.chiesti) == 2


def test_a_site_that_moves_asks_its_climate_again_and_is_not_compared_with_the_old_place(
    db,  # noqa: F811
    minimo_di_un_mese,
):
    finto = Finto(mese())
    climate.step(db, SITO, fetch=finto, now=ADESSO)
    spostato = {**SITO, "latitude": 33.4, "longitude": -111.9, "timezone": "America/Phoenix"}
    assert position.percentiles(db, SITO) is not None
    assert position.percentiles(db, spostato) is None
    assert climate.step(db, spostato, fetch=finto, now=ADESSO + timedelta(minutes=1)) == "ok"
    assert "latitude=33.4" in finto.chiesti[1]
    assert position.percentiles(db, spostato) is not None


def test_without_a_site_or_its_timezone_nothing_is_asked(db, minimo_di_un_mese):  # noqa: F811
    finto = Finto(mese())
    assert climate.step(db, None, fetch=finto, now=ADESSO) is None
    assert climate.step(db, {**SITO, "timezone": None}, fetch=finto, now=ADESSO) is None
    assert finto.chiesti == []


def test_the_percentiles_are_interpolated_between_the_two_nearest_nights():
    """Fra due notti vicine il percentile sta sulla retta che le unisce, non su una delle due."""
    percentili = climate._percentiles([40.0, 0.0, 10.0])
    assert (percentili[0], percentili[25], percentili[50], percentili[75], percentili[100]) == (
        0.0,
        5.0,
        10.0,
        25.0,
        40.0,
    )


@pytest.mark.parametrize(
    ("vento", "decimi"), [(-1.0, 0), (0.0, 0), (1000.0, 10), (5.0, 1), (50.0, 10)]
)
def test_the_position_is_how_many_nights_in_ten_had_less_wind(vento, decimi):
    percentili = [float(p) / 2 for p in range(101)]  # da 0 a 50 km/h
    assert position.tenths_below(percentili, vento) == decimi


def test_the_forecast_says_where_each_night_falls_once_the_climate_is_there(db, minimo_di_un_mese):  # noqa: F811
    def scritta(vento):
        forecast.refresh(db, SITO, fetch=Finto(risposta(wind_700hpa_kmh=vento)), now=ADESSO)
        view.rebuild(db, SITO)
        riga = db.execute("SELECT summary_json FROM weather_view ORDER BY night_date").fetchone()
        return json.loads(riga["summary_json"])

    prima = scritta(40.0)
    assert prima["wind_700hpa_kmh"] == 40.0
    assert prima["wind_700hpa_tenths"] is None  # senza climatologia non si confronta
    climate.step(db, SITO, fetch=Finto(mese(valore=lambda i: 20.0 + i % 7)), now=ADESSO)
    assert scritta(40.0)["wind_700hpa_tenths"] == 10
    assert scritta(5.0)["wind_700hpa_tenths"] == 0
