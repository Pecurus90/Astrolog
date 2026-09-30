"""Le regole della domanda "con che corredo sono state riprese queste pose", provate da sole.

Il gruppo e' la notte piu' i valori dell'header che dicono una camera e un'ottica (Marco,
23/9/2026: "si lavora a frame non cartelle"), la risposta che si rilegge, e le pose che non ci
stanno: qui si guarda la REGOLA, senza API. Che poi l'app la faccia davvero lo guarda
`test_review_rigless.py`.
"""

import json

from astrolog.clock import night_date
from astrolog.spine import declarations as decl
from astrolog.spine import header_asks, rigless
from conftest import add_folder

CAM, OTT = "ZWO ASI2600MM", "Newton 200/800"
NOTTE = "2026-03-14T21:00:00"  # la notte del 14


def _posa(conn, folder_id, rel_path, *, instrument=None, telescope=None, focal=None, copy_of=None,
          date: str | None = NOTTE, size=(6248, 4176), pixel=3.76):  # fmt: skip
    """Una posa con la sua posizione, senza scrivere un FITS: qui si guardano le query."""
    notte = night_date(date)  # come la scrive `scan` senza sito
    # i giudizi sul grezzo, come li scrive la scansione: senza, la posa prenderebbe il ripiego
    giudizi = header_asks.of({"instrument_raw": instrument, "telescope_raw": telescope})
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, instrument_raw, telescope_raw, focal_mm_raw,"
        " copy_of, date_obs, local_night, naxis1, naxis2, pixel_size_um, asks_camera, asks_filter,"
        " names_optics, header_json, created_at)"
        " VALUES(?, 'light', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', 'ora')",
        (
            f"{folder_id}:{rel_path}",
            instrument,
            telescope,
            focal,
            copy_of,
            date,
            notte,
            *size,
            pixel,
            giudizi["asks_camera"],
            giudizi["asks_filter"],
            giudizi["names_optics"],
        ),
    ).lastrowid
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, ?, 1, 1.0, 'ora')",
        (frame_id, folder_id, rel_path),
    )
    return frame_id


def _frame(conn, frame_id):
    return conn.execute("SELECT * FROM frames WHERE id = ?", (frame_id,)).fetchone()


def _chiave(conn, frame_id):
    """La chiave del gruppo di quella posa, come la calcola chi normalizza."""
    return rigless.key_of_frame(conn, _frame(conn, frame_id))


def test_the_group_is_the_night_and_the_header_not_the_folder(conn):
    """Due cartelle con la stessa notte e gli stessi valori sono un gruppo solo; la stessa cartella
    con due notti, o con due sensori diversi nella stessa notte, sono due. La piu' numerosa in
    cima, e la riga dice la notte e i valori, non un percorso."""
    radice = add_folder(conn, "D:/Astro")
    _posa(conn, radice, "M51/a.fits")
    _posa(conn, radice, "M51/b.fits", date="2026-03-15T01:00:00")  # ancora la notte del 14
    _posa(conn, radice, "altra/c.fits")
    _posa(conn, radice, "M51/d.fits", date="2026-03-21T21:00:00")
    _posa(conn, radice, "M51/e.fits", size=(3008, 3008), pixel=3.76)
    righe = [(g["night"], g["width_px"], g["frames"]) for g in rigless.by_group(conn)]
    assert righe == [("2026-03-14", 6248, 3), ("2026-03-14", 3008, 1), ("2026-03-21", 6248, 1)]
    assert rigless.by_group(conn)[0]["pixel_um"] == 3.76


def test_each_value_of_the_key_makes_its_own_group_and_the_row_says_it(conn):
    """Stessa notte, stesso sensore: un altro telescopio o un altro pixel sono un altro gruppo, e la
    riga porta il telescopio come lo scrive il file -- senza, due righe avrebbero lo stesso nome."""
    radice = add_folder(conn, "D:/Astro")
    _posa(conn, radice, "a/a.fits", telescope="AM5")
    _posa(conn, radice, "b/b.fits", telescope="EQ6")
    _posa(conn, radice, "c/c.fits", telescope="AM5", pixel=2.9)
    righe = sorted((g["telescope"], g["pixel_um"]) for g in rigless.by_group(conn))
    assert righe == [("AM5", 2.9), ("AM5", 3.76), ("EQ6", 3.76)]


