"""Le notti pronte per la pagina: ogni modello con le fonti del cielo e la Luna unite ora per ora,
ogni misura giudicata, l'accordo dei modelli contato. Le scrive chi scrive, chi legge non conta.
"""

import json

from astrolog.weather import forecast, rounds, view
from test_weather_forecast import (  # noqa: F401 - `db` e' una fixture
    ADESSO,
    SITO,
    Finto,
    db,
    risposta,
)
from test_weather_sky import aria, tutti


def vista(conn, modello="best_match"):
    return conn.execute(
        "SELECT night_date, model, fetched_at, hours_json, summary_json FROM weather_view"
        " WHERE model = ? ORDER BY night_date",
        (modello,),
    ).fetchall()


def riassunto(riga):
    return json.loads(riga["summary_json"])


def notte_di(conn, data, modello="best_match"):
    (riga,) = [r for r in vista(conn, modello) if r["night_date"] == data]
    return riga


def scritta(conn, fetch):
    forecast.refresh(conn, SITO, fetch=fetch, now=ADESSO)
    view.rebuild(conn, SITO)


def test_the_summary_is_written_with_the_forecast(db):  # noqa: F811
    """Chi legge non ricalcola: il verdetto si scrive quando arriva la previsione."""
    scritta(db, Finto(risposta(cloud_total_pct=80.0)))
    assert vista(db)
    for modello in ("best_match", "ecmwf_ifs025", "icon_seamless", "gfs_seamless"):
        assert all(riassunto(r)["verdict"] == "nogo" for r in vista(db, modello))


def test_a_night_without_the_total_cloud_is_written_without_a_verdict(db):  # noqa: F811
    scritta(db, Finto(risposta(cloud_total_pct=None)))
    assert vista(db)
    assert all(riassunto(r)["verdict"] is None for r in vista(db))


def test_each_night_says_how_many_models_agree(db):  # noqa: F811
    """L'accordo si scrive con la previsione, uguale in ogni modello: chi legge non conta."""
    diversi = {"ecmwf_ifs025": {"cloud_total_pct": 40.0}, "gfs_seamless": {"cloud_total_pct": None}}
    scritta(db, Finto(risposta(per_modello=diversi)))
    for modello in ("best_match", "ecmwf_ifs025"):
        assert riassunto(notte_di(db, "2026-09-25", modello))["agreement"] == {
            "go": 2, "marginal": 1, "nogo": 0, "unknown": 1, "total": 4
        }  # fmt: skip


def test_a_model_that_says_nothing_on_a_night_counts_among_those_that_do_not_know(db):  # noqa: F811
    vuoto = {nostro: None for nostro in forecast.openmeteo.VARIABLES.values()}
    scritta(db, Finto(risposta(per_modello={"gfs_seamless": vuoto})))
    assert riassunto(notte_di(db, "2026-09-25"))["agreement"] == {
        "go": 3, "marginal": 0, "nogo": 0, "unknown": 1, "total": 4
    }  # fmt: skip


def test_each_night_has_its_own_agreement(db):  # noqa: F811
    """ECMWF vede nuvole solo la prima notte: la seconda i modelli sono tutti d'accordo."""
    prima_notte = {"cloud_total_pct": lambda i: 40.0 if i < 24 + 36 else 0.0}
    scritta(db, Finto(risposta(per_modello={"ecmwf_ifs025": prima_notte})))
    accordi = {r["night_date"]: riassunto(r)["agreement"]["go"] for r in vista(db)}
    assert (accordi["2026-09-25"], accordi["2026-09-26"]) == (3, 4)


def test_the_round_writes_the_nights_with_the_sky_sources_joined_and_judged(db):  # noqa: F811
    """L'aerosol di CAMS entra nelle ore del modello, e il suo giudizio con lui: la notte e'
    "molto fosca" senza che chi legge sappia da dove viene l'aerosol."""
    rounds.refresh(db, SITO, fetch=tutti(**{"air-quality": aria(aod=1.2)}), now=ADESSO)
    riga = notte_di(db, "2026-09-25")
    ore = json.loads(riga["hours_json"])
    buio = [o for o in ore if o["sky"] == "dark"]
    assert {o["aerosol_optical_depth"] for o in buio} == {1.2}
    assert {o["levels"]["aerosol"] for o in buio} == {"nogo"}
    (aerosol,) = [m for m in riassunto(riga)["measures"] if m["code"] == "aerosol"]
    assert (aerosol["level"], aerosol["weighs"], aerosol["value"]) == ("nogo", True, 1.2)


