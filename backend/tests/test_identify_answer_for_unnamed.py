"""La regola delle pose **senza nome e senza cielo**: l'oggetto detto per il loro gruppo -- notte,
camera, telescopio e puntamento --, letto da `identify` a ogni giro (`spine/unnamed.py`). Qui la
dichiarazione si scrive a mano, come la scriverebbe la risposta dalla pagina.

Regole, e il test che le rompe:

* **Un oggetto detto per il gruppo aggancia le sue pose senza nome**, di catalogo o scritto, come
  parola dell'utente (`user`/`user`); **"non e' un oggetto"** le chiude senza oggetto e non le conta
  fra quelle che aspettano una risposta.
* **Vale per le pose che arriveranno**, e **si cambia idea** riscrivendo la dichiarazione.
* **Il cielo vince**: dove ha dei candidati la regola non tocca la posa; una posa che il nome lo
  scrive non la prende.
* **Una posa risolta a cono vuoto resta nel gruppo** anche agganciata, o il gruppo risposto si
  svuoterebbe da solo; e anche mentre e' in coda per essere rifatta, o sparirebbe dopo ogni Applica.
* **Una riga storta, o una voce di catalogo sparita, vale nessuna risposta**: le pose restano dove
  sono, mai fatte sparire.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import declarations as decl
from astrolog.spine import stages, unnamed
from astrolog.spine.identify import identify_frames
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from conftest import db, populate, review, unnamed_cards, write_fits

ROSETTA, M81 = "2024-03-12_Rosetta/LIGHT", "2024-04-01_M81"


# Dove puntava la montatura: nella stessa notte, con la stessa camera e senza nome, Rosetta e M81
# si separano solo cosi'. Focale e pixel danno il campo, che dice quanto lontano e' un altro.
PUNTA = {ROSETTA: (98.0, 4.9), M81: (149.0, 69.0)}


def _posa(path, minuto, **header):
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 120.0, "INSTRUME": "Canon EOS 700D"}
    card |= {"FOCALLEN": 400.0, "XPIXSZ": 4.3}
    ra, dec = next((p for k, p in PUNTA.items() if k in str(path)), PUNTA[ROSETTA])
    card |= {"RA": ra, "DEC": dec}
    return write_fits(path, {**card, "DATE-OBS": f"2024-03-12T21:{minuto:02d}:00", **header})


@pytest.fixture
def archivio(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):
        _posa(root / ROSETTA / f"r_{i}.fits", i)
    _posa(root / "calibrate" / "r_0.fits", 0, CALSTAT="BDF")  # la copia di r_0, altrove
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", 10 + i)
    _posa(root / M81 / "col_nome.fits", 20, OBJECT="M 81")
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _chiave(client, sotto):
    """La chiave del gruppo delle pose senza nome di quella cartella: qui ne fa uno solo."""
    with db(client) as conn:
        (frame_id,) = conn.execute(
            "SELECT f.id FROM frames f JOIN positions p ON p.frame_id = f.id"
            " WHERE p.rel_path LIKE ? AND f.object_raw IS NULL ORDER BY f.id",
            (f"{sotto}/%",),
        ).fetchone()
        return unnamed.key_of_frame(conn, frame_id)


def _frame(conn, sotto, nome):
    return conn.execute(
        "SELECT p.frame_id FROM positions p WHERE p.rel_path = ?", (f"{sotto}/{nome}",)
    ).fetchone()[0]


def _di(client, sotto, value):
    """Scrive l'oggetto del gruppo di quella cartella e fa rigirare `identify` su tutte le pose:
    torna la ricevuta dello stadio."""
    chiave = _chiave(client, sotto)
    with db(client) as conn:
        for (impronta,) in conn.execute(
            "SELECT frame_hash FROM frames WHERE unnamed_key = ?", (chiave,)
        ).fetchall():
            decl.write_declaration(conn, decl.FRAME, impronta, decl.FRAME_OBJECT, value)
        conn.commit()
    return _rigira(client)


def _rigira(client):
    with db(client) as conn:
        stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "identify")
        return list(identify_frames(conn))[-1]


def _oggetti_dei_file(client, sotto):
    """Il nome dell'oggetto di ogni posa senza nome in quella cartella (copie escluse), e lo stato
    di identify."""
    with db(client) as conn:
        righe = conn.execute(
            "SELECT n.name, s.status, s.reason FROM frames f"
            " JOIN positions p ON p.frame_id = f.id"
            " JOIN frame_stages s ON s.frame_id = f.id AND s.stage = 'identify'"
            " LEFT JOIN object_names n ON n.object_id = f.object_id AND n.is_primary = 1"
            " WHERE p.rel_path LIKE ? AND f.copy_of IS NULL AND f.object_raw IS NULL",
            (f"{sotto}/%",),
        ).fetchall()
    return {tuple(r) for r in righe}


def _frames_nel_gruppo(client, sotto):
    schede = {g["key"]: g["frames"] for g in unnamed_cards(review(client))}
    return schede.get(f"frames:{_chiave(client, sotto)}")


def _col_cielo(client, sotto, nome, ra, dec):
    """Da' a quella posa un cielo misurato a (ra, dec) e la rifa' da `identify`. Torna il suo id."""
    with db(client) as conn:
        frame_id = _frame(conn, sotto, nome)
        conn.execute(
            "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, rotation_deg,"
            " width_deg, height_deg, solved_at) VALUES(?, ?, ?, 3.7, 0, 1.0, 0.7, '2026-09-15')",
            (frame_id, ra, dec),
        )
        stages.invalidate(conn, [frame_id], "identify")
        list(identify_frames(conn))
    return frame_id


def test_a_name_said_for_the_group_puts_its_poses_on_that_object(archivio):
    _di(archivio, ROSETTA, "name:Nebulosa Rosetta")
    assert _oggetti_dei_file(archivio, ROSETTA) == {("Nebulosa Rosetta", "done", None)}
    with db(archivio) as conn:
        riga = conn.execute(
            "SELECT o.identity_method, o.identity_confidence FROM objects o"
            " JOIN object_names n ON n.object_id = o.id WHERE n.name = 'Nebulosa Rosetta'"
        ).fetchone()
    # la parola dell'utente: nessuna posa successiva ne abbassa la fiducia
    assert tuple(riga) == ("user", "user")
    assert _frames_nel_gruppo(archivio, ROSETTA) == 3  # il gruppo risposto resta intero
    assert _oggetti_dei_file(archivio, M81) == {(None, "skipped", "no_name_no_sky")}


def test_not_an_object_closes_the_poses_and_they_wait_for_nothing(archivio):
    ricevuta = _di(archivio, M81, "none")
    assert _oggetti_dei_file(archivio, M81) == {(None, "skipped", "not_an_object")}
    assert _frames_nel_gruppo(archivio, M81) == 2
    # aspettano una risposta le tre di Rosetta e la copia di r_0, altrove; le due di M81 no
    assert ricevuta["waiting"] == 4


def test_i_can_change_my_mind_and_the_poses_follow(archivio):
    _di(archivio, ROSETTA, "name:Nebulosa Rosetta")
    _di(archivio, ROSETTA, "none")
    assert _oggetti_dei_file(archivio, ROSETTA) == {(None, "skipped", "not_an_object")}
    _di(archivio, ROSETTA, "name:Caldwell 49")
    assert _oggetti_dei_file(archivio, ROSETTA) == {("Caldwell 49", "done", None)}


def test_the_rule_holds_for_the_poses_that_arrive_later(archivio, tmp_path):
    _di(archivio, ROSETTA, "name:Nebulosa Rosetta")
    _posa(tmp_path / "lib" / ROSETTA / "r_dopo.fits", 30)
    _posa(tmp_path / "lib" / ROSETTA / "col_nome.fits", 31, OBJECT="Caldwell 49")
    with db(archivio) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))
        for (frame_id,) in conn.execute("SELECT frame_id FROM frame_stages WHERE stage = 'solve'"
                                        " AND status = 'pending'").fetchall():  # fmt: skip
            stages.set_status(conn, frame_id, "solve", "failed", reason="no_solution")
        list(identify_frames(conn))
        (col_nome,) = conn.execute(
            "SELECT n.name FROM frames f JOIN object_names n ON n.object_id = f.object_id"
            " AND n.is_primary = 1 WHERE f.id = ?",
            (_frame(conn, ROSETTA, "col_nome.fits"),),
        ).fetchone()
    assert _oggetti_dei_file(archivio, ROSETTA) == {("Nebulosa Rosetta", "done", None)}
    assert _frames_nel_gruppo(archivio, ROSETTA) == 4
    # la posa che il nome lo scrive non prende l'oggetto del gruppo: non era una domanda
    assert col_nome == "Caldwell 49"


def test_a_solved_pose_whose_sky_finds_nothing_is_reached_and_stays_in_the_group(archivio):
    """Risolta, ma nel cono non c'e' niente (il catalogo qui non e' caricato): la regola la
    raggiunge, e agganciata resta nel gruppo -- se ne uscisse, un gruppo di sole pose cosi'
    sparirebbe dalla pagina appena risposta. Anche dopo "non e' un oggetto"."""
    _col_cielo(archivio, ROSETTA, "r_2.fits", 98.0, 4.9)
    _di(archivio, ROSETTA, "name:Nebulosa Rosetta")
    assert _oggetti_dei_file(archivio, ROSETTA) == {("Nebulosa Rosetta", "done", None)}
    assert _frames_nel_gruppo(archivio, ROSETTA) == 3
    _di(archivio, ROSETTA, "none")
    assert _frames_nel_gruppo(archivio, ROSETTA) == 3


def test_a_pose_whose_sky_finds_nothing_stays_asked_while_it_waits_to_be_redone(archivio):
    """Fra una rimessa in coda e il giro di `identify` la posa non esce dalla sua domanda: dopo un
    Applica la pagina si rilegge mentre il worker gira, e un gruppo fatto solo di pose cosi'
    sparirebbe dalla pagina e dal conto -- con o senza risposta."""
    frame_id = _col_cielo(archivio, ROSETTA, "r_2.fits", 98.0, 4.9)
    for data in (None, "name:Nebulosa Rosetta"):
        if data:
            _di(archivio, ROSETTA, data)
        with db(archivio) as conn:
            stages.invalidate(
                conn, [frame_id], "identify"
            )  # in coda, il worker non e' ancora passato
        assert _frames_nel_gruppo(archivio, ROSETTA) == 3


def test_the_sky_wins_over_the_group_where_it_has_candidates(db_path_col_catalogo, tmp_path):
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", i)
    populate(db_path_col_catalogo, root)
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        su_m81 = _col_cielo(c, M81, "m_1.fits", 148.888, 69.065)
        _di(c, M81, "name:Nebulosa inventata")
        with db(c) as conn:
            slug, metodo, motivo = conn.execute(
                "SELECT o.catalog_slug, o.identity_method, s.reason FROM frames f"
                " JOIN objects o ON o.id = f.object_id"
                " JOIN frame_stages s ON s.frame_id = f.id AND s.stage = 'identify' WHERE f.id = ?",
                (su_m81,),
            ).fetchone()
        # l'oggetto resta cio' che il cielo ha deciso, non "detto dall'utente", e la posa non entra
        # nel gruppo
        assert (slug, metodo != "user", motivo) == ("m-81", True, None)
        assert _frames_nel_gruppo(c, M81) == 1


def test_a_catalog_entry_puts_the_poses_on_its_object(db_path_col_catalogo, tmp_path):
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", i)
    populate(db_path_col_catalogo, root)
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        _di(c, M81, "catalog:m-81")
        assert _oggetti_dei_file(c, M81) == {("M 81", "done", None)}
        with db(c) as conn:
            assert unnamed.answer(conn, _chiave(c, M81)) == {
                "kind": "catalog",
                "value": "m-81",
                "name": "M 81",
            }


@pytest.mark.parametrize(
    "storta",
    [
        "catalog:m-81",  # una voce che il catalogo (qui non caricato) non ha
        "M 81",  # senza il tipo del bersaglio: tagliarla alla cieca darebbe un nome storpiato
        "name:   ",  # un nome fatto di soli spazi non e' un nome
    ],
)
def test_a_crooked_row_or_a_gone_entry_is_no_answer(archivio, storta):
    """La parola dell'utente sposta delle pose, mai le fa sparire: le pose restano una domanda."""
    _di(archivio, ROSETTA, storta)
    assert _oggetti_dei_file(archivio, ROSETTA) == {(None, "skipped", "no_name_no_sky")}
    with db(archivio) as conn:
        assert unnamed.answer(conn, _chiave(archivio, ROSETTA)) is None
