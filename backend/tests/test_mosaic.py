"""I mosaici scritti: le pose nei loro pannelli, i pannelli nei loro mosaici, una volta sola.

`group` piazza le pose (`spine/mosaic.py`, `place`), Da confermare legge cio' che e' scritto
(`spine/mosaic_proposals.py`), la risposta si scrive e non si ricalcola (Marco, 23/9/2026).

Le coordinate sono vere (IC 405) e gli scarti misurati: 0,0042 gradi e' il dithering dell'esempio
ufficiale di N.I.N.A., 0,5000 il passo di un pannello con la sovrapposizione al 17%, 3,0021 un
altro soggetto.
"""

import itertools
from dataclasses import asdict

import pytest

from astrolog.clock import now_iso
from astrolog.spine import declarations as decl
from astrolog.spine import mosaic
from astrolog.spine import mosaic_proposals as proposte
from astrolog.spine import objects as obj

# L'impronta di una posa e' il suo CONTENUTO, e due righe non possono condividerla.
_progressivo = itertools.count(1)

A = (79.122833, 34.356167)  # IC 405
DITHERATA = (79.127880, 34.356167)  # 0,0042 gradi: la stessa inquadratura
B = (79.728493, 34.356167)  # 0,5000 gradi: il pannello accanto
C = (80.334153, 34.356167)  # 1,0001 gradi: il terzo della striscia, che tocca B ma non A
D = (80.939813, 34.356167)  # il quarto: tocca C, e non A ne' B
E = (81.545453, 34.356167)  # il quinto: tocca D
LONTANO = (82.756794, 34.356167)  # 3,0021 gradi: un'altra regione
ACCANTO_A_LONTANO = (83.362794, 34.356167)  # 0,5003 gradi da LONTANO: un secondo mosaico
NOTTE, ALTRA_NOTTE = "2024-05-17T22:00:00Z", "2024-05-18T22:00:00Z"
TEMPO = 120.0  # il tempo di una posa del banco, in secondi; `tempo=None` e' la posa che non lo dice
SI = "catalog:ic-405"  # il si' si scrive col suo oggetto: "si', ed e' IC 405"


def prepara(conn):
    """Due oggetti e tre corredi: il mosaico li incrocia, non li crea."""
    for i in (1, 2):
        conn.execute(
            "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence,"
            " created_at) VALUES(?, ?, 'coord_confirmed', 'certain', ?)",
            (i, f"ic-40{i}", now_iso()),
        )
    for i in (1, 2, 3):
        conn.execute(
            "INSERT INTO rigs(id, focal_mm, detected, created_at) VALUES(?, ?, 1, ?)",
            (i, 700 + i, now_iso()),
        )
    return conn


def posa(
    conn, cielo, *, oggetto=1, corredo=1, quando=NOTTE, campo=(0.6, 0.4), copia=None, tempo=TEMPO
):
    """Una posa risolta, gia' identificata e col suo corredo, piazzata come la piazza `group`."""
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, date_obs, object_id, rig_id, copy_of,"
        " exposure_s, header_json, created_at) VALUES(?, 'light', ?, ?, ?, ?, ?, '[]', ?)",
        (f"h{next(_progressivo)}", quando, oggetto, corredo, copia, tempo, now_iso()),
    ).lastrowid
    if cielo is not None:
        conn.execute(
            "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
            " height_deg, rotation_deg, solved_at) VALUES(?, ?, ?, 2.0, ?, ?, 0.0, 'now')",
            (frame_id, *cielo, *campo),
        )
    mosaic.place(conn, [frame_id])
    return frame_id


def proposti(conn):
    return [asdict(m) for m in proposte.candidates(conn)]


def chiavi(trovati):
    return [(m["object"], m["panels"], m["frames"]) for m in trovati]


def rispondi(conn, value, riga=0):
    trovato = proposti(conn)[riga]
    mosaic.write_answer(conn, trovato["key"], value)
    return trovato


def chiave_di(conn, frame_id):
    return conn.execute("SELECT mosaic_key FROM frames WHERE id = ?", (frame_id,)).fetchone()[0]


