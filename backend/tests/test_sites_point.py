"""Cio' che la carta dei Siti (tavola v82) legge oltre al sito salvato: lo scarto dal tempo
universale accanto al fuso, l'anteprima di un punto prima di salvarlo, il cielo chiesto alla mappa
quando lo si sceglie."""

import datetime as dt
import zoneinfo

import pytest

from astrolog import place
from conftest import rete_giu
from test_sites import answers, create


def test_the_offset_follows_summer_time():
    """«Europe/Rome · UTC+1» in inverno, +2 d'estate: lo scarto e' quello del giorno."""
    rome = "Europe/Rome"
    assert place.utc_offset_minutes(rome, dt.datetime(2026, 1, 15, 12, tzinfo=dt.UTC)) == 60
    assert place.utc_offset_minutes(rome, dt.datetime(2026, 7, 15, 12, tzinfo=dt.UTC)) == 120
    assert place.utc_offset_minutes("Asia/Kolkata", dt.datetime(2026, 1, 1, tzinfo=dt.UTC)) == 330


def test_the_site_carries_the_offset_of_today(client_vuoto, offline):
    site = create(client_vuoto)
    now = dt.datetime.now(dt.UTC)
    expected = zoneinfo.ZoneInfo(site["timezone"]).utcoffset(now)
    assert expected is not None
    assert site["utc_offset_minutes"] == expected.total_seconds() // 60


def test_a_site_without_a_zone_has_no_offset(client_vuoto, offline, monkeypatch):
    monkeypatch.setattr(place, "timezone_of", lambda *_: None)
    site = create(client_vuoto)
    assert site["timezone"] is None and site["utc_offset_minutes"] is None


def test_a_point_says_its_zone_and_elevation_before_it_is_saved(client_vuoto, monkeypatch):
    """L'anteprima del Nuovo sito: fuso dalle coordinate, altitudine dal modello del terreno.
    Non scrive niente."""
    answers(monkeypatch, {"elevation": {"elevation": [1366.0]}})
    r = client_vuoto.get("/api/v1/places/point", params={"latitude": 45.85, "longitude": 11.57})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["timezone"] == "Europe/Rome"
    assert body["utc_offset_minutes"] in (60, 120)
    assert body["elevation_m"] == pytest.approx(1366.0)
    assert client_vuoto.get("/api/v1/sites").json()["total"] == 0


def test_a_point_without_network_has_no_elevation(client_vuoto, offline):
    r = client_vuoto.get("/api/v1/places/point", params={"latitude": 45.85, "longitude": 11.57})
    assert r.status_code == 200, r.text
    assert r.json()["elevation_m"] is None and r.json()["timezone"] == "Europe/Rome"


def test_a_point_outside_the_world_is_refused(client_vuoto, offline):
    r = client_vuoto.get("/api/v1/places/point", params={"latitude": 91, "longitude": 0})
    assert r.status_code == 422


def test_the_list_says_the_believable_sqm(client_vuoto, offline):
    """«Un numero da 7 a 23» sotto il campo SQM a mano: gli estremi li dice chi li controlla."""
    body = client_vuoto.get("/api/v1/sites").json()
    assert body["sqm_range"] == {"min": 7, "max": 23}


def test_the_map_is_asked_only_with_the_key(client_vuoto, offline):
    """«Dalla mappa» senza chiave: la tavola porta a Servizi, il backend dice perche'."""
    site = create(client_vuoto, bortle=4)
    r = client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/service")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "sky_service_no_key"


def test_the_map_writes_the_sky_with_its_source(client_vuoto, monkeypatch):
    answers(monkeypatch, {"lightpollutionmap": "0.5", "elevation": {"elevation": [1000.0]}})
    site = create(client_vuoto, bortle=2)
    client_vuoto.put("/api/v1/services/sky-key", json={"key": "k"})
    r = client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/service")
    assert r.status_code == 200, r.text
    assert r.json()["sky_source"] == "service"
    assert r.json()["sky_sqm"] == pytest.approx(20.51, abs=0.02)


def test_the_sky_key_is_tried_before_it_is_saved(client_vuoto, monkeypatch):
    """Servizi (tavola v82): Verifica. Una chiave sbagliata riceve 200 con una frase (provato il
    16/11/2026), e non si salva; quella buona si', e fuori esce solo come finisce."""
    url = "/api/v1/services/sky-key"
    answers(monkeypatch, {"lightpollutionmap": "Invalid authentication."})
    r = client_vuoto.put(url, json={"key": "sbagliata"}).json()
    assert r == {"status": "refused", "hint": None}
    answers(monkeypatch, {"lightpollutionmap": "0.04"})
    r = client_vuoto.put(url, json={"key": " buona1234\n"}).json()
    assert r["status"] == "ok" and r["hint"] == "...1234"
    answers(monkeypatch, {"lightpollutionmap": "<html>errore</html>"})
    r = client_vuoto.put(url, json={"key": "altra"}).json()
    assert r == {"status": "bad_answer", "hint": "...1234"}
    assert client_vuoto.get("/api/v1/settings").json()["values"]["sky_service_key"] == "...1234"
    assert client_vuoto.put(url, json={"key": ""}).json() == {"status": "removed", "hint": None}
    assert client_vuoto.get("/api/v1/settings").json()["values"]["sky_service_key"] is None


def test_a_silent_sky_service_saves_no_key(client_vuoto, offline):
    r = client_vuoto.put("/api/v1/services/sky-key", json={"key": "k"}).json()
    assert r == {"status": "unreachable", "hint": None}


def test_a_silent_map_leaves_the_sky_as_it_was(client_vuoto, offline, monkeypatch):
    site = create(client_vuoto, bortle=4)
    answers(monkeypatch, {"lightpollutionmap": "0.5"})
    client_vuoto.put("/api/v1/services/sky-key", json={"key": "k"})
    rete_giu(monkeypatch)
    r = client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/service")
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "sky_service_unavailable"
    again = client_vuoto.get("/api/v1/sites").json()["items"][0]
    assert again["sky_source"] == "scale" and again["bortle"] == 4
