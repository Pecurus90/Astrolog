"""La rotta del meteo: legge le notti scritte per il modello scelto, e chiede a richiesta.

Le prove che leggono soltanto partono da una previsione scritta **una volta** (`letto`): passare
ognuna dalla scrittura non prova niente in piu', e fa girare tutte queste prove a ogni sabotaggio di
chi scrive -- misurato, e' cio' che portava il cancello sopra il suo tetto. Sulla scrittura restano
le prove che la provano davvero: il pulsante, il giro in sottofondo, il servizio muto.
"""

import shutil
import threading
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect, create_database
from astrolog.spine.group_store import home_site
from astrolog.weather import forecast, openmeteo, rounds, sky
from conftest import wait_until
from test_weather_forecast import Finto, risposta

# i servizi che una prova non finge da se' non rispondono: e' il sito buio
pytestmark = pytest.mark.usefixtures("offline")


def attorno_ad_adesso():
    """Una risposta che copre la notte in corso e le prossime, qualunque giorno giri la prova."""
    inizio = (datetime.now(UTC) - timedelta(days=2)).strftime("%Y-%m-%dT00:00")
    return risposta(inizio=inizio, ore=12 * 24)


def metti_casa(db_path, timezone: str | None = "Europe/Rome"):
    c = connect(db_path)
    c.execute(
        "INSERT INTO sites(id, name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES(1, 'Casa', 45.55, 11.55, ?, 1, '2026-09-01T00:00:00Z')",
        (timezone,),
    )
    c.close()


@pytest.fixture
def con_casa(db_path, client_vuoto):
    metti_casa(db_path)
    return client_vuoto


def test_without_a_home_site_the_page_says_so_and_asks_nothing(client_vuoto, monkeypatch):
    finto = Finto(risposta())
    monkeypatch.setattr(forecast, "_fetch", finto)
    detto = client_vuoto.get("/api/v1/weather").json()
    assert detto["site"] is None
    assert detto["nights"] == []
    assert detto["models"] == list(openmeteo.MODELS)
    assert client_vuoto.post("/api/v1/weather/refresh").json() == {"status": "no_site"}
    assert finto.chiesti == []


def test_before_any_forecast_the_page_has_no_nights_and_no_time(con_casa):
    detto = con_casa.get("/api/v1/weather").json()
    assert detto["site"] == "Casa"
    assert detto["fetched_at"] is None
    assert detto["nights"] == []


def test_the_button_asks_and_the_page_reads_the_nights_of_the_chosen_model(con_casa, monkeypatch):
    monkeypatch.setattr(forecast, "_fetch", Finto(attorno_ad_adesso()))
    assert con_casa.post("/api/v1/weather/refresh").json() == {"status": "ok"}
    detto = con_casa.get("/api/v1/weather").json()
    assert detto["model"] == "best_match"
    assert detto["fetched_at"]
    notte = detto["nights"][0]
    assert notte["verdict"] == "go"
    assert len(notte["hours"]) in (23, 24, 25)
    assert {"at", "sky", "cloud_low_pct", "dew_point_c", "wind_gust_kmh"} <= set(notte["hours"][0])
    date = [n["night"] for n in detto["nights"]]
    assert date == sorted(date)


def test_the_switch_reads_another_model_without_asking_again(letto, monkeypatch, db_path):
    finto = Finto(attorno_ad_adesso())
    monkeypatch.setattr(forecast, "_fetch", finto)
    c = connect(db_path)
    c.execute(
        "UPDATE weather_view SET summary_json = json_set(summary_json, '$.verdict', 'nogo')"
        " WHERE model = 'icon_seamless'",
    )
    c.close()
    letto.patch("/api/v1/settings", json={"values": {"weather_model": "icon_seamless"}})
    detto = letto.get("/api/v1/weather").json()
    assert detto["model"] == "icon_seamless"
    assert {n["verdict"] for n in detto["nights"]} == {"nogo"}
    assert finto.chiesti == []


