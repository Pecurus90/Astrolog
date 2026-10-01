"""The nightly mutation shards: every mutant of the backend runs in exactly one of them."""

import io
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mutation_shards import FIXED, REST, main, modules, probes, shards  # noqa: E402
from mutation_shards import matches as matched  # noqa: E402


def owners(name, table):
    return [shard for shard, patterns in table.items() if matched(name, patterns)]


def test_every_module_of_the_backend_runs_in_exactly_one_shard():
    table = shards()
    for module in modules():
        for name in probes(module):
            assert len(owners(name, table)) == 1, (name, owners(name, table))


@pytest.mark.parametrize(
    ("name", "shard"),
    [
        # Names as the nightly run printed them.
        ("astrolog.fits.frame_type.x_image_type__mutmut_14", "rest"),
        ("astrolog.log.x\u01c1JsonLines\u01c1format__mutmut_17", "rest"),
        ("astrolog.weather.forecast.x\u01c1Cadence\u01c1__init____mutmut_2", "rest"),
        ("astrolog.spine.scan.x_scan__mutmut_1", "spine-n-z"),
        ("astrolog.spine.gear_usage.x_usage__mutmut_1", "spine-a-m"),
        ("astrolog.api.app.x_health__mutmut_1", "api"),
    ],
)
def test_a_real_mutant_name_lands_in_its_shard(name, shard):
    assert owners(name, shards()) == [shard]


def fake_package(root, *files):
    package = root / "astrolog"
    for file in ("api/app.py", "spine/alpha.py", "spine/zeta.py", *files):
        (package / file).parent.mkdir(parents=True, exist_ok=True)
        (package / file).write_text("")
    return package


def test_a_new_module_falls_in_the_rest_without_touching_the_table(tmp_path):
    package = fake_package(tmp_path, "newpkg/__init__.py", "newpkg/thing.py")
    table = shards(package)
    assert owners("astrolog.newpkg.thing.x_f__mutmut_1", table) == ["rest"]
    assert owners("astrolog.newpkg.x_f__mutmut_1", table) == ["rest"]
    assert owners("astrolog.newpkg.__init__.x_f__mutmut_1", table) == ["rest"]
    assert owners("astrolog.spine.zeta.x_f__mutmut_1", table) == ["spine-n-z"]


@pytest.mark.parametrize(
    ("shard", "file"),
    [("api", "api/app.py"), ("spine-a-m", "spine/alpha.py"), ("spine-n-z", "spine/zeta.py")],
)
def test_a_fixed_shard_left_without_modules_is_refused(tmp_path, shard, file):
    package = fake_package(tmp_path)
    (package / file).unlink()
    with pytest.raises(ValueError, match=f"shard {shard}:"):
        shards(package)


def test_a_rest_shard_left_without_modules_is_refused(tmp_path):
    with pytest.raises(ValueError, match="shard rest:"):
        shards(fake_package(tmp_path))


def test_every_fixed_shard_holds_a_real_module():
    table = shards()
    for shard in ("api", "spine-a-m", "spine-n-z"):
        assert any(owners(n, table) == [shard] for m in modules() for n in probes(m)), shard


@pytest.mark.parametrize("shard", ["api", "rest"])
def test_the_printed_patterns_are_the_shard_word_by_word(capsys, shard):
    assert main(["mutation_shards.py", shard]) == 0
    printed = capsys.readouterr().out.split()
    assert printed == shards()[shard]
    assert printed


def test_an_unknown_shard_or_option_is_refused():
    assert main(["mutation_shards.py", "nope"]) == 2
    assert main(["mutation_shards.py", "api", "--other"]) == 2


def test_the_report_keeps_the_shard_own_unrun_mutants_and_drops_the_others(capsys):
    results = io.StringIO(
        "    astrolog.api.app.x_health__mutmut_1: survived\n"
        "    astrolog.api.app.x_health__mutmut_2: not checked\n"
        "    astrolog.api.app.x_health__mutmut_3: killed\n"
        "a line naming no mutant\n"
        "    astrolog.log.x_f__mutmut_1: not checked\n"
        "    astrolog.log.x_f__mutmut_2: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "    astrolog.api.app.x_health__mutmut_1: survived",
        "    astrolog.api.app.x_health__mutmut_2: not checked",
        "a line naming no mutant",
    ]
    assert "shard api: 3 of 5 mutants are its own" in captured.err


def test_a_line_with_a_colon_that_names_no_mutant_passes_and_is_not_counted(capsys):
    results = io.StringIO(
        "hint: run mutmut show <name>\n    astrolog.api.app.x_health__mutmut_1: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "hint: run mutmut show <name>",
        "    astrolog.api.app.x_health__mutmut_1: survived",
    ]
    assert "shard api: 1 of 1 mutants are its own" in captured.err


def test_a_clean_shard_passes_and_prints_nothing(capsys):
    results = io.StringIO(
        "    astrolog.api.app.x_health__mutmut_1: killed\n"
        "    astrolog.log.x_f__mutmut_1: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "shard api: 1 of 2" in captured.err


def test_the_workflow_runs_every_shard_and_filters_each_report_to_its_own():
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    found = re.findall(r"^\s*shard:\s*\[(.*)\]\s*$", workflow, re.MULTILINE)
    assert len(found) == 1, found
    assert [s.strip() for s in found[0].split(",")] == [*FIXED, REST]
    # The report step keeps only its own shard's mutants, killed ones included in the input.
    assert "mutmut results --all true" in workflow
    assert "mutation_shards.py ${{ matrix.shard }} --filter" in workflow
    # A shard cut short still reports: the report always runs, and the run stops before the job.
    assert "if: always()" in workflow
    job, step = (int(v) for v in re.findall(r"^\s*timeout-minutes:\s*(\d+)", workflow, re.M))
    assert step < job


def test_a_mutant_no_shard_owns_fails_the_rest_report_alone(capsys):
    lines = (
        "    astrolog.log.x_f__mutmut_1: killed\n"
        "    astrolog.api.app.x_health__mutmut_1: killed\n"
        "    astrolog.other.y_f__mutmut_1: not checked\n"
    )
    assert main(["mutation_shards.py", "rest", "--filter"], io.StringIO(lines)) == 1
    captured = capsys.readouterr()
    assert "    astrolog.other.y_f__mutmut_1: not checked" in captured.out.splitlines()
    assert "shard rest: 1 mutants belong to no shard" in captured.err
    assert main(["mutation_shards.py", "api", "--filter"], io.StringIO(lines)) == 0
    assert "belong to no shard" not in capsys.readouterr().err


def test_a_report_where_the_shard_owns_no_mutant_is_refused(capsys):
    # Names that lost the package prefix: none of them reads as the shard's own.
    results = io.StringIO(
        "    log.x_f__mutmut_1: killed\n    api.app.x_health__mutmut_1: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results) == 1
    assert "shard api: 0 of 2" in capsys.readouterr().err
