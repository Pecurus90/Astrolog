"""Da confermare, le pose che non dicono con che camera sono state riprese: una domanda per
gruppo, cioe' per notte e valori dell'header (Marco, 23/9/2026), non per cartella.

Ci cadono anche le pose che portano il telescopio ma non la camera -- l'ASIAIR scrive la montatura
in `TELESCOP` -- che finiscono in un corredo mezzo vuoto e che nessuna domanda elencava. Si risponde
scegliendo un corredo fra quelli che l'app conosce, oppure scrivendo ottica e camera: i pezzi
nascono dai nomi, come nascono da un header. Le regole stanno in `spine/rigless.py` e nel contratto
`docs/domini/spina.md`.
"""

import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import rigless
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from conftest import (
    apply,
    by_name,
    correct,
    db,
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
    """Una posa che NON dice il filtro: cosi' si vede anche la domanda che viene dopo."""
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0}
    if minuto is not None:
        card["DATE-OBS"] = f"2026-03-14T21:{minuto:02d}:00"
        card["OBJECT"] = "M 51"
    return write_fits(path, {**card, **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):  # l'ASIAIR: la montatura in TELESCOP, la camera da nessuna parte
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


def _chiave(client, sotto, nome=""):
    """La chiave del gruppo delle pose senza camera di quella cartella -- nell'archivio di prova ne
    fa uno solo --, o del gruppo di quel file."""
    with db(client) as conn:
        riga = conn.execute(
            "SELECT f.* FROM frames f JOIN positions p ON p.frame_id = f.id"
            " WHERE p.rel_path LIKE ? AND f.instrument_raw IS NULL ORDER BY f.id",
            (f"{sotto}/{nome or '%'}",),
        ).fetchone()
        return rigless.key_of_frame(conn, riga)


def _gruppi(client):
    return {g["key"]: g for g in review(client)["rigless"]}


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


def test_a_group_says_what_the_sky_found_in_it(pagina):
    """Cosa hai ripreso in quel gruppo, per ricordare con che camera (`test_review_subjects`):
    la posa che dice la camera non e' nel gruppo, e quella senza nome ne' cielo non ha oggetto."""
    gruppi = _gruppi(pagina)
    assert gruppi[_chiave(pagina, M51)]["subjects"] == {
        "found": [{"name": "M 51", "frames": 3}],
        "not_found": 0,
        "not_yet": 0,
    }
    assert gruppi[_chiave(pagina, MUTA)]["subjects"] == {"found": [], "not_found": 1, "not_yet": 0}


def test_an_object_with_only_copies_in_a_group_is_not_something_imaged_there(pagina):
    """Una copia calibrata non e' un'altra posa: se in quel gruppo un oggetto ha solo copie,
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
    assert _gruppi(pagina)[_chiave(pagina, M51)]["subjects"]["found"] == [
        {"name": "M 51", "frames": 2}
    ]


def test_a_question_per_group_with_the_largest_first(pagina):
    """Una domanda per gruppo -- la notte e i valori dell'header, detti a video --, il piu'
    numeroso in cima, con quello che le pose dicono gia': il telescopio come indizio e la focale se
    la scrivono. La posa che la camera la dice non entra in nessun gruppo, e quella che non dice
    nemmeno l'oggetto o l'ora si chiede come le altre, nella notte in cui il file fu scritto."""
    assert [senza_soggetti(g) for g in review(pagina)["rigless"]] == [
        {
            "key": _chiave(pagina, M51),
            "night": "2026-03-14",
            "telescope": MONTATURA,
            "width_px": 4,
            "height_px": 3,
            "pixel_um": None,
            "frames": 3,
            "optics": MONTATURA,
            "focal_mm": None,
            "focal_suggested": None,
            "answer": None,
        },
        {
            "key": _chiave(pagina, NGC),
            "night": "2026-03-14",
            "telescope": None,
            "width_px": 4,
            "height_px": 3,
            "pixel_um": None,
            "frames": 1,
            "optics": None,
            "focal_mm": None,
            "focal_suggested": None,
            "answer": None,
        },
        {
            "key": _chiave(pagina, MUTA),
            "night": "2026-03-20",
            "telescope": None,
            "width_px": 4,
            "height_px": 3,
            "pixel_um": None,
            "frames": 1,
            "optics": None,
            "focal_mm": None,
            "focal_suggested": None,
            "answer": None,
        },
    ]


def test_answering_with_the_pieces_makes_the_rig_and_moves_the_poses(pagina):
    """Si scrivono ottica, camera e focale: i pezzi nascono dai nomi -- come nascono da un header --
    e le pose passano da quel corredo. L'ottica dichiarata **vince** su `TELESCOP`, che qui portava
    la montatura: e' la ragione per cui questa domanda esiste. Il gruppo resta in pagina con la sua
    risposta, perche' si deve poter cambiare idea."""
    out = apply(
        pagina,
        rigless=[
            {"key": _chiave(pagina, M51), "optics": OTT, "camera": CAM, "focal_mm": 800.0},
        ],
    )
    assert out["requeued"] == 3
    assert _corredo_della_posa(pagina, "a_0.fits") == (OTT, CAM, 800.0)
    assert _gruppi(pagina)[_chiave(pagina, M51)]["answer"] == {
        "optics": OTT,
        "camera": CAM,
        "focal_mm": 800.0,
    }
    # fra cui scegliere: il corredo mezzo vuoto nato dalla sola montatura, rimasto a zero pose,
    # non si offre piu'
    corredi = review(pagina)["rig_choices"]
    assert [(r["optics"], r["camera"]) for r in corredi] == [(OTT, CAM), (MONTATURA, DETTA)]


def test_the_camera_written_by_hand_becomes_a_piece_and_the_filter_question_follows(pagina):
    """La camera scritta a mano diventa un pezzo dell'attrezzatura con la sua scheda da compilare, e
    da quel momento le sue pose entrano nella domanda dopo: non dicono il filtro, e ora c'e' una
    camera a cui chiederlo. Prima della risposta quelle pose non stavano in nessuna domanda -- la
    sola camera a cui si chiedeva era quella che un file nomina."""
    assert [g["key"] for g in review(pagina)["unfiltered"]] == [DETTA]
    apply(pagina, rigless=[{"key": _chiave(pagina, M51), "camera": CAM, "focal_mm": 800.0}])
    scheda = by_name(gear(pagina)["instruments"], CAM)
    assert (scheda["kind"], scheda["frames"], scheda["pixel_size_um"]) == ("camera", 3, None)
    assert [g["key"] for g in review(pagina)["unfiltered"]] == [CAM, DETTA]


def test_choosing_a_rig_from_the_list_writes_its_names(pagina):
    """Si puo' rispondere scegliendo un corredo fra quelli che l'app conosce: si manda il suo
    numero di riga, che e' cio' che la pagina ha in mano dopo un clic, ma a essere scritti sono i
    **nomi** dei suoi pezzi -- un'unione cancella la riga rilevata, e una risposta scritta sul suo
    numero non sopravviverebbe a un azzeramento del rilevato."""
    apply(pagina, rigless=[{"key": _chiave(pagina, M51), "camera": CAM, "focal_mm": 800.0}])
    corredo = next(r for r in review(pagina)["rig_choices"] if r["camera"] == CAM)
    apply(pagina, rigless=[{"key": _chiave(pagina, NGC), "rig_id": corredo["id"]}])
    # il corredo scelto porta anche la sua ottica: si scegle un corredo intero, non la sola camera
    assert _gruppi(pagina)[_chiave(pagina, NGC)]["answer"] == {
        "optics": MONTATURA,
        "camera": CAM,
        "focal_mm": 800.0,
    }
    assert _corredo_della_posa(pagina, "b_0.fits") == (MONTATURA, CAM, 800.0)


def test_a_rig_without_a_camera_does_not_answer_this_question(pagina):
    """Il corredo mezzo vuoto nato dalla sola montatura non risponde: sceglierlo lascerebbe le pose
    esattamente dove sono. Non si offre, e mandarlo lo stesso si dice invece di scrivere una
    risposta che non sposta niente. Una casa sola per l'elenco e per chi lo rifiuta
    (`review_page.rig_choices`)."""
    with db(pagina) as conn:
        mezzo = conn.execute("SELECT id FROM rigs WHERE camera_id IS NULL").fetchone()
    assert mezzo["id"] not in [r["id"] for r in review(pagina)["rig_choices"]]
    corpo = {"rigless": [{"key": _chiave(pagina, M51), "rig_id": mezzo["id"]}]}
    r = pagina.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "unknown_target"


def test_the_declared_focal_does_not_leave_two_twin_rigs(pagina, tmp_path):
    """Un corredo e' ottica + camera **a una focale**, e una focale ignota non e' la stessa cosa di
    una focale nota: senza chiedere la focale, il corredo nato dalla risposta e quello che le pose
    diranno domani sarebbero due corredi gemelli per sempre, con le ore spartite fra i due
    (misurato su `rigs.rig_for`). Con la focale dichiarata la riga e' una sola."""
    apply(pagina, rigless=[{"key": _chiave(pagina, M51), "camera": CAM, "focal_mm": 800.0}])
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
    """La risposta e' un fatto sul gruppo, non su quelle pose: una posa che arriva dopo con la
    stessa notte e gli stessi valori la riceve, anche da un'altra cartella. La dichiarazione si
    rilegge a ogni giro, e per questo sopravvive anche a un azzeramento del rilevato."""
    apply(
        pagina,
        rigless=[{"key": _chiave(pagina, M51), "optics": OTT, "camera": CAM, "focal_mm": 800.0}],
    )
    _posa(tmp_path / "lib" / "altrove" / "dopo.fits", 31, TELESCOP=MONTATURA)
    _scansiona_ancora(pagina)
    assert _corredo_della_posa(pagina, "dopo.fits") == (OTT, CAM, 800.0)
    # e un'altra notte e' un'altra domanda, anche nella stessa cartella: l'attrezzatura puo'
    # essere cambiata
    _posa(tmp_path / "lib" / M51 / "e_0.fits", 40, TELESCOP=MONTATURA,
          **{"DATE-OBS": "2026-04-02T21:40:00"})  # fmt: skip
    _scansiona_ancora(pagina)
    altra = _gruppi(pagina)[_chiave(pagina, M51, "e_0.fits")]
    assert (altra["night"], altra["answer"]) == ("2026-04-02", None)


def test_the_focal_of_the_optics_card_is_what_the_page_proposes(pagina):
    """Se le pose non dicono la focale, la pagina propone quella nativa dell'ottica che l'utente ha
    in scheda: la risposta ha un valore da offrire invece di un campo vuoto."""
    ottica = by_name(gear(pagina)["instruments"], MONTATURA)
    assert correct(pagina, ottica["id"], focal_mm=800.0).status_code == 200
    assert _gruppi(pagina)[_chiave(pagina, M51)]["focal_suggested"] == 800.0


def test_answering_again_moves_the_poses_to_the_new_rig(pagina):
    """Si cambia idea rispondendo di nuovo: le pose lasciano il corredo di prima e passano a quello
    nuovo, invece di restare su una risposta che l'utente ha ritirato."""
    apply(pagina, rigless=[{"key": _chiave(pagina, MUTA), "camera": CAM, "focal_mm": 800.0}])
    assert _corredo_della_posa(pagina, "c_0.fits") == (None, CAM, 800.0)
    apply(pagina, rigless=[{"key": _chiave(pagina, MUTA), "camera": "Altra", "focal_mm": 250.0}])
    assert _corredo_della_posa(pagina, "c_0.fits") == (None, "Altra", 250.0)


def test_an_unanswered_group_counts_among_the_things_to_confirm(pagina):
    """Un gruppo senza risposta e' una domanda aperta e si conta; quello a cui si e' risposto resta
    in pagina ma non si conta piu'. Un conto che tornasse a zero con delle pose ancora senza corredo
    sarebbe un conto che mente -- ed e' il buco per cui questa domanda e' nata."""
    letta = review(pagina)
    assert [g["answer"] is None for g in letta["rigless"]].count(True) == 3
    assert letta["to_confirm"] == to_confirm_without(letta, "rigless") + 3
    apply(pagina, rigless=[{"key": _chiave(pagina, MUTA), "camera": CAM, "focal_mm": 800.0}])
    dopo = review(pagina)
    assert [g["answer"] is None for g in dopo["rigless"]].count(True) == 2
    # il gruppo risposto resta in pagina, e non conta piu'
    assert len(dopo["rigless"]) == len(letta["rigless"])
    assert dopo["to_confirm"] == to_confirm_without(dopo, "rigless") + 2


def test_after_the_answer_the_filter_question_reaches_those_poses(pagina):
    """La catena deve arrivare **in fondo**: risposto il corredo, quelle pose entrano nella domanda
    sul filtro e la risposta le raggiunge davvero. Prima no -- il filtro cercava la camera solo
    nell'header, dove non c'e' -- e restavano senza filtro mentre la pagina diceva "niente da
    confermare": lo stesso conto che mente per cui questa domanda e' nata."""
    apply(pagina, rigless=[{"key": _chiave(pagina, M51), "camera": CAM, "focal_mm": 800.0}])
    assert _senza_filtro(pagina, M51) == 3  # il corredo c'e', il filtro no: la domanda si apre
    apply(pagina, unfiltered=[{"key": CAM, "answer": "no_filter"}])
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
    """Un gruppo su cui non c'e' nessuna posa da chiedere e' una pagina vecchia, e si dice:
    scrivere una risposta verso il nulla la lascerebbe li' per sempre senza che nessuno la veda."""
    corpo = {"rigless": [{"key": "/mai/vista", "camera": CAM, "focal_mm": 800.0}]}
    r = pagina.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 404


@pytest.mark.parametrize(
    "corpo, perche_",
    [
        ({"key": "/x"}, "ne' un corredo ne' una camera"),
        ({"key": "/x", "camera": CAM, "rig_id": 1}, "tutti e due"),
        ({"key": "/x", "rig_id": 1, "optics": OTT}, "un corredo porta i suoi pezzi"),
        ({"key": "/x", "camera": ""}, "una camera senza nome"),
        ({"key": "/x", "camera": CAM, "focal_mm": 0}, "una focale che non e' una focale"),
        ({"key": "/x", "camera": CAM}, "la camera senza la sua focale: nascerebbe un gemello"),
    ],
)
def test_an_answer_that_says_two_things_or_none_is_refused(pagina, corpo, perche_):
    """Un corredo dall'elenco **oppure** i pezzi scritti: accettarli tutti e due vorrebbe dire
    scegliere noi quale vince, e nessuna delle due scelte e' quella dell'utente."""
    r = pagina.post("/api/v1/review/apply", json={"rigless": [corpo]})
    assert r.status_code == 422, perche_


def _camera_della_posa(client, nome):
    return (_corredo_della_posa(client, nome) or (None, None, None))[1]


def test_a_pose_without_camera_takes_the_one_of_its_night(pagina, tmp_path):
    """Se gli altri frame della stessa notte dicono una camera sola, e' quella (Marco, 23/9/2026):
    non si chiede. Vale anche se arriva dopo, in un'altra cartella; la posa che non dice quando e'
    stata ripresa sta nella notte del suo file, dove nessuno dice la camera, e resta da chiedere."""
    _posa(tmp_path / "lib" / "altra" / "cam.fits", 30, INSTRUME=CAM)
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") == CAM
    assert _camera_della_posa(pagina, "b_0.fits") == CAM
    assert set(_gruppi(pagina)) == {_chiave(pagina, MUTA)}


def test_in_one_scan_the_order_of_the_files_does_not_matter(db_path, tmp_path):
    """La posa senza camera prende quella della notte anche se il file che la dice arriva nella
    stessa scansione, prima o dopo di lei."""
    root = tmp_path / "lib"
    _posa(root / "a" / "senza.fits", 1)
    _posa(root / "z" / "detta.fits", 2, INSTRUME=CAM)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        assert _camera_della_posa(c, "senza.fits") == CAM
        assert review(c)["rigless"] == []


def test_two_cameras_in_the_night_leave_the_question(pagina, tmp_path):
    """Due camere nella stessa notte: quale fosse non si indovina, e il gruppo si chiede. Anche
    quando la seconda arriva dopo che la prima aveva gia' risposto per la notte."""
    _posa(tmp_path / "lib" / "altra" / "cam.fits", 30, INSTRUME=CAM)
    _scansiona_ancora(pagina)
    _posa(tmp_path / "lib" / "altra" / "detta.fits", 31, INSTRUME=DETTA)
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") is None
    assert _chiave(pagina, M51) in _gruppi(pagina)


def test_the_answer_moves_only_the_poses_of_its_night(pagina, tmp_path):
    """Un gruppo e' una notte: una posa della stessa cartella ripresa in un'altra notte sta in un
    altro gruppo -- qui la sua notte le da' la camera da sola --, e la risposta non la sposta. La
    riga conta cio' che la risposta sposta, niente di piu'."""
    _posa(tmp_path / "lib" / M51 / "x.fits", 1, **{"DATE-OBS": "2026-03-16T22:00:00"})
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "x.fits") == DETTA  # la sua notte ha solo DETTA
    assert _gruppi(pagina)[_chiave(pagina, M51)]["frames"] == 3
    apply(pagina, rigless=[{"key": _chiave(pagina, M51), "camera": CAM, "focal_mm": 800.0}])
    assert _camera_della_posa(pagina, "x.fits") == DETTA
    assert _camera_della_posa(pagina, "a_0.fits") == CAM