def test_a_model_outside_the_list_is_refused(con_casa):
    risposta_ = con_casa.patch("/api/v1/settings", json={"values": {"weather_model": "windy"}})
    assert risposta_.status_code == 422


def test_a_silent_service_says_why_and_the_last_forecast_stays(con_casa, monkeypatch):
    monkeypatch.setattr(forecast, "_fetch", Finto(attorno_ad_adesso()))
    con_casa.post("/api/v1/weather/refresh")
    prima = con_casa.get("/api/v1/weather").json()
    assert prima["last_request"]["status"] == "ok"
    monkeypatch.setattr(forecast, "_fetch", Finto(TimeoutError()))
    assert con_casa.post("/api/v1/weather/refresh").json() == {"status": "unreachable"}
    dopo = con_casa.get("/api/v1/weather").json()
    # la previsione resta com'era; l'ultima richiesta dice che non ha avuto risposta, e quando
    assert dopo["last_request"]["status"] == "unreachable"
    assert {**dopo, "last_request": None} == {**prima, "last_request": None}


def test_the_forecast_renews_itself_in_the_background(db_path, monkeypatch):
    """Con la cadenza accesa la previsione arriva da sola, subito e poi a ogni giro, col cielo."""
    metti_casa(db_path)
    finto = dintorni_del_cielo()
    monkeypatch.setattr(forecast, "_fetch", finto)
    monkeypatch.setattr(sky, "_fetch", finto)
    app = create_app(db_path, weather_every_s=3600)
    with TestClient(app, base_url="http://localhost") as c:
        assert wait_until(lambda: c.get("/api/v1/weather").json()["sources"])
        # il giro non tiene aperto il processo quando l'app si chiude
        giri = [t for t in threading.enumerate() if t.name == "astrolog-weather"]
        assert giri and all(t.daemon for t in giri)
    assert len([u for u in finto.chiesti if "/v1/forecast" in u]) == 1


def test_a_home_site_declared_later_gets_its_forecast_without_waiting_the_full_round(
    db_path, monkeypatch
):
    """Il giro guarda il sito di casa spesso: chi lo dichiara ora non aspetta tre ore."""
    from astrolog.api import app as fabbrica

    monkeypatch.setattr(fabbrica, "_WEATHER_TICK_S", 0.05)
    finto = Finto(attorno_ad_adesso())
    monkeypatch.setattr(forecast, "_fetch", finto)
    app = create_app(db_path, weather_every_s=3600)
    with TestClient(app, base_url="http://localhost") as c:
        assert c.get("/api/v1/weather").json()["nights"] == []
        metti_casa(db_path)
        assert wait_until(lambda: c.get("/api/v1/weather").json()["nights"])
    assert len(finto.chiesti) == 1


def test_the_time_of_the_forecast_is_of_the_site_even_when_a_model_brought_no_night(letto, db_path):
    """Un modello che l'ultima risposta non portava non fa dire "nessuna previsione ancora"."""
    c = connect(db_path)
    c.execute("DELETE FROM weather_nights WHERE source = ?", (forecast.source_of("gfs_seamless"),))
    c.execute("DELETE FROM weather_view WHERE model = 'gfs_seamless'")
    c.close()
    letto.patch("/api/v1/settings", json={"values": {"weather_model": "gfs_seamless"}})
    detto = letto.get("/api/v1/weather").json()
    assert detto["nights"] == []
    assert detto["fetched_at"]


def test_a_home_site_without_a_timezone_is_said(db_path, client_vuoto):
    metti_casa(db_path, timezone=None)
    detto = client_vuoto.get("/api/v1/weather").json()
    assert detto["site"] == "Casa"
    assert detto["missing"] == "no_timezone"


