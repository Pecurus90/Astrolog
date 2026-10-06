"""Le regole della domanda "cosa hai ripreso", provate da sole: il gruppo e' la notte, la camera, il
telescopio e **dove puntava la montatura** (Marco, 24/9/2026: due oggetti della stessa notte senza
nome si separano col puntamento), non la cartella. `OBJECT` non c'entra: qui e' sempre vuoto.
Che poi l'app lo faccia davvero lo guardano `test_review_unnamed.py` e
`test_identify_answer_for_unnamed.py`.
"""

import re

from astrolog.clock import night_date
from astrolog.spine import unnamed
from conftest import add_folder


def test_the_unnamed_groups_start_from_the_poses_without_a_name(conn):
    """I gruppi senza nome partono dalle pose che un gruppo ce l'hanno, con l'indice: partire dagli
    stadi del cielo vuol dire passare da ogni posa dell'archivio a ogni apertura della pagina."""
    piano = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + unnamed._BY_GROUP))
    assert re.search(r"INDEX frames_unnamed\b", piano), piano
    assert "frame_stages_pending" not in piano, piano


NOTTE = "2024-03-12T21:00:00"
ROSETTA, M81 = (98.0, 4.9), (149.0, 69.0)


def _posa(conn, folder_id, rel_path, *, date: str | None = NOTTE, pointing=ROSETTA,
          focal: float | None = 400.0, pixel=4.3, height=4000, instrument="Canon EOS 700D",
          telescope=None):  # fmt: skip
    """Una posa senza nome e senza cielo, a solver concluso, che arriva: prende il suo gruppo come
    glielo da' `identify`."""
    ra, dec = pointing if pointing else (None, None)
    notte = night_date(date)  # come la scrive `scan` senza sito
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, date_obs, local_night, object_raw,"
        " instrument_raw, telescope_raw, ra_hint_deg, dec_hint_deg, focal_mm_raw, pixel_size_um,"
        " naxis1, naxis2, header_json, created_at)"
        " VALUES(?, 'light', ?, ?, NULL, ?, ?, ?, ?, ?, ?, 6000, ?, '[]', 'ora')",
        (
            f"{folder_id}:{rel_path}",
            date,
            notte,
            instrument,
            telescope,
            ra,
            dec,
            focal,
            pixel,
            height,
        ),
    ).lastrowid
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, ?, 1, 1.0, 'ora')",
        (frame_id, folder_id, rel_path),
    )
    conn.execute(
        "INSERT INTO frame_stages(frame_id, stage, status, reason, updated_at)"
        " VALUES(?, 'solve', 'failed', 'no_solution', 'ora')",
        (frame_id,),
    )
    unnamed.assign(conn, frame_id)
    return frame_id


def _chiave(conn, frame_id):
    return unnamed.key_of_frame(conn, frame_id)


def test_two_objects_of_the_same_night_are_two_questions(conn):
    """Stessa notte, stessa camera, nessun nome: la montatura puntava in due posti, e sono due
    domande. Due cartelle con lo stesso puntamento invece sono una domanda sola."""
    radice = add_folder(conn, "D:/Astro")
    rosetta = _posa(conn, radice, "Rosetta/r_0.fits")
    altra = _posa(conn, radice, "altra/r_1.fits")
    m81 = _posa(conn, radice, "M81/m_0.fits", pointing=M81)
    assert _chiave(conn, rosetta) == _chiave(conn, altra) != _chiave(conn, m81)
    assert sorted(g["frames"] for g in unnamed.by_group(conn)) == [1, 2]


