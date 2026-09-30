"""La previsione: una chiamata a Open-Meteo con piu' modelli, e le notti scritte per ognuno.

Nessuna prova esce di casa: la chiamata e' un finto che risponde come il servizio vero (le chiavi
`<variabile>_<modello>`, gli orari UTC senza fuso), e che si fa guardare cosa gli si chiede.
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from astrolog.db.connect import connect, ensure_database
from astrolog.weather import forecast, openmeteo


def risposta(
    inizio="2026-09-24T00:00", ore=10 * 24, modelli=openmeteo.MODELS, per_modello=None, **valori
):
    """Una risposta di Open-Meteo: ogni variabile vale `valori.get(nostro_nome, 0)` per ogni ora,
    o una funzione dell'ora se e' una funzione; `per_modello` cambia i valori di un modello solo."""
    t0 = datetime.fromisoformat(inizio)
    tempi = [(t0 + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(ore)]
    hourly: dict[str, list] = {"time": tempi}
    for modello in modelli:
        suoi = {**valori, **(per_modello or {}).get(modello, {})}
        for loro, nostro in openmeteo.VARIABLES.items():
            v = suoi.get(nostro, 0.0)
            hourly[f"{loro}_{modello}"] = [v(i) if callable(v) else v for i in range(ore)]
    return {"hourly": hourly}


class Finto:
    def __init__(self, *risposte):
        self.risposte = list(risposte)
        self.chiesti = []

    def __call__(self, url):
        self.chiesti.append(url)
        r = self.risposte.pop(0) if len(self.risposte) > 1 else self.risposte[0]
        if isinstance(r, Exception):
            raise r
        return r


ADESSO = datetime(2026, 9, 25, 15, 0, tzinfo=UTC)
SITO = {"id": 1, "latitude": 45.55, "longitude": 11.55, "timezone": "Europe/Rome"}


@pytest.fixture
def db(tmp_path):
    percorso = tmp_path / "a.db"
    ensure_database(percorso)
    c = connect(percorso)
    c.execute(
        "INSERT INTO sites(id, name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES(1, 'Casa', 45.55, 11.55, 'Europe/Rome', 1, '2026-09-01T00:00:00Z')"
    )
    yield c
    c.close()


def righe(conn):
    return conn.execute(
        "SELECT night_date, source, fetched_at, hourly_json, summary_json FROM weather_nights"
        " ORDER BY source, night_date"
    ).fetchall()


def test_the_request_asks_every_model_the_hours_and_utc():
    url = openmeteo.forecast_url(45.55, 11.55)
    assert url.startswith(openmeteo.FORECAST_URL + "?")
    assert "models=" + "%2C".join(openmeteo.MODELS) in url
    assert "timezone=UTC" in url
    for loro in openmeteo.VARIABLES:
        assert loro in url


def test_the_answer_is_read_per_model_in_utc():
    tempi, letto = openmeteo.parse(risposta(ore=2, cloud_total_pct=lambda i: 10.0 * i))
    assert set(letto) == set(openmeteo.MODELS)
    assert tempi == [datetime(2026, 9, 24, 0, tzinfo=UTC), datetime(2026, 9, 24, 1, tzinfo=UTC)]
    assert letto["best_match"]["cloud_total_pct"] == [0.0, 10.0]


def test_a_model_the_service_did_not_send_is_left_out_not_invented():
    _, letto = openmeteo.parse(risposta(ore=2, modelli=("best_match",)))
    assert set(letto) == {"best_match"}


@pytest.mark.parametrize(
    "storta",
    ["<html>503</html>", {}, {"hourly": {}}, {"hourly": {"time": ["ieri"]}}, [1, 2]],
)
def test_an_answer_that_is_not_a_forecast_is_refused(storta):
    with pytest.raises(openmeteo.BadAnswerError):
        openmeteo.parse(storta)


def test_each_model_writes_its_nights_from_the_current_one(db):
    esito = forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    assert esito == "ok"
    scritte = righe(db)
    notti = sorted({r["night_date"] for r in scritte})
    assert notti[0] == "2026-09-25"  # alle 17 locali la notte in corso e' quella di oggi
    assert {r["source"] for r in scritte} == {f"open-meteo/{m}" for m in openmeteo.MODELS}
    for r in scritte:
        assert r["fetched_at"].startswith("2026-09-25T15:00")


def test_a_night_carries_its_hours_from_noon_to_noon_with_the_sky_of_each(db):
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    (riga,) = [
        r for r in righe(db) if r["night_date"] == "2026-09-25" and "best_match" in r["source"]
    ]
    ore = json.loads(riga["hourly_json"])
    assert len(ore) == 24
    assert ore[0]["at"] == "2026-09-25T12:00:00+02:00"
    assert ore[-1]["at"] == "2026-09-26T11:00:00+02:00"
    assert ore[0]["sky"] == "day"
    assert ore[12]["sky"] == "dark"  # mezzanotte a fine settembre in Veneto
    assert set(openmeteo.VARIABLES.values()) <= set(ore[0])


def test_the_night_the_clocks_change_has_its_true_hours(db):
    adesso = datetime(2026, 10, 24, 15, 0, tzinfo=UTC)
    forecast.refresh(db, SITO, fetch=Finto(risposta(inizio="2026-10-23T00:00")), now=adesso)
    (riga,) = [
        r for r in righe(db) if r["night_date"] == "2026-10-24" and "best_match" in r["source"]
    ]
    assert len(json.loads(riga["hourly_json"])) == 25


def test_the_summary_is_written_with_the_forecast(db):
    """Chi legge non ricalcola: il verdetto si scrive quando arriva la previsione."""
    forecast.refresh(db, SITO, fetch=Finto(risposta(cloud_total_pct=80.0)), now=ADESSO)
    for r in righe(db):
        assert json.loads(r["summary_json"])["verdict"] == "nogo"


def test_a_night_the_answer_does_not_reach_is_not_written(db):
    """Oltre l'orizzonte del modello la notte non c'e': meglio nessuna notte che una vuota."""
    forecast.refresh(db, SITO, fetch=Finto(risposta(ore=3 * 24)), now=ADESSO)
    assert {r["night_date"] for r in righe(db)} == {"2026-09-25"}


