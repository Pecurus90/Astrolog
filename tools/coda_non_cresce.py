"""docs/coda.md never grows in a commit: a defect found is repaired, not parked (Marco).

An idea that goes in pays its lines by removing others. Compares the staged file with HEAD.
"""

import subprocess
import sys

QUEUE = "docs/coda.md"


def lines(text: str) -> int:
    return len(text.splitlines())


def _git_show(ref: str) -> str:
    done = subprocess.run(
        ["git", "show", f"{ref}:{QUEUE}"], capture_output=True, encoding="utf-8", check=False
    )
    return done.stdout if done.returncode == 0 else ""


def main() -> int:
    before, after = lines(_git_show("HEAD")), lines(_git_show(""))
    if after > before:
        print(
            f"{QUEUE}: {before} -> {after} righe. La coda non cresce: un difetto si ripara,"
            " un'idea entra togliendo altrettante righe."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
