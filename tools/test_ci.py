"""La CI decide quando un lavoro e' chiuso (ADR 0040, regole 2 e 3): con la CI di main rossa non si
chiude, salvo una Issue `bloccato` che nomina il run; dopo un push si segue la CI fino all'esito."""

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))

import ci  # noqa: E402

# A curl that fails on the release page with GitHub's 504 and answers from the API (Issue #52).
FAKE_CURL = """#!/bin/sh
out=""; url=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o) out="$2"; shift ;;
    http*) url="$1" ;;
  esac
  shift
done
case "$url" in
  https://api.github.com/*)
    if [ -n "$out" ]; then cp "$FAKE_TGZ" "$out"; else cat "$FAKE_TGZ"; fi ;;
  *) echo "curl: (22) The requested URL returned error: 504" >&2; exit 22 ;;
esac
"""


def _bash() -> str | None:
    found = shutil.which("bash")
    # System32's bash is WSL: another filesystem, our paths would not reach it
    return None if found is None or "system32" in found.lower() else found


def _download_lines() -> str:
    with open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8") as f:
        steps = yaml.safe_load(f)["jobs"]["falle"]["steps"]
    step = next(s for s in steps if s.get("name", "").startswith("Segreti"))
    lines = step["run"].splitlines()
    last = next(i for i, line in enumerate(lines) if "tar " in line)
    return "\n".join(lines[: last + 1])


