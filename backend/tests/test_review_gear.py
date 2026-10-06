"""Da confermare, l'attrezzatura che i file non dicono: una scheda per firma dell'header (ADR 0014,
S1) che chiede insieme camera, ottica e filtro, solo le parti che mancano.

Ci cadono le pose che non dicono la camera -- anche quelle che portano il telescopio, perche'
l'ASIAIR scrive la montatura in `TELESCOP` -- e quelle che la camera la dicono ma non l'ottica. Si
risponde scegliendo un corredo fra quelli che l'app conosce, oppure scrivendo i pezzi: nascono dai
nomi, come da un header. La notte resta: se gli altri frame della stessa notte dicono una camera
sola, quella non si chiede. Le regole stanno in `spine/signature.py` e nel contratto
`docs/domini/spina.md`. Il filtro ha le sue prove in `test_review_gear_filter.py`.
"""

import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import signature
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from astrolog.spine.stages import invalidate
from conftest import (
    apply,
    by_name,
    correct,
    db,
    frame_by_file,
    gear,
    populate,
    review,
    senza_soggetti,
    to_confirm_without,
    write_fits,
)

MONTATURA, CAM, OTT, DETTA = "ZWO AM5", "ZWO ASI2600MM", "Newton 200/800", "ZWO ASI533MC"
M51, NGC, MUTA = "2026-03-14/M51/LIGHT", "2026-03-21/NGC7000", "senza_niente"


def _posa(path, minuto=None, **header):
    """Una posa che NON dice il filtro: la scheda chiede anche quello."""
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0}
    if minuto is not None:
        card["DATE-OBS"] = f"2026-03-14T21:{minuto:02d}:00"
        card["OBJECT"] = "M 51"
    return write_fits(path, {**card, **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):  # la montatura in TELESCOP, la camera da nessuna parte
        _posa(root / M51 / f"a_{i}.fits", i, TELESCOP=MONTATURA)
    # questa la camera la dice, ma in un'altra notte: non risponde per le altre
    _posa(root / M51 / "detta.fits", 9, TELESCOP=MONTATURA, INSTRUME=DETTA,
          **{"DATE-OBS": "2026-03-16T21:09:00"})  # fmt: skip
    _posa(root / NGC / "b_0.fits", 20)  # ne' telescopio ne' camera
    muta = _posa(root / MUTA / "c_0.fits")  # e nemmeno l'oggetto o l'ora: si chiede lo stesso
    scritta = datetime(2026, 3, 20, 21, 0, tzinfo=UTC).timestamp()  # la notte e' quella del file
    os.utime(muta, (scritta, scritta))
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _chiave(client, nome):
    """La firma della posa di quel file, come la calcola chi normalizza."""
    with db(client) as conn:
        return signature.key_of(signature.parts_of(frame_by_file(conn, nome)))


def _schede(client):
    return {g["key"]: g for g in review(client)["gear"]}


def _corredo_della_posa(client, nome):
    """(ottica, camera, focale) del corredo attaccato a quella posa, o None."""
    with db(client) as conn:
        riga = conn.execute(
            "SELECT o.name AS optics, c.name AS camera, g.focal_mm, g.id FROM frames f"
            " JOIN positions p ON p.frame_id = f.id LEFT JOIN rigs g ON g.id = f.rig_id"
            " LEFT JOIN instruments o ON o.id = g.optics_id"
            " LEFT JOIN instruments c ON c.id = g.camera_id WHERE p.rel_path LIKE ?",
            (f"%{nome}",),
        ).fetchone()
    return None if riga["id"] is None else (riga["optics"], riga["camera"], riga["focal_mm"])


def _camera_della_posa(client, nome):
    return (_corredo_della_posa(client, nome) or (None, None, None))[1]


def _senza_filtro(client, sotto):
    """Quante pose di quella cartella che non dicono la camera sono ancora senza filtro."""
    with db(client) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM frames f JOIN positions p ON p.frame_id = f.id"
            " WHERE f.filter_id IS NULL AND f.instrument_raw IS NULL AND p.rel_path LIKE ?",
            (f"{sotto}%",),
        ).fetchone()[0]


def _scansiona_ancora(client):
    with db(client) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))


def _rilavora_tutto(client):
    """Tutte le pose di nuovo in `normalize`: e' li' che un nome vecchio rinascerebbe."""
    with db(client) as conn:
        invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "normalize")
        list(normalize_frames(conn))


def test_a_group_says_what_the_sky_found_in_it(pagina):
    """Cosa hai ripreso con quella firma, per ricordare con che camera (`test_review_subjects`):
    la posa che dice la camera non e' nella scheda, e quella senza nome ne' cielo non ha oggetto."""
    schede = _schede(pagina)
    assert schede[_chiave(pagina, "a_0.fits")]["subjects"] == {
        "found": [{"name": "M 51", "frames": 3}],
        "not_found": 0,
        "not_yet": 0,
    }
    assert schede[_chiave(pagina, "c_0.fits")]["subjects"] == {
        "found": [{"name": "M 51", "frames": 1}],
        "not_found": 1,
        "not_yet": 0,
    }


