"""Le Notti della tavola v76 (`docs/domini/notti.md`): i criteri coi conteggi, i mesi
dell'elenco, il calendario del mese, la ripresa che lasciava la Luna, da dove viene il sito.

Quattro notti: tre a casa a maggio 2024 -- Luna nuova l'8, mezza il 15, piena il 23 -- e una a
Cima Ekar a gennaio 2025, coi frame che portano le coordinate.
"""

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import iso_z, night_date
from astrolog.db.connect import connect
from conftest import db  # noqa: F401 - fixture
from group_bench import ROMA, corri, filtro, luogo, posa, prepara

EKAR = ("Cima Ekar", 45.8667, 11.5167, "Europe/Rome")


def notti(client, **parametri):
    risposta = client.get("/api/v1/nights", params=parametri)
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


def calendario(client, mese):
    risposta = client.get("/api/v1/nights/calendar", params={"month": mese})
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


@pytest.fixture
def archivio(db_path):
    conn = connect(db_path)
    try:
        prepara(conn)
        for oggetto, nome, altro in ((1, "M 31", "Andromeda"), (2, "M 45", "Pleiadi")):
            conn.execute(
                "INSERT INTO object_names(object_id, name, origin, is_primary)"
                " VALUES(?, ?, 'catalog', 1), (?, ?, 'user', 0)",
                (oggetto, nome, oggetto, altro),
            )
        for slug, sigla, costellazione in (("m-31", "M 31", "And"), ("m-45", "M 45", "Tau")):
            conn.execute(
                "INSERT INTO catalog_entries(slug, name, ra_deg, dec_deg, x, y, z,"
                " constellation, type_code) VALUES(?, ?, 10.0, 40.0, 0.7, 0.1, 0.6, ?, 'GALAXY')",
                (slug, sigla, costellazione),
            )
        luogo(conn, ROMA)
        ekar = luogo(conn, EKAR, casa=False)
        ha, oiii = filtro(conn, "Ha"), filtro(conn, "OIII", "oiii")
        posa(conn, quando="2024-05-08T22:00:00Z", filtro_id=ha, esposizione=600.0, hash_="a")
        posa(conn, quando="2024-05-15T22:00:00Z", filtro_id=ha, esposizione=600.0, hash_="b1")
        posa(
            conn,
            quando="2024-05-15T23:00:00Z",
            oggetto=2,
            corredo=2,
            filtro_id=oiii,
            esposizione=300.0,
            hash_="b2",
        )
        posa(
            conn,
            quando="2024-05-23T22:00:00Z",
            oggetto=2,
            corredo=2,
            filtro_id=oiii,
            esposizione=300.0,
            hash_="c",
        )
        posa(
            conn,
            quando="2025-01-10T22:00:00Z",
            oggetto=2,
            corredo=2,
            coord=EKAR[1:3],
            filtro_id=oiii,
            esposizione=300.0,
            hash_="d",
        )
        corri(conn)
        conn.execute(
            "INSERT INTO weather_nights(site_id, night_date, kind, source, fetched_at,"
            " hourly_json, summary_json) SELECT site_id, night_date, 'observed', 'archive',"
            " '2024-06-01T00:00:00Z', '[]', ? FROM nights WHERE night_date = '2024-05-08'",
            (
                json.dumps(
                    {
                        "verdict": "go",
                        "cloud_total_pct": 8.0,
                        "usable_hours": 9,
                        "window": "dark",
                        "window_hours": 9,
                        "transparency": 92.0,
                    }
                ),
            ),
        )
        conn.commit()
        yield ekar
    finally:
        conn.close()


@pytest.fixture
def client(db_path, archivio):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        c.ekar = archivio
        yield c


def criteri(pagina):
    return {
        c["key"]: {o["value"]: (o["nights"], o["chosen"]) for o in c["options"]}
        for c in pagina["criteria"]
    }


def test_the_criteria_come_in_the_order_of_the_sheet(client):
    chiavi = [c["key"] for c in notti(client)["criteria"]]
    assert chiavi == ["year", "site", "setup", "filter", "constellation", "sky"]


def test_each_choice_says_how_many_nights_it_would_give(client):
    c = criteri(notti(client))
    assert c["year"] == {"2025": (1, False), "2024": (3, False)}
    assert c["site"] == {"1": (3, False), str(client.ekar): (1, False)}
    assert c["setup"] == {"1": (2, False), "2": (3, False)}
    assert c["filter"] == {"Ha": (2, False), "OIII": (3, False)}
    assert c["constellation"] == {"And": (2, False), "Tau": (3, False)}
    assert c["sky"] == {"go": (1, False), "unknown": (3, False)}


def test_the_criteria_count_with_the_other_choices_applied(client):
    """Scelto OIII, gli anni contano le notti in OIII; i filtri contano senza la propria
    scelta, o Ha si spegnerebbe e non si potrebbe aggiungere."""
    pagina = notti(client, filter="OIII")
    assert pagina["total"] == 3
    c = criteri(pagina)
    assert c["year"] == {"2025": (1, False), "2024": (2, False)}
    assert c["filter"] == {"Ha": (2, False), "OIII": (3, True)}


def test_within_a_criterion_any_across_all(client):
    assert notti(client, filter=["Ha", "OIII"])["total"] == 4
    assert notti(client, filter="Ha", site=client.ekar)["total"] == 0
    assert notti(client, filter="OIII", year="2024")["total"] == 2


