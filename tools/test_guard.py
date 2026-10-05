"""The PreToolUse guard: files and commands an agent may not touch on its own."""

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))

import guard  # noqa: E402


def edit(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(ROOT, path)}}


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


@pytest.mark.parametrize(
    "path",
    [
        "old/backend/x.py",
        "backend/uv.lock",
        "frontend/package-lock.json",
        "frontend/src/api/schema.d.ts",
        "backend/tests/__snapshots__/test_x.ambr",
    ],
)
def test_protected_files_are_denied(path):
    assert guard.reason(edit(path), ROOT) is not None


@pytest.mark.parametrize("path", ["backend/astrolog/units.py", "docs/coda.md", "oldies/x.py"])
def test_ordinary_files_pass(path):
    assert guard.reason(edit(path), ROOT) is None


@pytest.mark.parametrize(
    "command",
    [
        "uv lock",
        "uv add httpx",
        "uv remove httpx",
        "uv sync",
        "cd backend && uv sync --upgrade",
        "npm install left-pad",
        "npm i -D vitest",
        "npm --prefix frontend install react",
        "npm uninstall react",
        "npm update",
        "npm install --save-dev vitest",
        "npm rm react",
        "npm up",
        "python -m pytest --snapshot-update",
        # a leading echo does not clear what follows it
        "echo ok && uv add httpx",
        "echo start; npm install left-pad",
    ],
)
def test_dependency_and_snapshot_changes_are_denied(command):
    assert guard.reason(bash(command), ROOT) is not None


@pytest.mark.parametrize(
    "command",
    [
        "uv sync --locked",
        "uv sync --frozen",
        "npm ci",
        # CONTRIBUTING's setup step on Windows and Mac, and the CI's
        "npm install",
        "npm --prefix frontend install",
        "npm install --no-audit --no-fund",
        "npm i && npm test",
        "npm install 2>&1 | tail -5",
        "npm --prefix frontend install 2>&1",
        "npm install > install.log",
        "npm install --prefix frontend",
        "npm --prefix frontend run build",
        "python tools/tipi.py",
        "git status",
        'echo "npm install left-pad"',
    ],
)
def test_ordinary_commands_pass(command):
    assert guard.reason(bash(command), ROOT) is None


def test_the_hook_answers_deny_in_the_shape_claude_code_reads():
    payload = json.dumps(edit("backend/uv.lock"))
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    answer = json.loads(out.stdout)["hookSpecificOutput"]
    assert answer["hookEventName"] == "PreToolUse"
    assert answer["permissionDecision"] == "deny"
    assert "uv.lock" in answer["permissionDecisionReason"]


def test_a_dependency_command_asks_marco_instead_of_refusing():
    payload = json.dumps(bash("uv lock"))
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_the_hook_stays_silent_when_nothing_is_wrong():
    payload = json.dumps(edit("docs/coda.md"))
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout == ""
