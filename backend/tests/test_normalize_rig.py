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

import random

import pytest

from astrolog.db.connect import connect, create_database
from astrolog.spine import gear, gear_create
from astrolog.spine import rigs as corredi
from astrolog.spine.scan import scan_folder
from astrolog.vocab.software import Software
from conftest import add_folder, frame_by_file, one, rows, run_normalize, write_light


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
        (Software.ASIAIR,),
    )
    assert len(corredi) == 1
    assert corredi[0]["optics_id"] is None
    camera = one(conn, "SELECT name FROM instruments WHERE id = ?", (corredi[0]["camera_id"],))
    assert camera == "Canon EOS 700D"


def _montatura(conn, nome):
    return one(conn, "SELECT id FROM instruments WHERE kind = 'mount' AND name = ?", (nome,))


def _corredo_di(conn, file):
    return frame_by_file(conn, file)["rig_id"]


def _monta(conn, rig, montatura):
    return corredi.declare_part(conn, rig, "mount", montatura)


def _nuovo(conn, genere, nome):
    return gear_create.instrument(conn, genere, nome, "ora", detected=False)


def _portati(conn, colonna, rig):
    return {r[colonna] for r in rows(conn, "SELECT * FROM frames WHERE rig_id = ?", (rig,))}


@pytest.mark.parametrize("genere", ["reducer", "guide_scope"])
def test_a_part_the_files_never_name_is_carried_once_you_choose_it(conn, archive, genere):
    """Riduttore e ottica di guida nessun programma li scrive: scelti sul corredo, stanno su tutte
    le sue pose, e tolta la scelta le pose tornano senza."""
    rig = _corredo_di(conn, "L_001.fits")
    pezzo = _nuovo(conn, genere, "Scelto da me")
    assert corredi.declare_part(conn, rig, genere, pezzo)
    run_normalize(conn)
    assert _portati(conn, f"{genere}_id", rig) == {pezzo}

    assert corredi.declare_part(conn, rig, genere, None)
    run_normalize(conn)
    assert _portati(conn, f"{genere}_id", rig) == {None}


def test_a_wheel_you_choose_fills_only_the_frames_whose_file_is_silent(conn, archive):
    """Cio' che il file nomina resta (si rinomina, non si sostituisce): la ruota scelta sul corredo
    vale solo sulle pose che non ne nominano una. La montatura ha la regola opposta, qui sopra."""
    nominate = {
        r["id"]: (r["rig_id"], r["filter_wheel_id"])
        for r in rows(
            conn,
            "SELECT id, rig_id, filter_wheel_id FROM frames"
            " WHERE filter_wheel_id IS NOT NULL AND rig_id IS NOT NULL",
        )
    }
    assert nominate, "l'archivio di prova deve avere pose che nominano la ruota"
    muto = _corredo_di(conn, "Light_001.fits")
    assert _portati(conn, "filter_wheel_id", muto) == {None}
    mia = _nuovo(conn, "filter_wheel", "Ruota manuale")
    for rig in {muto, *(rig for rig, _ in nominate.values())}:
        corredi.declare_part(conn, rig, "filter_wheel", mia)
    run_normalize(conn)

    assert _portati(conn, "filter_wheel_id", muto) == {mia}
    dopo = {
        r["id"]: r["filter_wheel_id"]
        for r in rows(
            conn, "SELECT id, filter_wheel_id FROM frames WHERE filter_wheel_id != ?", (mia,)
        )
    }
    assert dopo == {posa: ruota for posa, (_, ruota) in nominate.items()}


def test_a_chosen_part_renamed_stays_the_part_of_its_rig(conn, archive):
    rig = _corredo_di(conn, "L_001.fits")
    riduttore = _nuovo(conn, "reducer", "0,8x")
    corredi.declare_part(conn, rig, "reducer", riduttore)
    gear.declare_instrument(conn, riduttore, {"name": "Riduttore 0,8x"})
    run_normalize(conn)
    assert _portati(conn, "reducer_id", rig) == {riduttore}
    assert corredi.chosen_for(conn, rig) == {"reducer": riduttore}