def test_an_object_with_only_copies_in_a_group_is_not_something_imaged_there(pagina):
    """Una copia calibrata non e' un'altra posa: se in quella scheda un oggetto ha solo copie,
    non compare fra cio' che hai ripreso -- nemmeno con zero pose."""
    with db(pagina) as conn:
        conn.execute(
            "INSERT INTO objects(catalog_slug, identity_method, identity_confidence, created_at)"
            " VALUES('ngc-7000', 'coord_confirmed', 'certain', '2026-09-15T00:00:00Z')"
        )
        altro = conn.execute("SELECT id FROM objects WHERE catalog_slug = 'ngc-7000'").fetchone()[0]
        ids = [r[0] for r in conn.execute(
            "SELECT p.frame_id FROM positions p WHERE p.rel_path LIKE ? ORDER BY p.rel_path",
            (f"{M51}/a_%",),
        )]  # fmt: skip
        conn.execute(
            "UPDATE frames SET copy_of = ?, object_id = ? WHERE id = ?", (ids[0], altro, ids[2])
        )
        conn.commit()
    assert _schede(pagina)[_chiave(pagina, "a_0.fits")]["subjects"]["found"] == [
        {"name": "M 51", "frames": 2}
    ]


def test_a_question_per_group_with_the_largest_first(pagina):
    """Una scheda per firma -- i valori dell'header, detti a video, mai la notte --, la piu'
    numerosa in cima, con le parti che chiede e quello che le pose dicono gia': il telescopio come
    indizio e la focale se la scrivono. La posa senza telescopio della notte del 14 e quella senza
    data sono una scheda sola: stessa firma. La posa che la camera la dice chiede solo il filtro."""
    vuota = {"camera": None, "telescope": None, "width_px": 4, "height_px": 3, "pixel_um": None}
    vuota |= {"focal_mm": None, "focal_suggested": None, "answer": None, "complete": False}
    assert [senza_soggetti(g) for g in review(pagina)["gear"]] == [
        {
            **vuota,
            "key": _chiave(pagina, "a_0.fits"),
            "telescope": MONTATURA,
            "frames": 3,
            "asks_camera": True,
            "asks_optics": False,
            "asks_filter": True,
            "optics": MONTATURA,
        },
        {
            **vuota,
            "key": _chiave(pagina, "b_0.fits"),
            "frames": 2,
            "asks_camera": True,
            "asks_optics": True,
            "asks_filter": True,
            "optics": None,
        },
        {
            **vuota,
            "key": _chiave(pagina, "detta.fits"),
            "camera": DETTA,
            "telescope": MONTATURA,
            "frames": 1,
            "asks_camera": False,
            "asks_optics": False,
            "asks_filter": True,
            "optics": MONTATURA,
        },
    ]


def test_answering_with_the_pieces_makes_the_rig_and_moves_the_poses(pagina):
    """Si scrivono ottica, camera e focale: i pezzi nascono dai nomi -- come nascono da un header --
    e le pose passano da quel corredo. L'ottica dichiarata **vince** su `TELESCOP`, che qui portava
    la montatura. La scheda resta in pagina con la sua risposta, perche' si deve poter cambiare
    idea."""
    chiave = _chiave(pagina, "a_0.fits")
    out = apply(pagina, gear=[{"key": chiave, "optics": OTT, "camera": CAM, "focal_mm": 800.0}])
    assert out["requeued"] == 3
    assert _corredo_della_posa(pagina, "a_0.fits") == (OTT, CAM, 800.0)
    risposta = _schede(pagina)[chiave]["answer"]
    assert risposta == {
        "optics": OTT,
        "camera": CAM,
        "focal_mm": 800.0,
        "filter": None,
        "filter_id": None,
    }
    # fra cui scegliere: il corredo mezzo vuoto nato dalla sola montatura, rimasto a zero pose,
    # non si offre piu'
    corredi = review(pagina)["rig_choices"]
    assert [(r["optics"], r["camera"]) for r in corredi] == [(OTT, CAM), (MONTATURA, DETTA)]


def test_the_camera_written_by_hand_becomes_a_piece_and_the_filter_question_follows(pagina):
    """La camera scritta a mano diventa un pezzo dell'attrezzatura con la sua scheda da compilare.
    La scheda della firma resta aperta finche' non dice anche il filtro, che le pose non scrivono:
    rispondere a meta' non chiude la domanda."""
    chiave = _chiave(pagina, "a_0.fits")
    apply(pagina, gear=[{"key": chiave, "camera": CAM, "focal_mm": 800.0}])
    scheda = by_name(gear(pagina)["instruments"], CAM)
    assert (scheda["kind"], scheda["frames"], scheda["pixel_size_um"]) == ("camera", 3, None)
    assert (_schede(pagina)[chiave]["asks_filter"], _schede(pagina)[chiave]["complete"]) == (
        True,
        False,
    )
    apply(pagina, gear=[{"key": chiave, "filter": "no_filter"}])
    assert _schede(pagina)[chiave]["complete"] is True
    assert _schede(pagina)[chiave]["answer"]["camera"] == CAM  # la parte data prima resta