# --- cosa si raggruppa ----------------------------------------------------------------------


def test_two_panels_side_by_side_are_a_mosaic(archivio):
    """Il caso per cui tutto questo esiste: due inquadrature affiancate riprese con lo stesso
    corredo sono un mosaico da proporre, con quanti pannelli e quante pose."""
    prepara(archivio)
    prima = posa(archivio, A)
    posa(archivio, B)
    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]
    impronta = archivio.execute("SELECT frame_hash FROM frames WHERE id = ?", (prima,)).fetchone()
    assert proposti(archivio)[0]["key"] == impronta[0], "la chiave e' la posa piu' vecchia"


def test_panels_without_the_rotation_still_make_a_mosaic(archivio):
    """The solver may leave the rotation out: grouping places the frame on the circle around its
    field instead of dropping the panel (the geometry's side is `test_mosaic_geometry.py`)."""
    prepara(archivio)
    for cielo in (A, B):
        frame_id = posa(archivio, None)
        archivio.execute(
            "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
            " height_deg, rotation_deg, solved_at) VALUES(?, ?, ?, 2.0, 0.6, 0.4, NULL, 'now')",
            (frame_id, *cielo),
        )
        mosaic.place(archivio, [frame_id])
    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]


def test_a_vertical_strip_is_a_mosaic_whatever_field_comes_first(archivio):
    """I pannelli uno sopra l'altro, in declinazione, con campi di misura diversa: la fascia in cui
    si cercano i vicini tiene conto del campo piu' largo, chiunque arrivi per primo."""
    prepara(archivio)
    posa(archivio, A, campo=(0.2, 0.2))
    posa(archivio, (A[0], A[1] + 0.5), campo=(1.2, 1.0))
    posa(archivio, A, corredo=2, campo=(1.2, 1.0))
    posa(archivio, (A[0], A[1] + 0.5), corredo=2, campo=(0.2, 0.2))
    assert [m["panels"] for m in proposti(archivio)] == [2, 2]


def test_a_mosaic_sums_the_hours_of_its_panels(archivio):
    """**La promessa del contratto**: le ore sono la **somma** dei pannelli. I due pannelli hanno
    un numero di pose diverso apposta: con due pannelli uguali la somma e il doppio del primo si
    assomiglierebbero troppo per distinguere le due regole."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    posa(archivio, B, quando=ALTRA_NOTTE)
    riga = proposti(archivio)[0]
    assert (riga["panels"], riga["frames"]) == (2, 3)
    assert riga["integration_s"] == 3 * TEMPO


def test_the_two_readers_count_the_same_hours_on_the_same_archive(archivio):
    """Le ore di un mosaico e quelle dei suoi oggetti sono due somme scritte in due posti: questa
    prova le fa girare sullo stesso archivio. Le pose mute sono **due** e quella da zero secondi
    **una**: con una e una, chi scambiasse le due regole otterrebbe 1 da tutte e due le parti."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, A, tempo=None)
    posa(archivio, B, tempo=None, quando=ALTRA_NOTTE)
    posa(archivio, B, tempo=0.0, quando=ALTRA_NOTTE)
    riga = proposti(archivio)[0]
    oggetti = [o for o in obj.listing(archivio) if o["frames"]]
    assert riga["integration_s"] == sum(o["integration_s"] for o in oggetti)
    assert riga["untimed"] == sum(o["untimed"] for o in oggetti)