def test_a_model_that_sends_only_empty_hours_writes_no_night(db):
    vuoto: dict[str, Any] = {nostro: None for nostro in openmeteo.VARIABLES.values()}
    forecast.refresh(db, SITO, fetch=Finto(risposta(**vuoto)), now=ADESSO)
    assert righe(db) == []


def test_a_night_without_the_total_cloud_is_written_without_a_verdict(db):
    forecast.refresh(db, SITO, fetch=Finto(risposta(cloud_total_pct=None)), now=ADESSO)
    assert righe(db)
    assert all(json.loads(r["summary_json"])["verdict"] is None for r in righe(db))


@pytest.mark.parametrize(("guasto", "codice"), [(None, "unreachable"), ("<html/>", "bad_answer")])
def test_a_silent_service_keeps_the_last_forecast_and_says_so(db, guasto, codice):
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    prima = [tuple(r) for r in righe(db)]
    fetch = Finto(TimeoutError()) if guasto is None else Finto(guasto)
    assert forecast.refresh(db, SITO, fetch=fetch, now=ADESSO + timedelta(hours=3)) == codice
    assert [tuple(r) for r in righe(db)] == prima


def test_without_a_home_site_or_its_timezone_nothing_is_asked(db):
    finto = Finto(risposta())
    assert forecast.refresh(db, None, fetch=finto, now=ADESSO) == "no_site"
    assert (
        forecast.refresh(db, {**SITO, "timezone": None}, fetch=finto, now=ADESSO) == "no_timezone"
    )
    assert finto.chiesti == []
    assert righe(db) == []


def test_a_new_forecast_replaces_the_old_one_of_that_site(db):
    forecast.refresh(db, SITO, fetch=Finto(risposta(cloud_total_pct=80.0)), now=ADESSO)
    dopo = ADESSO + timedelta(days=1)
    forecast.refresh(db, SITO, fetch=Finto(risposta(inizio="2026-09-25T00:00")), now=dopo)
    notti = {r["night_date"] for r in righe(db)}
    assert "2026-09-25" not in notti  # la notte passata non resta come se fosse una previsione
    assert all(json.loads(r["summary_json"])["verdict"] == "go" for r in righe(db))


def test_an_answer_that_brings_no_whole_night_leaves_the_last_forecast_alone(db):
    """Una risposta ben formata ma vuota non e' una previsione nuova: non cancella la vecchia."""
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    prima = [tuple(r) for r in righe(db)]
    vuota = {"hourly": {"time": ["2026-09-25T00:00", "2026-09-25T01:00"]}}
    assert forecast.refresh(db, SITO, fetch=Finto(vuota), now=ADESSO) == "bad_answer"
    assert [tuple(r) for r in righe(db)] == prima


