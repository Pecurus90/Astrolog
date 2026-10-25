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


def powershell(command):
    return {"tool_name": "PowerShell", "tool_input": {"command": command}}


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


@pytest.mark.parametrize("path", ["backend/astrolog/units.py", "docs/piano.md", "oldies/x.py"])
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


@pytest.mark.parametrize("path", ["CLAUDE.md", ".claude/commands/ripara.md", ".claude/hooks/ci.py"])
def test_the_frozen_method_asks_marco_before_an_edit(path):
    """ADR 0040: method frozen until 21/11; an edit to CLAUDE.md or .claude/ is Marco's click."""
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=json.dumps(edit(path)),
        capture_output=True,
        text=True,
        check=True,
    )
    answer = json.loads(out.stdout)["hookSpecificOutput"]
    assert answer["permissionDecision"] == "ask"
    assert "21/11" in answer["permissionDecisionReason"]


def test_the_frozen_method_ignores_case_windows_and_mac_do_too():
    assert guard.reason(edit("claude.md"), ROOT) == guard.FROZEN_WHY
    assert guard.reason(edit(".Claude/hooks/ci.py"), ROOT) == guard.FROZEN_WHY


@pytest.mark.parametrize(
    "call",
    [
        bash("sed -i 's/a/b/' CLAUDE.md"),
        bash("echo x >> CLAUDE.md"),
        bash("echo '{}' > .claude/settings.json"),
        bash("cd backend && rm -f ../.claude/hooks/ci.py"),
        bash("mv x.py .claude/hooks/guard.py"),
        bash("cat notes | tee -a claude.md"),
        bash("git checkout -- .claude/hooks/guard.py"),
        bash(f"cp x {ROOT.replace(os.sep, '/')}/CLAUDE.md"),
        powershell("Set-Content -Path .claude\\settings.json -Value x"),
        powershell("Remove-Item .claude/hooks/ask.py"),
        bash("rm -rf .claude"),
        bash("mv .claude old"),
        bash("git rm -r .claude"),
        powershell("Remove-Item -Recurse .claude"),
        bash("rm -rf ./.Claude"),
        bash(f"git -C {ROOT.replace(os.sep, '/')} checkout -- .claude/hooks/guard.py"),
        bash("git -c x=y restore CLAUDE.md"),
    ],
)
def test_a_command_that_writes_the_method_asks_marco_too(call):
    """ADR 0040: the freeze covers Bash and PowerShell, not only Edit and Write."""
    assert guard.reason(call, ROOT) == guard.FROZEN_WHY


@pytest.mark.parametrize(
    "command",
    [
        "cat CLAUDE.md",
        "python .claude/hooks/ci.py push",
        "git add .claude/hooks/guard.py tools/test_guard.py",
        "git diff -- .claude/ > /tmp/x.diff",
        "cat .claude/settings.json 2>&1 | head",
        'git commit -m "fix: guard; rm nothing in .claude/"',
        "rm -f ~/.claude/projects/x/memory/old.md",
        "grep -rn mv .claude/hooks",
        "rm -f .claude.json.bak",
        "git -C backend add .claude/hooks/guard.py",
    ],
)
def test_a_command_that_only_reads_the_method_passes(command):
    assert guard.reason(bash(command), ROOT) is None


def test_the_hook_stays_silent_when_nothing_is_wrong():
    payload = json.dumps(edit("docs/piano.md"))
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout == ""


@pytest.mark.parametrize(
    "call",
    [
        bash("taskkill /F /IM chrome.exe"),
        bash("cd x; taskkill /im python.exe /f"),
        bash("pkill -f astrolog"),
        bash("killall node"),
        powershell("Stop-Process -Name chrome -Force"),
        powershell("Get-Process chrome | Stop-Process"),
        powershell("taskkill /F /IM chrome.exe"),
    ],
)
def test_closing_programs_by_name_is_refused_it_closes_marcos_too(call):
    """Un audit ha chiuso tutti i Chrome della macchina per spegnere il suo (7/10): si spegne per
    PID solo cio' che si e' acceso."""
    assert guard.reason(call, ROOT) is not None


@pytest.mark.parametrize(
    "call",
    [bash("taskkill /F /PID 4242"), bash("kill 4242"), powershell("Stop-Process -Id 4242")],
)
def test_closing_a_process_by_its_pid_passes(call):
    assert guard.reason(call, ROOT) is None


@pytest.mark.parametrize(
    "call",
    [
        bash("cat >> backend/tests/x.py <<'EOF'\n\ndef f():\n    pass\nEOF"),
        bash("cat > docs/x.md <<EOF\ntesto\nEOF"),
        bash("tee notes.txt <<'EOF'\nriga\nEOF"),
        bash(
            "backend/.venv/Scripts/python.exe - <<'EOF'\nfrom pathlib import Path\n"
            "p = Path('tests/x.py')\np.write_text(p.read_text().replace('a', 'b'))\nEOF"
        ),
        bash("python - <<'EOF'\nopen('x.txt', 'w').write('a')\nEOF"),
        bash("python - <<'EOF'\nfrom pathlib import Path\nopen(Path('x.py'), 'w')\nEOF"),
        bash("cat <<EOF &>x.py\nx = 1\nEOF"),
        powershell("python - <<'EOF'\nimport pathlib; pathlib.Path('x').write_bytes(b'')\nEOF"),
    ],
)
def test_a_heredoc_that_writes_a_file_is_refused(call):
    """Testo nei file solo con Edit/Write (CLAUDE.md): in uno script le barre rovesciate e i
    backtick cambiano. Sbagliato due volte in una sessione: ora lo ferma la guardia."""
    assert guard.reason(call, ROOT) == guard.HEREDOC_WHY


@pytest.mark.parametrize(
    "call",
    [
        bash("git commit -m \"$(cat <<'EOF'\nfix: x\nEOF\n)\""),
        bash("git commit -m \"$(cat <<'EOF'\nfix: refuse .write_text( and open(p, 'w')\nEOF\n)\""),
        bash("python - <<'EOF'\nprint(open('a').read())\nEOF"),
        bash("python - <<'EOF'\nimport sqlite3\nprint(sqlite3.connect('a.db').execute('x'))\nEOF"),
        bash("python - <<'EOF'\nprint(1)\nEOF\n2>&1 | tail -3"),
        bash("pytest -q 2>&1 > /dev/null"),
    ],
)
def test_a_heredoc_that_only_reads_passes(call):
    assert guard.reason(call, ROOT) is None


def test_a_heredoc_write_is_denied_not_asked():
    payload = json.dumps(bash("cat >> x.py <<'EOF'\nx = 1\nEOF"))
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "git stash -q; pytest x; git stash pop -q",
        "git stash && make test && git stash apply",
        "git stash push -m tmp; ls; git stash pop",
        "git -C backend stash; pytest; git -C backend stash pop",
        "git stash\npytest\ngit stash pop",
    ],
)
def test_stash_then_pop_in_one_command_is_denied(command):
    """Con niente da mettere da parte, il pop riprende una stash vecchia: si confronta con un
    worktree o con git show."""
    assert guard.reason(bash(command), ROOT) == guard.STASH_WHY


@pytest.mark.parametrize(
    "command", ["git stash list", "git stash show stash@{0}", "git show HEAD:x"]
)
def test_reading_stashes_passes(command):
    assert guard.reason(bash(command), ROOT) is None


def test_closing_by_name_is_denied_not_asked():
    payload = json.dumps(bash("taskkill /F /IM chrome.exe"))
    out = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".claude", "hooks", "guard.py")],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
