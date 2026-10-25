"""PostToolUse hook on AskUserQuestion: each question to Marco and its answer, appended to a
local register outside git; technical ones counted on 21/11 (ADR 0040)."""

import datetime as dt
import json
import os
import sys
from pathlib import Path

REGISTER = (
    Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "reports" / "domande.jsonl"
)


def entry(payload: dict, at: str) -> dict | None:
    if payload.get("tool_name") != "AskUserQuestion":
        return None
    response = payload.get("tool_response") or {}
    answers = response.get("answers") or {}
    notes = response.get("annotations") or {}
    questions = (payload.get("tool_input") or {}).get("questions") or []
    rows = [
        {
            "header": q.get("header", ""),
            "question": q["question"],
            "answer": answers.get(q["question"], ""),
            "note": (notes.get(q["question"]) or {}).get("notes", ""),
        }
        for q in questions
    ]
    return {"at": at, "questions": rows}


def append(path: Path, line: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as h:
        h.write(json.dumps(line, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    line = entry(payload, dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))
    if line:
        append(REGISTER, line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
