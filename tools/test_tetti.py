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
        ("docs/piano.md", 80),
        ("docs/idee.md", 60),
        ("docs/adr/0030-x.md", 100),
        ("docs/domini/sito.md", 400),
        ("CLAUDE.md", 200),
    ],
)
def test_a_document_stops_above_its_ceiling(monkeypatch, path, ceiling):
    assert _check(monkeypatch, path, 0, ceiling) == 0
    assert _check(monkeypatch, path, 0, ceiling + 1) == 1


def test_a_document_over_its_ceiling_may_shrink(monkeypatch):
    assert _check(monkeypatch, "docs/domini/spina.md", 1072, 1000) == 0


def test_a_document_over_its_ceiling_may_not_grow(monkeypatch):
    assert _check(monkeypatch, "docs/domini/spina.md", 1072, 1073) == 1


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