def test_the_camera_answered_after_the_optics_keeps_the_optics(pagina):
    """Una parte alla volta, in qualunque ordine: la camera scritta dopo non cancella l'ottica gia'
    data, che non ha mandato."""
    chiave = _chiave(pagina, "b_0.fits")
    apply(pagina, gear=[{"key": chiave, "optics": OTT}])
    apply(pagina, gear=[{"key": chiave, "camera": CAM, "focal_mm": 800.0}])
    apply(pagina, gear=[{"key": chiave, "filter": "no_filter"}])
    scheda = _schede(pagina)[chiave]
    assert (scheda["answer"]["optics"], scheda["answer"]["camera"]) == (OTT, CAM)
    assert scheda["complete"] is True


def test_a_name_with_spaces_around_is_written_without_them(pagina):
    """L'ottica scritta con la camera si ripulisce come quella scritta da sola: con uno spazio in
    piu' nascerebbe un secondo pezzo accanto a quello che hai."""
    chiave = _chiave(pagina, "a_0.fits")
    risposta = {"key": chiave, "optics": f" {OTT} ", "camera": CAM, "focal_mm": 800.0}
    apply(pagina, gear=[risposta])
    assert _schede(pagina)[chiave]["answer"]["optics"] == OTT


def test_choosing_a_rig_from_the_list_writes_its_names(pagina):
    """Si puo' rispondere scegliendo un corredo fra quelli che l'app conosce: si manda il suo
    numero di riga, che e' cio' che la pagina ha in mano dopo un clic, ma a essere scritti sono i
    **nomi** dei suoi pezzi -- un'unione cancella la riga rilevata, e una risposta scritta sul suo
    numero non sopravviverebbe a un azzeramento del rilevato."""
    apply(pagina, gear=[{"key": _chiave(pagina, "a_0.fits"), "camera": CAM, "focal_mm": 800.0}])
    corredo = next(r for r in review(pagina)["rig_choices"] if r["camera"] == CAM)
    chiave = _chiave(pagina, "b_0.fits")
    apply(pagina, gear=[{"key": chiave, "rig_id": corredo["id"]}])
    # il corredo scelto porta anche la sua ottica: si sceglie un corredo intero, non la sola camera
    risposta = _schede(pagina)[chiave]["answer"]
    assert (risposta["optics"], risposta["camera"], risposta["focal_mm"]) == (
        MONTATURA,
        CAM,
        800.0,
    )
    assert _corredo_della_posa(pagina, "b_0.fits") == (MONTATURA, CAM, 800.0)


def test_a_rig_without_a_camera_does_not_answer_this_question(pagina):
    """Il corredo mezzo vuoto nato dalla sola montatura non risponde: sceglierlo lascerebbe le pose
    esattamente dove sono. Non si offre, e mandarlo lo stesso si dice invece di scrivere una
    risposta che non sposta niente. Una casa sola per l'elenco e per chi lo rifiuta
    (`review_page.rig_choices`)."""
    with db(pagina) as conn:
        mezzo = conn.execute("SELECT id FROM rigs WHERE camera_id IS NULL").fetchone()
    assert mezzo["id"] not in [r["id"] for r in review(pagina)["rig_choices"]]
    corpo = {"gear": [{"key": _chiave(pagina, "a_0.fits"), "rig_id": mezzo["id"]}]}
    r = pagina.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "unknown_target"


def test_the_declared_focal_does_not_leave_two_twin_rigs(pagina, tmp_path):
    """Un corredo e' ottica + camera **a una focale**, e una focale ignota non e' la stessa cosa di
    una focale nota: senza chiedere la focale, il corredo nato dalla risposta e quello che le pose
    diranno domani sarebbero due corredi gemelli per sempre, con le ore spartite fra i due
    (misurato su `rigs.rig_for`). Con la focale dichiarata la riga e' una sola."""
    apply(pagina, gear=[{"key": _chiave(pagina, "a_0.fits"), "camera": CAM, "focal_mm": 800.0}])
    # la posa che arriva dice tutto da se': la stessa montatura, la camera e la focale -- in
    # un'altra notte, perche' nella stessa darebbe la camera anche alle pose di NGC7000
    _posa(
        tmp_path / "lib" / M51 / "dopo.fits", 30, TELESCOP=MONTATURA, INSTRUME=CAM, FOCALLEN=800.0,
        **{"DATE-OBS": "2026-03-17T21:30:00"},
    )  # fmt: skip
    _scansiona_ancora(pagina)
    assert _corredo_della_posa(pagina, "dopo.fits") == (MONTATURA, CAM, 800.0)
    with db(pagina) as conn:
        quanti = conn.execute(
            "SELECT COUNT(*) FROM rigs g JOIN instruments c ON c.id = g.camera_id WHERE c.name = ?",
            (CAM,),
        ).fetchone()[0]
    assert quanti == 1


