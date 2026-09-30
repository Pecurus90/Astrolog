"""Il controllo di freschezza dei tipi del frontend, visto rosso.

I tipi si **generano** dallo schema OpenAPI: committarli senza un controllo vuol dire che il
giorno in cui una rotta cambia il file resta indietro e la pagina compila **contro una bugia** --
cioe' esattamente il difetto che generare i tipi doveva togliere. Qui si prova che il controllo
se ne accorge; e' la macchina che rende vera la riga del cancello.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tipi  # noqa: E402


def test_the_check_is_green_on_a_file_just_generated(tmp_path, monkeypatch):
    """Appena scritto, il file combacia: se questa cadesse, il controllo direbbe sempre di no e
    verrebbe spento entro una settimana."""
    monkeypatch.setattr(tipi, "OUT", tmp_path / "schema.d.ts")
    assert tipi.main([]) == 0
    assert tipi.main(["--check"]) == 0


def test_the_check_is_red_when_the_types_have_drifted(tmp_path, monkeypatch):
    """**La prova che conta.** Un file che non corrisponde piu' all'API diventa rosso: e' cio'
    che impedisce a una pagina di compilare contro campi che il backend non manda piu'."""
    fuori = tmp_path / "schema.d.ts"
    monkeypatch.setattr(tipi, "OUT", fuori)
    assert tipi.main([]) == 0
    fuori.write_text("export type paths = { vecchio: true }\n", encoding="utf-8")
    assert tipi.main(["--check"]) == 1


def test_the_check_is_red_when_the_file_is_missing(tmp_path, monkeypatch):
    """E anche quando il file non c'e' affatto: senza questa riga, cancellarlo sarebbe il modo
    piu' semplice di far tacere il controllo."""
    monkeypatch.setattr(tipi, "OUT", tmp_path / "mai-scritto.d.ts")
    assert tipi.main(["--check"]) == 1
