"""L'attrezzatura che `normalize` ricava dall'header: i pezzi, e il corredo che ne esce.

E' la meta' dell'attrezzatura delle prove di `normalize` -- i filtri, le regole imparate, la
copia calibrata e lo stadio come stadio stanno in `test_normalize.py`. Una regola, un test che
si rompe se la regola si rompe.

Tre di questi vengono da `test_normalize.py`, spostati e non tolti, quando quel file ha superato
il tetto di righe (il quarto, quello sulla montatura, nasce qui):
test-tolto: test_normalize_makes_instruments_and_rigs
test-tolto: test_normalize_groups_focal_lengths_within_five_percent
test-tolto: test_normalize_links_every_frame_to_its_rig
"""

import pytest

from astrolog.spine import gear
from astrolog.spine import rigs as corredi
from astrolog.vocab.software import ASIAIR as SW_ASIAIR
from conftest import frame_by_file, one, rows, run_normalize


def test_normalize_makes_instruments_and_rigs(conn, archive):
    """Ottica e camera vengono da TELESCOP e INSTRUME, e il corredo e' la coppia a una focale.
    Le ottiche sono TRE e non quattro: cio' che l'ASIAIR scrive in TELESCOP e' una montatura, e
    sta fra le montature (la regola e' qui sotto, `test_the_mount_asiair_writes_in_telescop...`)."""
    optics_names = sorted(
        r["name"] for r in rows(conn, "SELECT name FROM instruments WHERE kind='optics'")
    )
    assert optics_names == ["Askar 103Apo", "RC8", "TS 130 APO"]
    cameras = sorted(
        r["name"] for r in rows(conn, "SELECT name FROM instruments WHERE kind='camera'")
    )
    assert cameras == ["ASI2600MM Pro", "ATR2600M", "ATR2600M(USB2.0)", "Canon EOS 700D", "QHY268M"]
    assert one(conn, "SELECT COUNT(*) FROM instruments WHERE detected = 0") == 0
    # la camera a colori si riconosce dalla matrice, mai dal nome
    assert one(conn, "SELECT camera_type FROM instruments WHERE name = 'Canon EOS 700D'") == "color"
    assert one(conn, "SELECT camera_type FROM instruments WHERE name = 'QHY268M'") is None
    # la dimensione del pixel arriva dall'header, gia' compilata
    assert (
        one(conn, "SELECT pixel_size_um FROM instruments WHERE name = 'ATR2600M(USB2.0)'") == 3.76
    )
    assert one(conn, "SELECT pixel_size_um FROM instruments WHERE name = 'Canon EOS 700D'") == 4.29
    # chi non dichiara il binning non dice quale pixel fisico sia: la scheda resta da compilare
    assert one(conn, "SELECT pixel_size_um FROM instruments WHERE name = 'QHY268M'") is None


def test_the_pieces_a_frame_names_come_from_the_header_too(conn, archive):
    """**Non solo ottica e camera.** N.I.N.A. scrive la ruota portafiltri (`FWHEEL`) e il
    focheggiatore (`FOCNAME`), l'ASIAIR la camera di guida (`GUIDECAM`) -- e' negli header veri che
    teniamo in `tests/header/`. Prima l'app li ignorava, e chi li possedeva doveva scriverli a
    mano. Nascono **rilevati**, come ogni pezzo che viene dai file."""
    trovati = {
        r["kind"]: r["name"]
        for r in rows(
            conn,
            "SELECT kind, name FROM instruments"
            " WHERE kind IN ('filter_wheel', 'focuser', 'guide_camera')",
        )
    }

    assert trovati == {
        "filter_wheel": "ASCOM ToupTek FilterWheel",
        "focuser": "ASCOM ToupTek AAF",
        "guide_camera": "ZWO ASI120MM-S",
    }
    assert one(conn, "SELECT COUNT(*) FROM instruments WHERE kind = 'guide_scope'") == 0


def test_every_frame_says_which_of_them_it_used(conn, archive):
    """E' la differenza con la montatura: questi i file li legano alla **singola posa**, quindi le
    loro ore si sanno. Una posa di N.I.N.A. porta ruota e focheggiatore, una dell'ASIAIR la camera
    di guida -- e nessuna delle due porta quello che il suo programma non scrive."""
    nina = frame_by_file(conn, "L_001.fits")
    asiair = frame_by_file(conn, "Light_001.fits")

    assert nina["filter_wheel_id"] is not None
    assert nina["focuser_id"] is not None
    assert nina["guide_camera_id"] is None  # N.I.N.A. non la scrive
    assert asiair["guide_camera_id"] is not None
    assert asiair["filter_wheel_id"] is None  # l'ASIAIR non la scrive


