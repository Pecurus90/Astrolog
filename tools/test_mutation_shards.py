"""The nightly mutation shards: every mutant of the backend runs in exactly one of them."""

import io
import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mutation_shards import (
    FIXED,
    FRONTEND,
    FRONTEND_DIR,
    FRONTEND_SHARDS,
    REFERENCE,
    REST_PARTS,
    REST_SHARDS,
    files,
    frontend_shards,
    main,
    modules,
    probes,
    reopen,
    shards,
)
from mutation_shards import matches as matched


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
        ("astrolog.fits.frame_type.x_image_type__mutmut_14", "rest-"),
        ("astrolog.log.x\u01c1JsonLines\u01c1format__mutmut_17", "rest-"),
        ("astrolog.weather.forecast.x\u01c1Cadence\u01c1__init____mutmut_2", "rest-"),
        ("astrolog.spine.scan.x_scan__mutmut_1", "spine-n-z"),
        ("astrolog.spine.gear_usage.x_usage__mutmut_1", "spine-g-m"),
        ("astrolog.spine.copies.x_decide__mutmut_14", "spine-a-f"),
        ("astrolog.spine.mosaic.x_place__mutmut_29", "spine-g-m"),
        ("astrolog.api.app.x_health__mutmut_1", "api"),
    ],
)
def test_a_real_mutant_name_lands_in_its_shard(name, shard):
    found = owners(name, shards())
    assert len(found) == 1
    assert found[0] in REST_SHARDS if shard == "rest-" else found[0] == shard


def test_the_rest_is_cut_in_parts_of_near_equal_size_so_none_overruns():
    """rest, Nightly 44107096567: 9695 of 20763 mutants not run, ~7 a minute in its pipeline tail
    (#87); cut by size like the frontend, a growing package spreads over the parts."""
    table = shards()
    package = Path(__file__).resolve().parent.parent / "backend"
    sizes = [sum((package / f).stat().st_size for f in files(s, table)) for s in REST_SHARDS]
    assert len(sizes) == REST_PARTS >= 6
    assert max(sizes) < 2 * sum(sizes) / len(sizes)


def fake_package(root, *files):
    package = root / "astrolog"
    for file in ("api/app.py", "spine/alpha.py", "spine/mid.py", "spine/zeta.py", *files):
        (package / file).parent.mkdir(parents=True, exist_ok=True)
        (package / file).write_text("")
    return package


def test_a_new_module_falls_in_the_rest_without_touching_the_table(tmp_path):
    package = fake_package(tmp_path, "newpkg/__init__.py", "newpkg/thing.py")
    table = shards(package, parts=1)
    assert owners("astrolog.newpkg.thing.x_f__mutmut_1", table) == ["rest-0"]
    assert owners("astrolog.newpkg.x_f__mutmut_1", table) == ["rest-0"]
    assert owners("astrolog.newpkg.__init__.x_f__mutmut_1", table) == ["rest-0"]
    assert owners("astrolog.spine.zeta.x_f__mutmut_1", table) == ["spine-n-z"]


@pytest.mark.parametrize(
    ("shard", "file"),
    [
        ("api", "api/app.py"),
        ("spine-a-f", "spine/alpha.py"),
        ("spine-g-m", "spine/mid.py"),
        ("spine-n-z", "spine/zeta.py"),
    ],
)
def test_a_fixed_shard_left_without_modules_is_refused(tmp_path, shard, file):
    package = fake_package(tmp_path)
    (package / file).unlink()
    with pytest.raises(ValueError, match=f"shard {shard}:"):
        shards(package)


def test_a_rest_shard_left_without_modules_is_refused(tmp_path):
    with pytest.raises(ValueError, match="shard rest-0:"):
        shards(fake_package(tmp_path))


def test_a_rest_part_left_without_files_is_refused(tmp_path):
    with pytest.raises(ValueError, match="shard rest-1:"):
        shards(fake_package(tmp_path, "newpkg/thing.py"), parts=2)


def test_every_fixed_shard_holds_a_real_module():
    table = shards()
    for shard in ("api", "spine-a-f", "spine-g-m", "spine-n-z"):
        assert any(owners(n, table) == [shard] for m in modules() for n in probes(m)), shard


@pytest.mark.parametrize("shard", ["api", "rest-0", "rest-5"])
def test_the_printed_patterns_are_the_shard_word_by_word(capsys, shard):
    assert main(["mutation_shards.py", shard]) == 0
    printed = capsys.readouterr().out.split()
    assert printed == shards()[shard]
    assert printed


