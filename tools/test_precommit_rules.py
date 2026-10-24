"""The pygrep rules of .pre-commit-config.yaml, each seen red on what it must block and green on
what it must let through. A rule without a case here fails the suite."""

import os
import re

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# id -> (lines the rule must catch, lines it must let through)
CASES = {
    "foreign-software": (
        ['x = "MaxIm DL"', "# exported by Siril"],
        ["maximum = 1", 'x = "Siril"  # software-ok: the guard list'],
    ),
    "css-glob-comment": (["/* see .as-*/ then */"], ["/* .as-riga */"]),
    "no-monkeypatch-undo": (["    monkeypatch.undo()"], ["    # monkeypatch.undo() would unfence"]),
    "pasted-glyphs": (
        ["s = 'l\u2019altro'"],
        ["s = 'l\u2019altro'  # glifo-ok: wanted", "s = 'ascii'"],
    ),
    "control-characters": (["a\x08b", "a\x00b"], ["a\tb", "plain"]),
    "no-import-from-old": (
        ["from old.backend import x", "import x from '../old/a'", "const a = require('old/a')"],
        ['P = "old/docs/x.md"', "threshold_old = 1"],
    ),
    "ddl-outside-schema": (
        ['SQL = "CREATE TABLE x (a)"', "drop table x"],
        ['SQL = "CREATE TABLE x"  # ddl-ok: guard test', "created_table = 1"],
    ),
}


def _pygrep_hooks():
    with open(os.path.join(ROOT, ".pre-commit-config.yaml"), encoding="utf-8") as h:
        config = yaml.safe_load(h)
    return {
        hook["id"]: hook
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook.get("language") == "pygrep"
    }


def _catches(hook, text):
    # As pre-commit's pygrep: a bytes pattern, line by line or whole file with --multiline.
    data = text.encode()
    if "--multiline" in hook.get("args", []):
        return bool(re.compile(hook["entry"].encode(), re.MULTILINE | re.DOTALL).search(data))
    pattern = re.compile(hook["entry"].encode())
    return any(pattern.search(line) for line in data.splitlines(keepends=True))


def test_every_pygrep_rule_has_cases():
    assert sorted(_pygrep_hooks()) == sorted(CASES)


@pytest.mark.parametrize("hook_id", sorted(CASES))
def test_rule_catches_and_lets_through(hook_id):
    hook = _pygrep_hooks()[hook_id]
    hits, misses = CASES[hook_id]
    assert [t for t in hits if not _catches(hook, t)] == []
    assert [t for t in misses if _catches(hook, t)] == []


def test_every_extension_prettier_checks_is_checked_out_with_lf():
    """Prettier wants LF; Windows CI checks out with CRLF unless `.gitattributes` pins it."""
    with open(os.path.join(ROOT, ".pre-commit-config.yaml"), encoding="utf-8") as h:
        config = yaml.safe_load(h)
    prettier = next(k for r in config["repos"] for k in r["hooks"] if k["id"] == "prettier")
    extensions = re.search(r"\\\.\(([^)]*)\)\$", prettier["files"])
    assert extensions, prettier["files"]
    checked = extensions.group(1).split("|")
    with open(os.path.join(ROOT, ".gitattributes"), encoding="utf-8") as h:
        pinned = {
            parts[0].removeprefix("*.")
            for line in h
            if (parts := line.split()) and "eol=lf" in parts and parts[0].startswith("*.")
        }
    assert sorted(set(checked) - pinned) == []
