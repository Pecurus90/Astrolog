"""Every working document has a line ceiling (ADR 0027); one already over it can only shrink.

The queue is gone; ceiling zero keeps it from coming back: a defect is repaired, not parked (Marco).
Compares each staged file with HEAD.
"""

import fnmatch
import subprocess
import sys

CEILINGS = {
    "docs/coda.md": 0,
    "docs/piano.md": 80,
    "docs/idee.md": 60,
    "docs/adr/*.md": 100,
    "docs/domini/*.md": 400,
    "CLAUDE.md": 200,
}
# Lists born full that only shrink: the pre-porting files waiting outside Prettier, where a ported
# page leaves and none comes in. No ceiling: the list is as long as it is born.
NEVER_GROW = ("frontend/.prettierignore",)


def ceiling_of(path: str) -> int | None:
    for pattern, ceiling in CEILINGS.items():
        if fnmatch.fnmatch(path, pattern):
            return ceiling
    return None


def lines(text: str) -> int:
    return len(text.splitlines())


def _git_show(ref: str, path: str) -> str:
    done = subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, encoding="utf-8", check=False
    )
    return done.stdout if done.returncode == 0 else ""


def main(paths: list[str]) -> int:
    failed = 0
    for path in paths:
        normal = path.replace("\\", "/")
        ceiling = ceiling_of(normal)
        if ceiling is None and normal not in NEVER_GROW:
            continue
        before, after = lines(_git_show("HEAD", path)), lines(_git_show("", path))
        if normal in NEVER_GROW:
            if before and after > before:
                print(f"{path}: {before} -> {after} righe. Questo elenco solo si accorcia.")
                failed = 1
            continue
        if ceiling is not None and after > ceiling and after > before:
            print(
                f"{path}: {before} -> {after} righe, tetto {ceiling}. Sopra il tetto si scende"
                " soltanto: si toglie altrettanto, o il dettaglio va nella sua casa."
            )
            failed = 1
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