def test_the_key_is_made_in_one_place_from_what_the_header_says(conn):
    """La chiave si compone da una funzione sola, con la grafia di `TELESCOP` normalizzata come si
    cerca una regola imparata: chi normalizza la posa e la pagina che la chiede arrivano alla stessa
    chiave, e bianchi in piu' non fanno un altro gruppo."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "M51/a.fits", telescope="ZWO AM5")
    b = _posa(conn, radice, "altra/b.fits", telescope="  ZWO AM5 ")
    assert _chiave(conn, a) == _chiave(conn, b)
    assert [g["key"] for g in rigless.by_group(conn)] == [_chiave(conn, a)]


def test_renaming_the_optics_does_not_move_the_key(conn):
    """La chiave e' fatta dai grezzi: rinominare l'ottica che `TELESCOP` nomina cambia cio' che la
    riga propone, non il gruppo, e una risposta gia' data resta dov'e'."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "M51/a.fits", telescope="ZWO AM5")
    prima = _chiave(conn, a)
    conn.execute(
        "INSERT INTO instruments(kind, name, created_at) VALUES('optics', ?, 'ora')", (OTT,)
    )
    decl.learn(conn, "optics", "ZWO AM5", OTT)
    assert _chiave(conn, a) == prima
    assert rigless.by_group(conn)[0]["key"] == prima


def test_only_the_poses_whose_header_does_not_say_the_camera_are_asked(conn):
    """Il gruppo si riconosce dal GREZZO: chi scrive `INSTRUME` non si chiede. E si chiede anche a
    chi porta il telescopio ma non la camera -- l'ASIAIR scrive la montatura in `TELESCOP` -- che e'
    il caso per cui questa domanda esiste."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "notte/a.fits", telescope="ZWO AM5")
    # due camere nella stessa notte: la notte non risolve, e le scarta solo il grezzo che le dice
    _posa(conn, radice, "notte/b.fits", instrument="ZWO ASI533MC", date="2026-03-20T21:00:00")
    _posa(conn, radice, "notte/b2.fits", instrument="ZWO ASI294MM", date="2026-03-20T22:00:00")
    _posa(conn, radice, "notte/c.fits", instrument="   ", telescope="ZWO AM5")  # bianchi: niente
    gruppi = rigless.by_group(conn)
    assert [g["frames"] for g in gruppi] == [2]
    assert gruppi[0]["optics"] == "ZWO AM5"  # cio' che le pose dicono gia': un indizio


def test_a_pose_without_a_date_is_asked_in_a_group_of_its_own(conn):
    """Una posa senza notte si chiede lo stesso, in un gruppo senza notte, e la pagina lo dice. La
    scansione la notte la scrive sempre -- chi non dice la data prende quella del file
    (`test_local_night.py`) -- ma la domanda non deve rompersi su un vuoto."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "notte/a.fits")
    _posa(conn, radice, "notte/b.fits", date=None)
    assert sorted(g["night"] or "" for g in rigless.by_group(conn)) == ["", "2026-03-14"]


def test_a_rewritten_copy_is_not_another_pose_but_comes_back_in_the_queue(conn):
    """Le copie riscritte non si contano a video -- non sono un'altra ora di cielo -- ma una
    risposta le rimette in coda con le altre, anche se stanno in un'altra cartella."""
    radice = add_folder(conn, "/vol/astro")
    vera = _posa(conn, radice, "notte/a.fits")
    copia = _posa(conn, radice, "calibrate/a_cal.fits", copy_of=vera)
    riga = rigless.row_of(conn, _chiave(conn, vera))
    assert riga["frames"] == 1
    assert set(rigless.frames_of(conn, riga)) == {vera, copia}