def test_a_dither_stays_in_the_same_group(conn):
    """Il dithering e l'inseguimento spostano il puntamento di poco rispetto al campo inquadrato:
    lo stesso oggetto resta un gruppo, che dista meno di un campo inquadrato."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "R/a.fits", pointing=(98.00, 4.90))
    b = _posa(conn, radice, "R/b.fits", pointing=(98.05, 4.93))
    assert _chiave(conn, a) == _chiave(conn, b)


def test_what_must_not_split_a_group(conn):
    """Lo stesso oggetto resta un gruppo dovunque cada: una focale che nell'header oscilla di
    qualche per cento, un dithering a cavallo di RA 0, l'emisfero sud e il polo. Non c'e' una
    griglia, quindi non ci sono bordi."""
    radice = add_folder(conn, "D:/Astro")
    casi = [
        ((300.0, 30.0), (300.0, 30.0), {"focal": 2000.0}, {"focal": 2004.0}),
        ((350.0, 70.02), (350.0, 70.04), {}, {}),
        ((359.99, 10.0), (0.01, 10.0), {}, {}),
        ((120.0, -45.02), (120.01, -45.03), {}, {}),
        ((10.0, 89.97), (200.0, 89.98), {}, {}),
    ]
    for i, (p1, p2, h1, h2) in enumerate(casi):
        a = _posa(conn, radice, f"C{i}/a.fits", pointing=p1, **h1)
        b = _posa(conn, radice, f"C{i}/b.fits", pointing=p2, **h2)
        assert _chiave(conn, a) == _chiave(conn, b), (p1, p2, h1, h2)


def test_without_pointing_or_field_the_night_and_the_header_decide(conn):
    """Un file che non dice dove puntava, o di cui non si sa il campo (niente focale o pixel), non
    ha un puntamento che serva: si separa solo per notte, camera e telescopio."""
    radice = add_folder(conn, "D:/Astro")
    b = _posa(conn, radice, "B/b.fits", pointing=M81, focal=None)
    a = _posa(conn, radice, "A/a.fits", pointing=None)
    c = _posa(conn, radice, "C/c.fits", pointing=(M81[0], None))
    assert _chiave(conn, a) == _chiave(conn, b) == _chiave(conn, c)


def test_another_night_camera_or_telescope_is_another_group(conn):
    """La notte, la camera e il telescopio fanno il gruppo come per la domanda sulla camera:
    un'altra notte e' un'altra domanda, perche' l'oggetto puo' essere cambiato."""
    radice = add_folder(conn, "D:/Astro")
    base = _posa(conn, radice, "R/a.fits")
    chiavi = {
        _chiave(conn, _posa(conn, radice, "R/b.fits", date="2024-03-20T21:00:00")),
        _chiave(conn, _posa(conn, radice, "R/c.fits", instrument="ZWO ASI2600MM")),
        _chiave(conn, _posa(conn, radice, "R/d.fits", telescope="Newton 200/800")),
        _chiave(conn, _posa(conn, radice, "R/e.fits", telescope="RC 8")),
    }
    assert _chiave(conn, base) not in chiavi and len(chiavi) == 4


def test_the_row_says_what_makes_the_group(conn):
    """La riga dice la notte, la camera e il telescopio come li scrive il file, e dove puntava: e'
    cio' che la distingue dalle altre, al posto del percorso di una cartella."""
    radice = add_folder(conn, "D:/Astro")
    _posa(conn, radice, "R/a.fits", telescope="  Newton 200/800 ")
    (riga,) = unnamed.by_group(conn)
    assert {k: riga[k] for k in ("night", "camera", "telescope")} == {
        "night": "2024-03-12",
        "camera": "Canon EOS 700D",
        "telescope": "Newton 200/800",
    }
    assert (riga["ra_deg"], riga["dec_deg"]) == ROSETTA


def test_the_group_is_measured_from_who_opened_it(conn):
    """Chi arriva si confronta col puntamento di chi ha aperto il gruppo, non con l'ultima posa
    entrata: una fila di pose a meno di un campo l'una dall'altra non allunga il gruppo a catena.
    Il campo qui e' di circa 2,5 gradi."""
    radice = add_folder(conn, "D:/Astro")
    pose = [_posa(conn, radice, f"R/{i}.fits", pointing=(98.0 + 1.5 * i, 4.9)) for i in range(3)]
    assert _chiave(conn, pose[0]) == _chiave(conn, pose[1]) != _chiave(conn, pose[2])


