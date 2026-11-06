"""Il Bortle del sito dalle misure (docs/domini/sito.md, ADR 0039): frame buoni, una mediana per
notte, notti in almeno 4 mesi dei 12 fino all'ultima senza buchi oltre 3, livello annuo da un'onda
di un anno (Shah et al. 2025) e la mediana dei residui."""

import datetime as dt
import math
import random

import pytest

from astrolog.pipeline.filters import StandardFilter, answer, resolve
from astrolog.pipeline.site_sky import level_of, rebuild
from astrolog.pipeline.sqm_measure import declare_bias, sqm_root
from astrolog.spine import declarations as decl
from conftest import LATER
from test_pipeline_sqm_measure import _CARDS, _shot


def _season(m0: float, amplitude: float, day: dt.date) -> float:
    return m0 + amplitude * math.sin(2 * math.pi * day.toordinal() / 365.25)


def _every(start: dt.date, step_days: int, count: int) -> list[dt.date]:
    return [start + dt.timedelta(days=step_days * i) for i in range(count)]


def test_a_year_of_nights_gives_back_the_level_under_the_season():
    """Un'onda di 0,4 mag e un po' di rumore: il livello torna entro due centesimi."""
    rng = random.Random(7)
    days = _every(dt.date(2025, 1, 3), 9, 40)
    nights = {d.isoformat(): _season(21.0, 0.4, d) + rng.gauss(0, 0.03) for d in days}
    level = level_of(nights)
    assert level.sqm == pytest.approx(21.0, abs=0.02)
    assert (level.months, level.nights) == (12, 40)


def test_four_months_a_season_apart_are_enough():
    """Gennaio, aprile, luglio, ottobre: buchi di due mesi, e il fit tiene."""
    days = [dt.date(2025, m, d) for m in (1, 4, 7, 10) for d in (5, 12)]
    level = level_of({d.isoformat(): _season(20.5, 0.5, d) for d in days})
    assert level.months == 4
    assert level.sqm == pytest.approx(20.5, abs=0.02)


def test_three_months_are_too_few():
    days = [dt.date(2025, m, 10) for m in (1, 4, 7)]
    level = level_of({d.isoformat(): 21.0 for d in days})
    assert (level.sqm, level.months, level.nights) == (None, 3, 3)


def test_a_hole_of_four_months_is_too_much_even_across_the_year():
    """Gennaio, aprile, luglio, agosto: la finestra finisce ad agosto, e settembre-dicembre
    dell'anno prima sono un buco di quattro mesi. Il fit e' periodico: il buco si conta in giro."""
    days = [dt.date(2025, m, 10) for m in (1, 4, 7, 8)]
    assert level_of({d.isoformat(): 21.0 for d in days}).sqm is None


def test_the_window_is_the_twelve_months_up_to_the_last_night():
    """Una notte di 13 mesi prima dell'ultima non conta; un archivio vecchio conta lo stesso."""
    days = [dt.date(2019, m, 10) for m in (1, 4, 7, 10)] + [dt.date(2018, 9, 10)]
    level = level_of({d.isoformat(): 21.0 for d in days})
    assert (level.nights, level.first_night, level.last_night) == (4, "2019-01-10", "2019-10-10")
    assert level.sqm == 21.0


def test_a_cloudy_night_over_the_town_does_not_move_the_level():
    days = _every(dt.date(2025, 1, 3), 9, 40)
    nights = {d.isoformat(): _season(21.0, 0.3, d) for d in days}
    nights[days[5].isoformat()] = 18.0
    assert level_of(nights).sqm == pytest.approx(21.0, abs=0.02)


# --- dal database: quali frame contano, e di quale sito ---------------------------------------


def _site(conn, name="Casa", lat=45.494, lon=11.5218, home=True) -> int:
    cur = conn.execute(
        "INSERT INTO sites (name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES (?, ?, ?, 'Europe/Rome', ?, ?)",
        (name, lat, lon, int(home), LATER),
    )
    return cur.lastrowid


def _clone(conn, frame_id: int, number: int, **sky) -> int:
    """La stessa posa misurata, un'altra notte: righe di frame, misure, cielo e SQM copiate."""
    new = conn.execute(
        "INSERT INTO pipeline_frames (fingerprint, created_at) VALUES (?, ?)", (f"x{number}", LATER)
    ).lastrowid
    for table in ("pipeline_measures", "pipeline_solutions", "pipeline_sky", "pipeline_sqm"):
        select = f"SELECT * FROM {table} WHERE frame_id = ?"  # noqa: S608 - our names
        row = dict(conn.execute(select, (frame_id,)).fetchone())
        row["frame_id"] = new
        if table == "pipeline_sky":
            row |= sky
        marks = ", ".join("?" * len(row))  # segnaposto-ok: the columns
        insert = f"INSERT INTO {table} ({', '.join(row)}) VALUES ({marks})"  # noqa: S608
        conn.execute(insert, tuple(row.values()))
    return new