def dintorni_del_cielo():
    """I tre servizi, con risposte intorno ad adesso qualunque giorno giri la prova. Il vento in
    quota e' diverso per modello e per livello: una colonna letta dal posto sbagliato si vede."""
    from test_weather_sky import Instradato, aria

    adesso = datetime.now(UTC)
    inizio = (adesso - timedelta(days=2)).strftime("%Y-%m-%dT00:00")
    return Instradato(**{
        "/v1/forecast": risposta(
            inizio=inizio,
            ore=12 * 24,
            wind_250hpa_kmh=150.0,
            wind_200hpa_kmh=140.0,
            per_modello={"icon_seamless": {"wind_250hpa_kmh": 90.0}},
        ),
        "air-quality": aria(inizio=inizio, ore=10 * 24),
    })  # fmt: skip


def test_three_nights_are_full_and_the_following_are_a_trend(letto):
    notti = letto.get("/api/v1/weather").json()["nights"]
    assert len(notti) > 3
    assert [n["trend"] for n in notti[:3]] == [False, False, False]
    assert all(n["hours"] and n["measures"] for n in notti[:3])
    assert all(n["trend"] and not n["hours"] and not n["measures"] for n in notti[3:])
    assert all(n["verdict"] and n["agreement"] for n in notti[3:])
    # la tendenza non porta cio' che si legge dalle ore, e le notti si fermano alla settima
    assert all(n["usable_hours"] is None and n["usable_since"] is None for n in notti[3:])
    assert all(n["cloud_total_pct"] is not None and n["window_hours"] > 0 for n in notti[3:])
    assert len(notti) == 7
    detto = letto.get("/api/v1/weather").json()
    assert detto["full_nights"] == 3
    assert {f["source"] for f in detto["sources"]} == {"cams"}


def test_the_sky_aloft_joins_the_wind_of_the_model_and_the_seeing_of_its_hour(letto):
    notte = letto.get("/api/v1/weather").json()["nights"][1]
    assert {o["wind_250hpa_kmh"] for o in notte["hours"]} == {150.0}
    assert {o["wind_200hpa_kmh"] for o in notte["hours"]} == {140.0}
    # senza chiave Meteoblue il seeing non c'e': nessuna fonte lo stima al suo posto
    assert {o["seeing_arcsec"] for o in notte["hours"]} == {None}
    assert all("transparency_from" not in o for o in notte["hours"])
    assert {o["aerosol_optical_depth"] for o in notte["hours"]} == {0.12}
    # 150 km/h a 250 hPa: oltre i 126 di meteoblue, la corrente a getto pesa
    assert {o["levels"]["jet"] for o in notte["hours"]} == {"nogo"}
    (getto,) = [m for m in notte["measures"] if m["code"] == "jet"]
    assert (getto["level"], getto["weighs"], getto["value"]) == ("nogo", True, 150.0)
    assert notte["measures"][0]["code"] == "cloud"


def test_the_page_gets_the_thresholds_the_judgement_used(letto):
    """Le soglie arrivano dal backend, le stesse del giudizio: la pagina le disegna, non le sa."""
    scale = {s["code"]: s["steps"] for s in letto.get("/api/v1/weather").json()["scales"]}
    assert scale["jet"] == [{"level": "nogo", "bound": 126.0, "strict": False}]
    assert scale["seeing"][1] == {"level": "marginal", "bound": 2.0, "strict": True}
    # la condensa si conta verso il basso: lo dice il dato, non una nota
    verso = {s["code"]: s["lower_is_worse"] for s in letto.get("/api/v1/weather").json()["scales"]}
    assert verso["condensation"] is True
    assert verso["jet"] is False


def test_the_wind_aloft_is_the_one_of_the_chosen_model(letto):
    letto.patch("/api/v1/settings", json={"values": {"weather_model": "icon_seamless"}})
    notte = letto.get("/api/v1/weather").json()["nights"][1]
    assert {o["wind_250hpa_kmh"] for o in notte["hours"]} == {90.0}


def test_the_time_of_the_forecast_is_the_one_of_the_models_not_of_the_sky(letto, db_path):
    prima = letto.get("/api/v1/weather").json()["fetched_at"]
    c = connect(db_path)
    c.execute(
        "UPDATE weather_nights SET fetched_at = '2999-01-01T00:00:00.000Z' WHERE source = 'cams'"
    )
    c.close()
    assert letto.get("/api/v1/weather").json()["fetched_at"] == prima


