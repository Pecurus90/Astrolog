"""PreToolUse guard: an agent never edits these files or changes dependencies on its own.

They change only by their generator or by Marco's decision; the deny reason says which.
"""

import json
import os
import re
import sys

PROTECTED = (
    (re.compile(r"^old/"), "old/ is a quarry: read it, never edit it"),
    (re.compile(r"(^|/)uv\.lock$"), "uv.lock changes only with a dependency Marco approved"),
    (
        re.compile(r"(^|/)package-lock\.json$"),
        "package-lock.json changes only with a dependency Marco approved",
    ),
    (
        re.compile(r"^frontend/src/api/schema\.d\.ts$"),
        "schema.d.ts is generated: run python tools/tipi.py",
    ),
    (re.compile(r"(^|/)__snapshots__/"), "snapshots change only on purpose, never by hand"),
)

COMMANDS = (
    (re.compile(r"\buv\s+(lock|add|remove)\b"), "dependencies change only with Marco's approval"),
    (
        re.compile(r"\buv\s+sync\b(?!.*--(locked|frozen))"),
        "use uv sync --locked: a plain sync may rewrite uv.lock",
    ),
    (re.compile(r"--snapshot-update\b"), "snapshots change only on purpose, never by an agent"),
)

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
        return next((why for rule, why in PROTECTED if rule.search(rel)), None)
    if tool == "Bash":
        command = _quoted_out(data.get("command") or "")
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
        verdict = "ask" if payload.get("tool_name") == "Bash" else "deny"
        decision = {"hookEventName": "PreToolUse", "permissionDecision": verdict}
        decision["permissionDecisionReason"] = why
        sys.stdout.write(json.dumps({"hookSpecificOutput": decision}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
