"""La ricerca nella barra: oggetti, notti, attrezzatura e siti dell'archivio, da ogni pagina.

Il banco ha il **catalogo vero** dentro: un oggetto si trova per ogni suo nome, e i nomi comuni
("Andromeda") li porta il catalogo. Le notti nascono dallo stadio `group`, come nell'app.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.spine import archive, objects, search
from group_bench import ROMA, attrezzo, corri, filtro, luogo, posa, prepara


def nomina(conn, object_id, *nomi):
    """I nomi di un oggetto di catalogo come li scrive `identify`: la sigla primaria, poi il nome
    comune."""
    for i, nome in enumerate(nomi):
        conn.execute(
            "INSERT INTO object_names(object_id, name, origin, is_primary)"
            " VALUES(?, ?, 'catalog', ?)",
            (object_id, nome, int(i == 0)),
        )


def oggetto(conn, slug, *nomi):
    riga = conn.execute(
        "INSERT INTO objects(catalog_slug, identity_method, identity_confidence, created_at)"
        " VALUES(?, 'coord_confirmed', 'certain', ?)",
        (slug, now_iso()),
    ).lastrowid
    nomina(conn, riga, *nomi)
    return riga


@pytest.fixture
def banco(archivio):
    """A casa tre notti: il 17 maggio 2024 M 31, il 18 M 31 e M 45, il 5 giugno M 45. Il 5/6 e'
    ambiguo apposta: letto giorno/mese e' il 5 giugno, letto mese/giorno il 6 maggio."""
    prepara(archivio)
    nomina(archivio, 1, "M 31", "Andromeda Galaxy")
    nomina(archivio, 2, "M 45", "Pleiades")
    luogo(archivio, ROMA)
    posa(archivio, quando="2024-05-17T22:00:00Z", esposizione=300.0, hash_="a1")
    posa(archivio, quando="2024-05-18T22:00:00Z", esposizione=300.0, hash_="b1")
    posa(archivio, quando="2024-05-18T23:00:00Z", oggetto=2, esposizione=600.0, hash_="b2")
    posa(archivio, quando="2024-06-05T21:00:00Z", oggetto=2, esposizione=60.0, hash_="c1")
    corri(archivio)
    archivio.commit()
    return archivio


def date_trovate(trovato):
    return [n["night_date"] for n in trovato["nights"]["items"]]


def test_a_blank_search_finds_nothing_not_everything(banco):
    """Il campo vuoto non e' una domanda: tornare tutto l'archivio a ogni spazio battuto farebbe
    aprire un menu lungo quanto l'archivio."""
    trovato = search.find(banco, "   ", limit=5)

    for gruppo in ("objects", "nights", "gear", "sites"):
        assert trovato[gruppo] == {"items": [], "total": 0}, gruppo


@pytest.mark.parametrize("scritto", ["m31", "M 31", "ngc 224", "andromeda"])
def test_an_object_is_found_by_any_of_its_names(banco, scritto):
    """La sigla, l'altra sigla, il nome comune: lo stesso frammento dell'Archivio. Si mostra col
    nome dell'Archivio e accanto il nome comune, e porta cio' che hai: frame e ore."""
    oggetti = search.find(banco, scritto, limit=5)["objects"]

    assert [o["name"] for o in oggetti["items"]] == ["M 31"]
    m31 = oggetti["items"][0]
    assert m31["common_name"] == "Andromeda Galaxy"
    assert (m31["frames"], m31["integration_s"]) == (2, 600.0)
    assert m31["key"] == "m-31"


def test_the_key_opens_the_archive_on_that_object_alone(archivio):
    """`M 1` dentro `M 10` e `M 101`: cercare per frammento stringerebbe a tre. La chiave che la
    ricerca manda stringe l'Archivio a una riga sola, anche per un oggetto fuori catalogo."""
    for slug, nome in (("m-1", "M 1"), ("m-10", "M 10"), ("m-101", "M 101")):
        oggetto(archivio, slug, nome)
    oggetto(archivio, None, "Il campo dietro casa")
    oggetto(archivio, None, "Il campo dietro casa 2")

    for chiave, atteso in (("m-1", "M 1"), ("Il campo dietro casa", "Il campo dietro casa")):
        righe, quanti = archive.page(archivio, limit=50, offset=0, key=chiave)
        assert ([r["primary_name"] for r in righe], quanti) == ([atteso], 1), chiave


