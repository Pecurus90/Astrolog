"""The guard on removed tests: a test that disappears must be declared, with its reason."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guardia_test  # noqa: E402

DIFF_REMOVED = """\
diff --git a/backend/tests/test_x.py b/backend/tests/test_x.py
--- a/backend/tests/test_x.py
+++ b/backend/tests/test_x.py
@@ -10,3 +10,0 @@
-def test_the_rule_holds(tmp_path):
-    assert True
"""

DIFF_MOVED = (
    DIFF_REMOVED
    + """\
diff --git a/backend/tests/test_y.py b/backend/tests/test_y.py
--- a/backend/tests/test_y.py
+++ b/backend/tests/test_y.py
@@ -1,0 +2,2 @@
+def test_the_rule_holds(tmp_path):
+    assert True
"""
)

DIFF_DECLARED = (
    DIFF_REMOVED
    + """\
diff --git a/tools/test_tolti.txt b/tools/test_tolti.txt
--- a/tools/test_tolti.txt
+++ b/tools/test_tolti.txt
@@ -1,0 +2,1 @@
+test_the_rule_holds - replaced by the single equipment question (S1)
"""
)

DIFF_FRONTEND = """\
diff --git a/frontend/tests/notti.test.tsx b/frontend/tests/notti.test.tsx
--- a/frontend/tests/notti.test.tsx
+++ b/frontend/tests/notti.test.tsx
@@ -5,1 +5,0 @@
-  it("mostra le notti", () => {
"""


def test_a_removed_test_is_reported():
    assert guardia_test.undeclared(DIFF_REMOVED) == ["test_the_rule_holds"]


def test_a_test_moved_to_another_file_is_not_removed():
    assert guardia_test.undeclared(DIFF_MOVED) == []


def test_a_removal_declared_with_its_reason_passes():
    assert guardia_test.undeclared(DIFF_DECLARED) == []


def test_a_frontend_test_counts_too():
    assert guardia_test.undeclared(DIFF_FRONTEND) == ["mostra le notti"]


def test_a_deleted_test_file_reports_its_tests():
    diff = DIFF_REMOVED.replace("+++ b/backend/tests/test_x.py", "+++ /dev/null")
    assert guardia_test.undeclared(diff) == ["test_the_rule_holds"]


def test_a_title_with_apostrophes_keeps_its_whole_name():
    diff = """\
diff --git a/frontend/tests/a.test.tsx b/frontend/tests/a.test.tsx
--- a/frontend/tests/a.test.tsx
+++ b/frontend/tests/a.test.tsx
@@ -1,2 +1,1 @@
-  it("l'ordine lo sceglie l'utente", () => {
-  it("l'interruttore non si smonta", () => {
+  it("l'interruttore resta montato", () => {
"""
    assert guardia_test.undeclared(diff) == [
        "l'interruttore non si smonta",
        "l'ordine lo sceglie l'utente",
    ]


def test_lines_outside_test_files_are_ignored():
    diff = DIFF_REMOVED.replace("backend/tests/test_x.py", "backend/astrolog/x.py")
    assert guardia_test.undeclared(diff) == []
