"""Le misure di un oggetto e di una notte si cercano per indice, non scorrendo la tabella: a 10.000
frame lo scorrere costava 45 e 55 ms a lettura (audit del 20/11/2026)."""

import pytest

from astrolog.spine import counts
from astrolog.spine.night_measures_read import _SERIES
from astrolog.spine.object_measures_read import _where


def _plan(conn, sql, values):
    return [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql, values)]


@pytest.mark.parametrize("table", ["object_measures", "object_measure_groups"])
@pytest.mark.parametrize("row", [{"id": 7, "mosaic_key": None}, {"id": 0, "mosaic_key": "m1"}])
def test_an_objects_measures_are_found_by_index(conn, table, row):
    where, values = _where(row, counts.Scope())
    plan = _plan(conn, f"SELECT * FROM {table} g WHERE {where}", values)  # noqa: S608 - ours
    assert not [p for p in plan if p.startswith("SCAN")], plan


def test_a_nights_series_finds_each_frames_file_by_index(conn):
    plan = _plan(conn, _SERIES, (1,))
    assert not [p for p in plan if p.startswith("SCAN pf")], plan
