"""Schema of new pipeline against its code: labels, CHECK lists, columns as dataclass fields."""

import re
from dataclasses import fields
from enum import StrEnum
from pathlib import Path

import pytest

from astrolog.pipeline.card import Conditions
from astrolog.pipeline.scanner import Program, Skip
from astrolog.pipeline.sky import PointingSource

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
        ("pipeline_cards", "pointing_source", PointingSource),
        ("pipeline_files", "skip_reason", Skip),
    ],
)
def test_a_check_lists_every_member_of_its_enum(table: str, column: str, enum: type[StrEnum]):
    listed = re.search(rf"{column} IN \(([^)]*)\)", _table(table))
    assert listed is not None
    assert set(re.findall(r"'([^']+)'", listed.group(1))) == {m.value for m in enum}


def test_the_conditions_columns_are_the_conditions_fields():
    """INSERT nasce dai campi di Conditions: stessi nomi, stesso ordine."""
    columns = re.findall(r"^  ([a-z_\d]+) ", _table("pipeline_conditions"), re.MULTILINE)
    assert columns == ["file_id", *(f.name for f in fields(Conditions))]