def test_a_panel_pose_that_does_not_say_its_time_is_not_zero_hours(archivio):
    """Una posa che non dice il tempo non vale zero: si conta a parte."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B, tempo=None)
    riga = proposti(archivio)[0]
    assert (riga["frames"], riga["integration_s"], riga["untimed"]) == (2, TEMPO, 1)


def test_panels_identified_as_different_objects_are_one_mosaic(archivio):
    """Ogni pannello inquadra una parte diversa del complesso e l'app li identifica come oggetti
    diversi: il mosaico li raccoglie lo stesso, e li elenca tutti."""
    prepara(archivio)
    posa(archivio, A, oggetto=1)
    posa(archivio, B, oggetto=2)
    (riga,) = proposti(archivio)
    assert (riga["object"], riga["panels"]) == ("IC 401, IC 402", 2)


def test_a_subject_without_a_name_is_said_with_its_key(archivio):
    """Un oggetto senza nome e fuori catalogo non ha un nome da mostrare: si dice con la sua chiave,
    invece di un buco nella riga -- o di un `sorted` che salta mescolando `None` e testo."""
    prepara(archivio)
    archivio.execute(
        "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence, created_at)"
        " VALUES(3, 'fuori-catalogo', 'coord_confirmed', 'certain', ?)",
        (now_iso(),),
    )
    posa(archivio, A, oggetto=1)
    posa(archivio, B, oggetto=3)
    assert proposti(archivio)[0]["object"] == "IC 401, fuori-catalogo"


def test_one_framing_shot_many_times_is_not_a_mosaic(archivio):
    """Il dithering sposta la posa di pochi secondi d'arco: e' la stessa foto rifatta."""
    prepara(archivio)
    for cielo in (A, DITHERATA, A, DITHERATA):
        posa(archivio, cielo)
    assert proposti(archivio) == []


def test_the_same_framing_at_another_size_is_not_a_mosaic(archivio):
    """Lo stesso centro con un campo piu' largo contiene l'altro: non e' un pannello accanto."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, A, campo=(1.2, 0.8))
    assert proposti(archivio) == []


def test_panels_from_different_nights_are_the_same_mosaic(archivio):
    """Un mosaico si riprende in piu' sere: la notte non lo spezza."""
    prepara(archivio)
    posa(archivio, A, quando=NOTTE)
    posa(archivio, B, quando=ALTRA_NOTTE)
    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]


def test_another_rig_is_another_production(archivio):
    """Corredi diversi sono due progetti, anche sullo stesso cielo."""
    prepara(archivio)
    posa(archivio, A, corredo=1)
    posa(archivio, B, corredo=2)
    assert proposti(archivio) == []


def test_a_far_region_is_another_mosaic_not_this_one(archivio):
    """Due regioni lontane dello stesso corredo sono due mosaici, e un campo lontano non entra."""
    prepara(archivio)
    for cielo in (A, B, LONTANO, ACCANTO_A_LONTANO):
        posa(archivio, cielo)
    assert [m["panels"] for m in proposti(archivio)] == [2, 2]


def test_a_strip_of_three_panels_is_one_mosaic(archivio):
    """Il legame e' transitivo: in una striscia il primo e il terzo non si toccano, e a legarli e'
    quello in mezzo. Senza, il mosaico si spezzerebbe in due."""
    prepara(archivio)
    for cielo in (A, C, B):
        posa(archivio, cielo)
    assert [m["panels"] for m in proposti(archivio)] == [3]


def test_a_single_panel_is_not_a_mosaic(archivio):
    """Un'inquadratura sola e' un soggetto ripreso normalmente: proporla sarebbe una domanda senza
    risposta possibile."""
    prepara(archivio)
    posa(archivio, A)
    assert proposti(archivio) == []


def test_a_chain_of_small_steps_does_not_walk_across_the_sky(archivio):
    """Un pannello si misura sulla posa che l'ha aperto: cinque pose a 0,08 gradi l'una dall'altra
    non camminano fino a inghiottire il pannello accanto."""
    prepara(archivio)
    for passo in range(5):
        posa(archivio, (A[0] + passo * 0.097, A[1]))
    pannelli = {r[0] for r in archivio.execute("SELECT panel_id FROM frames")}
    assert len(pannelli) > 1


def test_a_pose_without_sky_does_not_break_the_others(archivio):
    """Senza coordinate non si sa dove guardasse: resta fuori, e le altre si raggruppano."""
    prepara(archivio)
    senza = posa(archivio, None)
    posa(archivio, A)
    posa(archivio, B)
    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]
    assert (
        archivio.execute("SELECT panel_id FROM frames WHERE id = ?", (senza,)).fetchone()[0] is None
    )


