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
DECLARED = re.compile(r"^(\S.*?)\s+-\s+\S")


def _name(line: str) -> str | None:
    match = PY_TEST.match(line)
    if match:
        return match.group(1)
    match = TS_TEST.match(line)
    return match.group(2) if match else None


def undeclared(diff: str) -> list[str]:
    """Names of tests the diff removes for good, minus those declared with a reason."""
    removed: set[str] = set()
    added: set[str] = set()
    declared: set[str] = set()
    current = old = ""
    for line in diff.splitlines():
        if line.startswith("--- "):
            old = line[6:] if line.startswith("--- a/") else ""
            continue
        if line.startswith("+++ "):
            # a deleted file has no new side: its tests are read under the old path
            current = line[6:] if line.startswith("+++ b/") else old
            continue
        if line.startswith(("diff ", "@@")):
            continue
        body = line[1:]
        if current == DECLARATIONS and line.startswith("+"):
            found = DECLARED.match(body)
            if found:
                declared.add(found.group(1).strip())
        elif TEST_FILE.search(current):
            name = _name(body)
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