@pytest.fixture(scope="session")
def _meteo_scritto(tmp_path_factory):
    """Un DB col sito di casa e un giro del meteo gia' scritto, dai servizi finti: si copia."""
    percorso = tmp_path_factory.mktemp("meteo") / "scritto.db"
    create_database(percorso)
    metti_casa(percorso)
    c = connect(percorso)
    try:
        assert rounds.refresh(c, dict(home_site(c)), fetch=dintorni_del_cielo()) == "ok"
    finally:
        c.close()
    return percorso


@pytest.fixture
def letto(db_path, _meteo_scritto):
    """La rotta davanti a una previsione gia' scritta: una copia di file, non un giro."""
    shutil.copy(_meteo_scritto, db_path)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_the_history_arrives_by_itself_in_the_background(db_path, monkeypatch):
    """Dopo la scansione non si chiede niente: il giro in sottofondo porta lo storico da solo."""
    from astrolog.weather import history
    from test_weather_history import archivio

    metti_casa(db_path)
    c = connect(db_path)
    c.execute("INSERT INTO nights(site_id, night_date, created_at) VALUES(1, '2026-03-10', 'x')")
    c.close()
    finto = Finto(archivio())
    monkeypatch.setattr(history, "_fetch", finto)
    monkeypatch.setattr(forecast, "_fetch", Finto(attorno_ad_adesso()))
    monkeypatch.setattr(sky, "_fetch", Finto(TimeoutError()))
    app = create_app(db_path, weather_every_s=3600)
    with TestClient(app, base_url="http://localhost") as cliente:
        assert wait_until(
            lambda: cliente.get("/api/v1/nights").json()["items"][0]["weather"]["state"] == "ok"
        )


def test_the_first_forecast_already_compares_the_wind_with_the_site(db_path, monkeypatch):
    """Il solito del sito si chiede prima della previsione: al primo avvio la previsione esce gia'
    col confronto, invece di aspettare il giro dopo, tre ore piu' tardi."""
    from astrolog.weather import climate
    from test_weather_climate import anno

    metti_casa(db_path)
    monkeypatch.setattr(climate, "_fetch", Finto(anno()))
    monkeypatch.setattr(forecast, "_fetch", Finto(attorno_ad_adesso()))
    monkeypatch.setattr(sky, "_fetch", Finto(TimeoutError()))
    app = create_app(db_path, weather_every_s=3600)
    with TestClient(app, base_url="http://localhost") as c:
        assert wait_until(lambda: c.get("/api/v1/weather").json()["nights"])
        assert c.get("/api/v1/weather").json()["nights"][0]["wind_700hpa_tenths"] == 0


def test_tonight_tells_the_weather_of_the_night_under_way(letto):
    """Stanotte legge il riassunto scritto della notte in corso, dal modello scelto."""
    detto = letto.get("/api/v1/tonight").json()
    assert detto["weather"]["verdict"] == "go"
    assert detto["weather"]["agreement"]["total"] == 4
    assert detto["weather"]["wind_700hpa_tenths"] is None  # la climatologia non c'e' ancora
    notti = letto.get("/api/v1/weather").json()["nights"]
    assert detto["night"] == notti[0]["night"]


def test_tonight_without_a_forecast_says_nothing_of_the_weather(con_casa):
    assert con_casa.get("/api/v1/tonight").json()["weather"] is None


def test_the_sky_aloft_carries_the_wind_at_700_hpa(letto):
    notte = letto.get("/api/v1/weather").json()["nights"][1]
    assert {o["wind_700hpa_kmh"] for o in notte["hours"]} == {0.0}


def test_a_trend_night_does_not_carry_the_wind_aloft(letto):
    tendenza = [n for n in letto.get("/api/v1/weather").json()["nights"] if n["trend"]][0]
    assert tendenza["wind_700hpa_kmh"] is None
    assert tendenza["wind_700hpa_tenths"] is None