def test_changing_one_of_them_does_not_make_a_second_rig(conn, archive):
    """**Non entrano nell'impronta del corredo.** Due pose con la stessa ottica, la stessa camera e
    la stessa focale ma due ruote diverse sono **un** corredo, non due: infilare la ruota
    nell'impronta spezzerebbe in due l'archivio di chi ne cambia una, senza che abbia cambiato
    telescopio. E' la decisione centrale della fetta, e prima viveva solo in un commento."""
    uno = frame_by_file(conn, "L_001.fits")
    altro = frame_by_file(conn, "R_001.fits")
    conn.execute(
        "UPDATE frames SET filter_wheel_raw = 'Un altra ruota', filter_wheel_id = NULL"
        " WHERE id = ?",
        (altro["id"],),
    )
    corredi_prima = one(conn, "SELECT COUNT(*) FROM rigs")

    from astrolog.spine import normalize
    from astrolog.spine.stages import invalidate

    invalidate(conn, [altro["id"]], "normalize")  # la posa torna in coda, come dopo una risposta
    conn.commit()
    esito = list(normalize.normalize_frames(conn))[-1]  # e' un generatore: va consumato
    assert esito["errors"] == 0, esito

    dopo = frame_by_file(conn, "R_001.fits")
    # la ruota nuova e' nata -- cioe' quella posa e' stata davvero rinormalizzata...
    assert one(conn, "SELECT COUNT(*) FROM instruments WHERE name = 'Un altra ruota'") == 1
    assert dopo["filter_wheel_id"] != uno["filter_wheel_id"]
    # ...e il corredo e' rimasto lo stesso, che e' la regola
    assert one(conn, "SELECT COUNT(*) FROM rigs") == corredi_prima
    assert dopo["rig_id"] == uno["rig_id"]


def test_renaming_one_of_them_teaches_the_old_spelling(conn, archive):
    """Rinominare la propria ruota deve **imparare la grafia dell'header**, come per un telescopio:
    senza, alla prima notte nuova quel nome rinasce e uno si ritrova la ruota doppia, con le ore
    spartite fra due righe e nessun modo di unirle dalla pagina."""
    from astrolog.spine import gear

    ruota = one(conn, "SELECT id FROM instruments WHERE kind = 'filter_wheel'")
    gear.declare_instrument(conn, ruota, {"name": "EFW 7x36"})
    conn.commit()

    imparate = [
        r["target_key"]
        for r in rows(conn, "SELECT target_key FROM header_aliases WHERE kind = 'filter_wheel'")
    ]
    assert imparate == ["EFW 7x36"]


def test_normalize_groups_focal_lengths_within_five_percent(conn, archive):
    """559, 560 e 561 mm sono la stessa focale: un corredo, non tre."""
    rig_ids = {frame_by_file(conn, n)["rig_id"] for n in ("L_001.fits", "L_003.fits", "L_004.fits")}
    assert len(rig_ids) == 1
    # ma due ottiche diverse restano due corredi, e 910 non e' 560
    assert one(conn, "SELECT COUNT(*) FROM rigs") == 5


def test_normalize_links_every_frame_to_its_rig(conn, archive):
    assert one(conn, "SELECT COUNT(*) FROM frames WHERE rig_id IS NULL") == 0
    askar = one(
        conn,
        "SELECT COUNT(*) FROM frames f JOIN rigs r ON r.id = f.rig_id"
        " JOIN instruments o ON o.id = r.optics_id WHERE o.name = 'Askar 103Apo'",
    )
    assert askar == 9  # gli otto N.I.N.A. piu' la copia riscritta


def test_the_mount_asiair_writes_in_telescop_is_not_an_optics(conn, archive):
    """**La regola.** Quando il file lo ha scritto l'ASIAIR, `TELESCOP` porta la MONTATURA: il
    pezzo nasce montatura e non ottica, e il corredo di quelle pose resta **senza ottica**
    finche' l'utente non dice quale fosse.

    Il criterio e' il **software**, non il nome. Il banco porta due montature diverse dallo
    stesso programma -- `EQMod Mount` e `ZWO AM3`, tutte e due vere e di due utenti diversi
    (`tests/header/asiair_am3.txt`) -- e una regola scritta su una lista di nomi passerebbe con
    la prima e cadrebbe sulla seconda. Le ottiche degli altri tre software non si toccano."""
    montature = sorted(
        r["name"] for r in rows(conn, "SELECT name FROM instruments WHERE kind='mount'")
    )
    assert montature == ["EQMod Mount", "ZWO AM3"]
    ottiche = {r["name"] for r in rows(conn, "SELECT name FROM instruments WHERE kind='optics'")}
    assert ottiche == {"Askar 103Apo", "RC8", "TS 130 APO"}

    # Le pose ASIAIR stanno in UN corredo solo: due nomi di montatura non fanno due corredi, ed
    # e' il danno che questa regola toglie.
    corredi = rows(
        conn,
        "SELECT DISTINCT r.id, r.optics_id, r.camera_id FROM frames f"
        " JOIN rigs r ON r.id = f.rig_id WHERE f.software = ?",
        (SW_ASIAIR,),
    )
    assert len(corredi) == 1
    assert corredi[0]["optics_id"] is None
    camera = one(conn, "SELECT name FROM instruments WHERE id = ?", (corredi[0]["camera_id"],))
    assert camera == "Canon EOS 700D"


