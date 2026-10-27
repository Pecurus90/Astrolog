"""Il calendario della Luna della Dashboard: lo scrive il giro, chi legge non calcola. Questo mese e
il prossimo, per il sito di casa, con le notti buone per la banda larga dalle due soglie."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db import config
from astrolog.db.connect import connect
from astrolog.spine import moon_calendar
from astrolog.spine.group_store import home_site
from astrolog.weather import forecast
from group_bench import ROMA, luogo, prepara

OGGI = dt.date(2026, 10, 16)

pytestmark = pytest.mark.filterwarnings("ignore:Tried to get polar motions:")


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    prepara(c)
    luogo(c, ROMA)
    c.commit()
    yield c
    c.close()


def casa(conn):
    return dict(home_site(conn))


def righe(conn):
    return conn.execute("SELECT * FROM moon_nights ORDER BY night_date").fetchall()


def test_the_round_writes_this_month_and_the_next(conn):
    assert moon_calendar.step(conn, casa(conn), OGGI) is True
    giorni = righe(conn)
    assert (giorni[0]["night_date"], giorni[-1]["night_date"], len(giorni)) == (
        "2026-10-01",
        "2026-11-30",
        61,
    )


def test_the_weather_round_writes_the_calendar_of_tonight_at_the_site(db_path, conn, monkeypatch):
    """Il giro di sottofondo lo scrive per la notte del sito: alle 12:30 di Roma del 1 novembre e'
    gia' la notte del 1, in UTC ancora quella del 31 ottobre."""
    import astrolog.api.app as app_mod

    monkeypatch.setattr(app_mod, "now_iso", lambda: "2026-11-01T11:30:00Z")
    monkeypatch.setattr(app_mod.climate, "step", lambda conn, site: None)
    monkeypatch.setattr(app_mod.rounds, "refresh", lambda conn, site: "ok")
    monkeypatch.setattr(app_mod.history, "step", lambda conn: None)
    app_mod._weather_round(str(db_path), forecast.Cadence(3600))
    giorni = righe(conn)  # da un'altra connessione: il giro l'ha salvato
    assert (giorni[0]["night_date"], giorni[-1]["night_date"]) == ("2026-11-01", "2026-12-31")


def test_a_second_round_with_nothing_changed_does_not_recompute(conn):
    moon_calendar.step(conn, casa(conn), OGGI)
    assert moon_calendar.step(conn, casa(conn), OGGI) is False


def test_a_moved_site_is_recomputed(conn):
    moon_calendar.step(conn, casa(conn), OGGI)
    conn.execute("UPDATE sites SET latitude = latitude + 1")
    assert moon_calendar.step(conn, casa(conn), OGGI) is True


def test_new_and_full_moon_are_marked_on_their_nights(conn):
    """Ottobre 2026: Luna nuova il 10 alle 15:50 UTC, piena il 26 alle 04:11 UTC (in Italia la
    notte del 25, che va da mezzogiorno a mezzogiorno)."""
    moon_calendar.step(conn, casa(conn), OGGI)
    eventi = {r["night_date"]: r["event"] for r in righe(conn) if r["event"]}
    assert eventi["2026-10-10"] == "new"
    assert eventi["2026-10-25"] == "full"


def test_a_good_broadband_night_has_little_moon_or_enough_dark_without_it(conn):
    """Di fabbrica: Luna sotto il 25%, oppure almeno 4 ore di buio senza Luna."""
    moon_calendar.step(conn, casa(conn), OGGI)
    for r in righe(conn):
        attesa = r["illumination_pct"] < 25 or r["moonless_dark_s"] >= 4 * 3600
        assert bool(r["broadband_good"]) == attesa, r["night_date"]


def test_changing_a_threshold_rejudges_the_nights_at_once(db_path, conn):
    moon_calendar.step(conn, casa(conn), OGGI)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_broadband_min_dark_h": 12}})
    assert r.status_code == 200, r.text
    assert config.read(conn).moon_broadband_min_dark_h == 12
    for row in righe(conn):
        assert bool(row["broadband_good"]) == (row["illumination_pct"] < 25), row["night_date"]


def test_a_threshold_out_of_range_is_refused(db_path):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_broadband_max_pct": 140}})
        letto = c.get("/api/v1/settings").json()
    # Un numero del tipo giusto ma fuori misura non e' un tipo sbagliato: lo schermo dice la misura.
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "out_of_range", "keys": ["moon_broadband_max_pct"]}
    # La misura la manda il backend, una volta: lo schermo non la riscrive.
    assert letto["ranges"]["moon_broadband_max_pct"] == {"min": 0, "max": 100}
    assert letto["ranges"]["moon_broadband_min_dark_h"] == {"min": 0, "max": 12}


def test_every_threshold_out_of_range_is_named(db_path):
    valori = {"moon_broadband_max_pct": 140, "moon_broadband_min_dark_h": 99}
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": valori})
    # Come unknown_setting e tried_elsewhere: tutte le chiavi, non la prima.
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "out_of_range", "keys": sorted(valori)}


def test_the_routes_read_what_the_round_wrote(db_path, conn):
    """Il calendario esce com'e' scritto, con le due soglie per la legenda; Stanotte dice la
    prossima nuova e piena da li', e l'eta', la distanza e da dove sorge la Luna."""
    oggi = dt.date.today()
    moon_calendar.step(conn, casa(conn), oggi)
    conn.commit()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        cal = c.get("/api/v1/moon/calendar").json()
        luna = c.get("/api/v1/tonight").json()["moon"]
    assert (cal["max_pct"], cal["min_dark_h"]) == (25, 4)
    assert len(cal["nights"]) >= 59
    assert {"date", "phase_key", "illumination_pct", "moonless_dark_s", "event", "good"} <= set(
        cal["nights"][0]
    )
    assert luna["next_new"] and luna["next_full"]
    assert 0 <= luna["age_days"] <= 30
    assert 356000 <= luna["distance_km"] <= 407000
    assert luna["rise_compass"] is None or luna["rise_compass"] in {"NE", "ENE", "E", "ESE", "SE"}


def test_a_moved_site_does_not_show_the_old_sky_until_the_round_rewrites_it(db_path, conn):
    """Spostato il sito, il calendario del posto di prima non esce piu': fino al giro dopo e' vuoto,
    come prima del primo giro. Cosi' la prossima nuova e piena."""
    moon_calendar.step(conn, casa(conn), dt.date.today())
    conn.execute("UPDATE sites SET latitude = latitude + 1")
    conn.commit()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        cal = c.get("/api/v1/moon/calendar").json()
        luna = c.get("/api/v1/tonight").json()["moon"]
    assert cal["nights"] == []
    assert (luna["next_new"], luna["next_full"]) == (None, None)


def test_before_the_round_the_calendar_is_empty_not_invented(db_path, conn):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        assert c.get("/api/v1/moon/calendar").json()["nights"] == []
