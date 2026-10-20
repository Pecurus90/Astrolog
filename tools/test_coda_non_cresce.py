"""The queue never grows in a commit: the guard stops a staged coda.md longer than HEAD's."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import coda_non_cresce  # noqa: E402


def _staged(monkeypatch, before: str, after: str) -> int:
    texts = {"HEAD": before, "": after}
    monkeypatch.setattr(coda_non_cresce, "_git_show", lambda ref: texts[ref])
    return coda_non_cresce.main()


def test_a_longer_queue_is_refused(monkeypatch):
    assert _staged(monkeypatch, "a\nb\n", "a\nb\nc\n") == 1


def test_an_idea_that_pays_its_lines_passes(monkeypatch):
    assert _staged(monkeypatch, "a\nb\n", "a\nc\n") == 0


def test_a_shorter_queue_passes(monkeypatch):
    assert _staged(monkeypatch, "a\nb\n", "a\n") == 0