def _montatura(conn, nome):
    return one(conn, "SELECT id FROM instruments WHERE kind = 'mount' AND name = ?", (nome,))


def _corredo_di(conn, file):
    return frame_by_file(conn, file)["rig_id"]


def test_the_mount_the_files_name_is_carried_by_every_frame(conn, archive):
    """Dove il programma la scrive, la montatura sta **sulla posa**, come la ruota: le due pose
    ASIAIR dello stesso corredo ne nominano due diverse, e ognuna tiene la sua. Una posa di un
    programma che non la scrive non ne ha nessuna, invece di una indovinata."""
    assert frame_by_file(conn, "Light_001.fits")["mount_id"] == _montatura(conn, "EQMod Mount")
    assert frame_by_file(conn, "Light_002.fits")["mount_id"] == _montatura(conn, "ZWO AM3")
    assert frame_by_file(conn, "L_001.fits")["mount_id"] is None


def test_a_mount_declared_on_a_rig_is_carried_by_all_its_frames(conn, archive):
    """Dove i file tacciono la dici tu, sul corredo: vale per tutte le sue pose, dopo che la spina
    le ha rilavorate."""
    rig = _corredo_di(conn, "L_001.fits")
    am3 = _montatura(conn, "ZWO AM3")
    rilavorate = corredi.declare_mount(conn, rig, am3)
    run_normalize(conn)

    assert rilavorate
    montate = {
        r["mount_id"] for r in rows(conn, "SELECT mount_id FROM frames WHERE rig_id = ?", (rig,))
    }
    assert montate == {am3}


def test_what_you_declare_wins_over_the_mount_the_files_name(conn, archive):
    rig = _corredo_di(conn, "Light_001.fits")
    am3 = _montatura(conn, "ZWO AM3")
    corredi.declare_mount(conn, rig, am3)
    run_normalize(conn)
    assert frame_by_file(conn, "Light_001.fits")["mount_id"] == am3

    # e tolta la tua parola, torna quella dei file
    corredi.declare_mount(conn, rig, None)
    run_normalize(conn)
    assert frame_by_file(conn, "Light_001.fits")["mount_id"] == _montatura(conn, "EQMod Mount")


def test_only_a_mount_can_be_the_mount_of_a_rig(conn, archive):
    rig = _corredo_di(conn, "L_001.fits")
    ottica = one(conn, "SELECT id FROM instruments WHERE kind = 'optics' LIMIT 1")
    with pytest.raises(corredi.NotAMountError):
        corredi.declare_mount(conn, rig, ottica)


def test_a_mount_renamed_or_merged_stays_the_mount_of_its_rigs(conn, archive):
    """La tua parola porta il **nome** della montatura, che sopravvive a una nuova lettura: se la
    rinomini o la unisci a un'altra, il corredo la segue invece di restare senza."""
    rig = _corredo_di(conn, "L_001.fits")
    corredi.declare_mount(conn, rig, _montatura(conn, "ZWO AM3"))
    gear.declare_instrument(conn, _montatura(conn, "ZWO AM3"), {"name": "AM3 di casa"})
    gear.merge_instrument(conn, _montatura(conn, "AM3 di casa"), _montatura(conn, "EQMod Mount"))
    run_normalize(conn)

    montate = {
        r["mount_id"] for r in rows(conn, "SELECT mount_id FROM frames WHERE rig_id = ?", (rig,))
    }
    assert montate == {_montatura(conn, "EQMod Mount")}


