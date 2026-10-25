"""The nightly's result as an Issue: a red night opens or comments `nightly-rosso`, a green one
closes it. Last job of nightly.yml: `python tools/nightly_issue.py <result> <run url>`."""

import json
import subprocess
import sys

LABEL = "nightly-rosso"


def action(result: str, open_issue: int | None) -> str:
    if result == "success":
        return "close" if open_issue else "none"
    return "comment" if open_issue else "open"


def _gh(*args: str) -> str:
    # stderr not captured: a failing gh says why in the job log
    done = subprocess.run(["gh", *args], stdout=subprocess.PIPE, encoding="utf-8", check=True)
    return done.stdout


def main(argv: list[str]) -> int:
    result, url = argv[0], argv[1]
    found = json.loads(
        _gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number")
    )
    number = found[0]["number"] if found else None
    todo = action(result, number)
    if todo == "open":
        body = (
            f"La Nightly (mutazione o CI completa con Windows) e' fallita: {url}. "
            "Si chiude da sola alla prima notte verde."
        )
        _gh("issue", "create", "--label", LABEL, "--title", "Nightly rossa", "--body", body)
    elif todo == "comment":
        _gh("issue", "comment", str(number), "--body", f"Ancora rossa: {url}")
    elif todo == "close":
        _gh("issue", "close", str(number), "--comment", f"Notte verde: {url}")
    print(todo)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
