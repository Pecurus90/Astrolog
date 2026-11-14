"""Il calendario della Luna della Dashboard: lo scrive il giro, chi legge non calcola. Questo mese e
il prossimo, per il sito di casa, coi gradini della regola della Luna delle Impostazioni."""

import datetime as dt
import shutil

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db import config
from astrolog.db.connect import connect, create_database
from astrolog.site_of import home_site
from astrolog.spine import moon_calendar
from astrolog.weather import forecast
from group_bench import ROMA, corri, luogo, posa, prepara

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


def _modello(tmp_path_factory, oggi):
    """Il calendario costa 6 s di effemeridi: si calcola una volta per modulo, i test lo copiano."""
    path = tmp_path_factory.mktemp("luna") / "modello.db"
    create_database(path)
    c = connect(path)
    try:
        prepara(c)
        luogo(c, ROMA)
        moon_calendar.step(c, home_site(c), oggi)
        c.commit()
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # tutto nel .db: e' un file che si copia
    finally:
        c.close()
    return path


@pytest.fixture(scope="module")
def _scritto_a_ottobre(tmp_path_factory):
    return _modello(tmp_path_factory, OGGI)


@pytest.fixture(scope="module")
def _scritto_oggi(tmp_path_factory):
    return _modello(tmp_path_factory, dt.date.today())


def _copia(modello, db_path):
    shutil.copy(modello, db_path)
    c = connect(db_path)
    yield c
    c.close()


@pytest.fixture
def scritto(_scritto_a_ottobre, db_path):
    """Il sito di casa col calendario di ottobre e novembre 2026 gia' scritto dal giro."""
    yield from _copia(_scritto_a_ottobre, db_path)


@pytest.fixture
def scritto_oggi(_scritto_oggi, db_path):
    yield from _copia(_scritto_oggi, db_path)


def righe(conn):
    return conn.execute("SELECT * FROM moon_nights ORDER BY night_date").fetchall()


def test_the_round_writes_this_month_and_the_next(conn):
    assert moon_calendar.step(conn, home_site(conn), OGGI) is True
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


def test_a_second_round_with_nothing_changed_does_not_recompute(scritto):
    assert moon_calendar.step(scritto, home_site(scritto), OGGI) is False


def test_a_moved_site_is_recomputed(scritto, monkeypatch):
    rifatti = []
    monkeypatch.setattr(moon_calendar, "rebuild", lambda conn, site, wanted: rifatti.append(site))
    scritto.execute("UPDATE sites SET latitude = latitude + 1")
    assert moon_calendar.step(scritto, home_site(scritto), OGGI) is True
    assert [s.latitude for s in rifatti] == [ROMA[1] + 1]


def test_new_and_full_moon_are_marked_on_their_nights(scritto):
    """Ottobre 2026: Luna nuova il 10 alle 15:50 UTC, piena il 26 alle 04:11 UTC (in Italia la
    notte del 25, che va da mezzogiorno a mezzogiorno)."""
    eventi = {r["night_date"]: r["event"] for r in righe(scritto) if r["event"]}
    assert eventi["2026-10-10"] == "new"
    assert eventi["2026-10-25"] == "full"


def test_each_night_has_its_step_on_the_meteo_moon_scale(scritto):
    """I tre gradini della tavola v79 (CalendarioNotti, Luna): fino al 25% banda larga buona, fino
    al 65% al limite, oltre solo banda stretta; la stessa scala della Luna del Meteo (ING)."""
    gradi = {r["night_date"]: (r["illumination_pct"], r["moon_level"]) for r in righe(scritto)}
    for data, (pct, grado) in gradi.items():
        atteso = "go" if pct < 25 else "marginal" if pct < 65 else "nogo"
        assert grado == atteso, data
    assert {g for _, g in gradi.values()} == {"go", "marginal", "nogo"}


def test_the_calendar_shows_the_nights_shot_on_its_days(db_path, scritto):
    """La stella della notte di ripresa: sito, oggetti, frame e ore, da qualunque sito."""
    scritto.execute(
        "INSERT INTO object_names(object_id, name, origin, is_primary) VALUES(1, 'M 31', 'user', 1)"
    )
    posa(scritto, quando="2026-10-12T21:00:00Z", esposizione=600.0, hash_="a")
    posa(scritto, quando="2026-10-12T22:00:00Z", hash_="b")
    corri(scritto)
    scritto.commit()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        notti = c.get("/api/v1/moon/calendar").json()["nights"]
    (giorno,) = [n for n in notti if n["shots"]]
    (ripresa,) = giorno["shots"]
    assert giorno["date"] == "2026-10-12"
    assert (ripresa["site"], ripresa["frames"], ripresa["integration_s"], ripresa["untimed"]) == (
        "Casa",
        2,
        600,
        1,
    )
    assert ripresa["objects"] == ["M 31"]
    assert ripresa["night_id"]


def test_changing_the_percentages_rewrites_the_steps_at_once(db_path, scritto):
    """La regola della Luna (tavola v82): buona e al limite cambiano i gradini."""
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch(
            "/api/v1/settings", json={"values": {"moon_good_pct": 10, "moon_limit_pct": 50}}
        )
    assert r.status_code == 200, r.text
    assert (config.read(scritto).moon_good_pct, config.read(scritto).moon_limit_pct) == (10, 50)
    for row in righe(scritto):
        pct = row["illumination_pct"]
        atteso = "go" if pct < 10 else "marginal" if pct < 50 else "nogo"
        assert row["moon_level"] == atteso, row["night_date"]


