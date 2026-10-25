"""PreToolUse guard: an agent never edits these files or changes dependencies on its own.

They change only by their generator or by Marco's decision; the deny reason says which.
"""

import json
import os
import re
import sys

PROTECTED = (
    (re.compile(r"^old/"), "old/ is a quarry: read it, never edit it"),
    (
        re.compile(r"(^|/)uv\.lock$"),
        "uv.lock changes only by Dependabot or with a dependency Marco approved",
    ),
    (
        re.compile(r"(^|/)package-lock\.json$"),
        "package-lock.json changes only by Dependabot or with a dependency Marco approved",
    ),
    (
        re.compile(r"^frontend/src/api/schema\.d\.ts$"),
        "schema.d.ts is generated: run python tools/tipi.py",
    ),
    (re.compile(r"(^|/)__snapshots__/"), "snapshots change only on purpose, never by hand"),
)

# The method is frozen (ADR 0040): an edit to its files is Marco's click, not a refusal.
FROZEN = re.compile(r"^(CLAUDE\.md$|\.claude/)")
FROZEN_WHY = "metodo congelato fino al 21/11/2026 (ADR 0040): la modifica la conferma Marco"

COMMANDS = (
    (re.compile(r"\buv\s+(lock|add|remove)\b"), "dependencies change only with Marco's approval"),
    (
        re.compile(r"\buv\s+sync\b(?!.*--(locked|frozen))"),
        "use uv sync --locked: a plain sync may rewrite uv.lock",
    ),
    (re.compile(r"--snapshot-update\b"), "snapshots change only on purpose, never by an agent"),
)

# Never right: closing a program by name closes Marco's own (an audit once shut every Chrome).
# Whoever starts a process stops it by its PID.
KILL_BY_NAME = (
    re.compile(r"\btaskkill\b[^;&|]*\s/im\b", re.IGNORECASE),
    re.compile(r"\b(pkill|killall)\b"),
    re.compile(r"\bStop-Process\b[^;&|]*-Name\b", re.IGNORECASE),
    re.compile(r"\bGet-Process\b[^;&|]*\|\s*Stop-Process\b", re.IGNORECASE),
)
KILL_BY_NAME_WHY = "never close a program by name: stop what you started by its PID"

# Text into files only by Edit/Write (CLAUDE.md): in a script backslashes and backticks change.
HEREDOC = re.compile(r"<<-?\s*['\"]?[A-Za-z_]\w*")
HEREDOC_WRITES = (
    re.compile(r"(?<![<>&\d])&?>{1,2}(?!&)\s*(?!/dev/null)[^\s|&;<>()]"),  # redirect, 1st line
    re.compile(r"\btee\b"),
)
# Script body checked only when heredoc feeds an interpreter: a commit message may name these.
TO_INTERPRETER = re.compile(r"\b(python3?|py)(\.exe)?\s+(-\w+\s+)*-\s*<<")
SCRIPT_WRITES = re.compile(
    r"\.write_(text|bytes)\(|\bopen\(.*?,\s*(mode\s*=\s*)?['\"][wax]b?\+?['\"]"
)
HEREDOC_WHY = "text goes into files only by Edit/Write, never a heredoc or a script"

# Nothing to stash, and the pop brings back an old stash of Marco's into the work.
_GIT_STASH = r"\bgit\s+(?:-\S+(?:\s+[^-\s]\S*)?\s+)*stash\b"  # global options allowed (-C dir)
STASH_THEN_POP = re.compile(
    _GIT_STASH + r"(?!\s+(list|show|pop|apply|drop)\b).*" + _GIT_STASH + r"\s+(pop|apply)\b",
    re.DOTALL,
)
STASH_WHY = "never stash and pop in one command: compare with git worktree or git show"

NPM_CHANGES = {"uninstall", "un", "remove", "rm", "r", "update", "up", "upgrade"}
NPM_INSTALLS = {"install", "i", "add"}
NPM_VALUE_OPTIONS = {"--prefix", "-C", "--cache", "--registry", "--workspace", "-w"}


def _npm_names_a_package(command: str) -> bool:
    """A bare `npm install` is CONTRIBUTING's setup step; naming a package changes dependencies."""
    for segment in re.split(r"&&|\|\||;|\|", command):
        words = segment.split()
        if "npm" not in words:
            continue
        rest = iter(words[words.index("npm") + 1 :])
        verb = None
        for word in rest:
            if word in NPM_VALUE_OPTIONS:
                next(rest, None)
            elif re.match(r"\d*[<>]", word):
                break
            elif verb is None and not word.startswith("-"):
                verb = word
                if verb in NPM_CHANGES:
                    return True
                if verb not in NPM_INSTALLS:
                    break
            elif verb is not None and not word.startswith("-"):
                return True
    return False


def _heredoc_writes(raw: str) -> bool:
    if not HEREDOC.search(raw):
        return False
    first = raw.split("\n", 1)[0]
    if any(rule.search(_quoted_out(first)) for rule in HEREDOC_WRITES):
        return True
    return bool(TO_INTERPRETER.search(first) and SCRIPT_WRITES.search(raw))


def _relative(path: str, root: str) -> str:
    try:
        rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    except ValueError:  # another drive on Windows
        return path.replace("\\", "/")
    return rel.replace("\\", "/")


def _quoted_out(command: str) -> str:
    # a word inside quotes (an echo, a commit message) is text, not a command
    return re.sub(r"\"[^\"]*\"|'[^']*'", "", command)


def reason(payload: dict, root: str) -> str | None:
    """Why this tool call is refused, or None when it may go ahead."""
    tool = payload.get("tool_name")
    data = payload.get("tool_input") or {}
    if tool in ("Edit", "Write", "NotebookEdit"):
        rel = _relative(data.get("file_path") or data.get("notebook_path") or "", root)
        if FROZEN.search(rel):
            return FROZEN_WHY
        return next((why for rule, why in PROTECTED if rule.search(rel)), None)
    if tool in ("Bash", "PowerShell"):
        if _heredoc_writes(data.get("command") or ""):
            return HEREDOC_WHY
        command = _quoted_out(data.get("command") or "")
        if any(rule.search(command) for rule in KILL_BY_NAME):
            return KILL_BY_NAME_WHY
        if STASH_THEN_POP.search(command):
            return STASH_WHY
        if _npm_names_a_package(command):
            return "dependencies change only with Marco's approval"
        return next((why for rule, why in COMMANDS if rule.search(command)), None)
    return None


def main() -> int:
    payload = json.load(sys.stdin)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    why = reason(payload, root)
    if why is not None:
        # a hand edit of these files is never right; a command that changes them is Marco's click
        denied = (KILL_BY_NAME_WHY, HEREDOC_WHY, STASH_WHY)
        asks = why == FROZEN_WHY or (payload.get("tool_name") == "Bash" and why not in denied)
        verdict = "ask" if asks else "deny"
        decision = {"hookEventName": "PreToolUse", "permissionDecision": verdict}
        decision["permissionDecisionReason"] = why
        sys.stdout.write(json.dumps({"hookSpecificOutput": decision}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
