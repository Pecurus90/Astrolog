"""The glossary's 'non si dice' column against the Italian texts (ADR 0025).

The column depends on context ("notte" is wrong for a session, right for a night), so a machine
checks only two things: every word shown for one thing and banned for another says why in a note,
and the guarded forms, which mean one thing only, stay out of the texts. `glossario-ok` on a line
lets a quotation through.
"""

import fnmatch
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "docs" / "domini" / "glossario.md"

# form -> the glossary row (its code) whose 'non si dice' names it
GUARDED = {"pose": "`frame`"}
SCOPE = (
    "README.md",
    "CONTRIBUTING.md",
    "docs/*.md",
    "handoff/*.md",
    "frontend/src/*",
    "backend/astrolog/*",
)
OUT_OF_SCOPE = (
    "docs/domini/glossario.md",
    "docs/registro.md",
    "frontend/src/i18n/en.ts",
    # Design's v58 sheet, copied byte for byte like handoff/design
    "frontend/src/stili/consegna/astrolog.css",
)
NOTE = re.compile(r"\([^)]*\)")
OPEN, CLOSE = chr(0xAB), chr(0xBB)  # the Italian quotes of the messages
CODE = re.compile(r"`[^`]*`")


@dataclass
class Row:
    code: str
    shown: list[str]
    banned: list[tuple[str, str]]  # (bare word, the item as written, note included)


def _bare(item: str) -> str:
    return NOTE.sub("", item).strip().strip(OPEN + CLOSE + "\"'*").lower()


def rows(text: str) -> list[Row]:
    found = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("| ") or len(cells) < 4 or cells[0] == "cosa e'":
            continue
        items = [i.strip() for i in re.split(r",(?![^()]*\))", cells[3]) if i.strip()]
        shown = [_bare(i) for i in NOTE.sub("", cells[2]).split(",")]
        found.append(Row(cells[1], shown, [(_bare(i), i) for i in items]))
    return found


def doubles_without_note(table: list[Row]) -> list[str]:
    owners = {w: r.code for r in table for w in r.shown if w}
    return [
        f"{r.code}: {OPEN}{word}{CLOSE} e' a schermo per {owners[word]}"
        for r in table
        for word, item in r.banned
        if word in owners and owners[word] != r.code and "(" not in item
    ]


def unhoused(table: list[Row]) -> list[str]:
    banned = {r.code: " ".join(item for _, item in r.banned).lower() for r in table}
    return [
        form
        for form, code in GUARDED.items()
        if not re.search(rf"(?<![\w-]){form}(?![\w-])", banned.get(code, ""))
    ]


def in_scope(path: str) -> bool:
    # fnmatch's * crosses /: Design's own folders under handoff/ are refused by depth
    if path in OUT_OF_SCOPE or (path.startswith("handoff/") and path.count("/") > 1):
        return False
    return any(fnmatch.fnmatch(path, p) for p in SCOPE)


def misuses(path: str, text: str) -> list[str]:
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        if "glossario-ok" in line:
            continue
        plain = CODE.sub("", line).lower()
        for form, code in GUARDED.items():
            if re.search(rf"(?<![\w-]){form}(?![\w-])", plain):
                found.append(f"{path}:{n}: {OPEN}{form}{CLOSE} -> {code.strip('`')}")
    return found


def main(paths: list[str]) -> int:
    problems = []
    if GLOSSARY.exists():
        table = rows(GLOSSARY.read_text(encoding="utf-8"))
        problems += doubles_without_note(table)
        problems += [
            f"{GLOSSARY.name}: {OPEN}{f}{CLOSE} sorvegliata ma non nel glossario"
            for f in unhoused(table)
        ]
    for path in paths:
        normal = path.replace("\\", "/")
        if in_scope(normal) and Path(path).is_file():
            problems += misuses(normal, Path(path).read_text(encoding="utf-8", errors="replace"))
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
