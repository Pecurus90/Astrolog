"""Schema of new pipeline against its code: labels, CHECK lists, columns as dataclass fields."""

import re
from dataclasses import fields
from enum import StrEnum
from pathlib import Path

import pytest

from astrolog.pipeline.card import Card, Conditions, FrameType
from astrolog.pipeline.filters import Band, StandardFilter
from astrolog.pipeline.scanner import Skip
from astrolog.pipeline.sky import PointingSource
from astrolog.pipeline.values import Program

_ALL = Path(__file__).parents[1].joinpath("astrolog", "schema.sql").read_text("utf-8")
SCHEMA = _ALL[_ALL.index("PIPELINE NUOVA") :]


def _table(name: str) -> str:
    table = SCHEMA[SCHEMA.index(f"CREATE TABLE {name} (") :]
    return table[: table.index(") STRICT;")]


def test_every_pipeline_table_says_who_writes_it():
    """Testata dello schema: DICHIARATO (utente) o RILEVATO (app, si ricalcola)."""
    blocks = re.findall(r"((?:--[^\n]*\n)+)CREATE TABLE (pipeline_\w+)", SCHEMA)
    assert blocks
    for comment, name in blocks:
        assert comment.startswith(("-- DICHIARATO", "-- RILEVATO")), name


@pytest.mark.parametrize(
    ("table", "column", "enum"),
    [
        ("pipeline_headers", "program", Program),
        ("pipeline_cards", "frame_type", FrameType),
        ("pipeline_cards", "pointing_source", PointingSource),
        ("pipeline_files", "skip_reason", Skip),
    ],
)
def test_a_check_lists_every_member_of_its_enum(table: str, column: str, enum: type[StrEnum]):
    listed = re.search(rf"{column} IN \(([^)]*)\)", _table(table))
    assert listed is not None
    assert set(re.findall(r"'([^']+)'", listed.group(1))) == {m.value for m in enum}


@pytest.mark.parametrize(
    ("table", "row"), [("pipeline_cards", Card), ("pipeline_conditions", Conditions)]
)
def test_the_columns_are_the_dataclass_fields(table: str, row: type):
    """INSERT nasce dai campi della dataclass: stessi nomi, stesso ordine."""
    columns = re.findall(r"^  ([a-z_\d]+) ", _table(table), re.MULTILINE)
    assert columns == ["file_id", *(f.name for f in fields(row))]


@pytest.mark.parametrize(("column", "enum"), [("standard", StandardFilter), ("band", Band)])
def test_every_filter_check_lists_every_member(column: str, enum: type[StrEnum]):
    """Standard e banda stanno in piu' tabelle: ognuna elenca tutto."""
    for listed in re.findall(rf"{column}\s+TEXT[^,]*?IN \(([^)]*)\)", SCHEMA):
        assert set(re.findall(r"'([^']+)'", listed)) == {m.value for m in enum}
    assert re.search(rf"{column}\s+TEXT[^,]*?IN \(", SCHEMA)
