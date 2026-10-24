"""Every working document has a line ceiling (ADR 0027); one already over it can only shrink."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tetti


def _check(monkeypatch, path: str, before: int, after: int) -> int:
    texts = {"HEAD": "x\n" * before, "": "x\n" * after}
    monkeypatch.setattr(tetti, "_git_show", lambda ref, _path: texts[ref])
    return tetti.main([path])


@pytest.mark.parametrize(
    ("path", "ceiling"),
    [
        ("docs/piano.md", 0),
        ("docs/idee.md", 60),
        ("docs/adr/0030-x.md", 100),
        ("docs/domini/sito.md", 400),
        ("CLAUDE.md", 100),
    ],
)
def test_a_document_stops_above_its_ceiling(monkeypatch, path, ceiling):
    assert _check(monkeypatch, path, 0, ceiling) == 0
    assert _check(monkeypatch, path, 0, ceiling + 1) == 1


def test_a_document_over_its_ceiling_may_shrink(monkeypatch):
    assert _check(monkeypatch, "docs/domini/spina.md", 1072, 1000) == 0


def test_a_document_over_its_ceiling_may_not_grow(monkeypatch):
    assert _check(monkeypatch, "docs/domini/spina.md", 1072, 1073) == 1


@pytest.mark.parametrize(
    "path",
    [
        "docs/coda.md",
        "docs/stato.md",
        "appunti.md",
        "backend/NOTE.md",
        "handoff/x/y.md",
        "docs/adr/sub/x.md",
        "docs/adr/stato.md",
        "docs/domini/x/stato.md",
        "docs/NOTE.MD",
    ],
)
def test_a_document_outside_its_house_is_refused(monkeypatch, path):
    assert _check(monkeypatch, path, 0, 1) == 1


@pytest.mark.parametrize(
    "path",
    [
        "CLAUDE.md",
        "docs/adr/0040-il-metodo.md",
        "docs/domini/meteo.md",
        "docs/guida-utente.md",
        "handoff/design-selezione.md",
        ".claude/skills/rotta-api/SKILL.md",
        ".claude/agents/revisore.md",
    ],
)
def test_a_document_in_its_house_passes(monkeypatch, path):
    assert _check(monkeypatch, path, 0, 1) == 0


def test_a_change_that_pays_its_lines_passes_over_the_ceiling(monkeypatch):
    assert _check(monkeypatch, "docs/coda.md", 10, 10) == 0


def test_the_queue_never_grows(monkeypatch):
    assert _check(monkeypatch, "docs/coda.md", 10, 11) == 1
    assert _check(monkeypatch, "docs/coda.md", 10, 9) == 0


def test_a_file_without_ceiling_passes(monkeypatch):
    assert _check(monkeypatch, "docs/guida-utente.md", 0, 5000) == 0


def test_a_deleted_document_passes(monkeypatch):
    assert _check(monkeypatch, "docs/coda.md", 10, 0) == 0


def test_a_list_that_never_grows_is_born_once_then_only_shrinks(monkeypatch):
    """L'elenco dei file fuori da Prettier nasce col suo contenuto, poi non cresce mai."""
    elenco = "frontend/.prettierignore"
    assert _check(monkeypatch, elenco, 0, 149) == 0
    assert _check(monkeypatch, elenco, 149, 150) == 1
    assert _check(monkeypatch, elenco, 149, 120) == 0
