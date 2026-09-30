"""Con che filtri hai ripreso qualcosa: la stessa domanda per una notte e per un oggetto.

Le Notti la facevano gia' per se'; l'Archivio ne aveva bisogno uguale. Averla scritta due volte
avrebbe voluto dire due modi di contare lo stesso tempo -- la notte che dice una cosa e l'oggetto
un'altra sulle **stesse pose** -- quindi qui si prova che la casa e' una e che i due soggetti ne
escono con gli stessi numeri.
"""

import pytest

from astrolog.spine import counts, filters_used
from conftest import one
from group_bench import filtro, luogo


def posa(conn, *, filtro, notte, oggetto, secondi=300.0, copia=None):
    return conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at, filter_id,"
        " night_id, object_id, exposure_s, copy_of) VALUES(?, 'light', '[]', 'ora', ?, ?, ?, ?, ?)",
        (f"h{conn.total_changes}-{filtro}-{oggetto}", filtro, notte, oggetto, secondi, copia),
    ).lastrowid


def banco(conn):
    """Una notte, un oggetto, due filtri: al rosso il doppio del tempo del verde."""
    sito = luogo(conn)
    notte = conn.execute(
        "INSERT INTO nights(night_date, site_id, created_at) VALUES('2026-05-18', ?, 'ora')",
        (sito,),
    ).lastrowid
    oggetto = conn.execute(
        "INSERT INTO objects(catalog_slug, created_at) VALUES('m-31', 'ora')"
    ).lastrowid
    rosso, verde = filtro(conn, "R", "r"), filtro(conn, "G", "g")
    for _ in range(2):
        posa(conn, filtro=rosso, notte=notte, oggetto=oggetto)
    posa(conn, filtro=verde, notte=notte, oggetto=oggetto)
    return notte, oggetto


def test_the_same_frames_give_the_same_filters_to_the_night_and_to_the_object(conn):
    """Il legame e' uno solo, quindi i due soggetti devono uscirne **identici**: se un giorno
    divergono, vuol dire che qualcuno ha riscritto la domanda da una parte sola -- ed e' esattamente
    il guasto per cui questa casa esiste."""
    notte, oggetto = banco(conn)

    della_notte = filters_used.of(conn, "night", [notte])[notte]
    dell_oggetto = filters_used.of(conn, "object", [oggetto])[oggetto]

    assert della_notte == dell_oggetto
    assert della_notte == [
        {"name": "R", "passband": "r", "frames": 2, "integration_s": 600.0},
        {"name": "G", "passband": "g", "frames": 1, "integration_s": 300.0},
    ]


def test_the_filter_with_more_time_comes_first(conn):
    """Prima cio' a cui hai dato piu' tempo, come ovunque si racconti un pezzo di archivio
    (`counts.ORDER_BY_TIME`): una pastiglia in cima che non e' il filtro dominante racconterebbe
    una ripresa che non hai fatto."""
    notte, _ = banco(conn)

    assert [f["name"] for f in filters_used.of(conn, "night", [notte])[notte]] == ["R", "G"]


def test_a_rewritten_copy_is_not_another_filter_hour(conn):
    """La regola delle copie vale **anche qui**. Chi elabora tiene il grezzo e il calibrato nella
    stessa cartella: contarli tutti e due darebbe al filtro il doppio del tempo che ha avuto."""
    notte, oggetto = banco(conn)
    grezza = one(conn, "SELECT id FROM frames ORDER BY id LIMIT 1")
    rosso = one(conn, "SELECT id FROM filters WHERE name = 'R'")
    posa(conn, filtro=rosso, notte=notte, oggetto=oggetto, copia=grezza)

    assert filters_used.of(conn, "night", [notte])[notte][0] == {
        "name": "R",
        "passband": "r",
        "frames": 2,
        "integration_s": 600.0,
    }


def test_the_subject_is_a_key_from_a_closed_list(conn):
    """Il soggetto non e' un pezzo di SQL che arriva da fuori: e' una chiave di un elenco chiuso,
    come in `counts`. Una funzione che si fa passare il nome di una colonna e' una porta aperta,
    anche quando chi la usa oggi passa una costante."""
    with pytest.raises(KeyError):
        filters_used.of(conn, "un soggetto che non esiste", [1])


def test_the_column_is_read_from_the_link_not_written_beside_it(conn):
    """Chi raggruppa un lotto ha bisogno del **nome della colonna**, chi chiede riga per riga del
    `WHERE`: e' lo stesso fatto visto da due lati. Tenerne due elenchi voleva dire due case, e una
    prova che li confrontasse guarderebbe due stringhe -- infatti la prima che avevo scritto
    confrontava il **prefisso**, e allargare un `WHERE` (`... AND f.filter_id IS NOT NULL`) la
    lasciava verde mentre le ore e i filtri della stessa riga cominciavano a contare pose diverse.

    Adesso la colonna si **ricava** dal legame, quindi non esiste un secondo posto dove scriverla
    diversa. Qui si prova che la lettura e' quella giusta e che non indovina dove non puo'.

    test-tolto: test_nobody_to_ask_about_costs_nothing -- diceva di provare che senza id non si
    chiede niente, e passava anche togliendo quel ramo: la regola e' di `db/idlist.py`, che ha la
    sua prova, non di questa casa.
    """
    # scritte a mano, non ricavate da cio' che si prova: un atteso che chiama la stessa funzione
    # della cosa provata e' un banco che si fa dire di si'
    assert {s: counts.column_of(s) for s in ("night", "object", "rig", "filter")} == {
        "night": "night_id",
        "object": "object_id",
        "rig": "rig_id",
        "filter": "filter_id",
    }

    # e dove il legame non e' una colonna sola non si indovina: raggruppare l'archivio intero o un
    # pezzo (che arriva alle sue pose per due strade) su una colonna conterebbe altre pose
    for soggetto in ("archive", "instrument"):
        with pytest.raises(KeyError):
            counts.column_of(soggetto)
