"""Comete e asteroidi: nomi che il catalogo non puo' riconoscere, perche' si spostano.

Un oggetto mobile non sta due notti nello stesso punto, quindi cercarlo nel catalogo per
coordinate darebbe sempre la risposta sbagliata -- e sarebbe una risposta **sicura di se'**.
Qui si riconosce dal solo nome, per non chiederglielo mai.

Ogni caso qui sotto e' un falso positivo vero, raccolto in `old/`: la guardia non e' stata
scritta di getto, e' cresciuta un errore alla volta.
"""

import pytest

from astrolog.vocab import moving


@pytest.mark.parametrize(
    "nome",
    [
        "12P/Pons-Brooks",  # cometa numerata, grafia canonica
        "12P Pons-Brooks",  # lo slash e' illegale nei nomi di cartella: N.I.N.A. scrive cosi'
        "12P_Pons-Brooks",
        "73P-C",  # un frammento
        "12P",  # la sola sigla
        "C/2023 A3",  # provvisoria con lo slash
        "P/2010 X1",
        "C 2023 A3",  # e senza, con l'ancora dell'anno
        "C-2020 F3",
        "(4) Vesta",  # asteroide numerato fra parentesi
        "2023 DZ2",  # provvisoria di asteroide
        "C/2023 M31",  # con lo slash anche le lettere ambigue passano: qui equivoco non c'e'
        "c/2023 a3",  # scritto tutto minuscolo: le maiuscole non contano
        "12p/pons-brooks",
    ],
)
def test_a_moving_object_is_recognised_from_its_name(nome):
    assert moving.is_moving_designation(nome) is True


@pytest.mark.parametrize(
    ("nome", "perche"),
    [
        ("3C 273", "le survey di Cambridge diventavano comete"),
        ("3C-273", "idem, con il trattino"),
        ("4C-21.53", "idem"),
        ("6C-B0905+3955", "idem"),
        ("C 109", "senza l'ancora dell'anno, il Caldwell 109 diventava una cometa"),
        ("2022 IC 1396", "senza l'ancora di fine, una cartella diventava l'asteroide 2022 IC"),
        ("C 2023 M31", "la cartella e la cometa hanno la stessa forma: senza slash non si passa"),
        ("433 Eros", "il prezzo dichiarato: a numero nudo non si distingue da una Flamsteed"),
        ("104 Herculis", "ed e' proprio una Flamsteed"),
        ("600 Second Darks", "e questo e' un nome di lavoro"),
        ("C 3023 A3", "l'anno dev'essere un anno vero: 3023 non lo e'"),
        ("C 1723 A3", "e nemmeno il 1723: le comete provvisorie partono dall'Ottocento"),
        ("M 31", "una sigla qualunque"),
        ("", "niente"),
        (None, "niente"),
    ],
)
def test_what_is_not_moving_is_not_taken_for_moving(nome, perche):
    """Un falso positivo qui e' peggio di un buco: dichiarare mobile un oggetto fisso lo toglie
    per sempre dalle code, e nessuno lo rivede. Chi cade fuori resta visibile e correggibile."""
    assert moving.is_moving_designation(nome) is False, perche
