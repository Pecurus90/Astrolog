"""Mutant-name patterns for one nightly mutation shard: the whole backend in one job overruns the
runner's limit. The last shard is computed, so a new module is never left out of the mutation."""

import fnmatch
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

PACKAGE = Path(__file__).resolve().parent.parent / "backend" / "astrolog"
# Score per shard of a complete night; the night fails only below it.
REFERENCE = Path(__file__).resolve().parent / "mutation_reference.json"
FRONTEND = "frontend"
FRONTEND_DIR = PACKAGE.parent.parent / "frontend"
# ~13 mutants a minute on the runner: 10 parts end well under the 160-minute stop.
FRONTEND_SHARDS = 10
DICTIONARY = re.compile(r"[a-z]{2}(-[a-z]+)?\.ts")  # i18n/it-meteo.ts; not index.ts, the logic

# Statuses of mutmut 3 and of the Stryker JSON report; any other one was not run.
DETECTED = {"killed", "timeout", "segfault", "caught by type check", "Killed", "Timeout"}
MISSED = {"survived", "no tests", "suspicious", "Survived", "NoCoverage"}

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
    statuses: Counter[str] = field(default_factory=Counter)


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
            report.statuses[status] += 1
        if not mutant or status != "killed":
            report.lines.append(line.rstrip("\n"))
    return report


def filter_results(
    shard: str, table: dict[str, list[str]], stdin: TextIO
) -> tuple[int, Counter[str]]:
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
    return (1 if failed else 0), report.statuses


def frontend_shards(frontend: Path = FRONTEND_DIR) -> list[list[str]]:
    """Sources by path, cut in runs of near equal size; translation tables left out: text, a
    mutant per string no test kills. Refuses an empty part: Stryker would run nothing."""
    files = sorted(
        p.relative_to(frontend).as_posix()
        for p in (frontend / "src").rglob("*")
        if p.suffix in (".ts", ".tsx")
        and not p.name.endswith(".d.ts")
        and not (p.parent.name == "i18n" and DICTIONARY.fullmatch(p.name))
    )
    sizes = [(frontend / f).stat().st_size for f in files]
    table: list[list[str]] = [[] for _ in range(FRONTEND_SHARDS)]
    done = 0
    for name, size in zip(files, sizes, strict=True):
        part = min(done * FRONTEND_SHARDS // sum(sizes), FRONTEND_SHARDS - 1)
        table[part].append(name)
        done += size
    if not all(table):
        raise ValueError("a frontend part holds no file")
    return table


def stryker_statuses(paths: list[str]) -> Counter[str]:
    """Statuses of every mutant in Stryker JSON reports (mutation-testing-report-schema)."""
    statuses: Counter[str] = Counter()
    for path in paths:
        files = json.loads(Path(path).read_text(encoding="utf-8"))["files"].values()
        statuses.update(m["status"] for f in files for m in f["mutants"])
    return statuses


def frontend(argv: list[str], reference: Path) -> int:
    """`frontend <part>` prints its files for `--mutate`; `frontend --filter <report>...` scores
    every part together, so a file moving between parts never moves the score."""
    if argv[:1] == [FILTER]:
        paths = argv[1:]
        if len(paths) != FRONTEND_SHARDS:
            sys.stderr.write(f"shard {FRONTEND}: {len(paths)} of {FRONTEND_SHARDS} shard reports\n")
            return 1
        statuses = stryker_statuses(paths)
        if not statuses.total():
            sys.stderr.write(f"shard {FRONTEND}: the reports hold no mutant\n")
            return 1
        return 1 if below_reference(FRONTEND, statuses, reference) else 0
    parts = [str(k) for k in range(FRONTEND_SHARDS)]
    if len(argv) != 1 or argv[0] not in parts:
        sys.stderr.write(f"usage: mutation_shards.py {FRONTEND} {{0..{FRONTEND_SHARDS - 1}}}\n")
        return 2
    sys.stdout.write(",".join(frontend_shards()[int(argv[0])]) + "\n")
    return 0


def below_reference(shard: str, statuses: Counter[str], reference: Path) -> bool:
    """Fails only a score under the saved one: a night cut short counts what it ran."""
    detected = sum(n for s, n in statuses.items() if s in DETECTED)
    checked = detected + sum(n for s, n in statuses.items() if s in MISSED)
    score = detected / checked if checked else 0.0
    not_run = statuses.total() - checked
    sys.stderr.write(
        f"shard {shard}: score {score:.4f} ({detected} of {checked} detected, {not_run} not run)\n"
    )
    saved = json.loads(reference.read_text(encoding="utf-8")).get(shard)
    if saved is None:
        sys.stderr.write(f"shard {shard}: no reference yet\n")
        return False
    if round(score, 4) > saved:
        sys.stderr.write(f"shard {shard}: raise the reference to {score:.4f}\n")
    return round(score, 4) < saved


def main(argv: list[str], stdin: TextIO = sys.stdin, reference: Path = REFERENCE) -> int:
    if argv[1:2] == [FRONTEND]:
        return frontend(argv[2:], reference)
    names = [*FIXED, REST]
    if len(argv) not in (2, 3) or argv[1] not in names or argv[2:] not in ([], [FILTER]):
        sys.stderr.write(f"usage: mutation_shards.py {{{','.join(names)}}} [{FILTER}]\n")
        return 2
    table = shards()
    if argv[2:]:
        code, statuses = filter_results(argv[1], table, stdin)
        return 1 if below_reference(argv[1], statuses, reference) else code
    sys.stdout.write(" ".join(table[argv[1]]) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
