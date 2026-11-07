"""Il glossario contro i testi (ADR 0025): doppioni con la loro nota, forme sorvegliate assenti."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import glossario

TABELLA = """
| cosa e' | nel codice | a schermo (it) | non si dice |
|---|---|---|---|
| un file | `frame` | frame | posa (e' il tempo; al plurale «pose» sono frame), scatto |
| il tempo di un frame | `exposure_s` | posa | esposizione, durata |
| la finestra | `night` | notte | sessione |
| una sessione | `session` | sessione | notte (e' la finestra, `night`) |
"""


def test_a_double_without_its_note_is_named():
    righe = glossario.rows(TABELLA)
    assert glossario.doubles_without_note(righe) == [
        "`night`: «sessione» e' a schermo per `session`"
    ]


def test_a_double_with_its_note_passes():
    righe = glossario.rows(TABELLA.replace("| sessione |\n", "| sessione (e' `session`) |\n"))
    assert glossario.doubles_without_note(righe) == []


def test_the_real_glossary_has_no_double_without_note():
    righe = glossario.rows(glossario.GLOSSARY.read_text(encoding="utf-8"))
    assert glossario.doubles_without_note(righe) == []


def test_a_guarded_form_lives_in_its_glossary_row():
    righe = glossario.rows(glossario.GLOSSARY.read_text(encoding="utf-8"))
    assert glossario.unhoused(righe) == []
    assert glossario.unhoused(glossario.rows(TABELLA.replace("«pose»", "«posate»"))) == ["pose"]


def test_the_plural_pose_is_a_frame():
    testo = "Le pose riprese.\nIl tempo di posa 300 s.\nOre di posa.\n"
    assert glossario.misuses("docs/x.md", testo) == ["docs/x.md:1: «pose» -> frame"]


def test_code_and_quotes_are_left_alone():
    testo = "`pose` nel codice\nle Pose qui <!-- glossario-ok -->\nposeidone\n"
    assert glossario.misuses("docs/x.md", testo) == []


def test_only_italian_texts_are_read():
    assert glossario.in_scope("docs/domini/notti.md")
    assert glossario.in_scope("frontend/src/i18n/it.ts")
    assert glossario.in_scope("backend/astrolog/schema.sql")
    assert not glossario.in_scope("frontend/src/i18n/en.ts")
    assert not glossario.in_scope("docs/domini/glossario.md")
    assert not glossario.in_scope("docs/registro.md")
    assert not glossario.in_scope("backend/tests/test_mosaic.py")
    assert not glossario.in_scope("old/docs/x.md")
    assert glossario.in_scope("handoff/design-selezione.md")
    assert not glossario.in_scope("handoff/design/docs/x.md")
    assert not glossario.in_scope("frontend/src/stili/consegna/astrolog.css")


def test_main_fails_on_a_misuse(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(glossario, "GLOSSARY", tmp_path / "senza-glossario.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("Le pose.\n", encoding="utf-8")
    assert glossario.main(["docs/x.md"]) == 1
    (tmp_path / "docs" / "x.md").write_text("I frame.\n", encoding="utf-8")
    assert glossario.main(["docs/x.md"]) == 0