def test_an_unknown_shard_or_option_is_refused():
    assert main(["mutation_shards.py", "nope"]) == 2
    assert main(["mutation_shards.py", "api", "--other"]) == 2


def test_the_report_keeps_the_shard_own_unrun_mutants_and_drops_the_others(tmp_path, capsys):
    results = io.StringIO(
        "    astrolog.api.app.x_health__mutmut_1: survived\n"
        "    astrolog.api.app.x_health__mutmut_2: not checked\n"
        "    astrolog.api.app.x_health__mutmut_3: killed\n"
        "a line naming no mutant\n"
        "    astrolog.log.x_f__mutmut_1: not checked\n"
        "    astrolog.log.x_f__mutmut_2: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results, write_reference(tmp_path)) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "    astrolog.api.app.x_health__mutmut_1: survived",
        "    astrolog.api.app.x_health__mutmut_2: not checked",
        "a line naming no mutant",
    ]
    assert "shard api: 3 of 5 mutants are its own" in captured.err


def test_a_line_with_a_colon_that_names_no_mutant_passes_and_is_not_counted(tmp_path, capsys):
    results = io.StringIO(
        "hint: run mutmut show <name>\n    astrolog.api.app.x_health__mutmut_1: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results, write_reference(tmp_path)) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        "hint: run mutmut show <name>",
        "    astrolog.api.app.x_health__mutmut_1: survived",
    ]
    assert "shard api: 1 of 1 mutants are its own" in captured.err


