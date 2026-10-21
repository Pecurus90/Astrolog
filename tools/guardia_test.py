"""A commit that makes a test disappear must declare it in tools/test_tolti.txt, with a reason.

Reads the staged diff: a test removed here and added elsewhere (moved, renamed in place) is fine.
"""

import re
import subprocess
import sys

DECLARATIONS = "tools/test_tolti.txt"
TEST_FILE = re.compile(r"(^|/)(test_\w+\.py|[\w.-]+\.test\.tsx?)$")
PY_TEST = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)")
# the closing quote is the opening one: Italian titles carry apostrophes
TS_TEST = re.compile(r"""^\s*(?:it|test)(?:\.\w+)?\(\s*(["'`])(.+?)(?<!\\)\1""")
# `it.each([...])("title")`: the title follows the closing of the table
TS_EACH = re.compile(r"""^\s*\]?\)\(\s*(["'`])(.+?)(?<!\\)\1""")
# `it(` alone on its line: the title is the next line
TS_OPEN = re.compile(r"^\s*(?:it|test)(?:\.\w+)?\(\s*$")
TS_TITLE = re.compile(r"""^\s*(["'`])(.+?)(?<!\\)\1""")
DECLARED = re.compile(r"^(\S.*?)\s+-\s+\S")


def _name(line: str, after_open: bool = False) -> str | None:
    match = PY_TEST.match(line)
    if match:
        return match.group(1)
    match = TS_TEST.match(line) or TS_EACH.match(line)
    if match is None and after_open:
        match = TS_TITLE.match(line)
    return match.group(2) if match else None


def undeclared(diff: str) -> list[str]:
    """Names of tests the diff removes for good, minus those declared with a reason."""
    removed: set[str] = set()
    added: set[str] = set()
    declared: set[str] = set()
    current = old = ""
    opened = ""  # the sign of a line holding `it(` alone, whose title is the next line
    for line in diff.splitlines():
        if line.startswith("--- "):
            old = line[6:] if line.startswith("--- a/") else ""
            continue
        if line.startswith("+++ "):
            # a deleted file has no new side: its tests are read under the old path
            current = line[6:] if line.startswith("+++ b/") else old
            continue
        if line.startswith(("diff ", "@@")):
            opened = ""
            continue
        body = line[1:]
        if current == DECLARATIONS and line.startswith("+"):
            found = DECLARED.match(body)
            if found:
                declared.add(found.group(1).strip())
        elif TEST_FILE.search(current):
            name = _name(body, after_open=opened == line[:1])
            opened = line[:1] if TS_OPEN.match(body) else ""
            if name and line.startswith("-"):
                removed.add(name)
            elif name and line.startswith("+"):
                added.add(name)
    return sorted(removed - added - declared)


def main() -> int:
    diff = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--no-color"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout
    missing = undeclared(diff)
    for name in missing:
        sys.stderr.write(f"removed test not declared in {DECLARATIONS}: {name}\n")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
