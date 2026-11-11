"""L'anno della Dashboard (tavola v37, `as-dashboard__anno`): "il 2026, fino a oggi". Le notti, le
ore, la media a notte e al mese, e un quadretto per giorno colorato per ore riprese."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.spine import year
from group_bench import ROMA, corri, filtro, luogo, posa, prepara

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


def test_in_the_first_month_the_average_divides_by_a_whole_month(conn):
    """Una notte il primo gennaio e' una notte al mese, non trentuno (Marco, 16/10/2026)."""
    posa(conn, quando="2025-01-01T21:00:00Z", esposizione=3600.0, hash_="capodanno")
    corri(conn)
    assert year.of(conn, dt.date(2025, 1, 1)).per_month == 1.0


def test_an_empty_year_has_no_average_per_night_instead_of_zero(conn):
    anno = year.of(conn, dt.date(2025, 2, 1))
    assert (anno.nights, anno.per_night_s, anno.per_month) == (0, None, 0)


def test_twelve_months_with_their_hours_the_current_one_and_those_to_come(conn):
    """Tavola v79, «Il 2026, fino a oggi»: una barra per mese, quella del mese in corso accesa,
    quelle dopo vuote."""
    mesi = year.of(conn, OGGI).months
    assert [m.month for m in mesi] == list(range(1, 13))
    assert mesi[4].integration_s == 23400
    assert [m.integration_s for i, m in enumerate(mesi) if i != 4] == [0] * 11
    assert [m.current for m in mesi].index(True) == 8
    assert [m.future for m in mesi] == [False] * 9 + [True] * 3


def test_the_year_before_month_by_month_and_in_the_same_period(conn):
    """Il tratteggio e' l'anno prima, mese intero; il confronto a parole e' lo stesso periodo, dal
    primo gennaio allo stesso giorno: il 30 dicembre 2023 sta nel mese, non nel periodo."""
    posa(conn, quando="2023-06-10T21:00:00Z", esposizione=7200.0, hash_="giugno")
    corri(conn)
    anno = year.of(conn, OGGI)
    assert anno.months[5].previous_s == 7200
    assert anno.months[11].previous_s == 3600
    assert anno.previous_same_period_s == 7200


def test_on_february_29_the_same_period_ends_on_the_28th(conn):
    posa(conn, quando="2023-02-28T21:00:00Z", esposizione=3600.0, hash_="28")
    corri(conn)
    assert year.of(conn, dt.date(2024, 2, 29)).previous_same_period_s == 3600


def test_the_bars_are_scaled_on_the_fullest_month_of_both_years(conn):
    """Il mese piu' pieno dei due anni e' la barra intera: il confronto si legge a occhio."""
    posa(conn, quando="2023-06-10T21:00:00Z", esposizione=46800.0, hash_="giugno")
    corri(conn)
    mesi = year.of(conn, OGGI).months
    assert mesi[5].previous_bar == 1.0
    assert mesi[4].bar == 0.5
    assert mesi[0].bar == 0.0


def test_the_hours_per_filter_with_their_share_and_the_frames_naming_none(conn):
    """«Filtri del 2026»: ore e quota di ogni filtro, dal piu' ripreso; i frame che non dicono il
    filtro sono ore loro, non di un filtro."""
    ha, oiii = filtro(conn, "Ha", "ha"), filtro(conn, "OIII", "oiii")
    posa(conn, quando="2024-06-01T21:00:00Z", esposizione=1800.0, filtro_id=oiii, hash_="o")
    posa(conn, quando="2024-06-02T21:00:00Z", esposizione=10800.0, filtro_id=ha, hash_="h")
    corri(conn)
    anno = year.of(conn, OGGI)
    assert [(f.name, f.passband, f.integration_s, f.share_pct) for f in anno.filters] == [
        ("Ha", "ha", 10800, 30),
        ("OIII", "oiii", 1800, 5),
    ]
    assert (anno.no_filter_s, anno.no_filter_pct) == (23400, 65)


def test_the_shares_add_up_to_100(conn):
    """Tre terzi arrotondati da soli fanno 99: il punto che manca va al resto piu' grande."""
    a, b = filtro(conn, "R", "r"), filtro(conn, "G", "g")
    posa(conn, quando="2024-06-01T21:00:00Z", esposizione=23400.0, filtro_id=a, hash_="r")
    posa(conn, quando="2024-06-02T21:00:00Z", esposizione=23400.0, filtro_id=b, hash_="g")
    corri(conn)
    anno = year.of(conn, OGGI)
    assert sum(f.share_pct for f in anno.filters) + anno.no_filter_pct == 100


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
        "months",
        "previous_same_period_s",
        "filters",
        "no_filter_s",
        "no_filter_pct",
    }
