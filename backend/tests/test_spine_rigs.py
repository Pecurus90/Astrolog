"""Il **setup** dal lato di chi dichiara: la chiave che gli sopravvive, e cosa succede a quella
chiave quando uno strumento cambia nome.

Un setup e' rilevato -- la spina lo rifa' a ogni corsa -- quindi il nome che gli dai non sta
nella sua riga ma fra le dichiarazioni, con una chiave fatta dei **nomi** di ottica e camera piu'
la focale. Da li' viene tutto quello che si prova qui: una rinomina sposta la chiave, e deve
spostarla **solo** quando quello strumento nella chiave c'e' davvero.
"""

import pytest

from astrolog.clock import now_iso
from astrolog.spine import declarations
from astrolog.spine import rigs as setups
from conftest import one, rows
from group_bench import attrezzo, prepara


def setup(conn, ottica, camera, focale=560.0):
    return conn.execute(
        "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
        " VALUES(?, ?, ?, 1, ?)",
        (ottica, camera, focale, now_iso()),
    ).lastrowid


def banco(conn):
    prepara(conn)
    ottica = attrezzo(conn, "optics", "Askar 103Apo")
    camera = attrezzo(conn, "camera", "ASI120MM Mini")
    return setup(conn, ottica, camera)


def nomi(conn):
    return {
        r["entity_key"]: r["value"]
        for r in rows(
            conn,
            "SELECT entity_key, value FROM declarations"
            " WHERE entity_type = 'rig' AND field = 'name'",
        )
    }


def test_a_rig_without_a_name_is_not_a_declaration(conn):
    """Un nome vuoto non e' una risposta: non si scrive niente, e chi chiama lo sa -- il conto
    delle risposte dell'Applica lo legge da qui, e contarne una che non c'e' sarebbe dire
    all'utente che ha scritto qualcosa quando non ha scritto niente."""
    rig = banco(conn)

    assert setups.declare_rig(conn, rig, "") is False
    assert nomi(conn) == {}


def test_naming_a_rig_says_it_was_written(conn):
    """E un nome vero invece **e'** una risposta: torna vero, e la dichiarazione c'e'."""
    rig = banco(conn)

    assert setups.declare_rig(conn, rig, "Il grande") is True
    assert nomi(conn) == {"Askar 103Apo|ASI120MM Mini|560.0": "Il grande"}


def test_a_rename_moves_only_the_keys_that_carry_that_name(conn):
    """La chiave di un setup porta i nomi di **ottica e camera**, non altro. Una rinomina deve
    spostare le chiavi che quel nome ce l'hanno e lasciare stare le altre: sono dichiarazioni di
    setup che con quello strumento non c'entrano, e riscriverle vuol dire perderne il nome."""
    rig = banco(conn)
    setups.declare_rig(conn, rig, "Il grande")
    altro = setup(
        conn, attrezzo(conn, "optics", "RC8"), attrezzo(conn, "camera", "QHY268M"), 1624.0
    )
    setups.declare_rig(conn, altro, "Il piccolo")

    setups.follow_rename(conn, "Askar 103Apo", "Askar 103 APO")

    assert nomi(conn) == {
        "Askar 103 APO|ASI120MM Mini|560.0": "Il grande",  # spostata
        "RC8|QHY268M|1624.0": "Il piccolo",  # lasciata stare
    }


def test_a_key_that_is_not_three_pieces_is_left_alone(conn):
    """La chiave si separa sulla barra, e un **nome che contiene una barra** ne produce una di
    quattro strumenti: li' non si sa piu' quale strumento sia l'ottica e quale la camera, e
    riscriverla a indovinare sposterebbe il nome del setup su una chiave che non esiste.

    Non e' un caso di scuola: il nome lo scrive chi ha fatto il file, e una barra ci sta."""
    ottica = attrezzo(conn, "optics", "Askar 103Apo")
    strana = attrezzo(conn, "camera", "ASI|120")
    setups.declare_rig(conn, setup(conn, ottica, strana), "Il quattro pezzi")
    prima = nomi(conn)

    setups.follow_rename(conn, "Askar 103Apo", "Askar 103 APO")

    assert nomi(conn) == prima


