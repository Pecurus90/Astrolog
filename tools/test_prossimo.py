"""L'hook Stop: ogni risposta a Marco chiude con una riga `Prossimo:` che dice cosa fare dopo
(/clear e ripartire, un altro lavoro, o cosa si aspetta), cosi' Marco non deve chiederlo."""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))

import prossimo  # noqa: E402

HOOK = os.path.join(ROOT, ".claude", "hooks", "prossimo.py")


def test_an_answer_without_the_next_step_is_blocked():
    assert prossimo.reason("Fatto: 3 test verdi.") is not None


def test_an_answer_ending_with_the_next_step_passes():
    assert prossimo.reason("Fatto.\n\nProssimo: /clear, poi riparazione 3 del passo 7.") is None


def test_markdown_around_the_label_still_counts():
    assert prossimo.reason("Fatto.\n\n**Prossimo:** aspettiamo la Nightly delle 23:17.") is None
    assert prossimo.reason("Fatto.\n\n- **Prossimo**: rispondi alla domanda.") is None
    assert prossimo.reason("Fatto.\n\n## Prossimo: /clear.") is None
    assert prossimo.reason("Fatto.\n\n1. Prossimo: /clear.") is None


def test_the_label_inside_code_does_not_count():
    assert prossimo.reason("Fatto.\n```\nProssimo: x\n```") is not None


def test_the_label_mid_sentence_does_not_count():
    assert prossimo.reason("Il Prossimo: passo e' scritto altrove.") is not None


def test_an_empty_answer_passes():
    """Un turno senza testo (solo strumenti) non ha nulla da chiudere."""
    assert prossimo.reason("") is None


def run(payload):
    out = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out) if out.strip() else None


def test_the_hook_reads_the_last_message_and_blocks_once():
    assert run({"last_assistant_message": "Fatto."})["decision"] == "block"
    assert run({"last_assistant_message": "Fatto.", "stop_hook_active": True}) is None
    assert run({"last_assistant_message": "Fatto.\nProssimo: /clear."}) is None


def test_a_hook_that_cannot_read_its_input_lets_the_turn_end():
    out = subprocess.run(
        [sys.executable, HOOK], input="non json", capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == ""