def test_the_moon_up_brings_its_lit_part_and_down_brings_nothing(db):  # noqa: F811
    """La notte del 3/10/2026 la Luna calante, al 48%, sorge verso le 00 locali: le prime ore buie
    non la hanno, le ultime si'."""
    adesso = ADESSO.replace(month=10, day=3)
    forecast.refresh(db, SITO, fetch=Finto(risposta(inizio="2026-10-02T00:00")), now=adesso)
    view.rebuild(db, SITO)
    ore = json.loads(notte_di(db, "2026-10-03")["hours_json"])
    su = {o["moon_pct"] for o in ore if o["sky"] == "dark"}
    assert None in su
    assert any(v is not None and 0 < v < 100 for v in su)


def test_every_hour_carries_the_judgement_of_each_judged_measure(db):  # noqa: F811
    scritta(db, Finto(risposta(wind_kmh=22.0, temperature_c=9.0, dew_point_c=7.5)))
    ore = json.loads(notte_di(db, "2026-09-25")["hours_json"])
    assert {o["levels"]["wind"] for o in ore} == {"marginal"}
    # la condensa si giudica sulla distanza fra aria e rugiada: l'ora la porta scritta
    assert {o["dew_spread_c"] for o in ore} == {1.5}
    assert {o["levels"]["condensation"] for o in ore} == {"nogo"}
    assert {o["levels"]["cloud"] for o in ore} == {"go"}


def test_the_clear_hours_are_an_interval_and_the_page_window_follows_the_season(db):  # noqa: F811
    scritta(db, Finto(risposta()))
    detto = riassunto(notte_di(db, "2026-09-25"))
    assert detto["usable_hours"] == detto["window_hours"] > 0
    assert detto["usable_since"] < detto["usable_until"]
    assert detto["shown_from"] < detto["usable_since"]


def test_a_rebuild_leaves_the_other_sites_alone(db):  # noqa: F811
    db.execute(
        "INSERT INTO sites(id, name, latitude, longitude, timezone, created_at)"
        " VALUES(2, 'Altrove', 40.0, 10.0, 'Europe/Rome', '2026-09-01T00:00:00Z')"
    )
    db.execute("INSERT INTO weather_view VALUES(2, '2026-09-20', 'best_match', 't', '[]', '{}')")
    scritta(db, Finto(risposta()))
    restano = db.execute("SELECT site_id FROM weather_view WHERE site_id = 2").fetchall()
    assert len(restano) == 1


def test_every_hour_says_whether_the_page_draws_it(db):  # noqa: F811
    """La pagina disegna dall'ultima ora di giorno prima del crepuscolo alla prima dopo l'alba."""
    scritta(db, Finto(risposta()))
    riga = notte_di(db, "2026-09-25")
    ore, detto = json.loads(riga["hours_json"]), riassunto(riga)
    disegnate = [o["at"] for o in ore if o["shown"]]
    assert disegnate[0] == detto["shown_from"]
    assert disegnate[-1] == detto["shown_until"]
    assert not ore[0]["shown"]


def test_an_hour_says_whether_it_is_a_clear_hour_of_the_night(db):  # noqa: F811
    """Il tratto sereno del cielo: le ore della finestra che il verdetto direbbe serene, le stesse
    che contano le ore utili."""
    scritta(db, Finto(risposta(cloud_total_pct=lambda i: 80.0 if i % 2 else 0.0)))
    riga = notte_di(db, "2026-09-25")
    ore, detto = json.loads(riga["hours_json"]), riassunto(riga)
    assert sum(o["clear"] for o in ore) == detto["usable_hours"] > 0
    assert not any(o["clear"] for o in ore if o["sky"] == "day")


def test_a_night_without_every_cloud_has_no_clear_hours_as_it_has_no_usable_hours(db):  # noqa: F811
    """Un'ora serena e' un'ora che conta fra le utili: dove le utili non si sanno, nemmeno lei."""
    scritta(db, Finto(risposta(cloud_total_pct=lambda i: None if i == 45 else 0.0)))
    riga = notte_di(db, "2026-09-25")
    assert riassunto(riga)["usable_hours"] is None
    assert not any(o["clear"] for o in json.loads(riga["hours_json"]))