@pytest.mark.parametrize(
    "parti", [("Askar 103Apo", "ASI2600MC", 533.0), ("Askar 103Apo", "ASI2600MC", None)]
)
def test_a_rig_key_reads_back_the_pieces_it_was_made_of(parti):
    """Una focale ignota resta ignota anche riletta: niente zero, niente schianto."""
    assert declarations.rig_key_parts(declarations.rig_key(*parti)) == parti


def test_a_rename_keeps_the_moment_it_was_told(conn):
    """L'istante che si scrive e' quello che il chiamante passa, non quello di adesso: tutta
    l'Applica e' un colpo solo, e datare una riga di mezzo con un altro orologio la farebbe
    sembrare un'altra risposta."""
    rig = banco(conn)
    setups.declare_rig(conn, rig, "Il grande")

    setups.follow_rename(conn, "Askar 103Apo", "Askar 103 APO", "2024-05-18T22:00:00Z")

    assert (
        one(conn, "SELECT created_at FROM declarations WHERE entity_type = 'rig'")
        == "2024-05-18T22:00:00Z"
    )


def test_the_subject_stays_a_key_on_both_shapes():
    """Il soggetto e' una **chiave da un elenco chiuso**, e lo resta anche sulla forma che usa i
    setup gia' giunti. Senza, chi chiedesse le ore di un setup con quella forma si prenderebbe
    in silenzio la condizione dello **strumento**: numeri sbagliati e nessun errore."""
    from astrolog.spine import counts

    with pytest.raises(KeyError):
        counts.of("un soggetto che non esiste")
    with pytest.raises(KeyError, match="non per rig"):  # l'errore dice chi l'ha chiesta
        counts.of("rig", rigs_joined=True)  # la forma giunta esiste solo per lo strumento


@pytest.mark.parametrize("kind", ["filter_wheel", "oag"])
def test_a_piece_the_frame_carries_reaches_it_without_a_rig(conn, kind):
    """Ruota, OAG e gli altri pezzi sul frame lo raggiungono dalla loro colonna, senza setup: e'
    il legame che conta frame e ore di un pezzo (`counts._piece`)."""
    from astrolog.spine import counts

    pezzo = conn.execute(
        "INSERT INTO instruments(kind, name, detected, created_at) VALUES(?, 'P', 1, ?)",
        (kind, now_iso()),
    ).lastrowid
    for carica in (pezzo, None):
        conn.execute(
            f"INSERT INTO frames(frame_hash, image_type, header_json, created_at, {kind}_id)"
            " VALUES(?, 'light', '[]', ?, ?)",
            (f"h{carica}", now_iso(), carica),
        )
    # built once at import: the count reads its copy, the builder is asked here
    legame = counts._piece("0")
    sql = f"SELECT COUNT(*) FROM frames f, instruments i WHERE i.id = ? AND {legame}"  # noqa: S608
    assert one(conn, sql, (pezzo,)) == 1


@pytest.mark.parametrize("kind", declarations.ALIAS_KINDS)
def test_every_kind_that_learns_a_spelling_is_one_the_schema_accepts(conn, kind):
    """I generi che imparano una grafia sono un elenco in Python (`ALIAS_KINDS`), e lo schema ne
    tiene un altro nel `CHECK` di `header_aliases`. Sono due case dello stesso fatto e niente le
    lega: un genere aggiunto di la' e dimenticato di qua schianterebbe alla **prima rinomina di un
    utente vero**, non qui. Questa prova e' quel legame."""
    prepara(conn)

    declarations.learn(conn, kind, "grafia vecchia", "nome nuovo")

    assert (
        one(conn, "SELECT target_key FROM header_aliases WHERE kind = ?", (kind,)) == "nome nuovo"
    )
