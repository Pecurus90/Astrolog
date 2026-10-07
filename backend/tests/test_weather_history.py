"""Lo storico: il meteo vero delle notti che hai ripreso, dall'archivio di Open-Meteo, una chiamata
per giro, definitivo dopo 5 giorni, e scritto una volta sola.

Le risposte finte hanno la forma di quelle vere (misurate il 26/9/2026): una serie sola, senza
modelli, ore UTC senza fuso.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from astrolog.db.connect import connect, ensure_database
from astrolog.weather import history, openmeteo
from astrolog.weather.fetches import Source
from test_weather_forecast import Finto

ADESSO = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)


def archivio(inizio="2026-01-01T00:00", giorni=400, nuvole=10.0):
    t0 = datetime.fromisoformat(inizio)
    ore = giorni * 24
    hourly: dict[str, list] = {
        "time": [(t0 + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(ore)]
    }
    for loro, nostro in history.VARIABLES.items():
        hourly[loro] = [nuvole if nostro == "cloud_total_pct" else 5.0] * ore
    return {"hourly": hourly}


@pytest.fixture
def db(tmp_path):
    percorso = tmp_path / "a.db"
    ensure_database(percorso)
    c = connect(percorso)
    for sito, nome, lat, fuso in ((1, "Casa", 45.55, "Europe/Rome"), (2, "Altrove", 40.0, None)):
        c.execute(
            "INSERT INTO sites(id, name, latitude, longitude, timezone, is_default, created_at)"
            " VALUES(?, ?, ?, 11.5, ?, ?, '2026-01-01T00:00:00Z')",
            (sito, nome, lat, fuso, int(sito == 1)),
        )
    yield c
    c.close()


def notte(conn, data, sito=1):
    conn.execute(
        "INSERT INTO nights(site_id, night_date, created_at) VALUES(?, ?, '2026-01-01T00:00:00Z')",
        (sito, data),
    )


def scritte(conn):
    return conn.execute(
        "SELECT site_id, night_date, kind, source, summary_json FROM weather_nights"
        " ORDER BY night_date"
    ).fetchall()


def test_a_night_older_than_five_days_gets_its_observed_weather(db):
    notte(db, "2026-03-10")
    assert history.step(db, fetch=Finto(archivio()), now=ADESSO) == "ok"
    (riga,) = scritte(db)
    assert (riga["night_date"], riga["kind"], riga["source"]) == (
        "2026-03-10",
        "observed",
        Source.ARCHIVE,
    )
    assert json.loads(riga["summary_json"])["verdict"] == "go"


def test_a_recent_night_waits_for_the_reanalysis(db):
    """Prima di 5 giorni l'archivio porta il modello di previsione, non ancora la rianalisi. Sul
    confine: la notte del 21 finisce la mattina del 22, e il 22 non ha ancora cinque giorni."""
    notte(db, "2026-09-21")
    finto = Finto(archivio())
    assert history.step(db, fetch=finto, now=ADESSO) is None
    assert finto.chiesti == []
    assert scritte(db) == []


def test_one_call_per_round_covers_many_nights_of_a_site(db):
    for data in ("2026-02-01", "2026-02-02", "2026-06-15"):
        notte(db, data)
    finto = Finto(archivio())
    history.step(db, fetch=finto, now=ADESSO)
    assert len(finto.chiesti) == 1
    assert [r["night_date"] for r in scritte(db)] == ["2026-02-01", "2026-02-02", "2026-06-15"]
    assert "start_date=2026-01-31" in finto.chiesti[0]


def test_a_call_never_asks_more_than_a_year(db):
    notte(db, "2024-03-01")
    notte(db, "2026-03-01")
    finto = Finto(archivio(inizio="2024-02-01T00:00", giorni=800))
    history.step(db, fetch=finto, now=ADESSO)
    assert [r["night_date"] for r in scritte(db)] == ["2024-03-01"]
    history.step(db, fetch=finto, now=ADESSO)
    assert [r["night_date"] for r in scritte(db)] == ["2024-03-01", "2026-03-01"]


def test_the_weather_of_a_night_is_written_once_and_never_again(db):
    notte(db, "2026-03-10")
    history.step(db, fetch=Finto(archivio(nuvole=10.0)), now=ADESSO)
    finto = Finto(archivio(nuvole=90.0))
    assert history.step(db, fetch=finto, now=ADESSO) is None
    assert finto.chiesti == []
    assert json.loads(scritte(db)[0]["summary_json"])["verdict"] == "go"


def test_a_site_without_a_timezone_is_not_asked(db):
    notte(db, "2026-03-10", sito=2)
    finto = Finto(archivio())
    assert history.step(db, fetch=finto, now=ADESSO) is None
    assert finto.chiesti == []


def test_a_silent_archive_waits_before_trying_again(db):
    notte(db, "2026-03-10")
    muto = Finto(TimeoutError())
    assert history.step(db, fetch=muto, now=ADESSO) == "unreachable"
    assert history.step(db, fetch=muto, now=ADESSO + timedelta(minutes=10)) is None
    assert len(muto.chiesti) == 1
    assert history.step(db, fetch=Finto(archivio()), now=ADESSO + timedelta(minutes=16)) == "ok"
    assert len(scritte(db)) == 1


def test_a_night_the_archive_has_nothing_for_is_written_without_a_verdict_and_not_asked_again(db):
    notte(db, "2026-03-10")
    vuoto = archivio(nuvole=10.0)
    for chiave in history.VARIABLES:
        vuoto["hourly"][chiave] = [None] * len(vuoto["hourly"]["time"])
    history.step(db, fetch=Finto(vuoto), now=ADESSO)
    (riga,) = scritte(db)
    assert json.loads(riga["summary_json"])["verdict"] is None
    finto = Finto(archivio())
    assert history.step(db, fetch=finto, now=ADESSO) is None
    assert finto.chiesti == []


@pytest.mark.parametrize("storta", ["<html/>", {}, {"hourly": {"time": ["ieri"]}}])
def test_an_answer_that_is_not_an_archive_is_refused_and_nothing_is_written(db, storta):
    notte(db, "2026-03-10")
    assert history.step(db, fetch=Finto(storta), now=ADESSO) == "bad_answer"
    assert scritte(db) == []


def test_the_archive_is_asked_for_the_same_hours_as_the_forecast_without_the_wind_aloft():
    assert "wind_speed_250hPa" in openmeteo.VARIABLES
    assert set(history.VARIABLES) == {
        "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "temperature_2m",
        "relative_humidity_2m", "dew_point_2m", "wind_speed_10m", "wind_gusts_10m", "precipitation",
    }  # fmt: skip


def test_the_nights_page_reads_the_weather_of_each_night_as_written(db):
    """Chi legge non ricalcola: `ok` col riassunto scritto, `waiting` finche' non c'e', `unknown`
    senza fuso."""
    from astrolog.spine import nights as notti

    notte(db, "2026-03-10")
    notte(db, "2026-09-22")
    notte(db, "2026-03-11", sito=2)
    history.step(db, fetch=Finto(archivio()), now=ADESSO)
    per_data = {
        r["night_date"]: r["weather"]
        for r in notti.page(
            db, limit=10, offset=0, weather=notti.Observed(history.KIND, history.arrives_on)
        )
    }
    assert per_data["2026-03-10"]["state"] == "ok"
    assert per_data["2026-03-10"]["verdict"] == "go"
    assert per_data["2026-03-10"]["usable_hours"] == per_data["2026-03-10"]["window_hours"]
    assert per_data["2026-09-22"]["state"] == "waiting"
    assert per_data["2026-09-22"]["verdict"] is None
    assert history.KIND == "observed"
    assert per_data["2026-03-11"]["state"] == "unknown"


def test_the_archive_is_never_asked_for_days_that_have_not_happened_yet(db):
    """L'archivio rifiuta (400) una richiesta che arriva nel futuro: si chiede fino all'ultima
    notte che serve, e un giorno di margine per il suo mattino."""
    notte(db, "2026-03-10")
    notte(db, "2026-04-02")
    finto = Finto(archivio())
    history.step(db, fetch=finto, now=ADESSO)
    assert "end_date=2026-04-04" in finto.chiesti[0]


def test_the_first_night_old_enough_is_the_one_whose_morning_has_five_days(db):
    notte(db, "2026-09-20")
    assert history.step(db, fetch=Finto(archivio()), now=ADESSO) == "ok"
    assert [r["night_date"] for r in scritte(db)] == ["2026-09-20"]


def test_a_call_covers_a_year_to_the_day(db):
    """Un anno esatto: la notte di un anno dopo entra, quella del giorno dopo va al giro dopo."""
    for data in ("2024-03-01", "2025-03-01", "2025-03-02"):
        notte(db, data)
    finto = Finto(archivio(inizio="2024-02-01T00:00", giorni=800))
    history.step(db, fetch=finto, now=ADESSO)
    assert [r["night_date"] for r in scritte(db)] == ["2024-03-01", "2025-03-01"]


def test_a_night_the_archive_covers_only_in_part_is_not_written(db):
    """La notte del 10 finisce il mattino dell'11: un archivio che si ferma prima non la scrive a
    meta', e si riprova."""
    notte(db, "2026-03-10")
    corto = archivio(inizio="2026-03-09T00:00", giorni=2)
    assert history.step(db, fetch=Finto(corto), now=ADESSO) == "bad_answer"
    assert scritte(db) == []