def test_the_focal_is_shown_only_when_the_poses_agree(conn):
    """La focale che le pose portano si mostra per riempire la risposta, ma **solo se dicono una
    cosa sola**: con due focali nello stesso gruppo non si sceglie per l'utente, e il campo resta
    vuoto -- un vuoto e' "non so", mai un valore inventato. Non fa un altro gruppo: varia di poco
    da un file all'altro."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "una/a.fits", telescope="AM5", focal=530.0)
    _posa(conn, radice, "una/b.fits", telescope="AM5", focal=530.0)
    _posa(conn, radice, "due/a.fits", telescope="AM5", focal=530.0, date="2026-03-20T21:00:00")
    _posa(conn, radice, "due/b.fits", telescope="AM5", focal=532.0, date="2026-03-20T21:00:00")
    focali = {g["night"]: (g["frames"], g["focal_mm"]) for g in rigless.by_group(conn)}
    assert focali == {"2026-03-14": (2, 530.0), "2026-03-20": (2, None)}


def test_the_focal_of_the_optics_card_is_proposed_when_the_poses_do_not_say_it(conn):
    """Un corredo e' ottica + camera **a una focale**: se le pose non la dicono, si propone quella
    nativa dell'ottica che l'utente ha in scheda. Senza una focale il corredo che nasce dalla
    risposta resterebbe un gemello separato per sempre da quello rilevato (`normalize_store`)."""
    radice = add_folder(conn, "/vol/astro")
    conn.execute(
        "INSERT INTO instruments(kind, name, focal_mm, created_at)"
        " VALUES('optics', ?, 800.0, 'ora')",
        (OTT,),
    )
    _posa(conn, radice, "notte/a.fits", telescope=OTT)
    gruppo = rigless.by_group(conn)[0]
    assert (gruppo["focal_mm"], gruppo["focal_suggested"]) == (None, 800.0)


def test_a_pose_that_lives_in_two_folders_counts_once(conn):
    """Lo stesso file in due cartelle e' una posa con due posizioni: si conta una volta."""
    prima = add_folder(conn, "/vol/prima")
    dopo = add_folder(conn, "/vol/dopo")
    frame_id = _posa(conn, prima, "notte/a.fits")
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, 'notte/a.fits', 1, 1.0, 'ora')",
        (frame_id, dopo),
    )
    assert [g["frames"] for g in rigless.by_group(conn)] == [1]


def test_a_retired_folder_and_a_file_that_is_gone_do_not_ask_anything(conn):
    """Una cartella che l'utente ha ritirato e un file che non si trova piu' non fanno domande: non
    c'e' niente su cui agire. Se la posa vive anche in una cartella viva, si chiede."""
    ritirata = add_folder(conn, "/vol/ritirata")
    conn.execute("UPDATE folders SET retired_at = 'ieri' WHERE id = ?", (ritirata,))
    viva = add_folder(conn, "/vol/viva")
    _posa(conn, ritirata, "notte/a.fits")
    sparita = _posa(conn, viva, "notte/b.fits")
    conn.execute("UPDATE positions SET status = 'missing' WHERE frame_id = ?", (sparita,))
    doppia = _posa(conn, ritirata, "notte/c.fits")
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, 'altra/c.fits', 1, 1.0, 'ora')",
        (doppia, viva),
    )
    assert [g["frames"] for g in rigless.by_group(conn)] == [1]


def test_the_answer_is_read_back_with_its_pieces(conn):
    """La risposta porta i **nomi** dei pezzi e la focale, e si rilegge tale e quale. Rispondere di
    nuovo la riscrive: si cambia idea."""
    rigless.declare(conn, "k", OTT, CAM, 530.0)
    assert rigless.answer(conn, "k") == {"optics": OTT, "camera": CAM, "focal_mm": 530.0}
    rigless.declare(conn, "k", None, "Altra", None)
    assert rigless.answer(conn, "k") == {"optics": None, "camera": "Altra", "focal_mm": None}
    assert rigless.answer(conn, "mai") is None


def _scrivi(conn, valore):
    conn.execute(
        "INSERT OR REPLACE INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES(?, 'k', ?, ?, 'ora')",
        (decl.FRAME_GROUP, decl.GROUP_RIG, valore),
    )


STORTE = [
    "non e' json",
    '"una stringa"',
    "[]",
    '{"optics": "Newton"}',  # senza la camera non c'e' risposta: e' quello che si chiedeva
    '{"camera": ""}',
    '{"camera": null}',
    '{"camera": 3}',
]


def test_an_answer_that_cannot_be_read_is_no_answer(conn):
    """Una riga storta vale **nessuna risposta**: le pose restano dove sono e la domanda resta
    aperta, invece di finire su un'ipotesi. La camera e' la sola cosa obbligatoria -- e' la domanda
    -- e senza di lei non c'e' niente da leggere."""
    for storta in STORTE:
        _scrivi(conn, storta)
        assert rigless.answer(conn, "k") is None, storta


def test_the_pose_reads_the_answer_of_its_own_group(conn):
    """Chi normalizza parte dalla posa e arriva alla risposta del SUO gruppo, anche se sta in
    un'altra cartella: quella di un'altra notte non la tocca, e senza risposta torna `None`."""
    radice = add_folder(conn, "/vol/astro")
    mia = _posa(conn, radice, "notte/a.fits")
    stessa = _posa(conn, radice, "altrove/b.fits")
    altra = _posa(conn, radice, "notte/c.fits", date="2026-03-20T21:00:00")
    assert rigless.rig_of_frame(conn, _frame(conn, mia)) is None
    rigless.declare(conn, _chiave(conn, mia), OTT, CAM, 530.0)
    assert rigless.rig_of_frame(conn, _frame(conn, mia))["camera"] == CAM
    assert rigless.rig_of_frame(conn, _frame(conn, stessa))["camera"] == CAM
    assert rigless.rig_of_frame(conn, _frame(conn, altra)) is None


