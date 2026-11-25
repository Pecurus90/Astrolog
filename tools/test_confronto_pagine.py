"""The step 40 bench: what it drops, what it calls a difference, an export end to end."""

import io
import json
import sys
from pathlib import Path

import pytest

import confronto_pagine as cp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


def test_ids_and_the_clock_go_numbers_and_names_stay():
    page = {
        "id": 4,
        "night_date": "2025-04-28",
        "rig_id": 2,
        "panel_ids": [1, 2],
        "tonight": "2026-11-25",
        "last_month": "2026-11",
        "items": [{"id": 9, "key": "m-97", "frames": 50}],
    }
    assert cp.without_volatile(page) == {
        "night_date": "2025-04-28",
        "items": [{"key": "m-97", "frames": 50}],
    }


def test_every_kind_of_difference_has_its_path():
    a = {"x": 1, "only_a": 0, "list": [1, 2], "deep": {"v": "M 97"}}
    b = {"x": 2, "only_b": 0, "list": [1], "deep": {"v": "NGC 3587"}}
    assert list(cp.differences(a, b)) == [
        '/deep/v: "M 97" -> "NGC 3587"',
        "/list: 2 items in A, 1 in B",
        "/only_a: only in A",
        "/only_b: only in B",
        "/x: 1 -> 2",
    ]
    assert list(cp.differences(a, a)) == []


def test_compare_says_one_when_anything_differs(tmp_path, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"n": [1]}), encoding="utf-8")
    b.write_text(json.dumps({"n": [2]}), encoding="utf-8")
    assert cp.main(["confronta", str(a), str(a)]) == 0
    assert cp.main(["confronta", str(a), str(b)]) == 1
    assert "/n[0]: 1 -> 2" in capsys.readouterr().out


def test_compare_writes_every_difference_through_a_cp1252_pipe(tmp_path, monkeypatch):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"f": ["L", "x"]}), encoding="utf-8")
    b.write_text(json.dumps({"f": ["Hα", "y"]}), encoding="utf-8")
    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252"))
    assert cp.main(["confronta", str(a), str(b)]) == 1
    sys.stdout.flush()
    assert raw.getvalue().decode("utf-8").splitlines() == [
        '/f[0]: "L" -> "Hα"',
        '/f[1]: "x" -> "y"',
    ]


def test_an_export_reads_every_page_and_leaves_the_database_as_it_was(tmp_path, monkeypatch):
    from astrolog.catalog import bundle
    from astrolog.db.connect import create_database

    monkeypatch.setattr(bundle, "path", lambda: None)  # no catalogue: 18 s for nothing here
    db = tmp_path / "astrolog.db"
    create_database(db)
    before = db.read_bytes()
    pages = cp.export(db)
    assert set(pages) == {"Notti", "Archivio e Oggetti", "Attrezzatura", "Da confermare"}
    assert pages["Notti"]["list"]["items"] == []
    assert db.read_bytes() == before
    assert list(cp.differences(pages, cp.export(db))) == []


def test_a_build_refuses_a_database_already_there(tmp_path):
    db = tmp_path / "astrolog.db"
    db.write_bytes(b"")
    with pytest.raises(SystemExit, match="exists"):
        cp.build(tmp_path, db)


def test_a_build_refuses_a_folder_another_build_used(tmp_path):
    (tmp_path / cp.BACKUP).write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="one folder per build"):
        cp.build(tmp_path, tmp_path / "head.db")


def test_a_build_without_nights_fails_instead_of_comparing_nothing(tmp_path, monkeypatch):
    from astrolog.catalog import bundle

    monkeypatch.setattr(bundle, "path", lambda: None)
    (tmp_path / "vuota").mkdir()
    (tmp_path / "db").mkdir()
    with pytest.raises(SystemExit, match="no night built"):
        cp.build(tmp_path / "vuota", tmp_path / "db" / "head.db")
