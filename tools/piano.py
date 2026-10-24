"""La lista unica (ADR 0040): `docs/piano.json`, un passo dopo l'altro.

`python tools/piano.py` stampa il primo passo aperto; `--tutto` la lista intera; `--controlla` il
formato (pre-commit); `--messaggio FILE` (commit-msg) vuole `docs(piano):` per ogni cambio che non
sia una spunta, perche' l'ordine lo decide Marco e un passo non sparisce in silenzio.
"""

import json
import re
import subprocess
import sys

PATH = "docs/piano.json"
FIELDS = ("n", "fase", "passo", "fatto_quando", "ricetta", "marco", "fatto")
RECIPES = {"costruisci", "ripara", "rifattorizza", "riordina", "rivedi", "marco"}
PLAN_PREFIX = "docs(piano):"
SHA = re.compile(r"^[0-9a-f]{7,40}$")


def faults(text: str) -> list[str]:
    try:
        plan = json.loads(text)
        steps = plan["passi"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        return [f"{PATH} non e' JSON con la chiave 'passi': {error}"]
    found = [f"{PATH}: chiave {k!r} fuori da 'passi'" for k in plan if k != "passi"]
    seen = set()
    for step in steps:
        n = step.get("n", "?")
        found += [f"passo {n}: manca {f}" for f in FIELDS if f not in step]
        if not step.get("fatto_quando"):
            found.append(f"passo {n}: manca fatto_quando")
        if step.get("ricetta") not in RECIPES:
            found.append(f"passo {n}: ricetta {step.get('ricetta')!r} sconosciuta")
        if step.get("fatto") and not SHA.match(step["fatto"]):
            found.append(f"passo {n}: fatto {step['fatto']!r} non e' uno sha")
        if n in seen:
            found.append(f"passo {n} due volte")
        seen.add(n)
    return list(dict.fromkeys(found))


def next_step(plan: dict) -> dict | None:
    return next((s for s in plan["passi"] if not s["fatto"]), None)


def only_ticks(before: str, after: str) -> bool:
    """Same steps, same order, same words; only empty `fatto` filled."""
    old, new = json.loads(before)["passi"], json.loads(after)["passi"]
    if len(old) != len(new):
        return False
    for a, b in zip(old, new, strict=True):
        if {k: v for k, v in a.items() if k != "fatto"} != {
            k: v for k, v in b.items() if k != "fatto"
        }:
            return False
        if "fatto" not in b or (a.get("fatto") != b["fatto"] and a.get("fatto")):
            return False
    return True


def plan_changed_fault(before: str | None, after: str | None, message: str) -> str | None:
    """The commit-msg check: a vanished or rewritten list needs its own message."""
    if before == after or (after is not None and before is not None and only_ticks(before, after)):
        return None
    if after is None and before is None:
        return None
    return message_fault(False, message)


def message_fault(only_ticks: bool, message: str) -> str | None:
    if only_ticks or message.startswith(PLAN_PREFIX):
        return None
    return (
        f"{PATH} cambia oltre una spunta: il messaggio deve cominciare con '{PLAN_PREFIX}'"
        " (l'ordine e i passi li decide Marco, ADR 0040)."
    )


def _git_show(ref: str) -> str | None:
    done = subprocess.run(
        ["git", "show", f"{ref}:{PATH}"], capture_output=True, encoding="utf-8", check=False
    )
    return done.stdout if done.returncode == 0 else None


def line(step: dict) -> str:
    who = f" -- Marco: {step['marco']}" if step["marco"] else ""
    return (
        f"{step['n']}. [{step['fase']}] {step['passo']} | fatto quando: {step['fatto_quando']}{who}"
    )


def main(argv: list[str]) -> int:
    if argv[:1] == ["--messaggio"]:
        with open(argv[1], encoding="utf-8") as h:
            message = h.read().strip()
        fault = plan_changed_fault(_git_show("HEAD"), _git_show(""), message)
        if fault:
            print(fault)
        return 1 if fault else 0
    with open(PATH, encoding="utf-8") as h:
        text = h.read()
    found = faults(text)
    if found or argv[:1] == ["--controlla"]:
        print("\n".join(found))
        return 1 if found else 0
    plan = json.loads(text)
    done = sum(1 for s in plan["passi"] if s["fatto"])
    if argv[:1] == ["--tutto"]:
        for step in plan["passi"]:
            print(("[x] " if step["fatto"] else "[ ] ") + line(step))
        return 0
    step = next_step(plan)
    print(f"Piano: {done} passi fatti su {len(plan['passi'])}.")
    print("Prossimo: " + (line(step) if step else "nessuno, la lista e' finita."))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