def test_the_answer_of_a_group_that_is_not_there_is_not_found(conn):
    """Un gruppo che non ha piu' pose da chiedere non c'e': la pagina era vecchia."""
    assert rigless.row_of(conn, "mai") is None


def test_the_optics_shown_is_the_name_the_user_gave_it(conn):
    """L'ottica che la pagina propone e' il nome **risolto**, non la grafia dell'header: se
    l'utente l'ha rinominata, proporgli la grafia vecchia e lasciargliela accettare farebbe
    nascere un secondo pezzo accanto a quello rinominato."""
    radice = add_folder(conn, "/vol/astro")
    conn.execute(
        "INSERT INTO instruments(kind, name, created_at) VALUES('optics', ?, 'ora')", (OTT,)
    )
    decl.learn(conn, "optics", "ZWO AM5", OTT)
    _posa(conn, radice, "notte/a.fits", telescope="ZWO AM5")
    assert rigless.by_group(conn)[0]["optics"] == OTT


FOCALI_STORTE = [True, 0, -800, "800", None, [800]]


def test_a_focal_that_is_not_a_focal_leaves_the_answer_standing(conn):
    """Una focale che non e' una misura non e' una focale: il campo resta vuoto, ignota e mai
    inventata. Ma la risposta **resta in piedi**, perche' la camera c'e' ed e' lei la domanda."""
    for storta in FOCALI_STORTE:
        _scrivi(conn, json.dumps({"optics": None, "camera": CAM, "focal_mm": storta}))
        atteso = {"optics": None, "camera": CAM, "focal_mm": None}
        assert rigless.answer(conn, "k") == atteso, storta


OTTICHE_STORTE = ["", 0, [], {"nome": "Newton"}]


def test_an_optics_that_is_not_a_name_is_no_optics(conn):
    """L'ottica e' facoltativa, ma quando c'e' deve essere un **nome**: vuota, un numero o una lista
    valgono "non l'ha detta", e la camera -- che e' la domanda -- resta in piedi comunque."""
    for storta in OTTICHE_STORTE:
        _scrivi(conn, json.dumps({"optics": storta, "camera": CAM, "focal_mm": 530.0}))
        atteso = {"optics": None, "camera": CAM, "focal_mm": 530.0}
        assert rigless.answer(conn, "k") == atteso, storta


def test_the_key_is_never_split_to_find_the_pieces(conn):
    """La chiave e' un nome, non un contenitore da riaprire. Un `TELESCOP` che porta una barra
    verticale -- il separatore con cui sono fatte altre chiavi dell'app -- si risponde e si rilegge
    come qualunque altro: chi ricavasse i pezzi spezzando la chiave sbaglierebbe qui, e in
    silenzio."""
    radice = add_folder(conn, "/vol/a|b")
    frame_id = _posa(conn, radice, "M51|Ha/a.fits", telescope="AM5|bis")
    riga = rigless.row_of(conn, _chiave(conn, frame_id))
    assert riga is not None
    rigless.declare(conn, riga["key"], OTT, CAM, 530.0)
    assert rigless.rig_of_frame(conn, _frame(conn, frame_id))["camera"] == CAM
    assert rigless.frames_of(conn, riga) == [frame_id]


def test_rigless_asks_the_rig_only_of_the_nights_of_its_poses(conn, monkeypatch):
    """Il corredo della notte si chiede per le sole notti delle pose che chiedono: una notte in cui
    ogni posa dice la camera non cambia nessuna domanda, e su un archivio che la camera la dice
    quasi sempre leggerle tutte costerebbe quasi l'archivio intero."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "notte/a.fits", telescope="ZWO AM5")
    _posa(conn, radice, "altra/b.fits", instrument=CAM, date="2026-03-20T21:00:00")
    chieste = []
    vero = rigless.night_rigs

    def registra(c, nights=None):
        chieste.append(nights)
        return vero(c, nights)

    monkeypatch.setattr(rigless, "night_rigs", registra)
    rigless.by_group(conn)
    assert chieste == [{"2026-03-14"}]