def test_the_answer_holds_for_the_poses_that_arrive_later_in_that_group(pagina, tmp_path):
    """La risposta e' un fatto sulla firma, non su quelle pose: una posa che arriva dopo con gli
    stessi valori la riceve, da un'altra cartella **e in un'altra notte** -- la notte non e' nella
    chiave (ADR 0014, S2). La dichiarazione si rilegge a ogni giro."""
    chiave = _chiave(pagina, "a_0.fits")
    apply(pagina, gear=[{"key": chiave, "optics": OTT, "camera": CAM, "focal_mm": 800.0}])
    _posa(tmp_path / "lib" / "altrove" / "dopo.fits", 31, TELESCOP=MONTATURA)
    _posa(tmp_path / "lib" / M51 / "e_0.fits", 40, TELESCOP=MONTATURA,
          **{"DATE-OBS": "2026-04-02T21:40:00"})  # fmt: skip
    _scansiona_ancora(pagina)
    assert _corredo_della_posa(pagina, "dopo.fits") == (OTT, CAM, 800.0)
    assert _corredo_della_posa(pagina, "e_0.fits") == (OTT, CAM, 800.0)
    assert _schede(pagina)[chiave]["frames"] == 5


def test_the_focal_of_the_optics_card_is_what_the_page_proposes(pagina):
    """Se le pose non dicono la focale, la pagina propone quella nativa dell'ottica che l'utente ha
    in scheda: la risposta ha un valore da offrire invece di un campo vuoto."""
    ottica = by_name(gear(pagina)["instruments"], MONTATURA)
    assert correct(pagina, ottica["id"], focal_mm=800.0).status_code == 200
    assert _schede(pagina)[_chiave(pagina, "a_0.fits")]["focal_suggested"] == 800.0


def test_answering_again_moves_the_poses_to_the_new_rig(pagina):
    """Si cambia idea rispondendo di nuovo: le pose lasciano il corredo di prima e passano a quello
    nuovo, invece di restare su una risposta che l'utente ha ritirato."""
    chiave = _chiave(pagina, "c_0.fits")
    apply(pagina, gear=[{"key": chiave, "camera": CAM, "focal_mm": 800.0}])
    assert _corredo_della_posa(pagina, "c_0.fits") == (None, CAM, 800.0)
    apply(pagina, gear=[{"key": chiave, "camera": "Altra", "focal_mm": 250.0}])
    assert _corredo_della_posa(pagina, "c_0.fits") == (None, "Altra", 250.0)


def test_an_unanswered_group_counts_among_the_things_to_confirm(pagina):
    """Una scheda conta finche' ogni parte che chiede non ha la sua risposta; quella completa resta
    in pagina ma non si conta piu'. Un conto che tornasse a zero con delle pose ancora senza
    corredo sarebbe un conto che mente."""
    letta = review(pagina)
    assert letta["to_confirm"] == to_confirm_without(letta, "gear") + 3
    chiave = _chiave(pagina, "detta.fits")  # chiede solo il filtro
    apply(pagina, gear=[{"key": chiave, "filter": "no_filter"}])
    dopo = review(pagina)
    assert len(dopo["gear"]) == len(letta["gear"])  # la scheda risposta resta in pagina
    assert dopo["to_confirm"] == to_confirm_without(dopo, "gear") + 2


def test_after_the_answer_the_filter_question_reaches_those_poses(pagina):
    """La catena deve arrivare **in fondo**: risposti camera e filtro nella stessa scheda, la
    risposta raggiunge davvero le pose -- prima del corredo il filtro non aveva una camera a cui
    chiederlo, e restavano senza filtro mentre la pagina diceva "niente da confermare"."""
    chiave = _chiave(pagina, "a_0.fits")
    apply(pagina, gear=[{"key": chiave, "camera": CAM, "focal_mm": 800.0}])
    assert _senza_filtro(pagina, M51) == 3
    apply(pagina, gear=[{"key": chiave, "filter": "no_filter"}])
    assert _senza_filtro(pagina, M51) == 0


def test_a_rig_whose_only_poses_are_copies_stays_in_the_page(pagina):
    """Un corredo le cui uniche pose sono copie riscritte **esiste**: nasconderlo lo renderebbe
    impossibile da scegliere. Si nasconde solo il corredo che non ha piu' nessuna posa, nemmeno una
    copia."""
    with db(pagina) as conn:
        detta = conn.execute("SELECT id FROM frames WHERE instrument_raw IS NOT NULL").fetchone()[
            "id"
        ]
        altra = conn.execute("SELECT id FROM frames WHERE id != ?", (detta,)).fetchone()["id"]
        conn.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (altra, detta))
        conn.commit()
    assert DETTA in [r["camera"] for r in review(pagina)["rig_choices"]]


def test_a_group_that_is_not_there_is_refused(pagina):
    """Una firma su cui non c'e' nessuna posa da chiedere e' una pagina vecchia, e si dice:
    scrivere una risposta verso il nulla la lascerebbe li' per sempre senza che nessuno la veda."""
    corpo = {"gear": [{"key": "/mai/vista", "camera": CAM, "focal_mm": 800.0}]}
    r = pagina.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 404


