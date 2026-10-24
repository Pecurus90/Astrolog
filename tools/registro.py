"""Registry of rules: every number in the code says its source (CLAUDE.md, principle 1).

Uso: python tools/registro.py            esce 1 se manca una fonte o il registro e' vecchio
     python tools/registro.py --scrivi   rigenera docs/registro.md e accorcia l'elenco

A number is a numeric literal other than 0 and 1 in a module's top-level statement (constants,
tables); numbers inside functions are not covered. Its source is a tag in a comment on its line,
in the comment block just above that line, or in the block before the statement:
[C ...] public convention, [M ...] our measure, [P ADR nnnn] Marco's decision by its home
(an ADR or docs/domini/<domain>.md), [T] technical, not a rule. Statements still without one
sit in `tools/registro_senza_fonte.txt`: the list only shrinks.
`docs/registro.md` is generated from code and ADRs, never written by hand.
"""

import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "backend" / "astrolog"
ADR = ROOT / "docs" / "adr"
PAGE = ROOT / "docs" / "registro.md"
BASELINE = Path(__file__).resolve().parent / "registro_senza_fonte.txt"

TAG = re.compile(r"\[([CMPT])\b([^\]]*)\]")
# P names the decision's home (ADR, domain contract): date and author live there, not in code.
TAGS = ("[C ...]", "[M ...]", "[P ADR nnnn]", "[T]")
SUPERA = re.compile(r"^\*\*Supera\*\* in `(?:docs/)?([^`]+)`", re.MULTILINE)
VALUE_WIDTH = 70


@dataclass(frozen=True)
class Entry:
    ident: str  # module path:symbol, never a line number
    parts: tuple[tuple[str, tuple[str, ...]], ...]  # (value, its sources): one per number line
    sourced: bool


def _comments(text: str) -> dict[int, str]:
    """Line -> comment text on it."""
    out: dict[int, str] = {}
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            out[token.start[0]] = token.string
    return out


def _block_above(line: int, comments: dict[int, str], lines: list[str]) -> list[str]:
    """Comment-only lines right above `line`."""
    block = []
    row = line - 1
    while row >= 1 and row in comments and lines[row - 1].lstrip().startswith("#"):
        block.append(comments[row])
        row -= 1
    return block


def _numbers(node: ast.AST) -> set[int]:
    """Lines holding a numeric literal other than 0 and 1."""
    return {
        n.lineno
        for n in ast.walk(node)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, int | float)
        and not isinstance(n.value, bool)
        and n.value not in (0, 1)
    }


def _symbol(node: ast.stmt, text: str) -> str:
    if isinstance(node, ast.Assign):
        names = [ast.unparse(t) for t in node.targets]
        return " = ".join(names)
    if isinstance(node, ast.AnnAssign):
        return ast.unparse(node.target)
    return (ast.get_source_segment(text, node) or "").split("\n")[0][:40]


def _tags(comments: list[str]) -> list[str]:
    return [f"{kind}{rest}".strip() for c in comments for kind, rest in TAG.findall(c)]


def _entry(
    node: ast.AST, text: str, comments: dict[int, str]
) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], bool] | None:
    """(parts, sourced) of a node holding numbers; None without any."""
    rows = _numbers(node)
    if not rows:
        return None
    lines = text.splitlines()
    leading = _tags(_block_above(node.lineno, comments, lines))  # type: ignore[attr-defined]
    whole = node.lineno == node.end_lineno  # type: ignore[attr-defined]
    parts = []
    for row in sorted(rows):
        here = _tags([comments.get(row, "")] + _block_above(row, comments, lines))
        shown = _short(_value(node, text) if whole else lines[row - 1])
        parts.append((shown, tuple(dict.fromkeys(leading + here))))
    return tuple(parts), all(sources for _, sources in parts)


def _value(node: ast.AST, text: str) -> str:
    """Right side of an assignment, else the node itself."""
    if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None:
        return ast.get_source_segment(text, node.value) or ""
    return ast.get_source_segment(text, node) or ""


def _short(text: str) -> str:
    """One line, code without its comment, cut to width."""
    code = " ".join(text.split("  #")[0].split())
    return code if len(code) <= VALUE_WIDTH else code[: VALUE_WIDTH - 3] + "..."


type Located = tuple[str, ast.AST]  # (symbol, node holding numbers)


def _signature(name: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Located]:
    """Decorators and defaults: evaluated when the module loads, not when the body runs."""
    out: list[Located] = []
    for decorator in node.decorator_list:
        call = decorator.func if isinstance(decorator, ast.Call) else decorator
        out.append((f"{name}@{ast.unparse(call)}", decorator))
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    tail = positional[len(positional) - len(args.defaults) :]
    pairs = list(zip(tail, args.defaults, strict=True))
    pairs += [
        (a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True) if d is not None
    ]
    out += [(f"{name}({arg.arg}=)", default) for arg, default in pairs]
    return out


