"""The esegui Workflow script, run under node with stubbed agents: what closes the review, where
hardening goes, and that a relaunch after a question does not build again."""

import json
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, ".claude", "workflows", "esegui.js")

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
  calls.push({ label, phase: opts.phase, prompt, schema: opts.schema })
  for (const [prefix, reply] of Object.entries(scenario.replies)) {
    if (label.startsWith(prefix)) return reply
  }
  throw new Error(`no reply for ${label}`)
}
const parallel = (fns) => Promise.all(fns.map((f) => f()))
const AsyncFunction = (async () => {}).constructor
const run = new AsyncFunction('args', 'agent', 'phase', 'log', 'parallel', src)
run(scenario.args, agent, () => {}, () => {}, parallel).then((result) => {
  process.stdout.write(JSON.stringify({ result, calls }))
})
"""

NODE = shutil.which("node")
# Only the tests that run the script need node; the LF guard reads git and bytes.
needs_node = pytest.mark.skipif(NODE is None, reason="node is not installed")

ARGS = {"task": "t", "plan": "p", "mode": "meccanico", "surface": False}
WORK = {"files": [], "checks": "ok", "question": None, "done": ["d"]}
EMPTY = {"findings": []}
HARDENING = "irrobustimento"
TAIL = {
    "audit:": {"ran": "r", "issues": []},
    "checks": {"all_passed": True, "failed": []},
    "Build": WORK,
    "fix:": WORK,
}


def finding(kind, problem="p", file="a.py", line=1):
    return {"file": file, "line": line, "severity": "low", "kind": kind, "problem": problem}


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


def labels(calls):
    return [c["label"] for c in calls]


@needs_node
def test_only_hardening_closes_the_review_in_one_round_and_is_parked(tmp_path):
    out = run(
        tmp_path,
        {"review:revisore#1": {"findings": [finding("irrobustimento")]}, "review:": EMPTY, **TAIL},
    )
    assert out["result"]["status"] == "done"
    assert out["result"]["review_rounds"] == 1
    assert out["result"]["parked"] == ["a.py:1 p"]
    assert not [x for x in labels(out["calls"]) if x.startswith("fix:")]


@needs_node
def test_a_defect_is_fixed_and_a_hardening_twice_is_parked_once(tmp_path):
    replies = {
        "review:revisore#1": {"findings": [finding("difetto", "bug"), finding("irrobustimento")]},
        "review:pr-review-toolkit:code-reviewer#1": {"findings": [finding("irrobustimento")]},
        "review:": EMPTY,
        **TAIL,
    }
    out = run(tmp_path, replies)
    assert out["result"]["status"] == "done"
    assert out["result"]["review_rounds"] == 2
    assert "fix:Review 1" in labels(out["calls"])
    fixed = next(c["prompt"] for c in out["calls"] if c["label"] == "fix:Review 1")
    assert '"problem": "bug"' in fixed
    assert '"kind": "irrobustimento"' not in fixed
    assert out["result"]["parked"] == ["a.py:1 p"]
    second = [
        c["prompt"]
        for c in out["calls"]
        if c["label"].startswith("review:") and c["label"].endswith("#2")
    ]
    assert len(second) == 5
    for prompt in second:
        assert "Irrobustimenti gia parcheggiati, non riproporli:\na.py:1 p" in prompt
    # Without the definition reviewers would pick `kind` freely, and a round could close on defects.
    first = [
        c["prompt"] for c in out["calls"] if c["label"].startswith("review:") and "#1" in c["label"]
    ]
    assert len(first) == 5
    for prompt in first:
        assert "Nel dubbio fra i due, difetto" in prompt
        assert "un doppione che il diff introduce, e difetto" in prompt
    # The schema makes every reviewer declare the kind; the prompt alone would not enforce it.
    item = next(c["schema"] for c in out["calls"] if c["label"].startswith("review:"))
    item = item["properties"]["findings"]["items"]
    assert "kind" in item["required"]
    assert item["properties"]["kind"]["enum"] == ["difetto", HARDENING]


@needs_node
def test_a_finding_without_kind_is_fixed_not_parked(tmp_path):
    bare = {"file": "a.py", "line": 1, "severity": "low", "problem": "bug"}
    out = run(tmp_path, {"review:revisore#1": {"findings": [bare]}, "review:": EMPTY, **TAIL})
    assert "fix:Review 1" in labels(out["calls"])
    assert out["result"]["parked"] == []


@needs_node
@pytest.mark.parametrize("mode", ["meccanico", "spostamento", "logica"])
def test_a_relaunch_after_a_question_applies_the_answer_and_does_not_build(tmp_path, mode):
    out = run(tmp_path, {"review:": EMPTY, **TAIL}, history=["domanda (Review 1): x?"], mode=mode)
    names = labels(out["calls"])
    assert "Build" not in names
    assert names[0] == "fix:Review ripresa"
    assert names[1].startswith("review:")
    resumed = out["calls"][0]["prompt"]
    assert "domanda (Review 1): x?" in resumed
    assert "mai in `repeated`" in resumed
    assert "In `repeated` metti quelli che ripropongono" not in resumed


@needs_node
def test_a_question_during_the_resume_stops_before_the_review(tmp_path):
    replies = {"fix:Review ripresa": {**WORK, "done": [], "question": "C o D?"}, **TAIL}
    out = run(tmp_path, replies, history=["domanda (Review 1): x?"])
    assert out["result"]["status"] == "question"
    assert out["result"]["where"] == "Review ripresa"
    assert "domanda (Review ripresa): C o D?" in out["result"]["history"]
    assert not [x for x in labels(out["calls"]) if x.startswith("review:")]


@needs_node
def test_a_first_logica_launch_goes_straight_to_review(tmp_path):
    out = run(tmp_path, {"review:": EMPTY, **TAIL}, mode="logica")
    names = labels(out["calls"])
    assert "Build" not in names
    assert not [x for x in names if x.startswith("fix:")]
    assert names[0].startswith("review:")


@needs_node
def test_a_relaunch_keeps_what_was_parked_before_the_question(tmp_path):
    replies = {
        "review:revisore#1": {
            "findings": [finding(HARDENING), finding(HARDENING, "old", "b.py", 2)]
        },
        "review:": EMPTY,
        **TAIL,
    }
    out = run(tmp_path, replies, history=["domanda (Review 1): x?"], parked=["b.py:2 old"])
    assert out["result"]["status"] == "done"
    assert out["result"]["parked"] == ["b.py:2 old", "a.py:1 p"]


@needs_node
def test_a_question_from_a_fix_is_written_in_history(tmp_path):
    replies = {
        "review:revisore#1": {"findings": [finding("difetto"), finding(HARDENING)]},
        "review:": EMPTY,
        **TAIL,
        "fix:": {**WORK, "done": [], "question": "A o B?"},
    }
    out = run(tmp_path, replies)
    assert out["result"]["status"] == "question"
    assert "domanda (Review 1): A o B?" in out["result"]["history"]
    # The command passes parked back on the relaunch, so a question must carry it.
    assert out["result"]["parked"] == ["a.py:1 p"]


@needs_node
def test_a_question_from_build_leaves_history_empty(tmp_path):
    out = run(tmp_path, {**TAIL, "Build": {**WORK, "question": "A o B?"}})
    assert out["result"]["status"] == "question"
    assert out["result"]["history"] == []
    assert labels(out["calls"]) == ["Build"]


@needs_node
def test_an_audit_with_only_hardening_holds_and_parks_it(tmp_path):
    replies = {
        "review:": EMPTY,
        "audit:spreco#1": {"ran": "r", "issues": [finding(HARDENING, "cache")]},
        **TAIL,
    }
    out = run(tmp_path, replies)
    assert out["result"]["status"] == "done"
    assert out["result"]["parked"] == ["a.py:1 cache"]
    assert not [x for x in labels(out["calls"]) if x.startswith("fix:")]
    spreco = next(a for a in out["result"]["audits"] if a["question"].startswith("spreco"))
    assert spreco["holds"] is True


@needs_node
def test_an_audit_defect_is_fixed_and_its_hardening_is_not(tmp_path):
    issues = [finding("difetto", "rotto"), finding(HARDENING, "cache", "b.py", 2)]
    replies = {"review:": EMPTY, "audit:promesse#1": {"ran": "r", "issues": issues}, **TAIL}
    out = run(tmp_path, replies)
    assert out["result"]["status"] == "done"
    fixed = next(c["prompt"] for c in out["calls"] if c["label"] == "fix:Audit 1")
    assert "a.py:1 rotto" in fixed
    assert "cache" not in fixed
    assert out["result"]["parked"] == ["b.py:2 cache"]
    second = next(c["prompt"] for c in out["calls"] if c["label"] == "audit:doppioni#2")
    assert "Irrobustimenti gia parcheggiati, non riproporli:\nb.py:2 cache" in second


@needs_node
def test_an_audit_issue_without_kind_is_fixed(tmp_path):
    bare = {"file": "a.py", "problem": "rotto"}
    replies = {"review:": EMPTY, "audit:promesse#1": {"ran": "r", "issues": [bare]}, **TAIL}
    out = run(tmp_path, replies)
    assert "fix:Audit 1" in labels(out["calls"])
    assert out["result"]["parked"] == []


@needs_node
def test_the_audit_declares_the_kind_of_every_issue(tmp_path):
    out = run(tmp_path, {"review:": EMPTY, **TAIL})
    audits = [c for c in out["calls"] if c["label"].startswith("audit:")]
    assert len(audits) == 4
    for call in audits:
        assert "Nel dubbio fra i due, difetto" in call["prompt"]
        assert call["prompt"].count("file e riga") == 1
        assert "se non hai potuto eseguire o misurare" in call["prompt"]
        item = call["schema"]["properties"]["issues"]["items"]
        assert "kind" in item["required"]
        assert item["properties"]["kind"]["enum"] == ["difetto", HARDENING]


@needs_node
def test_an_audit_defect_on_the_last_cycle_ends_audit_failing(tmp_path):
    replies = {
        "review:": EMPTY,
        "audit:promesse": {"ran": "r", "issues": [finding("difetto", "rotto")]},
        **TAIL,
    }
    out = run(tmp_path, replies)
    assert out["result"]["status"] == "audit_failing"
    promesse = next(a for a in out["result"]["audits"] if a["question"].startswith("promesse"))
    assert promesse["holds"] is False
    # The main session reads the result: each defect appears once, in `issues`.
    assert "defects" not in promesse


def test_the_workflow_scripts_stay_lf_in_git_and_on_disk():
    folder = os.path.join(ROOT, ".claude", "workflows")
    scripts = [os.path.join(folder, n) for n in os.listdir(folder) if n.endswith(".js")]
    assert scripts
    for path in scripts:
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        attr = subprocess.run(
            ["git", "-C", ROOT, "check-attr", "eol", "--", rel],
            capture_output=True,
            text=True,
        )
        assert attr.returncode == 0, attr.stderr
        assert attr.stdout.strip().endswith("eol: lf"), attr.stdout
        with open(path, "rb") as h:
            assert b"\r" not in h.read(), rel
