"""The costruisci Workflow, run under node with stubbed agents: one review, one verification of the
fixes, one audit, checks; what is still open stops the work instead of looping."""

import json
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, ".claude", "workflows", "costruisci.js")

# The Workflow tool runs the script body as an async function with these globals; replies maps a
# label prefix (or the phase, for calls without a label) to the agent's answer, first match wins.
RUNNER = r"""
const fs = require('fs')
const [scriptPath, scenarioPath] = process.argv.slice(2)
const src = fs.readFileSync(scriptPath, 'utf8').replace(/^export const meta/m, 'const meta')
const scenario = JSON.parse(fs.readFileSync(scenarioPath, 'utf8'))
const calls = []
const agent = async (prompt, opts) => {
  const label = opts.label || opts.phase
  calls.push({ label, prompt })
  for (const [prefix, reply] of Object.entries(scenario.replies)) {
    if (label.startsWith(prefix)) return reply
  }
  throw new Error(`no reply for ${label}`)
}
const AsyncFunction = (async () => {}).constructor
const run = new AsyncFunction('args', 'agent', 'phase', 'log', src)
run(scenario.args, agent, () => {}, () => {}).then((result) => {
  process.stdout.write(JSON.stringify({ result, calls }))
})
"""

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node is not installed")

ARGS = {"task": "t", "plan": "p", "mode": "meccanico", "surface": False}
WORK = {"question": None, "done": ["d"]}
CLEAN = {"ran": "r", "findings": []}
GREEN = {"all_passed": True, "failed": []}
BASE = {
    "Build": WORK,
    "review": CLEAN,
    "audit:": CLEAN,
    "checks": GREEN,
    "fix:": WORK,
    "verify:": CLEAN,
}


def finding(blocking=True, evidence="ran x: wrong", problem="p"):
    return {
        "file": "a.py",
        "line": 1,
        "blocking": blocking,
        "problem": problem,
        "evidence": evidence,
    }


def run(tmp_path, replies, **args):
    runner = tmp_path / "runner.js"
    runner.write_text(RUNNER, encoding="utf-8")
    scenario = tmp_path / "scenario.json"
    scenario.write_text(
        json.dumps({"args": {**ARGS, **args}, "replies": replies}), encoding="utf-8"
    )
    out = subprocess.run([NODE, str(runner), SCRIPT, str(scenario)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def labels(out):
    return [c["label"] for c in out["calls"]]


@needs_node
def test_a_clean_job_is_built_reviewed_once_audited_and_checked(tmp_path):
    out = run(tmp_path, BASE)
    assert out["result"]["status"] == "done"
    assert labels(out) == ["Build", "review", "audit:promesse", "checks"]


@needs_node
def test_a_logica_job_was_built_by_the_session_and_starts_from_the_review(tmp_path):
    out = run(tmp_path, BASE, mode="logica")
    assert labels(out)[0] == "review"


@needs_node
def test_a_finding_without_evidence_or_not_blocking_never_reopens_the_work(tmp_path):
    findings = [finding(evidence=""), finding(blocking=False, problem="wording")]
    out = run(tmp_path, {**BASE, "review": {"findings": findings}})
    assert out["result"]["status"] == "done"
    assert not [x for x in labels(out) if x.startswith(("fix:", "verify:"))]
    assert len(out["result"]["parked"]) == 2


@needs_node
def test_a_blocking_finding_is_fixed_once_and_verified_once(tmp_path):
    out = run(tmp_path, {**BASE, "review": {"findings": [finding()]}})
    assert out["result"]["status"] == "done"
    assert labels(out) == [
        "Build",
        "review",
        "fix:Review",
        "verify:Review",
        "audit:promesse",
        "checks",
    ]


@needs_node
def test_what_the_verification_still_finds_stops_the_work_instead_of_looping(tmp_path):
    replies = {**BASE, "review": {"findings": [finding()]}, "verify:": {"findings": [finding()]}}
    out = run(tmp_path, replies)
    assert out["result"]["status"] == "stopped"
    assert out["result"]["where"] == "Review"
    assert labels(out).count("review") == 1
    assert not [x for x in labels(out) if x.startswith("audit:")]


@needs_node
def test_the_fixer_may_refuse_and_must_not_add_machinery(tmp_path):
    out = run(tmp_path, {**BASE, "review": {"findings": [finding()]}})
    fixer = next(c["prompt"] for c in out["calls"] if c["label"] == "fix:Review")
    assert "Puoi rifiutarne" in fixer
    assert "Niente dipendenze, file o meccanismi nuovi" in fixer


@needs_node
def test_a_question_from_the_fixer_goes_to_marco(tmp_path):
    replies = {**BASE, "review": {"findings": [finding()]}, "fix:": {"question": "A o B?"}}
    out = run(tmp_path, replies)
    assert (out["result"]["status"], out["result"]["question"]) == ("question", "A o B?")


@needs_node
def test_a_surface_adds_the_browser_test(tmp_path):
    out = run(tmp_path, BASE, surface=True)
    assert "audit:collaudo" in labels(out)


@needs_node
def test_an_audit_defect_is_fixed_and_verified_like_a_review_one(tmp_path):
    # first match wins: the specific label goes before BASE's generic "audit:"
    out = run(tmp_path, {"audit:promesse": {"findings": [finding()]}, **BASE})
    assert out["result"]["status"] == "done"
    assert "fix:Audit" in labels(out) and "verify:Audit" in labels(out)


@needs_node
@pytest.mark.parametrize(
    ("second", "status"),
    [(GREEN, "done"), ({"all_passed": False, "failed": ["x"]}, "checks_failing")],
)
def test_red_checks_get_one_fix_then_stop(tmp_path, second, status):
    replies = {"checks:again": second, **BASE, "checks": {"all_passed": False, "failed": ["ruff"]}}
    out = run(tmp_path, replies)
    assert out["result"]["status"] == status
    assert labels(out).count("fix:Checks") == 1


def test_the_workflow_scripts_stay_lf_in_git_and_on_disk():
    folder = os.path.join(ROOT, ".claude", "workflows")
    scripts = [os.path.join(folder, n) for n in os.listdir(folder) if n.endswith(".js")]
    assert scripts
    for path in scripts:
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        attr = subprocess.run(
            ["git", "-C", ROOT, "check-attr", "eol", "--", rel], capture_output=True, text=True
        )
        assert attr.returncode == 0, attr.stderr
        assert attr.stdout.strip().endswith("eol: lf"), attr.stdout
        with open(path, "rb") as h:
            assert b"\r" not in h.read(), rel
