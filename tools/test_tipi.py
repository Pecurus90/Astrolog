"""Il controllo di freschezza dei tipi del frontend, visto rosso.

I tipi si **generano** dallo schema OpenAPI: committarli senza un controllo vuol dire che il
giorno in cui una rotta cambia il file resta indietro e la pagina compila **contro una bugia** --
cioe' esattamente il difetto che generare i tipi doveva togliere. Qui si prova che il controllo
se ne accorge; e' la macchina che rende vera la riga del cancello.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tipi


@pytest.fixture(scope="module")
def generato():
    """Il generatore gira una volta per il modulo: costruisce l'app e ricarica il catalogo, e le
    prove qui sotto provano il controllo, non lui."""
    return tipi.genera()


def test_the_check_is_green_on_a_file_just_generated(tmp_path, monkeypatch, generato):
    """Appena scritto, il file combacia: se questa cadesse, il controllo direbbe sempre di no e
    verrebbe spento entro una settimana. Due generazioni indipendenti danno lo stesso testo."""
    assert tipi.genera() == generato
    monkeypatch.setattr(tipi, "genera", lambda: generato)
    monkeypatch.setattr(tipi, "OUT", tmp_path / "schema.d.ts")
    assert tipi.main([]) == 0
    assert tipi.main(["--check"]) == 0


def test_the_check_is_red_when_the_types_have_drifted(tmp_path, monkeypatch, generato):
    """**La prova che conta.** Un file che non corrisponde piu' all'API diventa rosso: e' cio'
    che impedisce a una pagina di compilare contro campi che il backend non manda piu'."""
    fuori = tmp_path / "schema.d.ts"
    monkeypatch.setattr(tipi, "genera", lambda: generato)
    monkeypatch.setattr(tipi, "OUT", fuori)
    assert tipi.main([]) == 0
    fuori.write_text("export type paths = { vecchio: true }\n", encoding="utf-8")
    assert tipi.main(["--check"]) == 1


def test_the_check_is_red_when_the_file_is_missing(tmp_path, monkeypatch, generato):
    """E anche quando il file non c'e' affatto: senza questa riga, cancellarlo sarebbe il modo
    piu' semplice di far tacere il controllo."""
    monkeypatch.setattr(tipi, "genera", lambda: generato)
    monkeypatch.setattr(tipi, "OUT", tmp_path / "mai-scritto.d.ts")
    assert tipi.main(["--check"]) == 1


def test_a_non_ascii_docstring_survives_the_generator(monkeypatch):
    """Issue #82: su Windows l'uscita del generatore si leggeva in cp1252 e «Dalla mappa»
    arrivava storpiato nei tipi, verde qui e rosso in CI."""
    schema = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/x": {
                "get": {
                    "description": "Il cielo «Dalla mappa», 21,4 mag/arcsec²",
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    monkeypatch.setattr(tipi.openapi, "schema", lambda: schema)
    assert "Il cielo «Dalla mappa», 21,4 mag/arcsec²" in tipi.genera()


def test_without_the_frontend_dependencies_it_says_what_is_missing(tmp_path, monkeypatch):
    """Senza `frontend/node_modules` non e' il generatore a cadere: manca, e lo dice con il
    comando che lo installa, invece di "il generatore e' fallito"."""
    monkeypatch.setattr(tipi, "FRONTEND", tmp_path)
    try:
        tipi.genera()
    except SystemExit as uscita:
        assert "npm ci" in str(uscita)
    else:
        raise AssertionError("senza dipendenze il generatore non puo' girare")
