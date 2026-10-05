"""The comment rule of CLAUDE.md, checked by a machine: at most two lines, no dates, no names.

Route docstrings and model docstrings are exempt: they are the OpenAPI contract.
Usage: python tools/commenti.py [files...]   no files means the whole backend package.
"""

import ast
import io
import os
import re
import sys
import tokenize

MAX_LINES = 2
DIRECTIVE = re.compile(r"#\s*(noqa|type:|pyright:|fmt:|jscpd:|segnaposto-ok|software-ok)")
HISTORY = re.compile(r"\b(19|20)\d\d-\d\d-\d\d\b|\b\d{1,2}/\d{1,2}/(19|20)\d\d\b|\bMarco\b")
ROUTE_VERBS = {"get", "post", "put", "patch", "delete"}
CONTRACT_BASES = {"BaseModel", "Page"}

type Problem = tuple[int, str]


def _comment_problems(source: str) -> list[Problem]:
    found: list[Problem] = []
    block: list[int] = []
    previous_line = 0
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    full_line = {
        t.start[0]
        for t in tokens
        if t.type == tokenize.COMMENT and not t.line[: t.start[1]].strip()
    }
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        if HISTORY.search(token.string):
            found.append((line, "a date or a name in a comment: history belongs to git"))
        if line not in full_line or DIRECTIVE.match(token.string):
            continue
        if block and line == previous_line + 1:
            block.append(line)
        else:
            block = [line]
        previous_line = line
        if len(block) == MAX_LINES + 1:
            found.append((block[0], f"a comment block longer than {MAX_LINES} lines"))
    return found


def _is_route(node: ast.AST) -> bool:
    decorators = getattr(node, "decorator_list", [])
    for decorator in decorators:
        call = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(call, ast.Attribute) and call.attr in ROUTE_VERBS:
            return True
    return False


def _is_contract_model(node: ast.AST) -> bool:
    if not isinstance(node, ast.ClassDef):
        return False
    names = {b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in node.bases}
    names |= {getattr(b.value, "id", "") for b in node.bases if isinstance(b, ast.Subscript)}
    return bool(names & CONTRACT_BASES)


def _models_file(path: str) -> bool:
    # every class there is a pydantic model, subclasses of another model included
    return re.search(r"(^|/)api/models\w*\.py$", path) is not None


def _docstring_problems(tree: ast.Module, path: str) -> list[Problem]:
    found: list[Problem] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body = node.body
        first = body[0] if body else None
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            continue
        text = first.value.value
        line = first.lineno
        if HISTORY.search(text):
            found.append((line, "a date or a name in a docstring: history belongs to git"))
        if _is_route(node) or _is_contract_model(node):
            continue
        if isinstance(node, ast.ClassDef) and _models_file(path):
            continue
        if len(text.strip().splitlines()) > MAX_LINES:
            found.append((line, f"a docstring longer than {MAX_LINES} lines"))
    return found


def problems(source: str, path: str) -> list[Problem]:
    """Every breach of the rule in one file, sorted by line."""
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []
    return sorted(_comment_problems(source) + _docstring_problems(tree, path))


def check_tree(folder: str, root: str) -> list[str]:
    report: list[str] = []
    for current, _, files in os.walk(folder):
        for name in sorted(files):
            if name.endswith(".py"):
                report += check_file(os.path.join(current, name), root)
    return report


def check_file(path: str, root: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    rel = os.path.relpath(path, root).replace("\\", "/")
    return [f"{rel}:{line}: {why}" for line, why in problems(source, rel)]


def main(argv: list[str]) -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if argv:
        report = [line for path in argv for line in check_file(path, root)]
    else:
        report = check_tree(os.path.join(root, "backend", "astrolog"), root)
    for line in report:
        sys.stderr.write(line + "\n")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
