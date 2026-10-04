"""Whether a fix touched only prose (Python comments and docstrings, edited Markdown), so the
Workflow can skip the running audits; the checks still cover the OpenAPI text a route docstring
feeds."""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# old and new text of one file; None where the file does not exist on that side
type Change = tuple[str | None, str | None]


def _without_docstrings(tree: ast.Module) -> ast.Module:
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            first = body[0] if body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
    return tree


def same_code(old: str | None, new: str | None) -> bool:
    """Comments are not in the tree, docstrings are dropped: what is left is the code that runs."""
    if old is None or new is None:
        return False
    try:
        trees = [_without_docstrings(ast.parse(text)) for text in (old, new)]
    except SyntaxError:
        return False
    return ast.dump(trees[0]) == ast.dump(trees[1])


def prose_only(changes: dict[str, Change]) -> bool:
    for path, (old, new) in changes.items():
        # A file born or removed is code even in Markdown: other files may point to it.
        if old is None or new is None:
            return False
        if path.endswith(".md"):
            continue
        if not (path.endswith(".py") and same_code(old, new)):
            return False
    return True


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", check=True, env=env
    ).stdout


def snapshot(repo: Path) -> str:
    """The tracked files as on disk, as a tree; a scratch index, since `git stash create` exits
    with an error on the `git add -N` entries every new file carries."""
    index = Path(_git(repo, "rev-parse", "--git-path", "index").strip())
    if not index.is_absolute():
        index = repo / index
    with tempfile.TemporaryDirectory() as folder:
        scratch = Path(folder) / "index"
        if index.exists():
            shutil.copyfile(index, scratch)
        env = {**os.environ, "GIT_INDEX_FILE": str(scratch)}
        _git(repo, "add", "-u", env=env)
        return _git(repo, "write-tree", env=env).strip()


def changes_since(repo: Path, base: str) -> dict[str, Change]:
    """The working tree against `base`; a file not in `base` (untracked, or marked with
    `git add -N` after it) counts as new."""
    changes: dict[str, Change] = {}
    for path in _git(repo, "diff", "--name-only", base).splitlines():
        try:
            old: str | None = _git(repo, "show", f"{base}:{path}")
        except subprocess.CalledProcessError:
            old = None
        on_disk = repo / path
        new = on_disk.read_text(encoding="utf-8") if on_disk.exists() else None
        changes[path] = (old, new)
    for path in _git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
        changes[path] = (None, (repo / path).read_text(encoding="utf-8", errors="replace"))
    return changes


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: solo_prosa.py --base | <base>", file=sys.stderr)
        return 2
    if argv[1] == "--base":
        print(snapshot(ROOT))
    else:
        print("prose" if prose_only(changes_since(ROOT, argv[1])) else "code")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
