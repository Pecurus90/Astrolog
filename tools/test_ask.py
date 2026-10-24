"""L'hook Stop: una domanda a Marco arriva con le risposte da scegliere (AskUserQuestion), mai
come testo libero in fondo al turno."""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))

import ask  # noqa: E402


def user(text, **extra):
    return {"type": "user", "message": {"role": "user", "content": text}, **extra}


def said(text):
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def tool(name):
    block = {"type": "tool_use", "name": name, "input": {}}
    return {"type": "assistant", "message": {"role": "assistant", "content": [block]}}


def result():
    block = {"type": "tool_result", "content": "ok"}
    return {"type": "user", "message": {"role": "user", "content": [block]}}


def test_a_free_text_question_at_the_end_is_blocked():
    assert ask.reason([user("parti"), said("Fatto.\n\nVuoi che parta dal meteo?")]) is not None


def test_a_question_asked_with_the_tool_passes():
    entries = [user("parti"), tool("AskUserQuestion"), result(), said("Parto dal meteo?")]
    assert ask.reason(entries) is None


def test_no_question_passes():
    assert ask.reason([user("parti"), said("Fatto: 3 test verdi.")]) is None


def test_a_question_inside_code_or_mid_line_passes():
    """Solo una riga che finisce con "?": una regex o una frase citata non sono domande."""
    text = "Regex:\n```\nx = re.compile('a?')\nok?\n```\nIl campo `q?` resta."
    assert ask.reason([user("parti"), said(text)]) is None


def test_markdown_after_the_question_mark_still_counts():
    assert ask.reason([user("parti"), said("**Parto dal meteo?**")]) is not None


def test_the_tool_in_an_earlier_turn_does_not_count():
    entries = [user("a"), tool("AskUserQuestion"), result(), user("b"), said("Vado?")]
    assert ask.reason(entries) is not None


def test_reminders_and_tool_results_do_not_start_a_turn():
    entries = [
        user("parti"),
        tool("AskUserQuestion"),
        result(),
        user("<system-reminder>x</system-reminder>", isMeta=True),
        said("Vado?"),
    ]
    assert ask.reason(entries) is None


def test_subagent_lines_are_ignored():
    entries = [user("parti"), said("Fatto."), {**said("Vado?"), "isSidechain": True}]
    assert ask.reason(entries) is None


def test_the_hook_blocks_once_and_never_loops(tmp_path):
    transcript = tmp_path / "t.jsonl"
    lines = [user("parti"), said("Vado?")]
    transcript.write_text("".join(json.dumps(e) + "\n" for e in lines), encoding="utf-8")
    hook = os.path.join(ROOT, ".claude", "hooks", "ask.py")

    def run(active):
        payload = json.dumps({"transcript_path": str(transcript), "stop_hook_active": active})
        out = subprocess.run(
            [sys.executable, hook], input=payload, capture_output=True, text=True, check=True
        ).stdout
        return json.loads(out) if out.strip() else None

    assert run(False)["decision"] == "block"
    assert run(True) is None