def test_a_part_the_card_does_not_ask_is_refused(pagina):
    """Una parte che la scheda non chiede -- la camera a chi la scrive, l'ottica a chi la nomina --
    si dice invece di scriverla: la normalizzazione la ignorerebbe, e Applica direbbe "fatto"
    senza spostare niente."""
    chiave = _chiave(pagina, "detta.fits")
    for parte in ({"camera": CAM, "focal_mm": 800.0}, {"optics": OTT}):
        r = pagina.post("/api/v1/review/apply", json={"gear": [{"key": chiave, **parte}]})
        assert r.status_code == 422 and r.json()["detail"]["code"] == "not_asked", parte


@pytest.mark.parametrize(
    "corpo, perche_",
    [
        ({"key": "/x"}, "nessuna parte"),
        ({"key": "/x", "camera": CAM, "focal_mm": 800.0, "rig_id": 1}, "tutti e due"),
        ({"key": "/x", "rig_id": 1, "optics": OTT}, "un corredo porta i suoi pezzi"),
        ({"key": "/x", "camera": ""}, "una camera senza nome"),
        ({"key": "/x", "camera": "   ", "focal_mm": 800.0}, "una camera di soli spazi"),
        ({"key": "/x", "optics": "   "}, "an optics of only spaces"),
        ({"key": "/x", "camera": CAM, "focal_mm": 0}, "una focale che non e' una focale"),
        ({"key": "/x", "camera": CAM}, "la camera senza la sua focale: nascerebbe un gemello"),
        ({"key": "/x", "optics": OTT, "focal_mm": 800.0}, "la focale senza la camera"),
    ],
)
def test_an_answer_that_says_two_things_or_none_is_refused(pagina, corpo, perche_):
    """Un corredo dall'elenco **oppure** i pezzi scritti: accettarli tutti e due vorrebbe dire
    scegliere noi quale vince, e nessuna delle due scelte e' quella dell'utente."""
    r = pagina.post("/api/v1/review/apply", json={"gear": [corpo]})
    assert r.status_code == 422, perche_


def test_a_pose_without_camera_takes_the_one_of_its_night(pagina, tmp_path):
    """Se gli altri frame della stessa notte dicono una camera sola, e' quella (Marco, 23/9/2026):
    non si chiede. Vale anche se arriva dopo, in un'altra cartella; la posa che non dice quando e'
    stata ripresa sta nella notte del suo file, dove nessuno dice la camera, e resta da chiedere."""
    _posa(tmp_path / "lib" / "altra" / "cam.fits", 30, INSTRUME=CAM)
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") == CAM
    assert _camera_della_posa(pagina, "b_0.fits") == CAM
    chiedono = {k for k, g in _schede(pagina).items() if g["asks_camera"]}
    assert chiedono == {_chiave(pagina, "c_0.fits")}
    # la scheda di a_0 resta per il filtro, che la camera della notte non dice
    assert _schede(pagina)[_chiave(pagina, "a_0.fits")]["asks_filter"] is True


def test_in_one_scan_the_order_of_the_files_does_not_matter(db_path, tmp_path):
    """La posa senza camera prende quella della notte anche se il file che la dice arriva nella
    stessa scansione, prima o dopo di lei."""
    root = tmp_path / "lib"
    _posa(root / "a" / "senza.fits", 1, FILTER="L")
    _posa(root / "z" / "detta.fits", 2, INSTRUME=CAM, FILTER="L")
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        assert _camera_della_posa(c, "senza.fits") == CAM
        assert [g for g in review(c)["gear"] if g["asks_camera"]] == []


def test_two_cameras_in_the_night_leave_the_question(pagina, tmp_path):
    """Due camere nella stessa notte: quale fosse non si indovina, e la scheda chiede la camera.
    Anche quando la seconda arriva dopo che la prima aveva gia' risposto per la notte."""
    _posa(tmp_path / "lib" / "altra" / "cam.fits", 30, INSTRUME=CAM)
    _scansiona_ancora(pagina)
    _posa(tmp_path / "lib" / "altra" / "detta.fits", 31, INSTRUME=DETTA)
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") is None
    assert _schede(pagina)[_chiave(pagina, "a_0.fits")]["asks_camera"] is True


def test_two_spellings_of_one_camera_are_one_camera_of_the_night(pagina, tmp_path):
    """Due grafie nella stessa notte sono due camere finche' nessuno le unisce: la camera si
    chiede. Unite, la notte ha una camera sola, e le pose la prendono."""
    lib = tmp_path / "lib" / "altra"
    _posa(lib / "cam.fits", 30, INSTRUME=CAM)
    _posa(lib / "grafia.fits", 31, INSTRUME="ASI2600MM")
    _scansiona_ancora(pagina)
    assert _schede(pagina)[_chiave(pagina, "a_0.fits")]["asks_camera"] is True
    pezzi = {i["name"]: i["id"] for i in gear(pagina)["instruments"]}
    correct(pagina, pezzi["ASI2600MM"], merge_into=pezzi[CAM])
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") == CAM
    assert _schede(pagina)[_chiave(pagina, "a_0.fits")]["asks_camera"] is False


