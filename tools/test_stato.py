"""State at start (ADR 0040 rule 2): red shows by itself every session. Fake `gh` answers: no
network, and the test does not depend on today's GitHub."""

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stato

NOW = dt.datetime(2026, 10, 25, 12, 0, tzinfo=dt.UTC)


def _ago(hours):
    return (NOW - dt.timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def _fake(answers):
    def run(args):
        key = next(k for k in answers if k in " ".join(args))
        value = answers[key]
        if isinstance(value, Exception):
            raise value
        return json.dumps(value)

    return run


GREEN = {
    "workflow AstroLog": [{"conclusion": "success", "status": "completed", "createdAt": _ago(1)}],
    "workflow Nightly": [{"conclusion": "success", "status": "completed", "createdAt": _ago(5)}],
    "issue list": [],
    "pr list": [],
    "dependabot": [],
    "code-scanning": [],
}


def test_all_green_says_so():
    righe = stato.github_lines(_fake(GREEN), NOW)
    assert righe[0] == "CI di main: verde"
    assert righe[1] == "Nightly: verde (ultima 5 h fa)"
    assert "Issue aperte: nessuna" in righe
    assert "Avvisi di sicurezza: Dependabot 0, CodeQL 0" in righe
    assert "Proposte di Dependabot aperte: nessuna" in righe


def test_open_dependabot_proposals_are_counted_with_the_oldest_age():
    # patch and minor merge by themselves (ADR 0040): one still open is a major, a defect
    risposte = dict(GREEN)
    risposte["pr list"] = [{"createdAt": _ago(24 * 20)}, {"createdAt": _ago(30)}]
    righe = stato.github_lines(_fake(risposte), NOW)
    assert "Proposte di Dependabot aperte: 2 (la piu' vecchia 20 g)" in righe


def test_proposals_unreadable_say_so():
    risposte = dict(GREEN)
    risposte["pr list"] = OSError("gh failed")
    assert "Proposte di Dependabot aperte: non so" in stato.github_lines(_fake(risposte), NOW)


def test_red_ci_says_since_when():
    risposte = dict(GREEN)
    risposte["workflow AstroLog"] = [
        {"conclusion": "failure", "status": "completed", "createdAt": _ago(2)},
        {"conclusion": "failure", "status": "completed", "createdAt": _ago(10)},
        {"conclusion": "success", "status": "completed", "createdAt": _ago(30)},
    ]
    assert stato.github_lines(_fake(risposte), NOW)[0] == "CI di main: ROSSA da 30 h"


def test_a_running_ci_is_not_called_green():
    risposte = dict(GREEN)
    risposte["workflow AstroLog"] = [
        {"conclusion": "", "status": "in_progress", "createdAt": _ago(0)},
        {"conclusion": "success", "status": "completed", "createdAt": _ago(3)},
    ]
    assert stato.github_lines(_fake(risposte), NOW)[0] == "CI di main: in corso (prima verde)"


def test_a_nightly_that_did_not_run_counts_as_red():
    risposte = dict(GREEN)
    risposte["workflow Nightly"] = [
        {"conclusion": "success", "status": "completed", "createdAt": _ago(50)}
    ]
    assert stato.github_lines(_fake(risposte), NOW)[1] == "Nightly: FERMA, ultima corsa 50 h fa"


def test_a_red_nightly_says_its_last_green():
    risposte = dict(GREEN)
    risposte["workflow Nightly"] = [
        {"conclusion": "failure", "status": "completed", "createdAt": _ago(6)},
        {"conclusion": "success", "status": "completed", "createdAt": _ago(78)},
    ]
    assert stato.github_lines(_fake(risposte), NOW)[1] == "Nightly: ROSSA, ultima verde 78 h fa"


def test_issues_are_counted_by_label_with_the_oldest_age():
    risposte = dict(GREEN)
    risposte["issue list"] = [
        {"labels": [{"name": "difetto"}], "createdAt": _ago(72)},
        {"labels": [{"name": "difetto"}], "createdAt": _ago(5)},
        {"labels": [{"name": "bloccato"}], "createdAt": _ago(24)},
    ]
    righe = stato.github_lines(_fake(risposte), NOW)
    assert (
        "Issue aperte: bloccato 1 (la piu' vecchia 1 g), difetto 2 (la piu' vecchia 3 g)" in righe
    )


def test_security_alerts_are_counted():
    risposte = dict(GREEN)
    risposte["dependabot"] = [{}, {}]
    risposte["code-scanning"] = [{}]
    righe = stato.github_lines(_fake(risposte), NOW)
    assert "Avvisi di sicurezza: Dependabot 2, CodeQL 1" in righe


def test_one_failing_call_does_not_hide_a_red_ci():
    risposte = dict(GREEN)
    risposte["workflow AstroLog"] = [
        {"conclusion": "failure", "status": "completed", "createdAt": _ago(2)}
    ]
    risposte["code-scanning"] = OSError("HTTP 404: no analysis found")
    righe = stato.github_lines(_fake(risposte), NOW)
    assert righe[0] == "CI di main: ROSSA da sempre"
    assert "Avvisi di sicurezza: Dependabot 0, CodeQL non so" in righe


def test_a_ci_that_never_ran_is_not_green():
    risposte = dict(GREEN)
    risposte["workflow AstroLog"] = []
    assert stato.github_lines(_fake(risposte), NOW)[0] == "CI di main: mai corsa"


def test_a_running_nightly_is_not_called_red():
    risposte = dict(GREEN)
    risposte["workflow Nightly"] = [
        {"conclusion": "", "status": "in_progress", "createdAt": _ago(0)},
        {"conclusion": "success", "status": "completed", "createdAt": _ago(25)},
    ]
    assert stato.github_lines(_fake(risposte), NOW)[1] == "Nightly: in corso (prima verde)"


def test_alerts_are_counted_over_every_page():
    assert stato.count_pages("30\n15\n") == 45
    assert stato.count_pages("[{}, {}]") == 2


def test_github_unreachable_is_said_not_hidden():
    risposte = dict(GREEN)
    risposte["workflow AstroLog"] = OSError("rete")
    assert stato.github_lines(_fake(risposte), NOW) == [
        "GitHub non raggiungibile: stato da controllare a mano"
    ]


QUEUE = """# Per Design

Consegna controllata: abc1234

- [da dare] fonte pubblica al posto di ADR 0039
- [da dare] esclusi al posto di saltati
- [data] brief v59, punto 2
- [fatta v63] brief v59, punto 1
"""


def test_what_is_still_to_give_design_is_counted():
    lines = stato.design_lines(QUEUE, "abc1234", dirty=False)
    assert lines == [
        "Per Design: 2 voci da dare, 1 data in attesa della consegna (handoff/per-design.md)",
        "Consegna di Design: nessuna nuova",
    ]


def test_a_delivery_not_yet_checked_is_said():
    """A new commit under handoff/design, or files copied there and not committed."""
    assert stato.design_lines(QUEUE, "def5678", dirty=False)[1] == (
        "Consegna di Design: NUOVA, da controllare voce per voce"
    )
    assert stato.design_lines(QUEUE, "abc1234", dirty=True)[1] == (
        "Consegna di Design: NUOVA, da controllare voce per voce"
    )


def test_an_empty_queue_says_so():
    text = "# Per Design\n\nConsegna controllata: abc1234\n\n- [fatta v63] x\n"
    assert stato.design_lines(text, "abc1234", dirty=False)[0] == "Per Design: niente da dare"


def test_the_report_ends_with_the_rule():
    testo = stato.report(_fake(GREEN), NOW)
    assert testo.splitlines()[-1] == "Se qualcosa qui e' rosso, il lavoro di oggi e' quello."
    assert "Prossimo:" in testo
