"""La CI decide quando un lavoro e' chiuso (ADR 0040, regole 2 e 3): con la CI di main rossa non si
chiude, salvo una Issue `bloccato` che nomina il run; dopo un push si segue la CI fino all'esito."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))

import ci  # noqa: E402

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


def test_a_failed_watch_says_the_work_is_not_closed():
    message = ci.watch_message("abc1234", "https://x/9", failed=True)
    assert "abc1234" in message and "https://x/9" in message and "non e' chiuso" in message
