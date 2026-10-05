"""La chiave Meteoblue dall'API: si prova sul conto prima di salvarla, non esce mai intera, si
toglie, e il Meteo dice da dove viene il seeing -- e perche', quando non viene da Meteoblue."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.weather import forecast, meteoblue, sky
from test_api_weather import dintorni_del_cielo, metti_casa
from test_weather_meteoblue import CHIAVE, rifiuto, seeing

CONTO = {"items": [{"request_type": "seeing-1h", "request_credits": 8000}], "metadata": {}}
OTHER_KEY = "unaltrachiave5678"  # gitleaks:allow


def seeing_attorno(valore=0.9):
    inizio = (datetime.now(UTC) - timedelta(days=2)).strftime("%Y-%m-%d 00:00")
    return seeing(inizio=inizio, ore=10 * 24, valore=valore)


def servizi(**cambi):
    """I servizi intorno ad adesso: la previsione, il cielo, il seeing e il conto Meteoblue."""
    finto = dintorni_del_cielo()
    finto.per_servizio.update(
        {"packages/seeing-1h": seeing_attorno(), "account/usage": CONTO, **cambi}
    )
    return finto


@pytest.fixture
def app(db_path, monkeypatch):
    metti_casa(db_path)
    finto = servizi()
    monkeypatch.setattr(meteoblue, "_fetch", finto)
    monkeypatch.setattr(sky, "_fetch", finto)
    monkeypatch.setattr(forecast, "_fetch", finto)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_a_good_key_is_kept_and_shown_only_by_its_last_four_characters(app):
    detto = app.put("/api/v1/weather/meteoblue-key", json={"key": " " + CHIAVE + "\n"}).json()
    assert detto == {"status": "ok", "hint": "..." + CHIAVE[-4:]}
    valori = app.get("/api/v1/settings").json()["values"]
    assert valori["meteoblue_key"] == "..." + CHIAVE[-4:]
    assert CHIAVE not in app.get("/api/v1/settings").text


def test_a_key_the_account_refuses_is_not_kept(app, monkeypatch):
    monkeypatch.setattr(meteoblue, "_fetch", servizi(**{"account/usage": rifiuto("x")}))
    detto = app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE}).json()
    assert detto == {"status": "refused", "hint": None}
    assert app.get("/api/v1/settings").json()["values"]["meteoblue_key"] is None


def test_a_refused_key_leaves_the_previous_key_and_its_hint(app, monkeypatch):
    before = app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE}).json()["hint"]
    monkeypatch.setattr(meteoblue, "_fetch", servizi(**{"account/usage": rifiuto("x")}))
    answer = app.put("/api/v1/weather/meteoblue-key", json={"key": OTHER_KEY}).json()
    assert before is not None
    assert answer == {"status": "refused", "hint": before}
    assert app.get("/api/v1/settings").json()["values"]["meteoblue_key"] == before


def test_the_key_cannot_be_written_without_being_tried(app):
    risposta = app.patch("/api/v1/settings", json={"values": {"meteoblue_key": CHIAVE}})
    assert risposta.status_code == 422
    assert risposta.json()["detail"]["code"] == "tried_elsewhere"


def test_the_other_service_key_does_not_come_out_whole_either(app):
    fake_key = "cielo-abcd-9876"  # gitleaks:allow
    app.patch("/api/v1/settings", json={"values": {"sky_service_key": fake_key}})
    assert app.get("/api/v1/settings").json()["values"]["sky_service_key"] == "...9876"


def test_with_the_key_the_seeing_comes_from_meteoblue_hour_by_hour(app):
    app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE})
    detto = app.get("/api/v1/weather").json()
    assert detto["seeing"] == {"source": "meteoblue", "meteoblue": "ok"}
    notte = detto["nights"][0]
    valori = {(o["seeing_from"], o["seeing_to"]) for o in notte["aloft"]}
    assert valori == {(0.9, 0.9)}  # ogni ora, e non le fasce di 7Timer
    assert {f["source"] for f in detto["sources"]} >= {"meteoblue"}


def test_a_refused_key_falls_back_to_7timer_and_says_why(app, monkeypatch, db_path):
    app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE})
    c = connect(db_path)
    c.execute("UPDATE weather_fetches SET attempted_at = '2000-01-01T00:00:00.000Z'")
    c.close()
    rifiutata = servizi(**{"packages/seeing-1h": rifiuto("x")})
    monkeypatch.setattr(sky, "_fetch", rifiutata)
    monkeypatch.setattr(forecast, "_fetch", rifiutata)
    app.post("/api/v1/weather/refresh")
    assert app.get("/api/v1/weather").json()["seeing"] == {
        "source": "7timer",
        "meteoblue": "refused",
    }


def test_without_a_key_the_seeing_is_7timer_and_meteoblue_is_not_mentioned(app):
    app.post("/api/v1/weather/refresh")
    assert app.get("/api/v1/weather").json()["seeing"] == {"source": "7timer", "meteoblue": None}


def test_removing_the_key_removes_its_seeing(app):
    app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE})
    assert app.put("/api/v1/weather/meteoblue-key", json={"key": ""}).json() == {
        "status": "removed",
        "hint": None,
    }
    detto = app.get("/api/v1/weather").json()
    assert detto["seeing"]["meteoblue"] is None
    assert "meteoblue" not in {f["source"] for f in detto["sources"]}


def test_a_new_key_is_asked_at_once_not_twelve_hours_later(app, monkeypatch):
    app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE})
    altro = servizi(**{"packages/seeing-1h": seeing_attorno(valore=1.5)})
    monkeypatch.setattr(meteoblue, "_fetch", altro)
    monkeypatch.setattr(sky, "_fetch", altro)
    monkeypatch.setattr(forecast, "_fetch", altro)
    app.put("/api/v1/weather/meteoblue-key", json={"key": OTHER_KEY})
    notte = app.get("/api/v1/weather").json()["nights"][0]
    assert {o["seeing_from"] for o in notte["aloft"]} == {1.5}


def test_a_night_with_meteoblue_takes_no_seeing_from_7timer(app, db_path):
    """Dove Meteoblue da' la notte, le ore che non copre restano vuote invece di prendere le fasce
    di 7Timer: la pagina dice "viene da Meteoblue", e una notte a due fonti direbbe il falso."""
    app.put("/api/v1/weather/meteoblue-key", json={"key": CHIAVE})
    c = connect(db_path)
    riga = c.execute(
        "SELECT night_date, hourly_json FROM weather_nights WHERE source = 'meteoblue'"
        " ORDER BY night_date LIMIT 1 OFFSET 1"  # la notte dopo: 7Timer la copre tutta
    ).fetchone()
    ore = json.loads(riga["hourly_json"])
    c.execute(
        "UPDATE weather_nights SET hourly_json = ? WHERE source = 'meteoblue' AND night_date = ?",
        (json.dumps(ore[len(ore) // 2 :]), riga["night_date"]),
    )
    c.close()
    notte = next(
        n for n in app.get("/api/v1/weather").json()["nights"] if n["night"] == riga["night_date"]
    )
    visti = {(o["seeing_from"], o["seeing_to"]) for o in notte["aloft"]}
    assert visti <= {(0.9, 0.9), (None, None)}
    assert (None, None) in visti