def test_a_calibrated_copy_is_not_another_pose(archivio):
    """La copia calibrata non e' un'altra posa, come in tutto il resto dell'archivio."""
    prepara(archivio)
    grezzo = posa(archivio, A)
    posa(archivio, A, copia=grezzo)
    posa(archivio, B)
    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]


def test_a_mosaic_whose_rig_is_unknown_is_proposed_all_the_same(archivio):
    """Le pose che non dicono la camera fanno i loro mosaici come le altre."""
    prepara(archivio)
    posa(archivio, A, corredo=None)
    posa(archivio, B, corredo=None)
    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]


# --- scritto una volta ----------------------------------------------------------------------


def test_placing_again_does_not_redo_the_geometry(archivio, monkeypatch):
    """**La regola di Marco** (23/9/2026): scritto, non si ricalcola. Una posa che ripassa da
    `group` resta nel suo pannello senza nessun confronto fra campi."""
    prepara(archivio)
    pose = [posa(archivio, A), posa(archivio, B)]

    def esplode(*_args):
        raise AssertionError("la geometria e' ripartita su una posa gia' piazzata")

    monkeypatch.setattr(mosaic, "overlap", esplode)
    monkeypatch.setattr(mosaic, "same_pointing", esplode)
    mosaic.place(archivio, pose)

    assert chiavi(proposti(archivio)) == [("IC 401", 2, 2)]


def test_a_new_pose_is_compared_only_with_nearby_panels(archivio, monkeypatch):
    """Una posa nuova non si confronta con l'archivio intero: solo coi pannelli del suo corredo
    che potrebbero toccarla. Un pannello a 20 gradi di declinazione non entra nel conto."""
    prepara(archivio)
    posa(archivio, (A[0], A[1] + 20))
    posa(archivio, A)
    guardati = []
    vero = mosaic.same_pointing
    monkeypatch.setattr(
        mosaic, "same_pointing", lambda a, b: guardati.append(a["id"]) or vero(a, b)
    )

    posa(archivio, B)

    lontano = archivio.execute("SELECT id FROM panels WHERE dec_deg > 50").fetchone()[0]
    assert guardati and lontano not in guardati


def test_the_proposal_is_the_catalog_object_at_the_centre(archivio):
    """Il campo arriva compilato con la voce del catalogo in cui cade il centro del mosaico: qui
    IC 405, anche se le pose sono identificate come IC 401 -- e' il catalogo a dirlo, non loro."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    (riga,) = proposti(archivio)
    assert riga["proposed"] == "IC 405"
    assert "IC 405" in riga["names"]


def test_the_proposal_is_the_object_that_holds_the_centre_not_the_nearest(archivio):
    """Il centro cade a 6 primi da M 32, che e' piu' piccolo e non lo contiene, e dentro M 31: la
    proposta e' M 31, la voce in cui il centro cade, non la piu' vicina."""
    prepara(archivio)
    posa(archivio, (10.343213, 40.965278))
    posa(archivio, (11.005371, 40.965278))
    (riga,) = proposti(archivio)
    assert riga["proposed"] == "M 31"


def test_without_an_answer_a_mosaic_is_still_a_question(archivio):
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    (riga,) = proposti(archivio)
    assert riga["answer"] is None


def test_confirming_a_mosaic_is_an_answer_that_lasts(archivio):
    """Si risponde una volta sola: il si' resta, col nome, e la domanda si chiude."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    rispondi(archivio, SI)
    posa(archivio, LONTANO)
    (riga,) = proposti(archivio)
    assert (riga["answer"], riga["answer_name"]) == (decl.MosaicAnswer.YES, "IC 405")