def test_a_clean_shard_passes_and_prints_nothing(tmp_path, capsys):
    results = io.StringIO(
        "    astrolog.api.app.x_health__mutmut_1: killed\n"
        "    astrolog.log.x_f__mutmut_1: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results, write_reference(tmp_path)) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "shard api: 1 of 2" in captured.err


def test_the_workflow_runs_every_shard_and_filters_each_report_to_its_own():
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    found = re.findall(r"^\s*shard:\s*\[(.*)\]\s*$", workflow, re.MULTILINE)
    assert len(found) == 1, found
    assert [s.strip() for s in found[0].split(",")] == [*FIXED, *REST_SHARDS]
    # A part without its own cache yet starts from the old rest one: its verdicts stand (#87).
    assert re.search(
        r"restore-keys: \|\n\s+mutants-\$\{\{ matrix.shard \}\}-\n\s+mutants-rest-\n", workflow
    )
    # The report step keeps only its own shard's mutants, killed ones included in the input.
    assert "mutmut results --all true" in workflow
    assert "mutation_shards.py ${{ matrix.shard }} --filter" in workflow
    # A shard cut short still reports: the report always runs, and the run stops before the job.
    assert "if: always()" in workflow
    limits = [int(v) for v in re.findall(r"^\s*timeout-minutes:\s*(\d+)", workflow, re.M)]
    assert limits[1] < limits[0] and limits[3] < limits[2]  # mutation, then mutation-frontend
    # Each night resumes the last one, and saves even when cut short.
    assert workflow.count("actions/cache/save@") == 2
    assert workflow.count("actions/cache/restore@") == 2
    # mutmut refreshes the .py of a resumed mutants/, never the data: schema.sql must follow.
    assert "rsync -a --exclude='*.py' astrolog/ mutants/astrolog/" in workflow
    assert "rm -rf mutants/tests" in workflow and 'rm -f "$f" "$f.meta"' in workflow
    # A run stopped mid-write leaves a broken .meta: dropped before the run and before the cache.
    assert workflow.count("mutation_shards.py --drop-broken mutants") == 2


def test_a_meta_left_broken_by_a_stopped_run_is_dropped_with_its_module(tmp_path, capsys):
    # mutmut opens the .meta with "w" before json.dump: stopped in between, it stays empty.
    pkg = tmp_path / "astrolog"
    pkg.mkdir()
    for name, meta in [("good", '{"exit_code_by_key": {}}'), ("empty", ""), ("cut", '{"exit_')]:
        (pkg / f"{name}.py").write_text("x = 1\n", encoding="utf-8")
        (pkg / f"{name}.py.meta").write_text(meta, encoding="utf-8")
    assert main(["mutation_shards.py", "--drop-broken", str(tmp_path)]) == 0
    assert sorted(p.name for p in pkg.iterdir()) == ["good.py", "good.py.meta"]
    assert "2 broken" in capsys.readouterr().err


def test_a_mutant_no_shard_owns_fails_the_rest_report_alone(tmp_path, capsys):
    lines = (
        "    astrolog.log.x_f__mutmut_1: killed\n"
        "    astrolog.api.app.x_health__mutmut_1: killed\n"
        "    astrolog.other.y_f__mutmut_1: not checked\n"
    )
    path = write_reference(tmp_path)
    assert main(["mutation_shards.py", "rest-0", "--filter"], io.StringIO(lines), path) == 1
    captured = capsys.readouterr()
    assert "    astrolog.other.y_f__mutmut_1: not checked" in captured.out.splitlines()
    assert "shard rest-0: 1 mutants belong to no shard" in captured.err
    assert main(["mutation_shards.py", "api", "--filter"], io.StringIO(lines), path) == 0
    assert "belong to no shard" not in capsys.readouterr().err


API_RESULTS = (
    "    astrolog.api.app.x_health__mutmut_1: killed\n"
    "    astrolog.api.app.x_health__mutmut_2: timeout\n"
    "    astrolog.api.app.x_health__mutmut_3: survived\n"
    "    astrolog.api.app.x_health__mutmut_4: no tests\n"
    "    astrolog.api.app.x_health__mutmut_5: not checked\n"
    "    astrolog.api.app.x_health__mutmut_6: skipped\n"
)


def write_reference(tmp_path, **scores):
    path = tmp_path / "reference.json"
    path.write_text(json.dumps(scores), encoding="utf-8")
    return path


@pytest.mark.parametrize(("reference", "code"), [(0.5, 0), (0.4, 0), (0.51, 1)])
def test_the_score_fails_only_below_the_reference(tmp_path, capsys, reference, code):
    # 2 detected of 4 checked: not checked and skipped count neither way
    path = write_reference(tmp_path, api=reference)
    assert main(["mutation_shards.py", "api", "--filter"], io.StringIO(API_RESULTS), path) == code
    assert "shard api: score 0.5000 (2 of 4 detected, 2 not run)" in capsys.readouterr().err


def test_a_shard_without_reference_passes_and_says_so(tmp_path, capsys):
    path = write_reference(tmp_path)
    assert main(["mutation_shards.py", "api", "--filter"], io.StringIO(API_RESULTS), path) == 0
    assert "shard api: no reference yet" in capsys.readouterr().err


def test_a_better_score_asks_for_the_reference_to_rise(tmp_path, capsys):
    path = write_reference(tmp_path, api=0.25)
    assert main(["mutation_shards.py", "api", "--filter"], io.StringIO(API_RESULTS), path) == 0
    assert "raise the reference to 0.5000" in capsys.readouterr().err


def test_every_backend_file_is_mutated_by_exactly_one_shard():
    """Run without names (#87), each shard walks its files alone; spine/__init__ has a name in
    two shards and goes to the first."""
    table = shards()
    every = [f for shard in table for f in files(shard, table)]
    assert len(every) == len(set(every))
    package = Path(__file__).resolve().parent.parent / "backend" / "astrolog"
    assert set(every) == {p.relative_to(package.parent).as_posix() for p in package.rglob("*.py")}
    assert "astrolog/spine/__init__.py" in files("spine-a-f", table)
    assert "astrolog/api/app.py" in files("api", table)
    assert any("astrolog/log.py" in files(s, table) for s in REST_SHARDS)


def test_the_shard_files_go_into_the_mutmut_section_once(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mutmut]\npaths_to_mutate = ["astrolog/"]\n\n[x]\n', encoding="utf-8"
    )
    assert main(["mutation_shards.py", "api", "--only-mutate", str(pyproject)]) == 0
    lines = pyproject.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "[tool.mutmut]" and lines[2] == 'paths_to_mutate = ["astrolog/"]'
    assert json.loads(lines[1].removeprefix("only_mutate = ")) == files("api", shards())
    assert main(["mutation_shards.py", "api", "--only-mutate", str(pyproject)]) == 1


def test_a_looping_mutant_is_cut_within_two_minutes():
    """rest, Nightly 44060474083: 70 of 77 mutants timed out, ~6 min each at mutmut's 15x (#87).
    mutmut 3.8.1 wall limit: multiplier * (tests' time + constant), workers/isolation.py."""
    import tomllib

    pyproject = Path(__file__).resolve().parent.parent / "backend" / "pyproject.toml"
    cfg = tomllib.loads(pyproject.read_text(encoding="utf-8"))["tool"]["mutmut"]
    tests_s = 24
    wall_s = cfg.get("timeout_multiplier", 15.0) * (tests_s + cfg.get("timeout_constant", 1.0))
    assert wall_s <= 120