def test_my_answer_on_the_group_wins_over_the_night(pagina, tmp_path):
    """La risposta sulla firma e' scritta, e vince su cio' che la notte fa dedurre: la scheda resta
    in pagina con la risposta, per poterla cambiare."""
    chiave = _chiave(pagina, "a_0.fits")
    apply(pagina, gear=[{"key": chiave, "camera": DETTA, "focal_mm": 800.0}])
    _posa(tmp_path / "lib" / "altra" / "cam.fits", 30, INSTRUME=CAM)
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") == DETTA
    assert _schede(pagina)[chiave]["frames"] == 3


# L'ASIAIR: la montatura in TELESCOP, l'ottica da nessuna parte.
CAMERA, ALTRA, NEWTON = "ZWO ASI2600MC Pro", "QHY268M", "Newton 200/800"
ASIAIR = {"CREATOR": "ZWO ASIAIR Plus", "TELESCOP": "ZWO AM5", "INSTRUME": CAMERA, "FOCALLEN": 800}


def _scatto(path, minuto, **header):
    card = {
        "IMAGETYP": "Light Frame",
        "EXPTIME": 300.0,
        "DATE-OBS": f"2026-03-14T21:{minuto:02d}:00",
        "OBJECT": "M 51",
        "FILTER": "L",
    }
    return write_fits(path, {**card, **header})


@pytest.fixture
def ottiche(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):
        _scatto(root / "asiair" / f"a_{i}.fits", i, **ASIAIR)
    # la stessa camera, alla stessa focale, da un programma che l'ottica la scrive
    _scatto(root / "nina" / "n_0.fits", 30, CREATOR="N.I.N.A.", TELESCOP=NEWTON, INSTRUME=CAMERA,
            FOCALLEN=800)  # fmt: skip
    # un file che TELESCOP non lo scrive affatto: un'altra camera, a un'altra focale
    _scatto(root / "muta" / "m_0.fits", 40, INSTRUME=ALTRA, FOCALLEN=400)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _ottica_della_posa(client, nome):
    return (_corredo_della_posa(client, nome) or (None, None, None))[0]


def _pezzo(client, nome):
    return next(p for p in gear(client)["instruments"] if p["name"] == nome)["id"]


def test_poses_that_do_not_name_the_optics_are_asked_once_per_camera_and_focal(ottiche):
    """Le tre pose ASIAIR sono una scheda sola, che chiede solo l'ottica; il file senza `TELESCOP`
    un'altra. La posa di N.I.N.A. l'ottica la dice, e non si chiede."""
    schede = review(ottiche)["gear"]
    assert [
        (g["camera"], g["focal_mm"], g["frames"], g["asks_camera"], g["asks_optics"])
        for g in schede
    ] == [(CAMERA, 800.0, 3, False, True), (ALTRA, 400.0, 1, False, True)]
    assert all(g["answer"] is None and not g["asks_filter"] for g in schede)


def test_the_answer_gives_the_optics_and_the_poses_join_the_rig_that_has_it(ottiche):
    """Detta l'ottica, le pose ASIAIR stanno nel corredo che quell'ottica ha gia' con quella camera:
    lo stesso della posa di N.I.N.A., non un gemello. La scheda resta in pagina con la sua
    risposta, per cambiare idea, e non conta piu' fra le cose da confermare."""
    apply(ottiche, gear=[{"key": _chiave(ottiche, "a_0.fits"), "optics": NEWTON}])
    assert _ottica_della_posa(ottiche, "a_0.fits") == NEWTON
    assert _corredo_della_posa(ottiche, "a_0.fits") == _corredo_della_posa(ottiche, "n_0.fits")
    corredi = {(g["optics"], g["camera"]) for g in gear(ottiche)["rigs"]}
    assert (None, CAMERA) not in corredi and (NEWTON, CAMERA) in corredi
    risposta = _schede(ottiche)[_chiave(ottiche, "a_0.fits")]
    assert (risposta["answer"]["optics"], risposta["frames"], risposta["complete"]) == (
        NEWTON,
        3,
        True,
    )
    con_una = review(ottiche)["to_confirm"]
    apply(ottiche, gear=[{"key": _chiave(ottiche, "m_0.fits"), "optics": "Takahashi FSQ-85"}])
    assert review(ottiche)["to_confirm"] == con_una - 1


def test_an_optics_written_by_name_is_born_like_from_a_header(ottiche):
    """Un'ottica che l'Attrezzatura non ha si scrive, e nasce dal nome come da un file."""
    apply(ottiche, gear=[{"key": _chiave(ottiche, "m_0.fits"), "optics": "Takahashi FSQ-85"}])
    assert _ottica_della_posa(ottiche, "m_0.fits") == "Takahashi FSQ-85"
    nomi = {p["name"] for p in gear(ottiche)["instruments"] if p["kind"] == "optics"}
    assert "Takahashi FSQ-85" in nomi


def test_a_pose_that_arrives_later_takes_the_answer_by_itself(ottiche, tmp_path):
    """La risposta sta sulla firma: una posa ASIAIR della notte dopo, a una focale che balla di
    poco, prende l'ottica da sola."""
    apply(ottiche, gear=[{"key": _chiave(ottiche, "a_0.fits"), "optics": NEWTON}])
    _scatto(tmp_path / "lib" / "asiair" / "dopo.fits", 50, **{**ASIAIR, "FOCALLEN": 803})
    _scansiona_ancora(ottiche)
    assert _ottica_della_posa(ottiche, "dopo.fits") == NEWTON


