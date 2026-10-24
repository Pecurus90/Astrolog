"""La lista unica (ADR 0040): `docs/piano.json`, un passo dopo l'altro. All'avvio si stampa il primo
aperto; al commit l'agente puo' solo spuntare, ogni altro cambio vuole `docs(piano):`."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import piano

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _passo(n, fatto="", **campi):
    return {
        "n": n,
        "fase": "0 basi",
        "passo": f"passo {n}",
        "fatto_quando": "test",
        "ricetta": "costruisci",
        "marco": "",
        "fatto": fatto,
        **campi,
    }


def _lista(*passi):
    return json.dumps({"passi": list(passi)})


def test_a_good_list_has_no_faults():
    assert piano.faults(_lista(_passo("1"), _passo("2"))) == []


def test_the_first_open_step_is_the_next_one():
    lista = json.loads(_lista(_passo("1", fatto="ca6b2f61"), _passo("2"), _passo("3")))
    assert piano.next_step(lista)["n"] == "2"


def test_a_finished_list_has_no_next_step():
    assert piano.next_step(json.loads(_lista(_passo("1", fatto="ca6b2f61")))) is None


def test_every_step_says_when_it_is_done():
    assert "passo 1: manca fatto_quando" in piano.faults(_lista(_passo("1", fatto_quando="")))


def test_a_step_names_a_real_recipe():
    assert "passo 1: ricetta 'a mano' sconosciuta" in piano.faults(
        _lista(_passo("1", ricetta="a mano"))
    )


def test_two_steps_with_one_number_are_refused():
    assert "passo 1 due volte" in piano.faults(_lista(_passo("1"), _passo("1")))


def test_done_is_a_commit_not_a_word():
    assert "passo 1: fatto 'si' non e' uno sha" in piano.faults(_lista(_passo("1", fatto="si")))


def test_a_list_that_is_not_json_is_said():
    assert piano.faults("{rotto")[0].startswith("docs/piano.json non e' JSON")


def test_ticking_a_step_is_allowed_without_a_plan_message():
    prima = _lista(_passo("1"), _passo("2"))
    dopo = _lista(_passo("1", fatto="ca6b2f61"), _passo("2"))
    assert piano.only_ticks(prima, dopo)


def test_rewriting_or_removing_a_step_is_not_a_tick():
    prima = _lista(_passo("1"), _passo("2"))
    assert not piano.only_ticks(prima, _lista(_passo("1", passo="altro"), _passo("2")))
    assert not piano.only_ticks(prima, _lista(_passo("2")))
    assert not piano.only_ticks(prima, _lista(_passo("2"), _passo("1")))


def test_a_second_list_beside_the_steps_is_refused():
    lista = json.dumps({"passi": [_passo("1")], "dopo": ["altro"]})
    assert "docs/piano.json: chiave 'dopo' fuori da 'passi'" in piano.faults(lista)


def test_a_step_without_done_is_not_a_tick():
    prima = _lista(_passo("1"))
    senza = json.dumps({"passi": [{k: v for k, v in _passo("1").items() if k != "fatto"}]})
    assert not piano.only_ticks(prima, senza)


def test_deleting_the_list_needs_a_plan_message():
    assert piano.plan_changed_fault("x", None, "fix: altro") is not None
    assert piano.plan_changed_fault("x", None, "docs(piano): via la lista") is None
    assert piano.plan_changed_fault(None, None, "fix: altro") is None


def test_a_plan_change_needs_its_own_message():
    assert piano.message_fault(only_ticks=False, message="fix: altro") is not None
    assert piano.message_fault(only_ticks=False, message="docs(piano): sposta il passo 14") is None
    assert piano.message_fault(only_ticks=True, message="fix: altro") is None


def test_the_real_list_is_well_formed():
    with open(os.path.join(ROOT, "docs", "piano.json"), encoding="utf-8") as h:
        assert piano.faults(h.read()) == []
