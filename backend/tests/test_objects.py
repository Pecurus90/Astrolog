"""Le ore di un oggetto: la somma del tempo delle sue pose, letta dal database.

E' la prima casa di `spine/objects.py`, che fino a oggi era provato solo di rimbalzo attraverso
una rotta: le sue due regole -- una copia riscritta non e' un'altra ora di cielo, e una posa che
non dice il tempo non vale zero -- vivono qui, accanto alla query che le applica. Provarle solo
dalla pagina vorrebbe dire mettere la guardia a tre stanze da dove sta la regola.
"""

import itertools
import re

from astrolog.clock import now_iso
from astrolog.spine import objects as obj

# L'impronta di una posa e' il suo CONTENUTO, e due righe non possono condividerla.
_progressivo = itertools.count(1)

TEMPO = 120.0  # quanto dura una posa qui: il valore non conta, contano le somme che ne escono


def oggetto(conn, id_=1, slug="m-31"):
    """Un oggetto dell'archivio. Senza nomi propri e senza catalogo caricato si chiama `None`, e
    non importa: qui si contano le ore, non si legge il nome."""
    conn.execute(
        "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence, created_at)"
        " VALUES(?, ?, 'coord_confirmed', 'certain', ?)",
        (id_, slug, now_iso()),
    )
    return id_


def posa(conn, *, oggetto_id=1, tempo=TEMPO, copia=None):
    """Una posa attaccata a quell'oggetto. `copia` la rende la copia riscritta di un'altra."""
    return conn.execute(
        "INSERT INTO frames(frame_hash, image_type, object_id, copy_of, exposure_s,"
        " header_json, created_at) VALUES(?, 'light', ?, ?, ?, '[]', ?)",
        (f"o{next(_progressivo)}", oggetto_id, copia, tempo, now_iso()),
    ).lastrowid


def riga(conn, id_=1):
    return next(r for r in obj.listing(conn) if r["id"] == id_)


def test_the_hours_of_an_object_are_the_sum_of_its_poses(conn):
    """Le ore sono la somma del tempo delle pose, in secondi: l'unita' del dato e' il secondo, e a
    dire "ore" e' lo schermo (`goal_hours` / `goal_seconds` e' la stessa convenzione)."""
    oggetto(conn)
    for _ in range(3):
        posa(conn)
    assert (riga(conn)["frames"], riga(conn)["integration_s"]) == (3, 3 * TEMPO)


def test_a_rewritten_copy_is_not_another_hour_of_sky(conn):
    """Una copia riscritta resta in archivio con le sue posizioni, ma **le sue ore le conta
    l'originale**: e' la regola di tutto l'archivio, e le ore non sono l'eccezione. Senza questo
    filtro un archivio con le copie accanto ai grezzi raddoppierebbe le ore in silenzio."""
    oggetto(conn)
    originale = posa(conn)
    posa(conn, copia=originale)
    assert (riga(conn)["frames"], riga(conn)["integration_s"]) == (1, TEMPO)


def test_a_pose_that_does_not_say_its_time_is_not_zero_hours(conn):
    """ "Non lo sappiamo" e "zero ore" non sono la stessa cosa: la posa muta non entra nella somma
    e si conta a parte. Il progetto di prima le sommava come zeri (`COALESCE(SUM(exptime), 0)`) e
    nessuna riga distingueva i due casi."""
    oggetto(conn)
    posa(conn)
    posa(conn, tempo=None)
    trovata = riga(conn)
    assert (trovata["frames"], trovata["integration_s"], trovata["untimed"]) == (2, TEMPO, 1)


def test_an_object_whose_poses_never_say_the_time_says_so(conn):
    """Zero secondi sommati **con il perche' accanto**: due pose, nessuna che dica il tempo. Senza
    il conto a parte questo oggetto sarebbe indistinguibile da uno ripreso per zero secondi, che
    non esiste."""
    oggetto(conn)
    posa(conn, tempo=None)
    posa(conn, tempo=None)
    trovata = riga(conn)
    assert (trovata["frames"], trovata["integration_s"], trovata["untimed"]) == (2, 0.0, 2)


def test_a_copy_that_does_not_say_its_time_is_not_counted_as_untimed(conn):
    """Le due regole si incrociano dalla parte giusta: una copia non e' una posa, quindi non entra
    ne' nelle ore ne' nel conto di quelle che il tempo non lo dicono. Contarla li' farebbe apparire
    un dubbio su un archivio che non ne ha."""
    oggetto(conn)
    originale = posa(conn)
    posa(conn, copia=originale, tempo=None)
    trovata = riga(conn)
    assert (trovata["integration_s"], trovata["untimed"]) == (TEMPO, 0)


def test_a_pose_of_zero_seconds_is_a_measure_not_an_absence(conn):
    """Zero secondi **e'** un tempo: entra nella somma aggiungendo zero, e non si conta fra quelle
    che il tempo non lo dicono. Nel numero le due cose si assomigliano, nel significato no -- ed e'
    la distinzione su cui regge tutta questa fetta."""
    oggetto(conn)
    posa(conn)
    posa(conn, tempo=0.0)
    trovata = riga(conn)
    assert (trovata["frames"], trovata["integration_s"], trovata["untimed"]) == (2, TEMPO, 0)


def test_an_object_with_no_poses_has_no_hours(conn):
    """Un oggetto senza pose porta zero, non un vuoto: la somma di niente e' zero e si sa perche'
    -- non ci sono pose -- mentre un campo vuoto farebbe credere a un dato che manca."""
    oggetto(conn)
    trovata = riga(conn)
    assert (trovata["frames"], trovata["integration_s"], trovata["untimed"]) == (0, 0.0, 0)


def test_the_objects_listing_counts_the_poses_from_the_index_alone(conn):
    """I conti di ogni oggetto leggono le sue pose dall'indice, senza la tabella: senza, l'elenco di
    Da confermare rileggerebbe le righe dell'archivio a ogni apertura."""
    piano = [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + obj._LIST)]
    pose = [p for p in piano if re.match(r"(SCAN|SEARCH) f\b", p)]
    assert pose, piano
    assert all(re.search(r"COVERING INDEX frames_object\b", p) for p in pose), piano


def test_a_name_spelled_like_a_slug_loses_to_the_catalog_object(conn):
    """`by_key` looks a key up as slug and as primary name: an out-of-catalog name spelled like a
    slug (`OBJECT = m-31`) must not win over the catalog object, whatever the row order."""
    oggetto(conn, id_=1, slug=None)
    conn.execute(
        "INSERT INTO object_names(object_id, name, origin, is_primary) VALUES(1, 'm-31', 'raw', 1)"
    )
    oggetto(conn, id_=2, slug="m-31")
    assert obj.by_key(conn, "m-31")["id"] == 2