def test_the_answer_is_for_that_camera_only(ottiche, tmp_path):
    """Un'altra camera alla stessa focale e' un'altra firma: la risposta data per una non vale per
    l'altra."""
    _scatto(tmp_path / "lib" / "muta" / "altra.fits", 45, INSTRUME="QHY600M", FOCALLEN=800)
    _scansiona_ancora(ottiche)
    apply(ottiche, gear=[{"key": _chiave(ottiche, "a_0.fits"), "optics": NEWTON}])
    assert _ottica_della_posa(ottiche, "altra.fits") is None
    assert _schede(ottiche)[_chiave(ottiche, "altra.fits")]["answer"] is None


def test_changing_the_answer_moves_the_poses(ottiche):
    """Si cambia idea rispondendo di nuovo: le pose che l'ottica non la dicono vanno con quella
    nuova, e la posa di N.I.N.A., che la sua la dice, resta dov'era."""
    chiave = _chiave(ottiche, "a_0.fits")
    apply(ottiche, gear=[{"key": chiave, "optics": NEWTON}])
    apply(ottiche, gear=[{"key": chiave, "optics": "Askar 107PHQ"}])
    _rilavora_tutto(ottiche)  # rilavorata anche lei: la risposta non passa sopra al file
    assert _ottica_della_posa(ottiche, "a_1.fits") == "Askar 107PHQ"
    assert _ottica_della_posa(ottiche, "n_0.fits") == NEWTON


def test_renaming_the_optics_carries_the_answer(ottiche):
    """La risposta porta il **nome** dell'ottica: rinominata dall'Attrezzatura, la risposta la
    segue, e al giro dopo il nome vecchio non fa rinascere un pezzo."""
    chiave = _chiave(ottiche, "a_0.fits")
    apply(ottiche, gear=[{"key": chiave, "optics": NEWTON}])
    assert correct(ottiche, _pezzo(ottiche, NEWTON), name="Newton 8").status_code == 200
    _rilavora_tutto(ottiche)
    nomi = {p["name"] for p in gear(ottiche)["instruments"] if p["kind"] == "optics"}
    assert NEWTON not in nomi
    assert _ottica_della_posa(ottiche, "a_2.fits") == "Newton 8"
    assert _schede(ottiche)[chiave]["answer"]["optics"] == "Newton 8"


def test_renaming_the_camera_carries_the_answer(ottiche):
    """La firma e' la grafia del file, non il nome della camera: rinominata la camera, la scheda e
    la sua risposta restano, e le pose tengono la loro ottica."""
    chiave = _chiave(ottiche, "a_0.fits")
    apply(ottiche, gear=[{"key": chiave, "optics": NEWTON}])
    assert correct(ottiche, _pezzo(ottiche, CAMERA), name="ASI2600MC").status_code == 200
    _rilavora_tutto(ottiche)
    assert _ottica_della_posa(ottiche, "a_0.fits") == NEWTON
    scheda = _schede(ottiche)[chiave]
    assert (scheda["answer"]["optics"], scheda["frames"]) == (NEWTON, 3)


def test_merging_the_optics_into_another_carries_the_answer(ottiche):
    """Scritta con un nome nuovo, e poi detta la stessa di un'ottica che c'era: l'unione porta la
    risposta sull'ottica tenuta, e quella tolta non rinasce."""
    apply(ottiche, gear=[{"key": _chiave(ottiche, "a_0.fits"), "optics": "Newton 8"}])
    r = correct(ottiche, _pezzo(ottiche, "Newton 8"), merge_into=_pezzo(ottiche, NEWTON))
    assert r.status_code == 200
    _rilavora_tutto(ottiche)
    nomi = {p["name"] for p in gear(ottiche)["instruments"] if p["kind"] == "optics"}
    assert "Newton 8" not in nomi
    assert _ottica_della_posa(ottiche, "a_0.fits") == NEWTON


def test_a_rig_written_by_hand_stays_even_without_poses(ottiche):
    """I corredi rilevati rimasti senza pose spariscono a fine giro; uno scritto a mano no, anche
    vuoto: e' tuo, e lo aspetta la scansione che verra'."""
    body = {"optics_id": _pezzo(ottiche, NEWTON), "camera_id": _pezzo(ottiche, ALTRA)}
    body["focal_mm"] = 1000
    assert ottiche.post("/api/v1/gear/rigs", json=body).status_code in (200, 201)
    _rilavora_tutto(ottiche)
    corredi = {(g["optics"], g["camera"], g["focal_mm"]) for g in gear(ottiche)["rigs"]}
    assert (NEWTON, ALTRA, 1000.0) in corredi