def test_a_part_must_be_a_piece_of_its_kind(conn, archive):
    rig = _corredo_di(conn, "L_001.fits")
    with pytest.raises(corredi.NotOfKindError):
        corredi.declare_part(conn, rig, "reducer", _montatura(conn, "ZWO AM3"))


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
    rilavorate = _monta(conn, rig, am3)
    run_normalize(conn)

    assert rilavorate
    montate = {
        r["mount_id"] for r in rows(conn, "SELECT mount_id FROM frames WHERE rig_id = ?", (rig,))
    }
    assert montate == {am3}


def test_what_you_declare_wins_over_the_mount_the_files_name(conn, archive):
    rig = _corredo_di(conn, "Light_001.fits")
    am3 = _montatura(conn, "ZWO AM3")
    _monta(conn, rig, am3)
    run_normalize(conn)
    assert frame_by_file(conn, "Light_001.fits")["mount_id"] == am3

    # e tolta la tua parola, torna quella dei file
    _monta(conn, rig, None)
    run_normalize(conn)
    assert frame_by_file(conn, "Light_001.fits")["mount_id"] == _montatura(conn, "EQMod Mount")


def test_only_a_mount_can_be_the_mount_of_a_rig(conn, archive):
    rig = _corredo_di(conn, "L_001.fits")
    ottica = one(conn, "SELECT id FROM instruments WHERE kind = 'optics' LIMIT 1")
    with pytest.raises(corredi.NotOfKindError):
        _monta(conn, rig, ottica)


def test_a_mount_renamed_or_merged_stays_the_mount_of_its_rigs(conn, archive):
    """La tua parola porta il **nome** della montatura, che sopravvive a una nuova lettura: se la
    rinomini o la unisci a un'altra, il corredo la segue invece di restare senza."""
    rig = _corredo_di(conn, "L_001.fits")
    _monta(conn, rig, _montatura(conn, "ZWO AM3"))
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
    _monta(conn, rig, _montatura(conn, "ZWO AM3"))
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
    from astrolog.spine.normalize_rig import carried_by_frame

    conti = {"instruments": 0}
    posa = {
        "telescope_raw": "ZWO AM3",
        "filter_wheel_raw": None,
        "focuser_raw": None,
        "guide_camera_raw": None,
    }
    portati = carried_by_frame(conn, posa, None, Software.ASIAIR, conti, "ora")
    assert portati["mount"] == _montatura(conn, "ZWO AM3")


def test_two_rigs_that_become_one_keep_the_mount_of_the_one_kept(conn, archive):
    """Unite due grafie della stessa camera, due corredi diventano uno: vince la montatura che
    avevi dato al corredo che resta, come vince il suo nome."""
    vecchia = one(conn, "SELECT id FROM instruments WHERE kind = 'camera' AND name = 'ATR2600M'")
    tenuta = one(
        conn, "SELECT id FROM instruments WHERE kind = 'camera' AND name = 'ATR2600M(USB2.0)'"
    )
    via = one(conn, "SELECT id FROM rigs WHERE camera_id = ?", (vecchia,))
    resta = one(conn, "SELECT id FROM rigs WHERE camera_id = ?", (tenuta,))
    _monta(conn, via, _montatura(conn, "ZWO AM3"))
    _monta(conn, resta, _montatura(conn, "EQMod Mount"))
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
    assert _monta(conn, rig, am3)
    run_normalize(conn)

    assert _monta(conn, rig, am3) == []
    assert _monta(conn, _corredo_di(conn, "Light_001.fits"), None) == []


