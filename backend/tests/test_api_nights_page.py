"""I tre dati che la pagina Notti del disegno (forma A, il registro) chiede e prima non arrivavano:
le ore di ogni oggetto senza contare zero i frame senza durata, il giorno in cui arriva il meteo di
una notte giovane, e quanto ha fatto la lettura in corso.
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.weather import history
from group_bench import ROMA, corri, luogo, posa, prepara


def notti(client):
    risposta = client.get("/api/v1/nights")
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


def per_data(pagina):
    return {n["night_date"]: n for n in pagina["items"]}


@pytest.fixture
def banco(db_path):
    """Una notte vecchia con M 45 senza durata accanto a M 31, una notte di ieri, e un frame che
    la lettura non ha ancora messo in una notte."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        posa(conn, quando="2024-05-17T22:00:00Z", esposizione=300.0, hash_="a1")
        posa(conn, quando="2024-05-17T22:30:00Z", oggetto=2, esposizione=None, hash_="a2")
        ieri = (datetime.now(UTC) - timedelta(days=1)).replace(hour=21, minute=0, second=0)
        posa(conn, quando=ieri.strftime("%Y-%m-%dT%H:%M:%SZ"), esposizione=60.0, hash_="b1")
        corri(conn)
        # arrivato dopo il giro di `group`: la lettura lo deve ancora mettere in una notte
        posa(conn, quando="2024-05-18T22:00:00Z", esposizione=60.0, hash_="c1")
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_an_object_says_its_frames_without_a_duration_instead_of_zero_hours(banco):
    """M 45 ha un frame che non dice quanto e' durato: "senza tempo", non "0 h" (glossario)."""
    notte = per_data(notti(banco))["2024-05-17"]

    oggetti = {o["key"]: (o["integration_s"], o["untimed"]) for o in notte["objects"]}
    assert oggetti == {"m-31": (300.0, 0), "m-45": (0.0, 1)}


def test_a_young_night_says_the_day_its_weather_arrives(banco):
    """Il meteo di una notte arriva quando il suo mattino ha cinque giorni: il sesto giorno dopo
    la sera. Una notte vecchia il cui meteo non c'e' ancora non promette una data passata."""
    pagina = per_data(notti(banco))
    giovane = next(n for d, n in pagina.items() if d != "2024-05-17")

    attesa = date.fromisoformat(giovane["night_date"]) + timedelta(days=6)
    assert giovane["weather"]["state"] == "waiting"
    assert giovane["weather"]["arrives_on"] == attesa.isoformat()
    assert pagina["2024-05-17"]["weather"]["arrives_on"] is None


@pytest.mark.parametrize(
    ("adesso", "atteso"),
    [
        # le 11:59 del 10 ottobre a Roma: e' ancora la notte del 9, si aspetta il 10
        ("2026-10-10T09:59:00Z", "2026-10-10"),
        # mezzogiorno del 10 a Roma: la notte del 10, lo storico lo chiede, non si promette piu'
        ("2026-10-10T10:00:00Z", None),
    ],
)
def test_the_day_the_weather_arrives_is_counted_in_the_site_time_zone(adesso, atteso):
    quando = datetime.fromisoformat(adesso.replace("Z", "+00:00"))
    assert history.arrives_on("2026-10-04", "Europe/Rome", quando) == atteso


def test_the_reading_says_how_far_it_has_gone(banco):
    """Tre frame messi nelle notti, uno da mettere: la riga di lettura dice 75%, gia' fatto."""
    pagina = notti(banco)

    assert pagina["still_reading"] == 1
    assert pagina["reading_done_pct"] == 75


def test_nothing_to_read_has_no_percentage(client_vuoto):
    assert notti(client_vuoto)["reading_done_pct"] is None


def test_each_object_bar_is_its_share_of_the_longest_of_the_night(banco):
    """La barra di un oggetto e' lunga quanto le sue ore rispetto al piu' lungo della notte; un
    oggetto senza tempo non ha barra, invece di una barra finta."""
    notte = per_data(notti(banco))["2024-05-17"]

    assert {o["key"]: o["bar_pct"] for o in notte["objects"]} == {"m-31": 100, "m-45": 0}


def test_a_short_object_still_shows_a_sliver(db_path):
    """Un minuto accanto a dieci ore e' 0,17%: arrotondato sparirebbe, e sembrerebbe senza tempo."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        posa(conn, quando="2024-05-17T21:00:00Z", esposizione=36000.0, hash_="a1")
        posa(conn, quando="2024-05-17T22:00:00Z", oggetto=2, esposizione=60.0, hash_="a2")
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        notte = notti(c)["items"][0]

    assert {o["key"]: o["bar_pct"] for o in notte["objects"]} == {"m-31": 100, "m-45": 2}


def test_the_moon_of_a_night_says_which_side_is_lit(banco):
    """Il disco della Luna come in Stanotte: il lato illuminato dipende dalla fase e dall'emisfero
    del sito, e lo decide l'effemeride, non la pagina."""
    # il 17 maggio 2024 la Luna cresceva (nuova l'8, piena il 23): a nord e' illuminata a destra
    assert per_data(notti(banco))["2024-05-17"]["moon"]["lit_side"] == "right"
