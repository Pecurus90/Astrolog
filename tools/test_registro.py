"""Il registro delle regole: ogni numero del codice dice la sua fonte, e la pagina che li raccoglie
si genera dal codice, mai a mano (una casa per fatto)."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(ROOT, "tools"))

import registro  # noqa: E402


def _package(tmp_path: Path, **modules: str) -> Path:
    package = tmp_path / "astrolog"
    for name, text in modules.items():
        path = package / f"{name.replace('__', '/')}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return package


def _missing(package: Path) -> set[str]:
    return {entry.ident for entry in registro.entries(package) if not entry.sourced}


def test_a_number_without_its_source_is_found(tmp_path):
    package = _package(tmp_path, units="TIMEOUT_S = 60\n")
    assert _missing(package) == {"units.py:TIMEOUT_S"}


def test_a_tag_beside_above_or_before_the_statement_is_a_source(tmp_path):
    package = _package(
        tmp_path,
        units=(
            "A = 60  # [M 2x slowest solve]\n"
            "# [C N.I.N.A. PlateSolveSettings.cs]\n"
            "B = 30\n"
            "C = {\n"
            "    'x': 25.0,  # [C WMO 2700]\n"
            "    # [P ADR 0020]\n"
            "    'y': 50.0,\n"
            "}\n"
            "D = 2880  # [T]\n"
        ),
    )
    assert _missing(package) == set()


def test_one_line_without_its_source_leaves_the_statement_unsourced(tmp_path):
    package = _package(tmp_path, units="C = {\n    'x': 25.0,  # [C WMO 2700]\n    'y': 50.0,\n}\n")
    assert _missing(package) == {"units.py:C"}


def test_zero_one_strings_and_numbers_inside_functions_are_not_rules(tmp_path):
    package = _package(
        tmp_path,
        units=(
            "A = 0\nB = 1\nC = -1\nD = True\nE = 'chapter 12'\n"
            "def f():\n    return 60\n"
            "class K:\n    def g(self):\n        return 7\n"
        ),
    )
    assert _missing(package) == set()


def test_class_fields_defaults_and_decorators_are_rules_too(tmp_path):
    """Valutati al primo livello del modulo: i limiti di un campo, un default, un decoratore."""
    package = _package(
        tmp_path,
        api__models=(
            "class Site:\n    lat: float = Field(ge=-90, le=90)\n"
            "    def f(self, n=42):\n        return n\n"
            "@route(status_code=201)\ndef g(limit=Query(100, le=500)):\n    return 7\n"
        ),
    )
    assert _missing(package) == {
        "api/models.py:Site.lat",
        "api/models.py:Site.f(n=)",
        "api/models.py:g@route",
        "api/models.py:g(limit=)",
    }


def test_two_statements_with_one_symbol_stay_two(tmp_path):
    package = _package(tmp_path, units="X = 3  # [T]\nX = 9\n")
    assert _missing(package) == {"units.py:X#2"}


def test_the_first_run_says_why_it_fails(tmp_path, capsys):
    package = _package(tmp_path, units="A = 60  # [T]\n")
    page = tmp_path / "registro.md"
    page.write_text(registro.page(package, tmp_path / "adr"), encoding="utf-8")
    assert registro.main([], package, tmp_path / "senza.txt", page, tmp_path / "adr") == 1
    assert "--scrivi" in capsys.readouterr().out


def test_the_identity_holds_when_lines_move(tmp_path):
    """Per modulo e simbolo, mai per riga: il registro non cambia a ogni modifica sopra."""
    first = _package(tmp_path / "a", pipeline__solve="PASSES = 2\n")
    moved = _package(tmp_path / "b", pipeline__solve="import os\n\n\nPASSES = 2\n")
    assert _missing(first) == _missing(moved) == {"pipeline/solve.py:PASSES"}


def test_a_new_unsourced_number_and_a_listed_one_now_sourced_both_fail(tmp_path, capsys):
    """L'elenco senza fonte solo si accorcia: voce nuova = errore, voce ormai fatta = toglierla."""
    package = _package(tmp_path, units="A = 60\nB = 30  # [T]\n")
    baseline = tmp_path / "senza.txt"
    baseline.write_text("units.py:B\n", encoding="utf-8")
    page = tmp_path / "registro.md"
    page.write_text(registro.page(package, tmp_path / "adr"), encoding="utf-8")
    assert registro.main([], package, baseline, page, tmp_path / "adr") == 1
    said = capsys.readouterr().out
    assert "units.py:A" in said and "units.py:B" in said


def test_the_page_says_value_and_source_or_that_it_has_none(tmp_path):
    package = _package(tmp_path, units="A = 60  # [M 2x slowest solve]\nB = 30\n")
    text = registro.page(package, tmp_path / "adr")
    assert "| A | `60` | M 2x slowest solve |" in text
    assert "| B | `30` | **senza fonte** |" in text


def test_a_stale_page_fails_the_check(tmp_path, capsys):
    package = _package(tmp_path, units="A = 60  # [T]\n")
    baseline, page = tmp_path / "senza.txt", tmp_path / "registro.md"
    baseline.write_text("", encoding="utf-8")
    page.write_text("vecchia\n", encoding="utf-8")
    assert registro.main([], package, baseline, page, tmp_path / "adr") == 1
    assert "--scrivi" in capsys.readouterr().out
    assert registro.main(["--scrivi"], package, baseline, page, tmp_path / "adr") == 0
    assert registro.main([], package, baseline, page, tmp_path / "adr") == 0


def test_the_decisions_are_indexed_from_the_adr(tmp_path):
    adr = tmp_path / "adr"
    adr.mkdir()
    (adr / "0033-riconciliazione.md").write_text(
        "# 0033 -- Riconciliazione delle regole\n\n**Stato:** accettata, 23/10/2026.\n\n"
        '**Supera** in `docs/domini/meteo.md`: "a"; "b"\n',
        encoding="utf-8",
    )
    text = registro.page(_package(tmp_path, units=""), adr)
    assert "| 0033 | Riconciliazione delle regole | accettata, 23/10/2026. | domini/meteo.md |" in (
        text
    )


def test_every_tag_the_tool_asks_for_passes_the_comment_rule():
    """Il tag che lo strumento chiede si deve poter scrivere: niente date ne' nomi nel codice."""
    import commenti

    for tag in registro.TAGS:
        assert commenti.problems(f"A = 60  # {tag}\n", "units.py") == [], tag


def test_the_real_repository_is_in_order():
    """Il registro del repo e' aggiornato e nessun numero nuovo e' senza fonte."""
    assert registro.main([]) == 0
