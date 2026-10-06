"""Internal names in English (CLAUDE.md, "Nomi e commenti in inglese").

Uso: python tools/nomi_inglesi.py              esce 1 se un nome italiano non e' nell'elenco
     python tools/nomi_inglesi.py --riscrivi   toglie dall'elenco i nomi gia' rinominati

Reads every name the code defines in `backend/astrolog` (functions, classes, parameters,
variables, attributes, import aliases), split into words. A word is Italian when it is in
ITALIAN, or ends in a/i/o and is not in ENGLISH. The names still to rename sit in
`tools/nomi_italiani.txt`: the list only shrinks.
"""

import ast
import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "backend" / "astrolog"
BASELINE = Path(__file__).resolve().parent / "nomi_italiani.txt"

# English words, acronyms and proper names that end in a vowel the rule would flag.
ENGLISH = frozenset(
    [
        "a",
        "ap",
        "api",
        "ascii",
        "astro",
        "auto",
        "camera",
        "crota",
        "data",
        "duo",
        "eta",
        "extra",
        "go",
        "ha",
        "haoiii",
        "hi",
        "hpa",
        "i",
        "info",
        "ini",
        "into",
        "iso",
        "lo",
        "meta",
        "mono",
        "multi",
        "nina",
        "no",
        "nogo",
        "o",
        "oiii",
        "ra",
        "ratio",
        "redo",
        "schema",
        "sii",
        "siioiii",
        "to",
        "tri",
        "via",
    ]
)
# Italian words the vowel rule does not catch.
ITALIAN = frozenset(
    [
        "al",
        "alte",
        "altezze",
        "arrivate",
        "bande",
        "calibrazione",
        "camere",
        "canale",
        "cartelle",
        "certe",
        "chiave",
        "chiede",
        "chiedere",
        "classe",
        "colonne",
        "colore",
        "colpite",
        "con",
        "confine",
        "coppie",
        "costellazione",
        "cresce",
        "dal",
        "del",
        "descrizione",
        "dette",
        "domande",
        "dove",
        "eclittiche",
        "elencate",
        "elongazione",
        "fare",
        "fasce",
        "fase",
        "fattore",
        "ferme",
        "finisce",
        "focale",
        "fonte",
        "giu",
        "il",
        "incerte",
        "indice",
        "iniziate",
        "istante",
        "le",
        "lette",
        "lettere",
        "lune",
        "medie",
        "mezzanotte",
        "mie",
        "minuscole",
        "molte",
        "montature",
        "morde",
        "nel",
        "nome",
        "nord",
        "notte",
        "notturne",
        "nuvole",
        "ordine",
        "ore",
        "orfane",
        "origine",
        "ottiche",
        "padrone",
        "partite",
        "perche",
        "prese",
        "proposte",
        "provate",
        "quale",
        "quante",
        "raffiche",
        "righe",
        "rimesse",
        "riscritte",
        "saltate",
        "scansione",
        "scelte",
        "schede",
        "scritte",
        "sempre",
        "sensore",
        "serie",
        "soglie",
        "somme",
        "sorgente",
        "spostare",
        "staccate",
        "storte",
        "su",
        "tolte",
        "tre",
        "un",
        "utente",
        "valore",
        "vicine",
        "viste",
        "voce",
        "volute",
    ]
)
_WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])")


def words(name: str) -> list[str]:
    """The lowercase words of a snake_case or CamelCase name."""
    return [w.lower() for w in _WORD.findall(name)]


def is_italian(name: str) -> bool:
    """True when one word of the name is Italian."""
    return any(w in ITALIAN or (w[-1] in "aio" and w not in ENGLISH) for w in words(name))


def _defined(tree: ast.AST) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name
        elif isinstance(node, ast.arg):
            yield node.arg
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            yield node.id
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            yield node.attr
        elif isinstance(node, ast.alias) and node.asname:
            yield node.asname


def found(package: Path = PACKAGE) -> set[str]:
    """Every `path:name` with an Italian word, path relative to the package."""
    out = set()
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        out |= {f"{rel}:{n}" for n in _defined(tree) if is_italian(n)}
    return out


def read_baseline(path: Path = BASELINE) -> set[str]:
    """The names still waiting for their rename."""
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {line for line in lines if line and not line.startswith("#")}


def main(argv: list[str], package: Path = PACKAGE, baseline: Path = BASELINE) -> int:
    """Exit 1 on a new Italian name, or on a list that still names a renamed one."""
    now, listed = found(package), read_baseline(baseline)
    new, gone = sorted(now - listed), sorted(listed - now)
    for item in new:
        print(f"nome italiano: {item} (rinominalo in inglese)")
    if "--riscrivi" in argv and not new:
        header = "# Nomi italiani ancora da rinominare (tools/nomi_inglesi.py). Solo si accorcia.\n"
        baseline.write_text(header + "".join(f"{n}\n" for n in sorted(now)), encoding="utf-8")
        return 0
    for item in gone:
        print(
            f"gia' rinominato, togli dall'elenco: {item} (python tools/nomi_inglesi.py --riscrivi)"
        )
    return 1 if new or gone else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
