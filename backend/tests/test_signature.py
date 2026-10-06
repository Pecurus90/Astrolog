"""Le regole della domanda sull'attrezzatura per firma dell'header (ADR 0014, S1), provate da sole.

La firma e' cio' che l'header dice: grafia di camera e telescopio, focale, sensore -- mai la notte
o la cartella. La scheda chiede solo le parti che i file non dicono (camera, ottica, filtro), la
risposta si rilegge, e le pose che non ci stanno restano fuori: qui si guarda la REGOLA, senza API.
Che poi l'app la faccia davvero lo guarda `test_review_gear.py`.
"""

import json

from astrolog.clock import night_date
from astrolog.spine import declarations as decl
from astrolog.spine import header_asks, signature
from astrolog.spine import signature_page as cards
from conftest import add_folder

CAM, OTT = "ZWO ASI2600MM", "Newton 200/800"
NOTTE = "2026-03-14T21:00:00"  # la notte del 14


def _posa(conn, folder_id, rel_path, *, instrument=None, telescope=None, focal=None, copy_of=None,
          date: str | None = NOTTE, size=(6248, 4176), pixel=3.76,
          filtro: str | None = "L"):  # fmt: skip
    """Una posa con la sua posizione, senza scrivere un FITS: qui si guardano le query. Dice il
    filtro, salvo chiederlo: la domanda sul filtro ha le sue prove."""
    notte = night_date(date)  # come la scrive `scan` senza sito
    # i giudizi sul grezzo, come li scrive la scansione: senza, la posa prenderebbe il ripiego
    giudizi = header_asks.of(
        {"instrument_raw": instrument, "telescope_raw": telescope, "filter_raw": filtro}
    )
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, instrument_raw, telescope_raw, focal_mm_raw,"
        " filter_raw, copy_of, date_obs, local_night, naxis1, naxis2, pixel_size_um, asks_camera,"
        " asks_filter, names_optics, header_json, created_at)"
        " VALUES(?, 'light', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', 'ora')",
        (
            f"{folder_id}:{rel_path}",
            instrument,
            telescope,
            focal,
            filtro,
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
    """La firma di quella posa, come la calcola chi normalizza."""
    return signature.key_of(signature.parts_of(_frame(conn, frame_id)))


def _risposta_della_posa(conn, frame_id):
    parti = signature.parts_of(_frame(conn, frame_id))
    trovata = signature.answer_for(signature.answers(conn), parti)
    return trovata and trovata[1]


def test_the_signature_is_the_header_not_the_night_or_the_folder(conn):
    """Due cartelle e due notti con gli stessi valori sono una scheda sola: la notte non entra
    nella firma (ADR 0014, S2). Due sensori diversi sono due. La piu' numerosa in cima, e la riga
    dice i valori, non un percorso ne' una notte."""
    radice = add_folder(conn, "D:/Astro")
    _posa(conn, radice, "M51/a.fits")
    _posa(conn, radice, "M51/b.fits", date="2026-03-15T01:00:00")
    _posa(conn, radice, "altra/c.fits")
    _posa(conn, radice, "M51/d.fits", date="2026-03-21T21:00:00")
    _posa(conn, radice, "M51/e.fits", size=(3008, 3008), pixel=3.76)
    righe = [(g["width_px"], g["frames"]) for g in cards.by_signature(conn)]
    assert righe == [(6248, 4), (3008, 1)]
    assert cards.by_signature(conn)[0]["pixel_um"] == 3.76
    assert "night" not in cards.by_signature(conn)[0]


def test_each_value_of_the_key_makes_its_own_group_and_the_row_says_it(conn):
    """Stesso sensore: un altro telescopio o un altro pixel sono un'altra scheda, e la riga porta il
    telescopio come lo scrive il file -- senza, due righe avrebbero lo stesso nome."""
    radice = add_folder(conn, "D:/Astro")
    _posa(conn, radice, "a/a.fits", telescope="AM5")
    _posa(conn, radice, "b/b.fits", telescope="EQ6")
    _posa(conn, radice, "c/c.fits", telescope="AM5", pixel=2.9)
    righe = sorted((g["telescope"], g["pixel_um"]) for g in cards.by_signature(conn))
    assert righe == [("AM5", 2.9), ("AM5", 3.76), ("EQ6", 3.76)]


def test_the_key_is_made_in_one_place_from_what_the_header_says(conn):
    """La firma si compone da una funzione sola, con le grafie normalizzate come si cerca una regola
    imparata: chi normalizza la posa e la pagina che la chiede arrivano alla stessa chiave, e
    bianchi o maiuscole in piu' non fanno un'altra scheda."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "M51/a.fits", telescope="ZWO AM5")
    b = _posa(conn, radice, "altra/b.fits", telescope="  zwo AM5 ")
    assert _chiave(conn, a) == _chiave(conn, b)
    assert [g["key"] for g in cards.by_signature(conn)] == [_chiave(conn, a)]


def test_renaming_the_optics_does_not_move_the_key(conn):
    """La firma e' fatta dai grezzi: rinominare l'ottica che `TELESCOP` nomina cambia cio' che la
    riga propone, non la scheda, e una risposta gia' data resta dov'e'."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "M51/a.fits", telescope="ZWO AM5")
    prima = _chiave(conn, a)
    conn.execute(
        "INSERT INTO instruments(kind, name, created_at) VALUES('optics', ?, 'ora')", (OTT,)
    )
    decl.learn(conn, "optics", "ZWO AM5", OTT)
    assert _chiave(conn, a) == prima
    assert cards.by_signature(conn)[0]["key"] == prima


def test_only_the_poses_whose_header_does_not_say_the_camera_are_asked(conn):
    """La parte "camera" si riconosce dal GREZZO: chi scrive `INSTRUME` non la chiede. E la chiede
    anche chi porta il telescopio ma non la camera -- l'ASIAIR scrive la montatura in `TELESCOP`."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "notte/a.fits", telescope="ZWO AM5")
    # due camere nella stessa notte: la notte non risolve, e le scarta solo il grezzo che le dice
    _posa(conn, radice, "notte/b.fits", instrument="ZWO ASI533MC", telescope="RC8",
          date="2026-03-20T21:00:00")  # fmt: skip
    _posa(conn, radice, "notte/b2.fits", instrument="ZWO ASI294MM", telescope="RC8",
          date="2026-03-20T22:00:00")  # fmt: skip
    _posa(conn, radice, "notte/c.fits", instrument="   ", telescope="ZWO AM5")  # bianchi: niente
    schede = cards.by_signature(conn)
    assert [(g["frames"], g["asks_camera"]) for g in schede] == [(2, True)]
    assert schede[0]["optics"] == "ZWO AM5"  # cio' che le pose dicono gia': un indizio


def test_a_part_the_files_say_is_not_asked(conn):
    """La scheda chiede solo cio' che manca: la camera a chi non la scrive, l'ottica a chi non la
    nomina, il filtro a chi non lo dice su una camera che non e' a colori."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "a.fits", instrument=CAM)  # dice la camera, non l'ottica
    _posa(conn, radice, "b.fits", instrument="QHY", telescope="RC8", filtro=None)  # il filtro no
    parti = {
        g["camera"]: (g["asks_camera"], g["asks_optics"], g["asks_filter"])
        for g in cards.by_signature(conn)
    }
    assert parti == {CAM: (False, True, False), "QHY": (False, False, True)}


def test_a_rewritten_copy_is_not_another_pose_but_comes_back_in_the_queue(conn):
    """Le copie riscritte non si contano a video -- non sono un'altra ora di cielo -- ma una
    risposta le rimette in coda con le altre, anche se stanno in un'altra cartella."""
    radice = add_folder(conn, "/vol/astro")
    vera = _posa(conn, radice, "notte/a.fits")
    copia = _posa(conn, radice, "calibrate/a_cal.fits", copy_of=vera)
    riga = cards.row_of(conn, _chiave(conn, vera))
    assert riga["frames"] == 1
    assert set(signature.frames_of(conn, riga["key"])) == {vera, copia}


def test_the_focal_is_shown_only_when_the_poses_agree(conn):
    """La focale entra nella firma con la regola dei corredi (+-5 %): 530 e 532 sono una scheda,
    400 un'altra. Si mostra per riempire la risposta **solo se le pose dicono una cosa sola**: con
    due focali non si sceglie per l'utente, e il campo resta vuoto."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "una/a.fits", telescope="AM5", focal=530.0)
    _posa(conn, radice, "una/b.fits", telescope="AM5", focal=532.0)
    _posa(conn, radice, "due/a.fits", telescope="AM5", focal=400.0)
    _posa(conn, radice, "due/b.fits", telescope="AM5", focal=400.0)
    _posa(conn, radice, "due/c.fits", telescope="AM5", focal=400.0)
    focali = [(g["frames"], g["focal_mm"]) for g in cards.by_signature(conn)]
    assert focali == [(3, 400.0), (2, None)]


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
    scheda = cards.by_signature(conn)[0]
    assert (scheda["focal_mm"], scheda["focal_suggested"]) == (None, 800.0)


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
    assert [g["frames"] for g in cards.by_signature(conn)] == [1]


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
    assert [g["frames"] for g in cards.by_signature(conn)] == [1]


def test_the_answer_is_read_back_with_its_pieces(conn):
    """La risposta porta i **nomi** dei pezzi, la focale e il filtro, e si rilegge tale e quale.
    Rispondere di nuovo la riscrive: si cambia idea."""
    data = signature.Answer(CAM, OTT, 530.0, signature.FilterAnswer.ONE_OF_YOURS, "Lum")
    signature.declare(conn, "k", data)
    assert signature.answer(conn, "k") == data
    signature.declare(conn, "k", signature.Answer(camera="Altra"))
    assert signature.answer(conn, "k") == signature.Answer(camera="Altra")
    assert signature.answer(conn, "mai") is None


def _scrivi(conn, valore):
    conn.execute(
        "INSERT OR REPLACE INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES(?, 'k', ?, ?, 'ora')",
        (decl.EntityType.SIGNATURE, decl.SIGNATURE_GEAR, valore),
    )


STORTE = ["non e' json", '"una stringa"', "[]", "3"]


def test_an_answer_that_cannot_be_read_is_no_answer(conn):
    """Una riga storta vale **nessuna risposta**: le pose restano dove sono e la domanda resta
    aperta, invece di finire su un'ipotesi."""
    for storta in STORTE:
        _scrivi(conn, storta)
        assert signature.answer(conn, "k") is None, storta


def test_no_answer_yet_is_not_an_unreadable_answer(conn, caplog):
    """Una firma a cui nessuno ha risposto non e' una risposta persa: il log non lo dice."""
    assert signature.answer(conn, "mai") is None
    assert "illeggibile" not in caplog.text


def test_the_pose_reads_the_answer_of_its_own_group(conn):
    """Chi normalizza parte dalla posa e arriva alla risposta della SUA firma, in qualunque
    cartella e in qualunque notte: quella di un altro sensore non la tocca."""
    radice = add_folder(conn, "/vol/astro")
    mia = _posa(conn, radice, "notte/a.fits")
    stessa = _posa(conn, radice, "altrove/b.fits", date="2026-03-20T21:00:00")
    altra = _posa(conn, radice, "notte/c.fits", size=(3008, 3008))
    assert _risposta_della_posa(conn, mia) is None
    signature.declare(conn, _chiave(conn, mia), signature.Answer(CAM, OTT, 530.0))
    assert _risposta_della_posa(conn, mia).camera == CAM
    assert _risposta_della_posa(conn, stessa).camera == CAM
    assert _risposta_della_posa(conn, altra) is None


def test_a_focal_that_drifts_finds_the_same_answer(conn):
    """La focale si confronta con la regola dei corredi: una posa a 803 mm trova la risposta data
    a 800, una a 400 no."""
    radice = add_folder(conn, "/vol/astro")
    a = _posa(conn, radice, "a.fits", instrument=CAM, focal=800.0)
    b = _posa(conn, radice, "b.fits", instrument=CAM, focal=803.0)
    c = _posa(conn, radice, "c.fits", instrument=CAM, focal=400.0)
    signature.declare(conn, _chiave(conn, a), signature.Answer(optics=OTT))
    assert _risposta_della_posa(conn, b).optics == OTT
    assert _risposta_della_posa(conn, c) is None


def test_the_answer_of_a_group_that_is_not_there_is_not_found(conn):
    """Una firma che non ha piu' pose da chiedere non c'e': la pagina era vecchia."""
    assert cards.row_of(conn, "mai") is None


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
    assert cards.by_signature(conn)[0]["optics"] == OTT


FOCALI_STORTE = [True, 0, -800, "800", None, [800]]


def test_a_focal_that_is_not_a_focal_leaves_the_answer_standing(conn):
    """Una focale che non e' una misura non e' una focale: il campo resta vuoto, ignota e mai
    inventata. Ma la risposta **resta in piedi**."""
    for storta in FOCALI_STORTE:
        _scrivi(conn, json.dumps({"optics": None, "camera": CAM, "focal_mm": storta}))
        assert signature.answer(conn, "k") == signature.Answer(camera=CAM), storta


OTTICHE_STORTE = ["", "   ", 0, [], {"nome": "Newton"}]


def test_an_optics_that_is_not_a_name_is_no_optics(conn):
    """Quando c'e', l'ottica deve essere un **nome**: vuota, un numero o una lista valgono "non
    l'ha detta", e il resto della risposta resta in piedi comunque."""
    for storta in OTTICHE_STORTE:
        _scrivi(conn, json.dumps({"optics": storta, "camera": CAM, "focal_mm": 530.0}))
        assert signature.answer(conn, "k") == signature.Answer(camera=CAM, focal_mm=530.0), storta


def test_a_filter_word_that_is_not_an_answer_is_no_filter_answer(conn):
    """Il filtro si legge solo fra le due parole della risposta, e il nome del filtro solo con
    "uno dei tuoi": una parola sconosciuta vale "non l'ha detto"."""
    _scrivi(conn, json.dumps({"camera": CAM, "filter": "color", "filter_name": "Lum"}))
    assert signature.answer(conn, "k") == signature.Answer(camera=CAM)
    _scrivi(conn, json.dumps({"filter": "no_filter", "filter_name": "Lum"}))
    assert signature.answer(conn, "k") == signature.Answer(filter=signature.FilterAnswer.NO_FILTER)


def test_the_key_is_never_split_to_find_the_pieces(conn):
    """Un `TELESCOP` che porta una barra verticale -- il separatore con cui sono fatte altre chiavi
    dell'app -- si risponde e si rilegge come qualunque altro: la firma e' un elenco JSON, non una
    stringa da spezzare."""
    radice = add_folder(conn, "/vol/a|b")
    frame_id = _posa(conn, radice, "M51|Ha/a.fits", telescope="AM5|bis")
    riga = cards.row_of(conn, _chiave(conn, frame_id))
    assert riga is not None
    signature.declare(conn, riga["key"], signature.Answer(CAM, OTT, 530.0))
    assert _risposta_della_posa(conn, frame_id).camera == CAM
    assert signature.frames_of(conn, riga["key"]) == [frame_id]


def test_the_cards_ask_the_rig_only_of_the_nights_of_their_poses(conn, monkeypatch):
    """Il corredo della notte si chiede per le sole notti delle pose che chiedono la camera: una
    notte in cui ogni posa dice la camera non cambia nessuna parte, e su un archivio che la camera
    la dice quasi sempre leggerle tutte costerebbe quasi l'archivio intero."""
    radice = add_folder(conn, "/vol/astro")
    _posa(conn, radice, "notte/a.fits", telescope="ZWO AM5")
    _posa(conn, radice, "altra/b.fits", instrument=CAM, date="2026-03-20T21:00:00")
    chieste = []
    vero = cards.night_rigs

    def registra(c, nights=None):
        chieste.append(nights)
        return vero(c, nights)

    monkeypatch.setattr(cards, "night_rigs", registra)
    cards.by_signature(conn)
    assert chieste == [{"2026-03-14"}]


def test_renaming_a_piece_carries_the_answers_that_name_it(conn):
    """La risposta porta il NOME dei pezzi e del filtro: rinominati, la risposta li segue, o al giro
    dopo il nome vecchio farebbe rinascere un pezzo accanto a quello rinominato."""
    signature.declare(
        conn, "k", signature.Answer(CAM, OTT, 530.0, signature.FilterAnswer.ONE_OF_YOURS, "Lum")
    )
    signature.follow_piece(conn, "optics", OTT, "Newton 8")
    signature.follow_piece(conn, "camera", CAM, "La mia")
    signature.follow_filter(conn, "Lum", "Astronomik L")
    atteso = signature.Answer(
        "La mia", "Newton 8", 530.0, signature.FilterAnswer.ONE_OF_YOURS, "Astronomik L"
    )
    assert signature.answer(conn, "k") == atteso
