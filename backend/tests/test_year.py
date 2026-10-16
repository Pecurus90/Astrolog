"""L'anno della Dashboard (tavola v37, `as-dashboard__anno`): "il 2026, fino a oggi". Le notti, le
ore, la media a notte e al mese, e un quadretto per giorno colorato per ore riprese."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.spine import year
from group_bench import ROMA, corri, luogo, posa, prepara

OGGI = dt.date(2024, 9, 30)


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    prepara(c)
    luogo(c, ROMA)
    # 17 maggio: 1 h 30; 18 maggio: 5 h; 2023: fuori dall'anno
    posa(c, quando="2024-05-17T22:00:00Z", esposizione=5400.0, hash_="a")
    posa(c, quando="2024-05-18T21:00:00Z", esposizione=10800.0, hash_="b")
    posa(c, quando="2024-05-18T23:00:00Z", esposizione=7200.0, hash_="c")
    posa(c, quando="2023-12-30T22:00:00Z", esposizione=3600.0, hash_="d")
    corri(c)
    c.commit()
    yield c
    c.close()


def test_the_year_counts_its_nights_and_hours_until_today(conn):
    anno = year.of(conn, OGGI)
    assert (anno.year, anno.until, anno.nights, anno.integration_s) == (
        2024,
        "2024-09-30",
        2,
        23400,
    )


def test_the_averages_are_per_night_and_per_elapsed_month(conn):
    """A notte: le ore diviso le notti. Al mese: le notti diviso i mesi passati, il mese in corso
    per la parte trascorsa (al 30 settembre, 9 mesi)."""
    anno = year.of(conn, OGGI)
    assert anno.per_night_s == 11700
    assert anno.per_month == 0.2  # gia' a un decimale, come la mostra lo schermo


def test_one_square_per_day_with_its_level_and_the_days_still_to_come(conn):
    """Le soglie sono quelle della legenda della tavola: 0 h, meno di 2, 2-4, 4-6, oltre 6."""
    giorni = {g.date: g for g in year.of(conn, OGGI).days}
    assert len(giorni) == 366  # il 2024 e' bisestile
    assert giorni["2024-05-17"].level == "under2"
    assert giorni["2024-05-18"].level == "4to6"
    assert giorni["2024-05-18"].integration_s == 18000
    assert giorni["2024-05-19"].level == "none"
    assert giorni["2024-10-01"].level == "future"


def test_the_grid_starts_on_monday(conn):
    """Sette righe da lunedi': il primo gennaio 2024 e' un lunedi', il 2026 comincia di giovedi'."""
    assert year.of(conn, OGGI).lead_blank == 0
    assert year.of(conn, dt.date(2026, 3, 1)).lead_blank == 3


def test_an_empty_year_has_no_average_per_night_instead_of_zero(conn):
    anno = year.of(conn, dt.date(2025, 2, 1))
    assert (anno.nights, anno.per_night_s, anno.per_month) == (0, None, 0)


def test_the_route_answers_the_year_of_the_home_site(db_path, conn):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        r = c.get("/api/v1/year")
    assert r.status_code == 200, r.text
    detto = r.json()
    assert set(detto) >= {
        "year",
        "until",
        "nights",
        "integration_s",
        "per_night_s",
        "per_month",
        "lead_blank",
        "days",
    }