def test_two_spellings_of_one_camera_are_one_camera_of_the_night(pagina, tmp_path):
    """Due grafie nella stessa notte sono due camere finche' nessuno le unisce: il gruppo si
    chiede. Unite, la notte ha una camera sola, e le pose la prendono."""
    lib = tmp_path / "lib" / "altra"
    _posa(lib / "cam.fits", 30, INSTRUME=CAM)
    _posa(lib / "grafia.fits", 31, INSTRUME="ASI2600MM")
    _scansiona_ancora(pagina)
    assert _chiave(pagina, M51) in _gruppi(pagina)
    pezzi = {i["name"]: i["id"] for i in gear(pagina)["instruments"]}
    correct(pagina, pezzi["ASI2600MM"], merge_into=pezzi[CAM])
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") == CAM
    assert _chiave(pagina, M51) not in _gruppi(pagina)


def test_my_answer_on_the_group_wins_over_the_night(pagina, tmp_path):
    """La risposta sul gruppo e' scritta, e vince su cio' che la notte fa dedurre: il gruppo resta
    in pagina con la risposta, per poterla cambiare."""
    apply(pagina, rigless=[{"key": _chiave(pagina, M51), "camera": DETTA, "focal_mm": 800.0}])
    _posa(tmp_path / "lib" / "altra" / "cam.fits", 30, INSTRUME=CAM)
    _scansiona_ancora(pagina)
    assert _camera_della_posa(pagina, "a_0.fits") == DETTA
    assert _gruppi(pagina)[_chiave(pagina, M51)]["frames"] == 3
