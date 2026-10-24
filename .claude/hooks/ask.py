"""Stop hook: a question to Marco comes with answers to pick (AskUserQuestion), never as free text
at the end of the turn. Blocks once; `stop_hook_active` lets the retry through."""

import json
import re
import sys

ASK_TOOL = "AskUserQuestion"
FENCE = re.compile(r"^\s*```")
# a line ending in "?" once trailing markdown (bold, italics, code, brackets) is peeled off
QUESTION = re.compile(r"\?[\s*_`)\]]*$")
WHY = (
    "La risposta finisce con una domanda in testo libero: a Marco si chiede con AskUserQuestion, "
    "a scelta multipla, la consigliata in cima (CLAUDE.md, principio 2)."
)


def _blocks(entry: dict) -> list[dict]:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content or [] if isinstance(b, dict)]


def _starts_turn(entry: dict) -> bool:
    """A message Marco typed: not a tool result, not a system reminder."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    return not any(b.get("type") == "tool_result" for b in _blocks(entry))


def _asks(text: str) -> bool:
    inside = False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
        elif not inside and QUESTION.search(line):
            return True
    return False


def reason(entries: list[dict]) -> str | None:
    """Why the turn may not end, or None."""
    main = [
        e for e in entries if e.get("type") in ("user", "assistant") and not e.get("isSidechain")
    ]
    start = max((i for i, e in enumerate(main) if _starts_turn(e)), default=-1)
    turn = [b for e in main[start + 1 :] if e.get("type") == "assistant" for b in _blocks(e)]
    if any(b.get("type") == "tool_use" and b.get("name") == ASK_TOOL for b in turn):
        return None
    texts = [b.get("text", "") for b in turn if b.get("type") == "text"]
    return WHY if texts and _asks(texts[-1]) else None


def _read(path: str) -> list[dict]:
    entries = []
    with open(path, encoding="utf-8") as lines:
        for line in lines:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def main() -> int:
    # a hook that cannot read its input lets the turn end, never shows a traceback
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active") or not payload.get("transcript_path"):
            return 0
        why = reason([e for e in _read(payload["transcript_path"]) if isinstance(e, dict)])
    except (OSError, ValueError, AttributeError):
        return 0
    if why:
        sys.stdout.write(json.dumps({"decision": "block", "reason": why}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