def test_a_new_forecast_leaves_other_sites_and_the_observed_weather_alone(db):
    db.execute(
        "INSERT INTO sites(id, name, latitude, longitude, timezone, created_at)"
        " VALUES(2, 'Altrove', 40.0, 10.0, 'Europe/Rome', '2026-09-01T00:00:00Z')"
    )
    riga = "INSERT INTO weather_nights VALUES(?, '2026-09-20', ?, 'x', 't', '[]', NULL)"
    db.execute(riga, (2, "forecast"))
    db.execute(riga, (1, "observed"))
    forecast.refresh(db, SITO, fetch=Finto(risposta()), now=ADESSO)
    restano = db.execute(
        "SELECT site_id, kind FROM weather_nights WHERE night_date = '2026-09-20' ORDER BY site_id"
    ).fetchall()
    assert [tuple(r) for r in restano] == [(1, "observed"), (2, "forecast")]


def test_the_round_runs_when_a_home_site_appears_or_changes():
    cadenza = forecast.Cadence(3600)
    assert not cadenza.due(None, 0.0)
    assert cadenza.due(SITO, 0.0)
    cadenza.done(SITO, "ok", 0.0)
    assert not cadenza.due(SITO, 60.0)
    assert cadenza.due({**SITO, "latitude": 40.0}, 60.0)


def test_after_a_good_round_the_next_is_the_full_interval():
    cadenza = forecast.Cadence(3600)
    cadenza.done(SITO, "ok", 100.0)
    assert not cadenza.due(SITO, 100.0 + 3599)
    assert cadenza.due(SITO, 100.0 + 3600)


@pytest.mark.parametrize("esito", ["unreachable", "bad_answer"])
def test_after_a_failed_round_it_tries_again_sooner(esito):
    cadenza = forecast.Cadence(3600)
    cadenza.done(SITO, esito, 0.0)
    assert not cadenza.due(SITO, forecast.RETRY_S - 1)
    assert cadenza.due(SITO, forecast.RETRY_S)


def test_a_site_without_timezone_is_not_tried_again_every_few_minutes():
    senza = {**SITO, "timezone": None}
    cadenza = forecast.Cadence(3600)
    cadenza.done(senza, "no_timezone", 0.0)
    assert not cadenza.due(senza, forecast.RETRY_S)
    assert cadenza.due(senza, 3600)


def test_a_silent_service_is_said_once_in_the_log_and_a_wrong_answer_is_said(db, caplog):
    caplog.set_level("INFO")
    forecast.refresh(db, SITO, fetch=Finto(TimeoutError()), now=ADESSO)
    assert [r.name for r in caplog.records] == ["astrolog.net"]
    caplog.clear()
    forecast.refresh(db, SITO, fetch=Finto("<html/>"), now=ADESSO)
    assert [r.name for r in caplog.records] == ["astrolog.weather.forecast"]


def test_each_night_says_how_many_models_agree(db):
    """L'accordo si scrive con la previsione, uguale in ogni modello: chi legge non conta."""
    diversi = {"ecmwf_ifs025": {"cloud_total_pct": 40.0}, "gfs_seamless": {"cloud_total_pct": None}}
    forecast.refresh(db, SITO, fetch=Finto(risposta(per_modello=diversi)), now=ADESSO)
    for r in righe(db):
        if r["night_date"] == "2026-09-25":
            accordo = json.loads(r["summary_json"])["agreement"]
            assert accordo == {"go": 2, "marginal": 1, "nogo": 0, "unknown": 1, "total": 4}


def test_a_model_that_says_nothing_on_a_night_counts_among_those_that_do_not_know(db):
    vuoto = {nostro: None for nostro in openmeteo.VARIABLES.values()}
    forecast.refresh(
        db, SITO, fetch=Finto(risposta(per_modello={"gfs_seamless": vuoto})), now=ADESSO
    )
    (riga,) = [
        r for r in righe(db) if r["night_date"] == "2026-09-25" and "best_match" in r["source"]
    ]
    assert json.loads(riga["summary_json"])["agreement"] == {
        "go": 3, "marginal": 0, "nogo": 0, "unknown": 1, "total": 4
    }  # fmt: skip


def test_each_night_has_its_own_agreement(db):
    """ECMWF vede nuvole solo la prima notte: la seconda i modelli sono tutti d'accordo."""
    prima_notte = {"cloud_total_pct": lambda i: 40.0 if i < 24 + 36 else 0.0}
    forecast.refresh(
        db, SITO, fetch=Finto(risposta(per_modello={"ecmwf_ifs025": prima_notte})), now=ADESSO
    )
    accordi = {
        r["night_date"]: json.loads(r["summary_json"])["agreement"]["go"]
        for r in righe(db)
        if "best_match" in r["source"]
    }
    assert (accordi["2026-09-25"], accordi["2026-09-26"]) == (3, 4)