def _measured(conn, tmp_path) -> int:
    root = _shot(conn, tmp_path, *_CARDS, "FILTER  = 'L'")
    declare_bias(conn, "ZWO ASI2600MM Pro", 50, 500.0, LATER)
    sqm_root(conn, root, LATER, tmp_path / "astap")
    return conn.execute("SELECT frame_id FROM pipeline_sqm").fetchone()[0]


def _nights_in_four_seasons(conn, frame_id: int, sqm: float = 21.2, **sky) -> None:
    for i, month in enumerate((1, 4, 7, 10)):
        mid = f"2025-{month:02d}-15T23:00:00.000000+00:00"
        values = {"mid_utc": mid, "sun_altitude_deg": -40.0, "moon_altitude_deg": -20.0,
                  "altitude_deg": 60.0} | sky  # fmt: skip
        new = _clone(conn, frame_id, i, **values)
        conn.execute("UPDATE pipeline_sqm SET sqm = ? WHERE frame_id = ?", (sqm, new))
    conn.execute("DELETE FROM pipeline_sqm WHERE frame_id = ?", (frame_id,))  # resta il file


def _measures(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM site_sky_measures ORDER BY site_id")]


def test_the_good_frames_give_the_site_its_sky(conn, tmp_path):
    site = _site(conn)
    _nights_in_four_seasons(conn, _measured(conn, tmp_path))
    rebuild(conn, LATER)
    (row,) = _measures(conn)
    assert (row["site_id"], row["nights"], row["months"], row["sqm"]) == (site, 4, 4, 21.2)
    assert (row["first_night"], row["last_night"]) == ("2025-01-15", "2025-10-15")


@pytest.mark.parametrize(
    "sky",
    [
        {"sun_altitude_deg": -17.0},  # crepuscolo astronomico
        {"moon_altitude_deg": -4.0},  # Luna appena sotto l'orizzonte: ancora luce
        {"altitude_deg": 29.0},  # il bagliore delle citta' che lo SQM non corregge
    ],
)
def test_twilight_moon_and_a_low_sky_do_not_count(conn, tmp_path, sky):
    _site(conn)
    _nights_in_four_seasons(conn, _measured(conn, tmp_path), **sky)
    rebuild(conn, LATER)
    assert _measures(conn) == []


def test_without_the_camera_bias_a_frame_does_not_count(conn, tmp_path):
    _site(conn)
    _nights_in_four_seasons(conn, _measured(conn, tmp_path))
    conn.execute("UPDATE pipeline_sqm SET bias_adu = NULL")
    rebuild(conn, LATER)
    assert _measures(conn) == []


def test_the_frame_goes_to_the_site_its_night_goes_to(conn, tmp_path):
    """Casa entro 1 km vince su un sito piu' vicino, come per le notti (`site_of.site_at`)."""
    home = _site(conn, "Casa", 45.494 + 0.007, 11.5218)  # 0,8 km
    _site(conn, "Vicino", 45.494 + 0.003, 11.5218, home=False)  # 0,3 km
    _nights_in_four_seasons(conn, _measured(conn, tmp_path))
    rebuild(conn, LATER)
    assert [r["site_id"] for r in _measures(conn)] == [home]


def test_the_user_answer_for_the_coordinates_wins_beyond_one_km(conn, tmp_path):
    _site(conn, "Casa", 44.0, 11.0)
    far = _site(conn, "Monte", 45.52, 11.5218, home=False)  # 3 km
    decl.declare_coordinates(conn, "45.49,11.52", "Monte")
    _nights_in_four_seasons(conn, _measured(conn, tmp_path))
    rebuild(conn, LATER)
    assert [r["site_id"] for r in _measures(conn)] == [far]


def test_far_from_every_site_nothing_is_measured_and_no_site_is_born(conn, tmp_path):
    _site(conn, "Casa", 44.0, 11.0)
    _nights_in_four_seasons(conn, _measured(conn, tmp_path))
    rebuild(conn, LATER)
    assert _measures(conn) == []
    assert conn.execute("SELECT COUNT(*) FROM sites").fetchone()[0] == 1


def test_a_bias_declared_later_rewrites_the_site_sky(conn, tmp_path):
    _site(conn)
    frame = _measured(conn, tmp_path)
    _nights_in_four_seasons(conn, frame)
    rebuild(conn, LATER)
    declare_bias(conn, "ZWO ASI2600MM Pro", 50, 400.0, LATER)
    (row,) = _measures(conn)
    assert row["sqm"] != 21.2  # riscritto dai frame col bias nuovo


def test_a_filter_answered_later_rewrites_the_site_sky(conn, tmp_path):
    """Un nome di filtro che l'app non conosce non conta; detto L, le sue pose contano."""
    _site(conn)
    _nights_in_four_seasons(conn, _measured(conn, tmp_path))
    conn.execute("UPDATE pipeline_cards SET filter = 'Lumen'")
    resolve(conn, "Lumen")
    rebuild(conn, LATER)
    assert _measures(conn) == []
    answer(conn, "Lumen", StandardFilter.L)
    assert [r["nights"] for r in _measures(conn)] == [4]