def test_the_name_and_mount_of_the_rig_without_optics_go_with_its_poses(ottiche):
    """Il nome e la montatura che avevi dato al corredo senza ottica non si perdono con la risposta:
    passano al corredo dove vanno le sue pose, e le pose tengono la montatura. Il file senza
    `TELESCOP` la montatura non la dice: senza, resterebbe senza."""
    senza = next(g for g in gear(ottiche)["rigs"] if g["camera"] == ALTRA)
    montatura = ottiche.post("/api/v1/gear/instruments", json={"kind": "mount", "name": "EQ6-R"})
    assert montatura.status_code in (200, 201), montatura.text
    corredo = f"/api/v1/gear/rigs/{senza['id']}"
    assert ottiche.patch(corredo, json={"name": "Il piccolo"}).status_code == 200
    r = ottiche.put(f"{corredo}/mount", json={"mount_id": montatura.json()["id"]})
    assert r.status_code == 200, r.text
    ottiche.app.state.worker.join(10.0)
    chiave = _chiave(ottiche, "m_0.fits")
    # e anche cambiando idea: il corredo della seconda risposta li ritrova
    for ottica in ("Takahashi FSQ-85", "Askar 107PHQ"):
        apply(ottiche, gear=[{"key": chiave, "optics": ottica}])
        nuovo = next(g for g in gear(ottiche)["rigs"] if g["camera"] == ALTRA)
        assert (nuovo["optics"], nuovo["name"], nuovo["mount_id"]) == (
            ottica,
            "Il piccolo",
            montatura.json()["id"],
        )
        with db(ottiche) as conn:
            pose = conn.execute(
                "SELECT f.mount_id FROM frames f JOIN positions p ON p.frame_id = f.id"
                " WHERE p.rel_path LIKE '%m_0.fits'"
            ).fetchone()
        assert pose["mount_id"] == montatura.json()["id"]


def test_a_rig_that_was_already_there_keeps_its_own_word(ottiche):
    """Se le pose vanno in un corredo che c'era gia', quello tiene la sua parola, anche quando e'
    "nessun nome": il nome del corredo senza ottica passa solo a un corredo che nasce li'."""
    senza = next(g for g in gear(ottiche)["rigs"] if g["camera"] == CAMERA and g["optics"] is None)
    r = ottiche.patch(f"/api/v1/gear/rigs/{senza['id']}", json={"name": "Il gemello"})
    assert r.status_code == 200, r.text
    apply(ottiche, gear=[{"key": _chiave(ottiche, "a_0.fits"), "optics": NEWTON}])
    assert next(g for g in gear(ottiche)["rigs"] if g["optics"] == NEWTON)["name"] is None


def test_an_answer_to_a_question_that_is_not_there_is_refused(ottiche):
    """Una risposta per una scheda che non c'e' e' una pagina vecchia: si dice, non si scrive."""
    corpo = {"gear": [{"key": '["nessuna", null, 100.0, 4, 3, null]', "optics": NEWTON}]}
    assert ottiche.post("/api/v1/review/apply", json=corpo).status_code == 404


def test_the_camera_question_does_not_offer_the_mount_as_optics(db_path, tmp_path):
    """Se la posa non dice la camera, la scheda propone come ottica cio' che dice `TELESCOP` -- ma
    con l'ASIAIR li' c'e' la montatura, e proporla sarebbe riempire il campo con un pezzo
    sbagliato."""
    root = tmp_path / "lib"
    senza_camera = {k: v for k, v in ASIAIR.items() if k != "INSTRUME"}
    _scatto(root / "asiair" / "s_0.fits", 0, **senza_camera)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        schede = review(c)["gear"]
    assert [(g["telescope"], g["optics"]) for g in schede] == [("ZWO AM5", None)]


def test_a_mixed_group_does_not_offer_the_mount_as_optics_either(db_path, tmp_path):
    """Lo stesso `TELESCOP` scritto dall'ASIAIR e da un altro programma: due firme, perche' per
    l'ASIAIR e' la montatura e non entra nella firma. Ma se l'ASIAIR dice che quel nome e' la
    montatura, nessuna scheda lo propone come ottica."""
    root = tmp_path / "lib"
    senza_camera = {k: v for k, v in ASIAIR.items() if k != "INSTRUME"}
    _scatto(root / "asiair" / "s_0.fits", 0, **senza_camera)
    _scatto(root / "nina" / "s_1.fits", 1, **{**senza_camera, "CREATOR": "N.I.N.A."})
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        schede = review(c)["gear"]
    assert [(g["telescope"], g["frames"], g["optics"]) for g in schede] == [
        ("ZWO AM5", 1, None),
        ("ZWO AM5", 1, None),
    ]


def test_two_mount_names_of_one_asiair_are_one_card(db_path, tmp_path):
    """Con l'ASIAIR `TELESCOP` e' la montatura, e non dice niente dell'ottica: due nomi di
    montatura con la stessa camera alla stessa focale sono una scheda sola, non due domande sulla
    stessa ottica."""
    root = tmp_path / "lib"
    _scatto(root / "asiair" / "a.fits", 0, **ASIAIR)
    _scatto(root / "asiair" / "b.fits", 1, **{**ASIAIR, "TELESCOP": "EQMod Mount"})
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        schede = review(c)["gear"]
    assert [(g["camera"], g["frames"], g["asks_optics"]) for g in schede] == [(CAMERA, 2, True)]