def test_survivors_are_reopened_and_final_verdicts_stand(tmp_path, capsys):
    """Every night retested every mutant, so the same tail was cut at 120 minutes (#87). Now a
    night tries only the unchecked: survivors reopened, for a new test to kill them."""
    codes = {
        "k": 1,
        "t": 36,
        "s": 34,
        "c": 37,
        "v": 0,
        "n": 33,
        "q": 35,
        "x": 255,
        "g": -9,
    }
    meta = tmp_path / "astrolog" / "a.py.meta"
    meta.parent.mkdir()
    meta.write_text(json.dumps({"exit_code_by_key": codes, "durations_by_key": {}}), "utf-8")
    assert reopen(tmp_path, ["astrolog/a.py"]) == 0
    data = json.loads(meta.read_text(encoding="utf-8"))
    assert data["exit_code_by_key"] == {**codes, "v": None, "n": None, "q": None}
    assert data["durations_by_key"] == {}
    assert "3 mutants without a final verdict reopened" in capsys.readouterr().err


def test_survivors_wait_while_the_shard_has_mutants_never_run(tmp_path, capsys):
    """Night of 16/11/2026: 1060 survivors reopened took 92 of the 120 minutes, the 10717 never
    run stayed so (#87). Survivors reopen only once the tail is done."""
    survivor = {"exit_code_by_key": {"v": 0, "k": 1}, "durations_by_key": {}}
    unrun = {"exit_code_by_key": {"u": None, "k": 1}, "durations_by_key": {}}
    (tmp_path / "astrolog").mkdir()
    (tmp_path / "astrolog" / "a.py.meta").write_text(json.dumps(survivor), "utf-8")
    (tmp_path / "astrolog" / "b.py.meta").write_text(json.dumps(unrun), "utf-8")
    assert reopen(tmp_path, ["astrolog/a.py", "astrolog/b.py"]) == 0
    data = json.loads((tmp_path / "astrolog" / "a.py.meta").read_text(encoding="utf-8"))
    assert data["exit_code_by_key"] == {"v": 0, "k": 1}
    assert "1 mutants never run: survivors wait" in capsys.readouterr().err


def test_unrun_mutants_of_files_outside_the_shard_do_not_hold_its_survivors(tmp_path, capsys):
    """rest, Nightly 44107096567: its cache held 30191 never run, 9695 its own; the others, from
    files mutmut no longer walks there, would hold the survivors for ever (#87)."""
    survivor = {"exit_code_by_key": {"v": 0, "k": 1}, "durations_by_key": {}}
    foreign = {"exit_code_by_key": {"u": None}, "durations_by_key": {}}
    (tmp_path / "astrolog").mkdir()
    (tmp_path / "astrolog" / "a.py.meta").write_text(json.dumps(survivor), "utf-8")
    (tmp_path / "astrolog" / "z.py.meta").write_text(json.dumps(foreign), "utf-8")
    assert main(["mutation_shards.py", "api", "--reopen", str(tmp_path)]) == 0
    assert reopen(tmp_path, ["astrolog/a.py"]) == 0
    data = json.loads((tmp_path / "astrolog" / "a.py.meta").read_text(encoding="utf-8"))
    assert data["exit_code_by_key"] == {"v": None, "k": 1}
    untouched = json.loads((tmp_path / "astrolog" / "z.py.meta").read_text(encoding="utf-8"))
    assert untouched == foreign
    assert "1 mutants without a final verdict reopened" in capsys.readouterr().err


def test_the_workflow_stop_lets_mutmut_save_on_ubuntu_26_04():
    """uutils timeout 0.10 (Ubuntu 26.04) with -k sends KILL at once and exits 137: every shard
    died at 120 minutes without saving and failed (Nightly 43881105376)."""
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    stops = [line for line in workflow.splitlines() if re.search(r"\btimeout -", line)]
    assert len(stops) == 2
    assert all(" -k " not in line for line in stops)


