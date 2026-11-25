"""Il cielo di stanotte lo scrive chi scrive, e la rotta lo legge (#96): sul NAS ricalcolarlo a ogni
lettura costava 1,35 s alla Dashboard."""

import pytest

from astrolog.api import tonight_sky
from astrolog.db.connect import connect
from astrolog.site_of import home_site

pytestmark = [
    pytest.mark.filterwarnings("ignore:Tried to get polar motions:"),
    pytest.mark.usefixtures("offline"),
]


def _casa(client, lat=45.5455, lon=11.5354):
    r = client.post(
        "/api/v1/sites",
        json={"name": "Vicenza", "latitude": lat, "longitude": lon, "is_default": True},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _guasto(*_a, **_k):
    raise AssertionError("la lettura ha calcolato il cielo")


def test_reading_tonight_computes_no_sky(client_vuoto, monkeypatch):
    """Scritto il cielo col sito, la rotta risponde lo stesso con le effemeridi rotte: lo legge."""
    _casa(client_vuoto)
    prima = client_vuoto.get("/api/v1/tonight").json()
    for nome in ("night_track", "phase"):
        monkeypatch.setattr(f"astrolog.ephemeris.moon.{nome}", _guasto)
    monkeypatch.setattr("astrolog.ephemeris.sun.night_bands", _guasto)
    monkeypatch.setattr("astrolog.ephemeris.planets.night_tracks", _guasto)

    dopo = client_vuoto.get("/api/v1/tonight")

    assert dopo.status_code == 200, dopo.text
    assert dopo.json() == prima
    assert prima["moon"] is not None and prima["sky_bands"]


def test_the_round_writes_the_next_night_once(client_vuoto, db_path, monkeypatch):
    """Il giro scrive stanotte e la notte dopo; a mezzogiorno la dopo c'e' gia', e un giro che
    trova tutto scritto non rifa' niente."""
    monkeypatch.setattr(tonight_sky, "now_iso", lambda: "2026-11-10T16:00:00.000Z")
    _casa(client_vuoto)
    conn = connect(db_path)
    try:
        casa = home_site(conn)
        notti = [r[0] for r in conn.execute("SELECT night_date FROM tonight_sky ORDER BY 1")]
        assert notti == ["2026-11-10", "2026-11-11"]
        assert tonight_sky.step(conn, casa, "2026-11-10T20:00:00.000Z") is False
        # passato mezzogiorno, la notte nuova si legge gia'; il giro aggiunge quella dopo
        assert tonight_sky.step(conn, casa, "2026-11-11T12:30:00.000Z") is True
        notti = [r[0] for r in conn.execute("SELECT night_date FROM tonight_sky ORDER BY 1")]
        assert notti == ["2026-11-11", "2026-11-12"]
    finally:
        conn.close()


def test_a_moved_home_site_gets_its_sky_at_once(client_vuoto):
    """Spostato il sito predefinito, la Luna di stanotte e' quella del posto nuovo, gia' alla
    lettura dopo: la riga vecchia, scritta altrove, non vale piu'."""
    sito = _casa(client_vuoto)
    qui = client_vuoto.get("/api/v1/tonight").json()

    r = client_vuoto.patch(
        f"/api/v1/sites/{sito['id']}", json={"latitude": -36.8485, "longitude": 174.7633}
    )
    assert r.status_code == 200, r.text
    la = client_vuoto.get("/api/v1/tonight").json()

    assert la["moon"] is not None
    assert la["moon"]["ceiling_deg"] != qui["moon"]["ceiling_deg"]


def test_a_new_moon_rule_rewrites_tonight_at_once(client_vuoto, monkeypatch):
    """La regola della Luna giudica stanotte: cambiata, il giudizio scritto cambia subito. Il
    29/10/2026 a Vicenza la Luna all'81% sorge a buio fatto: con la regola di fabbrica e' da banda
    stretta, con una che tollera il 90% non piu'."""
    for modulo in ("tonight", "tonight_sky"):
        monkeypatch.setattr(f"astrolog.api.{modulo}.now_iso", lambda: "2026-10-29T16:00:00.000Z")
    _casa(client_vuoto)
    prima = client_vuoto.get("/api/v1/tonight").json()
    r = client_vuoto.patch(
        "/api/v1/settings", json={"values": {"moon_good_pct": 90, "moon_limit_pct": 95}}
    )
    assert r.status_code == 200, r.text
    dopo = client_vuoto.get("/api/v1/tonight").json()

    assert (prima["moon_in_dark"]["level"], dopo["moon_in_dark"]["level"]) == ("nogo", "go")
    assert dopo["moon"] == prima["moon"]