@pytest.mark.skipif(_bash() is None, reason="needs a POSIX bash")
def test_gitleaks_arrives_even_when_the_release_page_answers_504(tmp_path):
    tgz = io.BytesIO()
    with tarfile.open(fileobj=tgz, mode="w:gz") as archive:
        body = b"#!/bin/sh\n"
        entry = tarfile.TarInfo("gitleaks")
        entry.size = len(body)
        archive.addfile(entry, io.BytesIO(body))
    (tmp_path / "gitleaks.tar.gz").write_bytes(tgz.getvalue())
    shims = tmp_path / "shims"
    shims.mkdir()
    (shims / "curl").write_text(FAKE_CURL, newline="\n")
    (shims / "curl").chmod(0o755)
    work = tmp_path / "work"
    work.mkdir()
    (work / "step.sh").write_text(_download_lines(), newline="\n")
    env = {**os.environ, "FAKE_TGZ": "../gitleaks.tar.gz"}
    # GitHub runs a step as `bash -e`, without pipefail
    script = 'export PATH="$(pwd)/../shims:$PATH"; . ./step.sh'
    bash = _bash()
    assert bash is not None
    done = subprocess.run(
        [bash, "-e", "-c", script], cwd=work, env=env, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    assert (work / "gitleaks").exists()


def _checks_oses(event: str) -> list[str]:
    with open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8") as f:
        expr = yaml.safe_load(f)["jobs"]["checks"]["strategy"]["matrix"]["os"]
    push, other = (s.split("'")[1] for s in expr.split("&&")[1].split("||"))
    return yaml.safe_load(push if event == "push" else other)


def test_a_push_runs_no_mac_and_the_rest_keep_apple_silicon():
    """arm64 macOS runners are short (Issue #50): a push queued 15 min, then cancelled.
    Intel cannot stand in: llvmlite has no x86_64 macOS wheel (ADR 0043)."""
    assert not [os_ for os_ in _checks_oses("push") if os_.startswith("macos")]
    assert "macos-latest" in _checks_oses("pull_request")


def _ci_jobs() -> dict:
    with open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8") as f:
        return yaml.safe_load(f)["jobs"]


def test_the_flaky_rounds_run_at_night_not_at_push():
    """Issue #101: five rounds are 32 of 48 runner-minutes of a push; the Nightly runs them."""
    cond = _ci_jobs()["instabilita"]["if"]
    events = json.loads(cond.split("fromJSON('")[1].split("')")[0])
    assert "push" not in events and "pull_request" not in events
    assert {"schedule", "workflow_dispatch"} <= set(events)


def test_the_frontend_part_runs_exactly_the_hooks_the_backend_part_skips():
    """Issue #101: checks in two parallel parts; a hook in neither would run nowhere."""
    steps = _ci_jobs()["checks"]["steps"]
    skipped = {h for s in steps if "SKIP" in s.get("env", {}) for h in s["env"]["SKIP"].split(",")}
    run = {
        line.split("--hook-stage manual ")[1].strip()
        for s in steps
        if "frontend" in str(s.get("if", ""))
        for line in s.get("run", "").splitlines()
        if "--hook-stage manual " in line
    }
    with open(os.path.join(ROOT, ".pre-commit-config.yaml"), encoding="utf-8") as f:
        config = yaml.safe_load(f)
    manual = {
        h["id"] for r in config["repos"] for h in r["hooks"] if "manual" in h.get("stages", [])
    }
    assert skipped and skipped == run
    assert skipped <= manual


RED = {"databaseId": 123, "status": "completed", "conclusion": "failure", "url": "https://x/123"}


def test_a_red_main_blocks_with_its_link():
    reason = ci.stop_reason([RED], [])
    assert reason is not None
    assert "https://x/123" in reason


def test_green_running_or_unknown_main_does_not_block():
    green = {**RED, "conclusion": "success"}
    running = {**RED, "status": "in_progress", "conclusion": ""}
    assert ci.stop_reason([green], []) is None
    assert ci.stop_reason([running], []) is None
    assert ci.stop_reason([], []) is None


def test_a_blocked_issue_naming_the_run_lets_it_close():
    issue = {"title": "CI rossa", "body": "run 123 aspetta un fix di GitHub"}
    assert ci.stop_reason([RED], [issue]) is None


def test_a_blocked_issue_about_something_else_does_not():
    issue = {"title": "Aspetta un Mac", "body": "file solo online"}
    assert ci.stop_reason([RED], [issue]) is not None


def test_only_a_git_push_starts_the_watch():
    assert ci.is_push("git push -q origin main")
    assert ci.is_push("cd x && git push origin main 2>&1 | grep error")
    assert ci.is_push("git add x\ngit push origin main")
    assert not ci.is_push("git status")
    assert not ci.is_push("echo 'git push later'")


def test_the_run_is_looked_up_by_the_full_sha():
    """GitHub's --commit filter wants the whole sha: a short one finds nothing, ever."""
    asked = []

    def gh(args):
        asked.append(args)
        return '[{"databaseId": 9, "url": "https://x/9"}]'

    full = "5b5432d8" + "0" * 32
    assert ci.find_run(gh, full, sleep=lambda _s: None) == {"databaseId": 9, "url": "https://x/9"}
    assert asked[0][asked[0].index("--commit") + 1] == full


def test_a_run_that_never_appears_is_none():
    assert ci.find_run(lambda _a: "[]", "f" * 40, sleep=lambda _s: None) is None


def test_the_outcome_comes_from_the_run_not_from_the_watch_exit():
    """gh run watch can fail by itself (API limit, HTTP 403): only a run that failed is red."""
    assert ci.outcome("success", "abc1234", "https://x/9") == (0, None)
    for unknown in (None, ""):  # gh silent, or the run not finished yet
        code, message = ci.outcome(unknown, "abc1234", "https://x/9")
        assert code == 0 and "non so" in message
    code, message = ci.outcome("cancelled", "abc1234", "https://x/9")
    assert code == 0 and "cancelled" in message  # not a fault, but not green either
    code, message = ci.outcome("failure", "abc1234", "https://x/9")
    assert code == 2 and "ROSSA" in message


def test_a_failed_watch_says_the_work_is_not_closed():
    message = ci.watch_message("abc1234", "https://x/9", failed=True)
    assert "abc1234" in message and "https://x/9" in message and "non e' chiuso" in message