def test_a_mutant_that_eats_memory_fails_alone_instead_of_losing_the_runner():
    """rest-5 lost its runner at 82 and 102 minutes, before the 120-minute stop, and saved
    nothing (Nightly 44498987010, 44538093259): the run is capped per process."""
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    lines = workflow.splitlines()
    run = next(i for i, line in enumerate(lines) if "mutmut run --max-children 4" in line)
    cap = [line for line in lines[:run] if re.search(r"^\s*ulimit -v \d+\s*$", line)]
    assert len(cap) == 1, cap
    # 4 children on a 16 GB runner: two runaways at the cap still leave room for the others
    assert 4 * 1024 * 1024 <= int(cap[0].split()[-1]) <= 6 * 1024 * 1024


def test_the_workflow_runs_each_shard_on_its_files_and_what_they_have_left():
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    assert "mutation_shards.py ${{ matrix.shard }} --only-mutate pyproject.toml" in workflow
    assert "mutation_shards.py ${{ matrix.shard }} --reopen mutants" in workflow
    # named, mutmut retests every mutant it is given
    assert re.search(r"mutmut run --max-children 4 \|\|", workflow)


def write_reports(tmp_path, *files, stale=None):
    """One Stryker report per frontend shard, written in reverse so no order is assumed; the files
    past those given hold one Killed each. Returns the paths and the parts that own the files."""
    stale = stale or {}
    table = []
    for k in range(FRONTEND_SHARDS):
        mutants = files[k] if k < len(files) else {f"src/k{k}.ts": [{"status": "Killed"}]}
        table.append(list(mutants))
    paths = []
    for k in reversed(range(FRONTEND_SHARDS)):
        mutants = {**(files[k] if k < len(files) else {table[k][0]: [{"status": "Killed"}]})}
        mutants.update(stale.get(k, {}))
        report = {"files": {name: {"mutants": m} for name, m in mutants.items()}}
        path = tmp_path / f"stryker-{k}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        paths.append(str(path))
    return paths, table


def test_the_frontend_score_adds_up_the_stryker_report_of_every_shard(tmp_path, capsys):
    first = {"src/a.ts": [{"status": "Killed"}, {"status": "Survived"}]}
    second = {"src/b.ts": [{"status": "Timeout"}, {"status": "NoCoverage"}, {"status": "Ignored"}]}
    paths, table = write_reports(tmp_path, first, second)
    detected = 2 + FRONTEND_SHARDS - 2
    checked = 4 + FRONTEND_SHARDS - 2
    reference = write_reference(tmp_path, frontend=round(detected / checked, 4))
    argv = ["mutation_shards.py", "frontend", "--filter", *paths]
    assert main(argv, reference=reference, parts=table) == 0
    expected = f"shard frontend: score {detected / checked:.4f} ({detected} of {checked} detected"
    assert expected in capsys.readouterr().err


def test_a_frontend_report_counts_only_the_files_of_its_part(tmp_path, capsys):
    """The incremental cache keeps files of an older split, deleted ones too: counted, they are
    stale and twice. Only the files the part mutates tonight count."""
    first = {"src/a.ts": [{"status": "Killed"}]}
    old = {"src/a.ts": [{"status": "Survived"}], "src/gone.ts": [{"status": "Survived"}] * 5}
    paths, table = write_reports(tmp_path, first, stale={1: old})
    reference = write_reference(tmp_path, frontend=1.0)
    argv = ["mutation_shards.py", "frontend", "--filter", *paths]
    assert main(argv, reference=reference, parts=table) == 0
    err = capsys.readouterr().err
    assert f"score 1.0000 ({FRONTEND_SHARDS} of {FRONTEND_SHARDS} detected" in err
    assert "6 mutants of files outside their part left out" in err


def test_a_frontend_shard_without_its_report_fails_the_night(tmp_path, capsys):
    """A part lost with its runner leaves no report: never a score of the parts left."""
    paths, table = write_reports(tmp_path)
    assert main(["mutation_shards.py", "frontend", "--filter", *paths[1:]], parts=table) == 1
    assert f"{FRONTEND_SHARDS - 1} of {FRONTEND_SHARDS} shard reports" in capsys.readouterr().err


def test_a_frontend_report_without_mutants_is_refused(tmp_path, capsys):
    paths, table = write_reports(tmp_path, *[{f"src/{k}.ts": []} for k in range(FRONTEND_SHARDS)])
    reference = write_reference(tmp_path)
    argv = ["mutation_shards.py", "frontend", "--filter", *paths]
    assert main(argv, reference=reference, parts=table) == 1
    assert "the reports hold no mutant" in capsys.readouterr().err


