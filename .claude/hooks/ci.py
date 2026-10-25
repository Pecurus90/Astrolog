"""CI decides when work is closed (ADR 0040, rules 2-3). `stop`: no closing with main red, unless
a `bloccato` Issue names the run. `push`: after a git push, watch CI; exit 2 wakes the agent."""

import json
import re
import subprocess
import sys
import time

# Conclusions that mean main is broken; cancelled is someone stopping a run by hand, not a fault.
RED = {"failure", "timed_out", "startup_failure"}
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def stop_reason(runs: list[dict], blocked: list[dict]) -> str | None:
    if not runs or runs[0]["status"] != "completed" or runs[0]["conclusion"] not in RED:
        return None
    run = runs[0]
    named = str(run["databaseId"])
    if any(named in f"{i.get('title', '')} {i.get('body', '')}" for i in blocked):
        return None
    return (
        f"CI di main ROSSA: {run['url']}. Il lavoro non si chiude: si ripara (/ripara), oppure, se "
        f"bloccato da fuori, una Issue `bloccato` che nomina il run {named} (ADR 0040)."
    )


def is_push(command: str) -> bool:
    """A `git push` as a command of its own, not inside a quoted string."""
    segments = re.split(r"[;&|\n]+", QUOTED.sub("", command))
    return any(s.strip().startswith("git push") for s in segments)


def watch_message(sha: str, url: str, failed: bool) -> str:
    if failed:
        return f"La CI del push {sha} e' ROSSA: {url}. Il lavoro non e' chiuso: si ripara."
    return f"La CI del push {sha} e' verde: {url}."


def outcome(conclusion: str | None, sha: str, url: str) -> tuple[int, str | None]:
    """From the run's own conclusion: watch can fail by itself (API limit), a run cannot lie."""
    if conclusion in RED:
        return 2, watch_message(sha, url, failed=True)
    if not conclusion:  # gh silent, or the run not finished
        return 0, f"La CI del push {sha}: non so se e' finita ({url}). Da guardare a mano."
    if conclusion != "success":
        return 0, f"La CI del push {sha} e' finita '{conclusion}', non verde: {url}."
    return 0, None


def _gh(args: list[str], timeout: float = 30) -> str:
    done = subprocess.run(
        ["gh", *args], capture_output=True, encoding="utf-8", timeout=timeout, check=True
    )
    return done.stdout


def _stop() -> int:
    try:
        fields = "databaseId,status,conclusion,url"
        runs = json.loads(_gh(["run", "list", "--workflow", "AstroLog", "--branch", "main",
                               "--limit", "1", "--json", fields]))  # fmt: skip
        blocked = json.loads(_gh(["issue", "list", "--state", "open", "--label", "bloccato",
                                  "--limit", "1000", "--json", "title,body"]))  # fmt: skip
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0  # no network: the session-start report says so
    reason = stop_reason(runs, blocked)
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def find_run(gh, sha: str, sleep=time.sleep) -> dict | None:
    """The run of a commit, by its full sha (GitHub's --commit filter ignores a short one)."""
    for _ in range(30):  # the run appears a few seconds after the push
        found = json.loads(gh(["run", "list", "--workflow", "AstroLog", "--commit", sha,
                               "--limit", "1", "--json", "databaseId,url"]))  # fmt: skip
        if found:
            return found[0]
        sleep(10)
    return None


def _push(payload: dict) -> int:
    if not is_push((payload.get("tool_input") or {}).get("command", "")):
        return 0
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, encoding="utf-8", check=True
        ).stdout.strip()
        run = find_run(_gh, sha)
        if run is None:
            return 0
        # one poll a minute: the default 3 s burns the API limit shared by every gh call
        subprocess.run(
            ["gh", "run", "watch", str(run["databaseId"]), "--interval", "60", "--compact"],
            capture_output=True, encoding="utf-8", check=False,
        )  # fmt: skip
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0
    try:
        conclusion = json.loads(
            _gh(["run", "view", str(run["databaseId"]), "--json", "conclusion"])
        )["conclusion"]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        conclusion = None
    code, message = outcome(conclusion, sha[:8], run["url"])
    if message:
        print(message, file=sys.stderr)
    return code


def main(argv: list[str]) -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    return _push(payload) if argv[:1] == ["push"] else _stop()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