def test_the_group_is_written_once(conn):
    """Il gruppo si sceglie quando la posa arriva, e non si rifa' quando ne arrivano altre: una
    posa gia' in un gruppo ci resta anche se dopo ne arriva uno piu' vicino."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "R/a.fits", pointing=(98.0, 4.9))
    b = _posa(conn, radice, "R/b.fits", pointing=(100.0, 4.9))
    prima = _chiave(conn, b)
    c = _posa(conn, radice, "R/c.fits", pointing=(101.5, 4.9))
    assert _chiave(conn, c) != prima
    assert unnamed.assign(conn, b) == prima == _chiave(conn, a)


def test_the_answer_reaches_a_pose_of_the_same_group_in_another_folder(conn):
    """La risposta si scrive sul gruppo e la ritrova chi lo compone dalla posa: `identify` la legge
    anche per un file in un'altra cartella, se notte, puntamento e il resto sono gli stessi."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "R/a.fits")
    b = _posa(conn, radice, "altrove/b.fits")
    unnamed.declare(conn, _chiave(conn, a), name="Rosetta")
    assert unnamed.named_by_group(conn, _chiave(conn, b)) == ("Rosetta", None)


def test_the_answer_hangs_on_the_poses_not_on_a_key_with_the_night(conn):
    """La risposta si scrive sull'impronta di ogni posa del gruppo, non su una chiave con la notte
    (ADR 0014, S2): cambiare il fuso di casa non la sposta, e un backup la ritrova."""
    radice = add_folder(conn, "D:/Astro")
    pose = [_posa(conn, radice, f"R/{i}.fits") for i in range(2)]
    unnamed.declare(conn, _chiave(conn, pose[0]), name="Rosetta")
    righe = conn.execute(
        "SELECT entity_type, entity_key, value FROM declarations WHERE field = 'object'"
        " AND entity_type <> 'object'"
    ).fetchall()
    impronte = {f"{radice}:R/{i}.fits" for i in range(2)}
    assert {tuple(r) for r in righe} == {("frame", k, "name:Rosetta") for k in impronte}


def test_the_answer_follows_its_poses_into_another_group(conn):
    """Una posa che cambia gruppo -- la notte si sposta col fuso di casa -- porta con se' la sua
    risposta: nessuno la deve trasportare."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "R/a.fits")
    unnamed.declare(conn, _chiave(conn, a), name="Rosetta")
    conn.execute(
        "UPDATE frames SET unnamed_key = NULL, local_night = '2024-03-13' WHERE id = ?", (a,)
    )
    assert unnamed.named_by_group(conn, unnamed.assign(conn, a)) == ("Rosetta", None)


def test_changing_my_mind_reaches_a_missing_pose_too(conn):
    """Si cambia idea dopo che un file e' sparito: la risposta nuova si scrive anche sul mancante,
    o il gruppo resterebbe con due risposte e una domanda che rispondere non chiude."""
    radice = add_folder(conn, "D:/Astro")
    a = _posa(conn, radice, "R/a.fits")
    b = _posa(conn, radice, "R/b.fits")
    chiave = _chiave(conn, a)
    unnamed.declare(conn, chiave, name="Rosetta")
    conn.execute("UPDATE positions SET status = 'missing' WHERE frame_id = ?", (b,))
    unnamed.declare(conn, chiave, name="Caldwell 49")
    assert unnamed.named_by_group(conn, chiave) == ("Caldwell 49", None)


def test_two_answers_in_one_group_are_no_answer(conn):
    """Due pose dello stesso gruppo con risposte diverse: il gruppo non ne sceglie una, la domanda
    torna aperta; una posa senza risposta prende quella del gruppo."""
    radice = add_folder(conn, "D:/Astro")
    chiave = _chiave(conn, _posa(conn, radice, "R/a.fits"))
    _posa(conn, radice, "R/b.fits")
    unnamed.declare(conn, chiave, name="Rosetta")
    _posa(conn, radice, "R/dopo.fits")
    assert unnamed.named_by_group(conn, chiave) == ("Rosetta", None)
    conn.execute(
        "UPDATE declarations SET value = 'name:Caldwell 49' WHERE entity_key = ?",
        (f"{radice}:R/b.fits",),
    )
    assert unnamed.answer(conn, chiave) is None