def test_every_frontend_source_is_mutated_in_exactly_one_shard_translations_left_out():
    """The translation tables are text, not logic: a mutant per string no test can kill. The
    i18n code (`t`, number and coordinate formats) stays in."""
    table = frontend_shards()
    assert len(table) == FRONTEND_SHARDS and all(table)
    files = [f for shard in table for f in shard]
    assert len(files) == len(set(files))
    assert "src/i18n/index.ts" in files and "src/i18n/lingue.ts" in files
    src = FRONTEND_DIR / "src"
    every = {
        p.relative_to(FRONTEND_DIR).as_posix()
        for p in src.rglob("*.ts*")
        if p.suffix in (".ts", ".tsx") and not p.name.endswith(".d.ts")
    }
    tables = [*(src / "i18n").glob("it*.ts"), *(src / "i18n").glob("en*.ts")]
    dictionaries = {f"src/i18n/{p.name}" for p in tables}
    assert set(files) == every - dictionaries


def test_the_frontend_shards_are_split_by_size_so_none_runs_too_long():
    sizes = [sum((FRONTEND_DIR / f).stat().st_size for f in s) for s in frontend_shards()]
    assert max(sizes) < 2 * sum(sizes) / len(sizes)


def test_a_frontend_shard_prints_its_files_for_stryker(capsys):
    assert main(["mutation_shards.py", "frontend", "0"]) == 0
    assert capsys.readouterr().out.strip().split(",") == frontend_shards()[0]
    assert main(["mutation_shards.py", "frontend", str(FRONTEND_SHARDS)]) == 2


def test_the_workflow_runs_every_frontend_shard_and_scores_them_together():
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    found = re.findall(r"^\s*part:\s*\[(.*)\]\s*$", workflow, re.MULTILINE)
    assert [s.strip() for s in found[0].split(",")] == [str(k) for k in range(FRONTEND_SHARDS)]
    assert "mutation_shards.py frontend ${{ matrix.part }}" in workflow
    assert "--incrementalFile reports/stryker-${{ matrix.part }}.json" in workflow
    assert "frontend --filter reports/stryker-*.json" in workflow


def test_a_timeout_left_in_the_cache_is_dropped_so_the_night_runs_it_again(tmp_path, capsys):
    """Incremental Stryker reuses a Timeout: one cut by a crowded runner stays 'detected'."""
    report = {
        "files": {
            "src/a.ts": {"mutants": [{"status": "Timeout"}, {"status": "Killed"}]},
            "src/b.ts": {"mutants": [{"status": "Survived"}, {"status": "Timeout"}]},
        },
        "testFiles": {"tests/a.test.ts": {"tests": []}},
    }
    path = tmp_path / "stryker-0.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert main(["mutation_shards.py", "frontend", "--drop-timeouts", str(path)]) == 0
    kept = json.loads(path.read_text(encoding="utf-8"))
    assert [m["status"] for f in kept["files"].values() for m in f["mutants"]] == [
        "Killed",
        "Survived",
    ]
    assert kept["testFiles"] == report["testFiles"]
    assert "2 Timeout dropped" in capsys.readouterr().err


def test_a_first_night_without_a_cache_has_no_timeout_to_drop(tmp_path, capsys):
    path = tmp_path / "stryker-0.json"
    assert main(["mutation_shards.py", "frontend", "--drop-timeouts", str(path)]) == 0
    assert not path.exists()
    assert "no report" in capsys.readouterr().err


def test_the_frontend_mutants_run_two_per_runner_and_skip_the_static_ones():
    """4 vCPU are 2 cores with 2 threads (lscpu, 21/11/2026): 4 runners cut a mutant that
    survives with 2. A static mutant reruns the whole suite: Stryker leaves it out."""
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
    assert "--concurrency 2" in workflow
    assert "mutation_shards.py frontend --drop-timeouts" in workflow
    config = json.loads((FRONTEND_DIR / "stryker.config.json").read_text(encoding="utf-8"))
    assert config["ignoreStatic"] is True


def test_the_saved_reference_names_only_real_shards():
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    assert set(reference) <= {*FIXED, *REST_SHARDS, FRONTEND}
    assert all(0 <= score <= 1 for score in reference.values())


def test_a_report_where_the_shard_owns_no_mutant_is_refused(capsys):
    # Names that lost the package prefix: none of them reads as the shard's own.
    results = io.StringIO(
        "    log.x_f__mutmut_1: killed\n    api.app.x_health__mutmut_1: survived\n"
    )
    assert main(["mutation_shards.py", "api", "--filter"], results) == 1
    assert "shard api: 0 of 2" in capsys.readouterr().err