def test_a_choice_at_zero_stays_listed_with_its_zero(client):
    """Una scelta a zero si vede spenta: sparire farebbe saltare la tendina sotto il dito."""
    c = criteri(notti(client, site=client.ekar))
    assert c["filter"]["Ha"] == (0, False)


def test_a_night_without_a_filter_is_found_by_its_own_choice(client, db_path):
    """Frame senza filtro nell'header: una scelta sua in fondo ai filtri, che li trova."""
    conn = connect(db_path)
    conn.execute("UPDATE frames SET filter_id = NULL WHERE date_obs LIKE '2024-05-08%'")
    conn.commit()
    conn.close()
    filtri = [o["value"] for o in notti(client)["criteria"][3]["options"]]
    assert filtri[-1] == "__no_filter__"
    trovate = notti(client, filter="__no_filter__")["items"]
    assert [n["night_date"] for n in trovate] == ["2024-05-08"]


def test_an_object_is_found_by_name_and_common_name(client):
    """Come la Ricerca: ogni nome dell'oggetto, senza spazi ne' maiuscole."""
    assert notti(client, q="m45")["total"] == 3
    assert notti(client, q="pleia")["total"] == 3
    assert [n["night_date"] for n in notti(client, q="andromeda")["items"]] == [
        "2024-05-15",
        "2024-05-08",
    ]


def test_the_sky_criterion_reads_the_verdict(client):
    assert [n["night_date"] for n in notti(client, sky="go")["items"]] == ["2024-05-08"]


def test_a_month_says_its_nights_and_hours(client):
    """I mesi dell'elenco contano le notti dei criteri, non solo le righe caricate."""
    mesi = notti(client, limit=1)["months"]
    assert [(m["month"], m["nights"], m["integration_s"]) for m in mesi] == [
        ("2025-01", 1, 300.0),
        ("2024-05", 3, 1800.0),
    ]
    assert [m["month"] for m in notti(client, filter="Ha")["months"]] == ["2024-05"]


def test_a_night_says_where_its_site_comes_from(client, db_path):
    per_data = {n["night_date"]: n["site_from"] for n in notti(client)["items"]}
    assert per_data["2025-01-10"] == "frames"
    assert per_data["2024-05-08"] == "home"
    conn = connect(db_path)
    conn.execute("UPDATE nights SET site_source = 'declared' WHERE night_date = '2024-05-08'")
    conn.commit()
    conn.close()
    per_data = {n["night_date"]: n["site_from"] for n in notti(client)["items"]}
    assert per_data["2024-05-08"] == "answer"


def test_a_past_night_says_how_much_broadband_the_moon_left(client):
    """Luna nuova: tutta banda larga. Piena e su tutta la notte: solo banda stretta. Mezza, che
    tramonta a notte fonda: mista, con le ore di banda larga accanto."""
    per_data = {n["night_date"]: n["shooting"] for n in notti(client)["items"]}
    assert per_data["2024-05-08"]["kind"] == "broadband"
    assert per_data["2024-05-23"]["kind"] == "narrowband"
    mista = per_data["2024-05-15"]
    assert mista["kind"] == "mixed"
    assert 0 < mista["broadband_hours"] < mista["dark_hours"]


def test_the_month_has_a_sign_per_night_and_its_totals(client):
    mese = calendario(client, "2024-05")
    assert [(g["day"], [n["verdict"] for n in g["nights"]]) for g in mese["days"]] == [
        (8, ["go"]),
        (15, [None]),
        (23, [None]),
    ]
    assert (mese["nights"], mese["good"], mese["integration_s"]) == (3, 1, 1800.0)
    assert [g["verdict"] for g in mese["days"]] == ["go", None, None]


def test_the_months_go_from_the_first_night_to_today(client):
    mese = calendario(client, "2024-05")
    oggi = night_date(iso_z(datetime.now(UTC)), "Europe/Rome")
    assert (mese["first_month"], mese["last_month"]) == ("2024-05", oggi[:7])


def test_a_month_without_nights_is_an_empty_month_not_an_error(client):
    mese = calendario(client, "2024-07")
    assert (mese["days"], mese["nights"], mese["good"]) == ([], 0, 0)


def test_a_month_that_is_not_a_month_is_refused(client):
    for mese in ("maggio", "0000-01", "9999-12"):
        assert client.get("/api/v1/nights/calendar", params={"month": mese}).status_code == 422


def test_a_value_no_night_holds_stays_chosen_at_zero(client):
    """Un indirizzo scritto a mano: la scelta resta elencata a zero, non un errore."""
    for criterio, valore in (("site", "abc"), ("setup", "x"), ("sky", "foo")):
        c = criteri(notti(client, **{criterio: valore}))
        assert c[criterio][valore] == (0, True)


def test_one_night_by_id_wins_over_the_criteria(client):
    tutte = notti(client)["items"]
    vecchia = tutte[-1]["id"]
    pagina = notti(client, night=vecchia, filter="Ha")
    assert ([n["id"] for n in pagina["items"]], pagina["total"]) == ([vecchia], 1)


def test_the_pages_of_a_chosen_list_follow_one_another(client):
    prima = notti(client, filter="OIII", limit=2)
    dopo = notti(client, filter="OIII", limit=2, offset=2)
    assert (prima["total"], dopo["total"]) == (3, 3)
    assert [n["night_date"] for n in prima["items"] + dopo["items"]] == [
        "2025-01-10",
        "2024-05-23",
        "2024-05-15",
    ]