def _located(body: list[ast.stmt], text: str, prefix: str = "") -> list[Located]:
    """Statements run at import: module and class bodies, signatures; never function bodies."""
    out: list[Located] = []
    for node in body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            out += _signature(prefix + node.name, node)
        elif isinstance(node, ast.ClassDef):
            out += _located(node.body, text, f"{prefix}{node.name}.")
        else:
            out.append((prefix + _symbol(node, text), node))
    return out


def entries(package: Path = PACKAGE) -> list[Entry]:
    """Every number run at import, module by module; a repeated symbol gets #2, #3."""
    out = []
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package).as_posix()
        text = path.read_text(encoding="utf-8")
        comments = _comments(text)
        seen: dict[str, int] = {}
        for symbol, node in _located(ast.parse(text).body, text):
            entry = _entry(node, text, comments)
            if entry is None:
                continue
            seen[symbol] = seen.get(symbol, 0) + 1
            ident = symbol if seen[symbol] == 1 else f"{symbol}#{seen[symbol]}"
            out.append(Entry(f"{rel}:{ident}", *entry))
    return out


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _decisions(adr: Path) -> list[str]:
    rows = []
    for path in sorted(adr.glob("[0-9][0-9][0-9][0-9]-*.md")) if adr.exists() else []:
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ") if text else path.stem
        number, _, name = title.partition(" -- ")
        state = re.search(r"\*\*Stato:\*\*\s*(.+)", text)
        superseded = ", ".join(SUPERA.findall(text))
        rows.append(
            f"| {number} | {_cell(name)} | {_cell(state[1].strip() if state else '')} "
            f"| {_cell(superseded)} |"
        )
    return rows


def page(package: Path = PACKAGE, adr: Path = ADR) -> str:
    """The registry page: values with their source, then the decisions."""
    found = entries(package)
    lines = [
        "# Registro delle regole",
        "",
        "Generato da `tools/registro.py --scrivi`: non si scrive a mano. La casa di ogni valore",
        "e' il codice, con la fonte accanto: C convenzione citata, M misura nostra, P decisione",
        "di Marco, T tecnico (non una regola).",
        "",
        f"Valori: {len(found)}; senza fonte: {sum(not e.sourced for e in found)}.",
        "",
        "## Valori e tabelle nel codice (`backend/astrolog`)",
    ]
    module = None
    for entry in found:
        rel, symbol = entry.ident.split(":", 1)
        if rel != module:
            module = rel
            lines += ["", f"### {rel}", "", "| simbolo | valore | fonte |", "|---|---|---|"]
        for shown, sources in entry.parts:
            source = "; ".join(sources) if sources else "**senza fonte**"
            lines.append(f"| {_cell(symbol)} | `{_cell(shown)}` | {_cell(source)} |")
    lines += [
        "",
        "## Decisioni (ADR)",
        "",
        "| ADR | titolo | stato | supera in |",
        "|---|---|---|---|",
        *_decisions(adr),
        "",
    ]
    return "\n".join(lines)


def read_baseline(path: Path = BASELINE) -> set[str]:
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {line for line in lines if line and not line.startswith("#")}


def _write_baseline(path: Path, idents: list[str]) -> None:
    header = "# Valori ancora senza fonte (tools/registro.py). Solo si accorcia.\n"
    path.write_text(header + "".join(f"{i}\n" for i in idents), encoding="utf-8")


def main(
    argv: list[str],
    package: Path = PACKAGE,
    baseline: Path = BASELINE,
    page_path: Path = PAGE,
    adr: Path = ADR,
) -> int:
    """Exit 1 on a new unsourced value, a listed one now sourced, or a stale page."""
    missing = sorted(e.ident for e in entries(package) if not e.sourced)
    first_run = not baseline.exists()
    listed = set(missing) if first_run else read_baseline(baseline)
    new, done = sorted(set(missing) - listed), sorted(listed - set(missing))
    for ident in new:
        print(f"senza fonte: {ident} (tag {', '.join(TAGS)})")
    fresh = page(package, adr)
    if "--scrivi" in argv:
        if new:
            return 1
        _write_baseline(baseline, missing)
        page_path.write_text(fresh, encoding="utf-8")
        return 0
    for ident in done:
        print(f"ha la fonte, togli dall'elenco: {ident} (python tools/registro.py --scrivi)")
    if first_run:
        print(f"{baseline.name} non c'e': python tools/registro.py --scrivi")
    current = page_path.read_text(encoding="utf-8") if page_path.exists() else ""
    stale = current.replace("\r\n", "\n") != fresh
    if stale:
        print("docs/registro.md e' vecchio: python tools/registro.py --scrivi")
    return 1 if new or done or stale or first_run else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