def test_a_new_mount_the_files_name_is_born_even_on_a_rig_you_gave_one(conn, archive):
    """La tua parola sceglie cosa va sulla posa, non cancella un pezzo: una montatura nuova scritta
    dall'ASIAIR nasce in Attrezzatura anche se a quel corredo ne hai data un'altra."""
    rig = _corredo_di(conn, "Light_001.fits")
    corredi.declare_mount(conn, rig, _montatura(conn, "ZWO AM3"))
    conn.execute("UPDATE frames SET telescope_raw = 'ZWO AM5' WHERE rig_id = ?", (rig,))
    run_normalize(conn)

    assert _montatura(conn, "ZWO AM5") is not None
    assert frame_by_file(conn, "Light_001.fits")["mount_id"] == _montatura(conn, "ZWO AM3")


def test_with_one_mount_only_a_rig_the_files_do_not_name_stays_without(conn, archive):
    """Nessuna montatura si indovina: anche se ne possiedi una sola, un corredo che i file non
    legano a niente e a cui non l'hai data resta senza."""
    conn.execute(
        "UPDATE frames SET mount_id = NULL, telescope_raw = 'EQMod Mount'"
        " WHERE telescope_raw = 'ZWO AM3'"
    )
    conn.execute("DELETE FROM instruments WHERE kind = 'mount' AND name = 'ZWO AM3'")
    conn.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'normalize'")
    run_normalize(conn)
    assert one(conn, "SELECT COUNT(*) FROM instruments WHERE kind = 'mount'") == 1
    assert frame_by_file(conn, "L_001.fits")["mount_id"] is None


def test_a_frame_without_a_rig_still_takes_the_mount_its_file_names(conn, archive):
    from astrolog.spine.normalize_rig import mount_for_frame

    conti = {"instruments": 0}
    montatura = mount_for_frame(conn, {"telescope_raw": "ZWO AM3"}, None, SW_ASIAIR, conti, "ora")
    assert montatura == _montatura(conn, "ZWO AM3")


def test_two_rigs_that_become_one_keep_the_mount_of_the_one_kept(conn, archive):
    """Unite due grafie della stessa camera, due corredi diventano uno: vince la montatura che
    avevi dato al corredo che resta, come vince il suo nome."""
    vecchia = one(conn, "SELECT id FROM instruments WHERE kind = 'camera' AND name = 'ATR2600M'")
    tenuta = one(
        conn, "SELECT id FROM instruments WHERE kind = 'camera' AND name = 'ATR2600M(USB2.0)'"
    )
    via = one(conn, "SELECT id FROM rigs WHERE camera_id = ?", (vecchia,))
    resta = one(conn, "SELECT id FROM rigs WHERE camera_id = ?", (tenuta,))
    corredi.declare_mount(conn, via, _montatura(conn, "ZWO AM3"))
    corredi.declare_mount(conn, resta, _montatura(conn, "EQMod Mount"))
    gear.merge_instrument(conn, vecchia, tenuta)
    run_normalize(conn)

    dette = rows(
        conn, "SELECT value FROM declarations WHERE entity_type = 'rig' AND field = 'mount'"
    )
    assert [r["value"] for r in dette] == ["EQMod Mount"]
    montate = {
        r["mount_id"]
        for r in rows(
            conn,
            "SELECT f.mount_id FROM frames f JOIN rigs g ON g.id = f.rig_id WHERE g.camera_id = ?",
            (tenuta,),
        )
    }
    assert montate == {_montatura(conn, "EQMod Mount")}


def test_the_same_mount_again_sends_nothing_back_to_be_read(conn, archive):
    """Ridare la montatura che il corredo ha gia', o toglierne una che non c'e', non cambia niente:
    nessuna posa torna in coda, e il giro non riparte per niente."""
    rig = _corredo_di(conn, "L_001.fits")
    am3 = _montatura(conn, "ZWO AM3")
    assert corredi.declare_mount(conn, rig, am3)
    run_normalize(conn)

    assert corredi.declare_mount(conn, rig, am3) == []
    assert corredi.declare_mount(conn, _corredo_di(conn, "Light_001.fits"), None) == []


def test_a_frame_that_reaches_the_mount_two_ways_counts_once(conn, archive):
    """Data sul corredo la stessa montatura che il file nomina, la posa ci arriva per due strade:
    le ore della montatura restano quelle delle sue pose, una volta ciascuna."""
    from astrolog.spine import gear_usage

    rig = _corredo_di(conn, "Light_001.fits")
    eqmod = _montatura(conn, "EQMod Mount")
    corredi.declare_mount(conn, rig, eqmod)
    run_normalize(conn)
    gear_usage.write(conn)

    pose = one(conn, "SELECT COUNT(*) FROM frames WHERE mount_id = ? AND copy_of IS NULL", (eqmod,))
    contate = one(
        conn,
        "SELECT frames FROM gear_usage WHERE subject = 'instrument' AND subject_id = ?",
        (eqmod,),
    )
    assert pose == 3
    assert contate == pose
