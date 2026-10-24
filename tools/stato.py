"""Lo stato del progetto all'avvio di ogni sessione (ADR 0040, regola 2: prima il rosso).

Hook SessionStart: cio' che stampa entra nel contesto. Passo aperto, CI di main, Nightly, Issue per
etichetta, avvisi di sicurezza, modifiche non salvate. Senza rete lo dice, non tace.
"""

import datetime as dt
import json
import os
import subprocess
import sys
from collections.abc import Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import piano

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# GitHub may skip a cron without telling: a nightly older than this is stopped, not green.
NIGHTLY_STALE_H = 36
RULE = "Se qualcosa qui e' rosso, il lavoro di oggi e' quello."

type Run = Callable[[list[str]], str]


def _gh(args: list[str]) -> str:
    done = subprocess.run(
        ["gh", *args], capture_output=True, encoding="utf-8", cwd=ROOT, timeout=15, check=True
    )
    return done.stdout


def _hours(stamp: str, now: dt.datetime) -> int:
    return int(
        (now - dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds() // 3600
    )


def _runs(run: Run, workflow: str) -> list[dict]:
    fields = "conclusion,status,createdAt"
    args = ["run", "list", "--workflow", workflow, "--limit", "30", "--json", fields]
    if workflow == "AstroLog":
        args += ["--branch", "main"]
    return json.loads(run(args))


def _last_green(runs: list[dict]) -> dict | None:
    return next((r for r in runs if r["conclusion"] == "success"), None)


def _ci_line(runs: list[dict], now: dt.datetime) -> str:
    done = [r for r in runs if r["status"] == "completed"]
    if runs and runs[0]["status"] != "completed":
        before = "verde" if done and done[0]["conclusion"] == "success" else "ROSSA"
        return f"CI di main: in corso (prima {before})"
    if not runs:
        return "CI di main: mai corsa"
    if done[0]["conclusion"] == "success":
        return "CI di main: verde"
    green = _last_green(done)
    since = f"da {_hours(green['createdAt'], now)} h" if green else "da sempre"
    return f"CI di main: ROSSA {since}"


def _nightly_line(runs: list[dict], now: dt.datetime) -> str:
    if not runs:
        return "Nightly: mai corsa"
    last = runs[0]
    age = _hours(last["createdAt"], now)
    if age > NIGHTLY_STALE_H:
        return f"Nightly: FERMA, ultima corsa {age} h fa"
    if last["status"] != "completed":
        done = [r for r in runs if r["status"] == "completed"]
        before = "verde" if done and done[0]["conclusion"] == "success" else "ROSSA"
        return f"Nightly: in corso (prima {before})"
    if last["conclusion"] == "success":
        return f"Nightly: verde (ultima {age} h fa)"
    green = _last_green(runs)
    since = f"ultima verde {_hours(green['createdAt'], now)} h fa" if green else "mai verde"
    return f"Nightly: ROSSA, {since}"


def _issues_line(issues: list[dict], now: dt.datetime) -> str:
    oldest: dict[str, int] = {}
    count: dict[str, int] = {}
    for issue in issues:
        for label in issue["labels"] or [{"name": "senza etichetta"}]:
            name = label["name"]
            count[name] = count.get(name, 0) + 1
            oldest[name] = max(oldest.get(name, 0), _hours(issue["createdAt"], now))
    if not count:
        return "Issue aperte: nessuna"
    parts = [f"{n} {count[n]} (la piu' vecchia {oldest[n] // 24} g)" for n in sorted(count)]
    return "Issue aperte: " + ", ".join(parts)


def count_pages(out: str) -> int:
    """`gh api --paginate --jq length` prints one count per page; a plain list counts itself."""
    try:
        value = json.loads(out)
        return len(value) if isinstance(value, list) else int(value)
    except ValueError:
        return sum(int(x) for x in out.split())


_FAILED = (OSError, subprocess.SubprocessError, ValueError)


def _alerts(run: Run, kind: str) -> str:
    path = f"repos/{{owner}}/{{repo}}/{kind}/alerts?state=open&per_page=100"
    try:
        return str(count_pages(run(["api", "--paginate", path, "--jq", "length"])))
    except _FAILED:  # feature off or token without scope: unknown, not zero
        return "non so"


def github_lines(run: Run, now: dt.datetime) -> list[str]:
    """Each line stands alone: one failing call says 'non so', never hides a red already read."""
    try:
        lines = [_ci_line(_runs(run, "AstroLog"), now)]
    except _FAILED:
        return ["GitHub non raggiungibile: stato da controllare a mano"]
    try:
        lines.append(_nightly_line(_runs(run, "Nightly"), now))
    except _FAILED:
        lines.append("Nightly: non so")
    try:
        args = ["issue", "list", "--state", "open", "--limit", "1000", "--json", "labels,createdAt"]
        lines.append(_issues_line(json.loads(run(args)), now))
    except _FAILED:
        lines.append("Issue aperte: non so")
    dependabot, codeql = _alerts(run, "dependabot"), _alerts(run, "code-scanning")
    lines.append(f"Avvisi di sicurezza: Dependabot {dependabot}, CodeQL {codeql}")
    return lines


def _plan_line() -> str:
    with open(os.path.join(ROOT, piano.PATH), encoding="utf-8") as h:
        plan = json.load(h)
    step = piano.next_step(plan)
    return "Prossimo: " + (piano.line(step) if step else "nessuno, la lista e' finita.")


def _dirty_line() -> str:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, encoding="utf-8", cwd=ROOT,
            timeout=15, check=True,
        ).stdout  # fmt: skip
    except (OSError, subprocess.SubprocessError):
        return "Modifiche non salvate: non so"
    n = len(out.splitlines())
    return f"Modifiche non salvate: {n} file" + (" (un lavoro in volo: si chiede)" if n else "")


def report(run: Run, now: dt.datetime) -> str:
    return "\n".join(
        ["Stato di AstroLog:", *github_lines(run, now), _plan_line(), _dirty_line(), RULE]
    )


if __name__ == "__main__":
    print(report(_gh, dt.datetime.now(dt.UTC)))