def test_a_higher_floor_gives_more_dark_without_the_moon(db_path, scritto):
    """'La Luna conta sopra' 10 gradi: sotto i 10 non conta, il buio senza Luna cresce."""
    prima = {r["night_date"]: r["moonless_dark_s"] for r in righe(scritto)}
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_above_deg": 10}})
    assert r.status_code == 200, r.text
    dopo = {r["night_date"]: r["moonless_dark_s"] for r in righe(scritto)}
    assert dopo.keys() == prima.keys()
    assert all(dopo[d] >= prima[d] for d in prima)
    assert any(dopo[d] > prima[d] for d in prima)


def test_a_rule_change_rewrites_the_forecast_of_the_home_site(db_path, scritto, monkeypatch):
    import astrolog.api.settings as impostazioni

    rifatti = []
    monkeypatch.setattr(impostazioni.view, "rebuild", lambda conn, site: rifatti.append(site.name))
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_good_pct": 20}})
    assert r.status_code == 200, r.text
    assert rifatti == ["Casa"]


def test_an_imported_rule_rewrites_the_calendar_at_once(db_path, scritto):
    """Come dalla pagina: la regola che arriva da un file giudica subito, non al mese dopo."""
    from astrolog.spine import backup

    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.post(
            "/api/v1/backup/import",
            json={"version": backup.VERSION, "config": {"moon_good_pct": "10"}},
        )
    assert r.status_code == 200, r.text
    for row in righe(scritto):
        pct = row["illumination_pct"]
        atteso = "go" if pct < 10 else "marginal" if pct < 65 else "nogo"
        assert row["moon_level"] == atteso, row["night_date"]


def test_the_floor_is_one_of_the_four_choices(db_path):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_above_deg": 3}})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "wrong_type"


def test_marginal_never_under_good(db_path, scritto):
    """La tavola: 'Deve essere almeno N%'. Niente si scrive."""
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_good_pct": 70}})
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "moon_limit_below_good", "keys": ["moon_limit_pct"]}
    assert config.read(scritto).moon_good_pct == 25


def test_a_threshold_out_of_range_is_refused(db_path):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": {"moon_good_pct": 140}})
        letto = c.get("/api/v1/settings").json()
    # Un numero del tipo giusto ma fuori misura non e' un tipo sbagliato: lo schermo dice la misura.
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "out_of_range", "keys": ["moon_good_pct"]}
    # La misura la manda il backend, una volta: lo schermo non la riscrive.
    assert letto["ranges"]["moon_good_pct"] == {"min": 0, "max": 100}
    assert letto["ranges"]["moon_limit_pct"] == {"min": 0, "max": 100}


def test_every_threshold_out_of_range_is_named(db_path):
    valori = {"moon_good_pct": 140, "moon_limit_pct": 199}
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.patch("/api/v1/settings", json={"values": valori})
    # Come unknown_setting e tried_elsewhere: tutte le chiavi, non la prima.
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "out_of_range", "keys": sorted(valori)}


def test_the_routes_read_what_the_round_wrote(db_path, scritto_oggi):
    """Il calendario esce com'e' scritto, coi limiti della regola per la legenda; Stanotte dice la
    prossima nuova e piena da li', e l'eta', la distanza e da dove sorge la Luna."""
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        cal = c.get("/api/v1/moon/calendar").json()
        luna = c.get("/api/v1/tonight").json()["moon"]
    assert (cal["good_pct"], cal["limit_pct"]) == (25, 65)
    assert len(cal["nights"]) >= 59
    keys = {"date", "phase_key", "illumination_pct", "dark_s", "moonless_dark_s", "event", "level"}
    assert keys <= set(cal["nights"][0])
    # il buio come il giro l'ha scritto: le prossime notti lo dicono anche senza previsione (#66)
    scritti = dict(scritto_oggi.execute("SELECT night_date, dark_s FROM moon_nights").fetchall())
    assert all(n["dark_s"] == scritti[n["date"]] for n in cal["nights"])
    assert all(n["moonless_dark_s"] <= n["dark_s"] for n in cal["nights"])
    assert luna["next_new"] and luna["next_full"]
    assert 0 <= luna["age_days"] <= 30
    assert 356000 <= luna["distance_km"] <= 407000
    assert luna["rise_compass"] is None or luna["rise_compass"] in {"NE", "ENE", "E", "ESE", "SE"}


def test_a_moved_site_does_not_show_the_old_sky_until_the_round_rewrites_it(db_path, scritto_oggi):
    """Spostato il sito, il calendario del posto di prima non esce piu': fino al giro dopo e' vuoto,
    come prima del primo giro. Cosi' la prossima nuova e piena."""
    scritto_oggi.execute("UPDATE sites SET latitude = latitude + 1")
    scritto_oggi.commit()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        cal = c.get("/api/v1/moon/calendar").json()
        luna = c.get("/api/v1/tonight").json()["moon"]
    assert cal["nights"] == []
    assert (luna["next_new"], luna["next_full"]) == (None, None)


def test_before_the_round_the_calendar_is_empty_not_invented(db_path, conn):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        assert c.get("/api/v1/moon/calendar").json()["nights"] == []