def test_the_row_key_is_the_stable_key_of_its_object(archivio):
    """La chiave che l'Archivio legge in SQL e quella che le altre pagine scrivono in Python
    (`objects.stable_key`) devono coincidere, o `?key=` non trova cio' che le Notti nominano."""
    oggetto(archivio, "m-1", "M 1")
    oggetto(archivio, None, "Il campo dietro casa")
    # senza nomi propri: la chiave e' la sigla-chiave, il nome viene dal catalogo
    oggetto(archivio, "ic-1396")

    righe, _ = archive.page(archivio, limit=50, offset=0)

    assert [r["key"] for r in righe] == [objects.stable_key(r) for r in righe]
    assert len(righe) == 3


@pytest.mark.parametrize(
    ("scritto", "date"),
    [
        ("2024-05-17", ["2024-05-17"]),
        ("17/5", ["2024-05-17"]),
        ("17/5/2024", ["2024-05-17"]),
        ("17.05.24", ["2024-05-17"]),
        ("17 maggio", ["2024-05-17"]),
        ("17 May 2024", ["2024-05-17"]),
        ("May 17", ["2024-05-17"]),
        ("maggio 2024", ["2024-05-18", "2024-05-17"]),
        ("June", ["2024-06-05"]),
        # ambigui: tutte e due le letture
        ("5/6", ["2024-06-05"]),
        ("6/5", ["2024-06-05"]),
    ],
)
def test_a_night_is_found_by_date_in_the_common_forms(banco, scritto, date):
    assert date_trovate(search.find(banco, scritto, limit=5)) == date


@pytest.mark.parametrize("scritto", ["17 maggio 2023", "31/2", "13/13", "2024-13-01", "maggiore"])
def test_what_is_not_one_of_your_dates_finds_no_night(banco, scritto):
    """Un'altra data, una data che non esiste, una parola che comincia come un mese."""
    assert date_trovate(search.find(banco, scritto, limit=5)) == []


def test_a_night_is_found_by_the_object_shot_in_it(banco):
    """Cercare M45 mette nelle Notti anche le notti di M 45, la piu' recente prima (Marco,
    7/10/2026)."""
    trovato = search.find(banco, "M45", limit=5)

    assert date_trovate(trovato) == ["2024-06-05", "2024-05-18"]
    notte = trovato["nights"]["items"][1]
    assert notte["site"] == "Casa"
    # la notte intera, come la riga delle Notti: non solo le pose di M 45
    assert (notte["frames"], notte["integration_s"]) == (2, 900.0)


def test_each_group_says_how_many_beyond_the_few_it_shows(banco):
    trovato = search.find(banco, "maggio 2024", limit=1)

    assert date_trovate(trovato) == ["2024-05-18"]
    assert trovato["nights"]["total"] == 2


def test_a_piece_and_a_filter_are_found_by_name_with_what_is_known_of_them(banco):
    """Un pezzo ancora da contare non dice zero ore: dice che non e' contato."""
    camera = attrezzo(banco, "camera", "ZWO ASI2600MM Pro")
    ha = filtro(banco, "Ha 3nm")
    banco.execute(
        "INSERT INTO gear_usage(subject, subject_id, frames, integration_s, untimed, nights,"
        " objects_json, position) VALUES('filter', ?, 4, 1200.0, 0, 2, '[]', 0)",
        (ha,),
    )

    pezzi = search.find(banco, "2600mm", limit=5)["gear"]["items"]
    filtri = search.find(banco, "ha 3", limit=5)["gear"]["items"]

    assert [(p["id"], p["kind"], p["counted"], p["frames"]) for p in pezzi] == [
        (camera, "camera", False, None)
    ]
    assert [(f["id"], f["kind"], f["counted"], f["frames"]) for f in filtri] == [
        (ha, "filter", True, 4)
    ]


def test_no_filter_is_not_a_filter_you_own(banco):
    banco.execute(
        "INSERT INTO filters(name, passband, is_none, created_at) VALUES('Nessun filtro', 'none',"
        " 1, ?)",
        (now_iso(),),
    )

    assert search.find(banco, "nessun", limit=5)["gear"]["items"] == []


def test_a_site_is_found_by_name_with_its_nights(banco):
    siti = search.find(banco, "cas", limit=5)["sites"]["items"]

    assert [(s["name"], s["nights"]) for s in siti] == [("Casa", 3)]


def test_the_route_answers_the_four_groups(db_path_col_catalogo):
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as client:
        risposta = client.get("/api/v1/search", params={"q": "m31"})
        troppo = client.get("/api/v1/search", params={"q": "x" * 201})
        chiave = client.get("/api/v1/archive", params={"key": "m-31"})

    assert risposta.status_code == 200, risposta.text
    assert set(risposta.json()) == {"objects", "nights", "gear", "sites"}
    assert troppo.status_code == 422
    assert chiave.status_code == 200, chiave.text
