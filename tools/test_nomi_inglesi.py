"""Internal names in English, checked by a machine (tools/nomi_inglesi.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nomi_inglesi  # noqa: E402


def test_an_italian_word_in_a_name_is_found():
    assert nomi_inglesi.is_italian("righe_senza_tipo")
    assert nomi_inglesi.is_italian("_ORA_DI_INIZIO")
    assert nomi_inglesi.is_italian("LocalNotte")


def test_an_italian_word_not_ending_in_a_vowel_is_found_by_the_list():
    assert nomi_inglesi.is_italian("nome")
    assert nomi_inglesi.is_italian("per_notte") and nomi_inglesi.is_italian("notte")


def test_english_names_pass_even_when_a_word_ends_in_a_vowel():
    assert not nomi_inglesi.is_italian("camera_specs")
    assert not nomi_inglesi.is_italian("read_ini")
    assert not nomi_inglesi.is_italian("NightRig")


def _package(tmp_path, source):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "m.py").write_text(source, encoding="utf-8")
    return package


def test_every_kind_of_defined_name_is_read(tmp_path):
    source = (
        "import os as sistema\n"
        "class Riga:\n    campo: int\n"
        "def leggi(valore):\n    righe = 1\n    self.posto = 2\n"
    )
    found = nomi_inglesi.found(_package(tmp_path, source))
    assert found == {
        f"m.py:{n}" for n in ("sistema", "Riga", "campo", "leggi", "valore", "righe", "posto")
    }


def test_a_name_only_used_is_not_ours_to_rename(tmp_path):
    assert nomi_inglesi.found(_package(tmp_path, "x = os.path.join(tempo)\n")) == set()


def test_a_new_italian_name_fails_and_a_listed_one_passes(tmp_path):
    package = _package(tmp_path, "def f(riga):\n    return riga\n")
    baseline = tmp_path / "list.txt"
    assert nomi_inglesi.main([], package, baseline) == 1
    baseline.write_text("# header\nm.py:riga\n", encoding="utf-8")
    assert nomi_inglesi.main([], package, baseline) == 0


def test_a_renamed_name_left_in_the_list_fails_until_rewritten(tmp_path):
    package = _package(tmp_path, "def f(row):\n    return row\n")
    baseline = tmp_path / "list.txt"
    baseline.write_text("m.py:riga\n", encoding="utf-8")
    assert nomi_inglesi.main([], package, baseline) == 1
    assert nomi_inglesi.main(["--riscrivi"], package, baseline) == 0
    assert nomi_inglesi.read_baseline(baseline) == set()
    assert nomi_inglesi.main([], package, baseline) == 0


def test_rewriting_never_adds_a_new_name_to_the_list(tmp_path):
    package = _package(tmp_path, "def f(riga):\n    return riga\n")
    baseline = tmp_path / "list.txt"
    assert nomi_inglesi.main(["--riscrivi"], package, baseline) == 1
    assert nomi_inglesi.read_baseline(baseline) == set()
