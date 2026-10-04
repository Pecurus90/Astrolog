"""What counts as a prose-only change: the Workflow skips the running audits on it."""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import solo_prosa  # noqa: E402


def test_a_comment_or_a_docstring_is_prose():
    old = 'def f(x):\n    """Old words."""\n    # why\n    return x + 1\n'
    new = 'def f(x):\n    """New words, longer."""\n    # another why\n    return x + 1\n'
    assert solo_prosa.same_code(old, new)


def test_a_changed_expression_is_code():
    old = "def f(x):\n    return x + 1\n"
    new = "def f(x):\n    return x + 2\n"
    assert not solo_prosa.same_code(old, new)


def test_an_annotation_is_code():
    # Pyright reads annotations, and a wrong one can hide a None: not prose.
    assert not solo_prosa.same_code("def f(x):\n    return x\n", "def f(x: int):\n    return x\n")


def test_a_string_that_is_not_a_docstring_is_code():
    old = 'def f():\n    x = "a"\n    return x\n'
    new = 'def f():\n    x = "b"\n    return x\n'
    assert not solo_prosa.same_code(old, new)


def test_a_new_or_removed_python_file_is_code():
    assert not solo_prosa.same_code(None, "x = 1\n")
    assert not solo_prosa.same_code("x = 1\n", None)


def test_a_file_that_does_not_parse_is_code():
    assert not solo_prosa.same_code("x = 1\n", "x = (\n")


@pytest.mark.parametrize(
    ("path", "prose"),
    [
        ("docs/coda.md", True),
        ("CLAUDE.md", True),
        ("frontend/src/api/schema.d.ts", False),
        ("ruff.toml", False),
        ("backend/astrolog/schema.sql", False),
    ],
)
def test_only_markdown_is_prose_among_other_files(path, prose):
    assert solo_prosa.prose_only({path: ("a\n", "b\n")}) is prose


@pytest.mark.parametrize("change", [(None, "note\n"), ("note\n", None)])
def test_a_new_or_removed_markdown_file_is_code(change):
    assert not solo_prosa.prose_only({"docs/nota.md": change})


def test_one_code_change_makes_the_whole_change_code():
    changes = {
        "docs/coda.md": ("a\n", "b\n"),
        "backend/x.py": ("x = 1\n", "x = 2\n"),
    }
    assert not solo_prosa.prose_only(changes)


def test_no_change_is_prose_only():
    assert solo_prosa.prose_only({})


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text('"""Old."""\nx = 1\n', encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    _git(tmp_path, "commit", "-q", "-m", "a")
    return tmp_path


def _prose(repo, base):
    return solo_prosa.prose_only(solo_prosa.changes_since(repo, base))


def test_it_reads_the_change_from_a_git_base(tmp_path):
    repo = _repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "a.py").write_text('"""New."""\nx = 1\n', encoding="utf-8")
    assert _prose(repo, base)
    (repo / "a.py").write_text('"""New."""\nx = 2\n', encoding="utf-8")
    assert not _prose(repo, base)


@pytest.mark.parametrize("text", ["gradi °", "Ángulo", "я"])
def test_a_non_ascii_literal_reads_the_same_from_git_and_from_disk(tmp_path, text):
    repo = _repo(tmp_path)
    (repo / "a.py").write_text(f'"""Old."""\nX = "{text}"\n', encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "b")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "a.py").write_text(f'"""New."""\nX = "{text}"  # note\n', encoding="utf-8")
    assert _prose(repo, base)


@pytest.mark.parametrize("mark", [True, False])
def test_a_file_born_after_the_base_is_code_marked_or_not(tmp_path, mark):
    repo = _repo(tmp_path)
    base = solo_prosa.snapshot(repo)
    (repo / "b.py").write_text("x = 1\n", encoding="utf-8")
    if mark:
        _git(repo, "add", "-N", "b.py")
    assert not _prose(repo, base)


@pytest.mark.parametrize("name", ["a.py", "nota.md"])
def test_a_file_removed_after_the_base_is_code(tmp_path, name):
    repo = _repo(tmp_path)
    (repo / "nota.md").write_text("note\n", encoding="utf-8")
    _git(repo, "add", "nota.md")
    _git(repo, "commit", "-q", "-m", "b")
    base = solo_prosa.snapshot(repo)
    (repo / name).unlink()
    assert not _prose(repo, base)


def test_the_base_holds_a_new_marked_file_and_leaves_the_real_index_alone(tmp_path):
    repo = _repo(tmp_path)
    (repo / "n.py").write_text('"""Old."""\nx = 1\n', encoding="utf-8")
    _git(repo, "add", "-N", "n.py")
    (repo / "a.py").write_text('"""Old."""\nx = 2\n', encoding="utf-8")
    status = _git(repo, "status", "--porcelain")
    base = solo_prosa.snapshot(repo)
    assert _git(repo, "status", "--porcelain") == status
    assert _prose(repo, base)
    (repo / "n.py").write_text('"""New."""\nx = 1\n', encoding="utf-8")
    assert _prose(repo, base)
    assert _git(repo, "diff", "--name-only", base) == "n.py"
    (repo / "n.py").write_text('"""New."""\nx = 3\n', encoding="utf-8")
    assert not _prose(repo, base)


def test_the_command_line_prints_the_base_then_measures_from_it(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    monkeypatch.setattr(solo_prosa, "ROOT", repo)
    assert solo_prosa.main(["solo_prosa.py", "--base"]) == 0
    base = capsys.readouterr().out.strip()
    assert base == solo_prosa.snapshot(repo)
    (repo / "a.py").write_text('"""New."""\nx = 1\n', encoding="utf-8")
    assert solo_prosa.main(["solo_prosa.py", base]) == 0
    assert capsys.readouterr().out.strip() == "prose"
    (repo / "a.py").write_text('"""New."""\nx = 2\n', encoding="utf-8")
    assert solo_prosa.main(["solo_prosa.py", base]) == 0
    assert capsys.readouterr().out.strip() == "code"


def test_the_command_line_without_an_argument_is_a_usage_error():
    assert solo_prosa.main(["solo_prosa.py"]) == 2
