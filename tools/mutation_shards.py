"""Mutant-name patterns for one nightly mutation shard: the whole backend in one job overruns the
runner's limit. The last shard is computed, so a new module is never left out of the mutation."""

import fnmatch
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

PACKAGE = Path(__file__).resolve().parent.parent / "backend" / "astrolog"

# Split by package; anything these miss falls into the computed rest shard.
FIXED = {
    "api": ["astrolog.api.*"],
    "spine-a-m": ["astrolog.spine.[_a-m]*"],
    "spine-n-z": ["astrolog.spine.[n-z]*"],
}
REST = "rest"
FILTER = "--filter"
MUTANT = re.compile(r"\S+__mutmut_\d+")


def modules(package: Path = PACKAGE) -> list[str]:
    """Dotted names as mutmut writes them; a package's `__init__` both ways, since mutmut drops
    it from some names and not others."""
    names = []
    for path in sorted(package.rglob("*.py")):
        parts = path.relative_to(package.parent).with_suffix("").parts
        names.append(".".join(parts))
        if parts[-1] == "__init__":
            names.append(".".join(parts[:-1]))
    return names


def probes(module: str) -> list[str]:
    """One mutant name per kind mutmut makes in `module`: a function and a method."""
    return [f"{module}.x_f__mutmut_1", f"{module}.x\u01c1C\u01c1m__mutmut_1"]


def matches(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def shards(package: Path = PACKAGE) -> dict[str, list[str]]:
    """Refuses a fixed pattern that matches no module: mutmut would run nothing and stay green."""
    names = [name for m in modules(package) for name in probes(m)]
    for shard, patterns in FIXED.items():
        for pattern in patterns:
            if not any(fnmatch.fnmatchcase(name, pattern) for name in names):
                raise ValueError(f"shard {shard}: pattern {pattern} matches no module")
    fixed = [p for patterns in FIXED.values() for p in patterns]
    rest = [
        f"{m}.x*" for m in modules(package) if not all(matches(name, fixed) for name in probes(m))
    ]
    if not rest:
        raise ValueError(f"shard {REST}: no patterns, the job would run nothing")
    return {**FIXED, REST: rest}


@dataclass
class Report:
    lines: list[str]
    owned: int
    total: int
    orphans: list[str]


def own_results(lines: TextIO, shard: str, table: dict[str, list[str]]) -> Report:
    """Reads `mutmut results --all true`: keeps this shard's mutants not killed, unrun ones
    included, so a shard cut short shows what it never tried; a line naming no mutant passes."""
    report = Report([], 0, 0, [])
    for line in lines:
        name, _, status = line.strip().partition(": ")
        mutant = MUTANT.fullmatch(name) is not None
        if mutant:
            report.total += 1
            if not any(matches(name, patterns) for patterns in table.values()):
                report.orphans.append(line.rstrip("\n"))
            if not matches(name, table[shard]):
                continue
            report.owned += 1
        if not mutant or status != "killed":
            report.lines.append(line.rstrip("\n"))
    return report


def filter_results(shard: str, table: dict[str, list[str]], stdin: TextIO) -> int:
    """Refuses a report where the shard owns no mutant (mutmut's names no longer match the
    patterns) and, in the rest shard alone, one with mutants no shard ever runs."""
    report = own_results(stdin, shard, table)
    sys.stdout.writelines(f"{line}\n" for line in report.lines)
    sys.stderr.write(f"shard {shard}: {report.owned} of {report.total} mutants are its own\n")
    failed = not report.owned
    if shard == REST and report.orphans:
        sys.stdout.writelines(f"{line}\n" for line in report.orphans)
        sys.stderr.write(f"shard {shard}: {len(report.orphans)} mutants belong to no shard\n")
        failed = True
    return 1 if failed else 0


def main(argv: list[str], stdin: TextIO = sys.stdin) -> int:
    names = [*FIXED, REST]
    if len(argv) not in (2, 3) or argv[1] not in names or argv[2:] not in ([], [FILTER]):
        sys.stderr.write(f"usage: mutation_shards.py {{{','.join(names)}}} [{FILTER}]\n")
        return 2
    table = shards()
    if argv[2:]:
        return filter_results(argv[1], table, stdin)
    sys.stdout.write(" ".join(table[argv[1]]) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
