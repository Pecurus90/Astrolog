"""Stop hook: every answer to Marco ends with a `Prossimo:` line saying what comes next (/clear and
start again, other work, or what we wait for), so he never has to ask. Blocks once."""

import json
import re
import sys

FENCE = re.compile(r"^\s*```")
# the label at a line's start, past list marks and bold
LABEL = re.compile(r"^[\s>#*_\-]*(?:\d+[.)]\s*)?[*_]*Prossimo[*_]*\s*:", re.IGNORECASE)
WHY = (
    "La risposta non dice a Marco come si prosegue. Chiudi con una riga 'Prossimo:' -- "
    "'/clear, poi <cosa>' se il lavoro e' chiuso; '<lavoro>' se resta da fare ora; "
    "'aspettiamo <cosa, fino a quando>' se si attende; 'scegli nella domanda sopra' se tocca a lui "
    "(la domanda va con AskUserQuestion, mai in testo libero)."
)


def reason(text: str) -> str | None:
    """Why the turn may not end, or None."""
    if not text.strip():
        return None
    inside = False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
        elif not inside and LABEL.match(line):
            return None
    return WHY


def main() -> int:
    # a hook that cannot read its input lets the turn end, never shows a traceback
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active"):
            return 0
        why = reason(str(payload.get("last_assistant_message") or ""))
    except (ValueError, AttributeError):
        return 0
    if why:
        sys.stdout.write(json.dumps({"decision": "block", "reason": why}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
