"""The commit message rule, on `-m` messages and on real editor files."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commit_msg import SCISSORS, problems  # noqa: E402

EDITOR_TEMPLATE = (
    "\n# Bitte geben Sie eine Commit-Beschreibung f\u00fcr Ihre \u00c4nderungen ein.\n"
    "# Auf Branch main\n"
)


@pytest.mark.parametrize(
    "raw",
    [
        "fix: one line\n",
        "fix: one line\n" + EDITOR_TEMPLATE,
        "fix: one line\r\n\r\n# commento\r\n",
        f"fix: one line\n# {SCISSORS}\ndiff --git a/x b/x\n"
        "+Kamera \u041a\u0430\u043c\u0435\u0440\u0430\n",
    ],
)
def test_one_ascii_line_passes(raw):
    assert problems(raw) == []


@pytest.mark.parametrize(
    ("raw", "why"),
    [
        ("fix: a\n\nCo-Authored-By: x\n", "one line expected, found 2"),
        ("fix: perch\u00e9\n", "non-ASCII characters"),
        ("\n# only comments\n", "one line expected, found 0"),
    ],
)
def test_the_rule_blocks(raw, why):
    assert why in problems(raw)


def test_a_stored_message_keeps_its_hash_lines():
    # `git commit -m "fix: x" -m "#12"` stores two lines: the final check must see both.
    stored = "fix: x\n\n#12\n"
    assert problems(stored) == []
    assert problems(stored, final=True) == ["one line expected, found 2"]
    assert problems("fix: x\n", final=True) == []
