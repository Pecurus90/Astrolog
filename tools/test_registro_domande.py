"""Ogni domanda a Marco finisce in un registro locale (ADR 0040, regola 5): il 21/11 si contano
quelle tecniche, che devono essere zero."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import registro_domande

PAYLOAD = {
    "tool_name": "AskUserQuestion",
    "tool_input": {
        "questions": [
            {"question": "Tema nel primo avvio?", "header": "Tema", "options": [{"label": "Si"}]}
        ]
    },
    "tool_response": {"answers": {"Tema nel primo avvio?": "Si"}},
}


def test_a_question_becomes_one_line_with_its_answer():
    line = registro_domande.entry(PAYLOAD, "2026-10-25T10:00:00Z")
    assert line == {
        "at": "2026-10-25T10:00:00Z",
        "questions": [
            {"header": "Tema", "question": "Tema nel primo avvio?", "answer": "Si", "note": ""}
        ],
    }


def test_the_register_appends_and_never_rewrites(tmp_path):
    path = tmp_path / "domande.jsonl"
    registro_domande.append(path, {"at": "1"})
    registro_domande.append(path, {"at": "2"})
    assert [json.loads(x)["at"] for x in path.read_text(encoding="utf-8").splitlines()] == [
        "1",
        "2",
    ]


def test_a_free_note_beside_the_answer_is_kept():
    payload = {**PAYLOAD, "tool_response": {**PAYLOAD["tool_response"],
               "annotations": {"Tema nel primo avvio?": {"notes": "anche scuro"}}}}  # fmt: skip
    assert registro_domande.entry(payload, "t")["questions"][0]["note"] == "anche scuro"


def test_another_tool_is_not_a_question():
    assert registro_domande.entry({"tool_name": "Bash", "tool_input": {}}, "x") is None