def test_a_refused_mosaic_is_not_asked_again(archivio):
    """Un no e' una risposta come un si': resta scritta sulla riga del mosaico."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    rispondi(archivio, decl.MosaicAnswer.NO)
    (riga,) = proposti(archivio)
    assert riga["answer"] == decl.MosaicAnswer.NO


def test_an_answer_nobody_can_read_is_no_answer(archivio):
    """Un valore che non e' ne' un no ne' un bersaglio l'ha scritto qualcosa che non e' passata
    di qui: darlo per buono spegnerebbe una domanda su un dato illeggibile."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    rispondi(archivio, "forse")
    (riga,) = proposti(archivio)
    assert riga["answer"] is None


def test_an_unknown_mosaic_is_refused(archivio):
    """Rispondere a un mosaico che non c'e' e' una pagina vecchia: lo si dice invece di scrivere."""
    with pytest.raises(LookupError):
        mosaic.write_answer(archivio, "nessuno", SI)


def test_the_answer_holds_when_the_mosaic_grows(archivio):
    """Un pannello ripreso dopo entra nel mosaico gia' confermato, e porta la sua chiave."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    rispondi(archivio, SI)
    nuovo = posa(archivio, C, quando=ALTRA_NOTTE)
    (riga,) = proposti(archivio)
    assert (riga["panels"], riga["answer"]) == (3, decl.MosaicAnswer.YES)
    assert chiave_di(archivio, nuovo) == riga["key"]


def test_an_answer_does_not_silence_another_mosaic_of_the_same_rig(archivio):
    """Un corredo ha una risposta per ognuna delle sue regioni."""
    prepara(archivio)
    for cielo in (A, B, LONTANO, ACCANTO_A_LONTANO):
        posa(archivio, cielo)
    rispondi(archivio, SI)
    assert [m["answer"] for m in proposti(archivio)] == [decl.MosaicAnswer.YES, None]


def test_an_answer_does_not_silence_another_rig(archivio):
    """La stessa regione ripresa con un'altra attrezzatura e' un'altra produzione, e resta una
    domanda sua."""
    prepara(archivio)
    for corredo in (1, 2):
        posa(archivio, A, corredo=corredo)
        posa(archivio, B, corredo=corredo)
    rispondi(archivio, SI, riga=0)
    assert [m["answer"] for m in proposti(archivio)] == [decl.MosaicAnswer.YES, None]


def test_a_confirmed_mosaic_is_written_on_its_poses(archivio):
    """Il si' si scrive sulle pose del mosaico, e su quelle soltanto."""
    prepara(archivio)
    dentro = [posa(archivio, A), posa(archivio, B)]
    fuori = posa(archivio, LONTANO)
    riga = rispondi(archivio, SI)
    assert [chiave_di(archivio, p) for p in dentro] == [riga["key"]] * 2
    assert chiave_di(archivio, fuori) is None


def test_an_object_inside_and_outside_a_mosaic_keeps_its_own_poses(archivio):
    """Lo stesso oggetto ripreso dentro un mosaico e poi da solo, con un altro corredo: solo le
    pose del mosaico stanno nel mosaico."""
    prepara(archivio)
    dentro = [posa(archivio, A, oggetto=1), posa(archivio, B, oggetto=2)]
    da_solo = posa(archivio, A, oggetto=1, corredo=2)
    rispondi(archivio, SI)
    assert all(chiave_di(archivio, p) for p in dentro)
    assert chiave_di(archivio, da_solo) is None


def test_dissolving_a_confirmed_mosaic_frees_its_panels(archivio):
    """Dal si' al no: le pose tornano ai loro oggetti."""
    prepara(archivio)
    pose = [posa(archivio, A), posa(archivio, B)]
    rispondi(archivio, SI)
    rispondi(archivio, decl.MosaicAnswer.NO)
    assert [chiave_di(archivio, p) for p in pose] == [None, None]


def test_the_page_reads_the_name_that_was_answered(archivio):
    """Il nome del mosaico e' quello che l'utente ha detto, non quello proposto."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B, oggetto=2)
    rispondi(archivio, "name:La mia regione")
    (riga,) = proposti(archivio)
    assert (riga["answer"], riga["answer_name"]) == (decl.MosaicAnswer.YES, "La mia regione")