def test_a_frame_that_reaches_the_mount_two_ways_counts_once(conn, archive):
    """Data sul corredo la stessa montatura che il file nomina, la posa ci arriva per due strade:
    le ore della montatura restano quelle delle sue pose, una volta ciascuna."""
    from astrolog.spine import gear_usage

    rig = _corredo_di(conn, "Light_001.fits")
    eqmod = _montatura(conn, "EQMod Mount")
    _monta(conn, rig, eqmod)
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


def _rigs_read_in(tmp_path, rounds, camera="CamK", optics="Ottica K"):
    """Each round writes its frames and reads the folder again; returns the focals per rig.
    A round of (focal, optics, camera) pairs mixes setups."""
    create_database(tmp_path / "a.db")
    conn = connect(tmp_path / "a.db")
    folder = add_folder(conn, tmp_path / "lib")
    for i, focals in enumerate(rounds):
        for j, shot in enumerate(focals):
            setup = shot if isinstance(shot, tuple) else (shot, optics, camera)
            focal, telescope, instrument = setup
            write_light(
                tmp_path / "lib" / f"r{i}_{j}.fits",
                date=f"2024-05-1{i}T2{j}:00:00",
                TELESCOP=telescope,
                INSTRUME=instrument,
                FOCALLEN=float(focal),
            )
        list(scan_folder(conn, folder))
        run_normalize(conn)
    by_rig: dict[int, set[float]] = {}
    for r in rows(conn, "SELECT rig_id, focal_mm_raw FROM frames"):
        by_rig.setdefault(r["rig_id"], set()).add(r["focal_mm_raw"])
    conn.close()
    return sorted(sorted(v) for v in by_rig.values())


@pytest.mark.parametrize(
    "rounds",
    [[[1060], [1000], [1010]], [[1000], [1060], [1010]], [[1010], [1060], [1000]]],
    ids=["1060-1000-1010", "1000-1060-1010", "1010-1060-1000"],
)
def test_the_rig_of_a_frame_does_not_depend_on_the_order_it_was_read(tmp_path, rounds):
    """Lo stesso archivio letto in tre volte, in un ordine qualunque, mette le ore sugli stessi
    setup di quando lo si legge tutto insieme: 1000 e 1010 stanno nel 5%, 1060 no da 1000."""
    insieme = _rigs_read_in(tmp_path / "insieme", [[1060, 1000, 1010]])
    assert insieme == [[1000.0, 1010.0], [1060.0]]
    assert _rigs_read_in(tmp_path / "a-pezzi", rounds) == insieme


def test_another_setup_does_not_split_a_rig_it_has_nothing_to_do_with(tmp_path):
    """I gruppi di focale sono della camera: un frame di un'altra camera a 960 non sposta
    l'ancora dei 1000 e 1040 di CamK, che restano un setup solo."""
    assert _rigs_read_in(tmp_path, [[1000, 1040], [(960, "Ottica Z", "CamZ")]]) == [
        [960.0],
        [1000.0, 1040.0],
    ]


@pytest.mark.parametrize("seed", range(4, 10))
def test_one_group_of_focals_ends_on_one_rig_in_any_order_of_reading(tmp_path, seed):
    """Sei focali di una camera, lette in tre volte a caso: quando i gruppi si spostano due setup
    possono finire nello stesso gruppo, e i frame vanno sul primo. L'ultima lettura (un'altra
    camera) fa ripassare chi e' rimasto fuori posto. Il caso del revisore e' il seme 9."""
    rnd = random.Random(seed)
    focals = rnd.sample([950, 980, 1000, 1010, 1030, 1045, 1060, 1090, 1120], 6)
    a, b = sorted(rnd.sample(range(1, 6), 2))
    insieme = _rigs_read_in(tmp_path / "insieme", [focals])
    rounds = [focals[:a], focals[a:b], focals[b:], [(500, "Ottica Z", "CamZ")]]
    a_pezzi = [rig for rig in _rigs_read_in(tmp_path / "a-pezzi", rounds) if rig != [500.0]]
    assert a_pezzi == insieme, (focals, a, b)
