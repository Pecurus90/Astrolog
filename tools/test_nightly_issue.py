"""Una Nightly rossa non la vede nessuno (GitHub avvisa solo chi ha scritto il cron): diventa
un'Issue `nightly-rosso`, commentata a ogni notte rossa e chiusa dalla prima verde (ADR 0040)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nightly_issue


def test_a_red_night_without_an_issue_opens_one():
    assert nightly_issue.action("failure", open_issue=None) == "open"


def test_a_red_night_with_an_issue_comments_on_it():
    assert nightly_issue.action("failure", open_issue=42) == "comment"


def test_a_cancelled_or_timed_out_night_is_red_too():
    assert nightly_issue.action("cancelled", open_issue=None) == "open"


def test_a_green_night_closes_the_issue():
    assert nightly_issue.action("success", open_issue=42) == "close"


def test_a_green_night_without_an_issue_does_nothing():
    assert nightly_issue.action("success", open_issue=None) == "none"
