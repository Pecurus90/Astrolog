"""Da confermare, **le pose senza nome e senza cielo**: l'header non dice l'oggetto e il cielo non
dice niente, quindi l'app non ha niente da cui dedurlo. Si chiede per gruppo: notte, camera,
telescopio e dove puntava la montatura (Marco, 24/9/2026), non per cartella.

Regole, e il test che le rompe:

* **Il gruppo non e' la cartella**: due oggetti della stessa notte si separano col puntamento, e le
  regole della chiave le prova `test_unnamed.py`.
* **Il gruppo si riconosce dalla posa** -- il gruppo scritto, niente cielo -- a solver concluso:
  una posa il cui cielo potrebbe ancora arrivare non si chiede.
* **Il cielo che non dice niente vale come nessun cielo**: una posa risolta a cono vuoto si chiede.
* **Un file che non si trova piu' e una cartella ritirata non chiedono niente**: non c'e' niente su
  cui agire.
* **Si risponde dalla pagina** con un oggetto -- di catalogo o scritto -- oppure "non e' un
  oggetto", una risposta sola; risposto, il gruppo resta in pagina con la risposta e si cambia
  idea. Cosa la risposta fa alle pose lo provano i test della regola
  (`test_identify_answer_for_unnamed.py`).
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import stages, unnamed
from astrolog.spine.identify import identify_frames
from conftest import all_objects, apply, db, populate, review, unnamed_cards, write_fits

ROSETTA, M81, CALIBRATE = "2024-03-12_Rosetta/LIGHT", "2024-04-01_M81", "calibrate"


# Dove puntava la montatura: Rosetta e M81 nella stessa notte, con la stessa camera e senza nome,
# si separano solo cosi'. Focale e pixel danno il campo, che dice quanto lontano e' un altro.
PUNTA = {ROSETTA: (98.0, 4.9), M81: (149.0, 69.0)}


def _posa(path, minuto, **header):
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 120.0, "INSTRUME": "Canon EOS 700D"}
    card |= {"FOCALLEN": 400.0, "XPIXSZ": 4.3}
    ra, dec = next((p for k, p in PUNTA.items() if k in str(path)), PUNTA[ROSETTA])
    card |= {"RA": ra, "DEC": dec}
    return write_fits(path, {**card, "DATE-OBS": f"2024-03-12T21:{minuto:02d}:00", **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):
        _posa(root / ROSETTA / f"r_{i}.fits", i)
    _posa(root / CALIBRATE / "r_0.fits", 0, CALSTAT="BDF")  # la copia di r_0, in un'altra cartella
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", 10 + i)
    _posa(root / M81 / "col_nome.fits", 20, OBJECT="M 81")  # il nome c'e': non si chiede
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _chiave(client, sotto):
    """La chiave della scheda del gruppo delle pose senza nome di quella cartella: nell'archivio di
    prova ogni cartella ne fa uno solo."""
    with db(client) as conn:
        (frame_id,) = conn.execute(
            "SELECT f.id FROM frames f JOIN positions p ON p.frame_id = f.id"
            " WHERE p.rel_path LIKE ? AND f.object_raw IS NULL ORDER BY f.id",
            (f"{sotto}/%",),
        ).fetchone()
        return f"frames:{unnamed.key_of_frame(conn, frame_id)}"


def _gruppi(client):
    return {g["key"]: g for g in unnamed_cards(review(client))}


def _col_cielo(client, sotto, nome, ra, dec):
    """Da' a quella posa un cielo misurato a (ra, dec) e la rimette in coda da `identify`: e' lo
    stato di una posa che il solver ha risolto. Torna il suo id."""
    with db(client) as conn:
        (frame_id,) = conn.execute(
            "SELECT p.frame_id FROM positions p WHERE p.rel_path = ?", (f"{sotto}/{nome}",)
        ).fetchone()
        conn.execute(
            "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, rotation_deg,"
            " width_deg, height_deg, solved_at) VALUES(?, ?, ?, 3.7, 0, 1.0, 0.7, '2026-09-15')",
            (frame_id, ra, dec),
        )
        stages.invalidate(conn, [frame_id], "identify")
        list(identify_frames(conn))
    return frame_id


def _senza_ore(scheda):
    ore = ("first_frame", "last_frame")
    return {**scheda, "group": {k: v for k, v in scheda["group"].items() if k not in ore}}


def _scheda(key, ra_deg, dec_deg, frames, answer):
    """A group card as the page shows it, hours aside: 120 s frames, nothing found by the app."""
    return {
        "key": key,
        "id": None,
        "name": None,
        "slug": None,
        "method": None,
        "confidence": None,
        "group": {
            "night": "2024-03-12",
            "camera": "Canon EOS 700D",
            "telescope": None,
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
        },
        "frames": frames,
        "integration_s": 120.0 * frames,
        "untimed": 0,
        "confirmed": False,
        "candidates": [],
        "answer": answer,
    }


def test_a_question_per_group_with_what_makes_it(pagina):
    """Una domanda per gruppo, il piu' numeroso in cima, con la notte, la camera, il telescopio e il
    puntamento che lo fanno; la posa col nome non c'e', e la copia calibrata -- in un'altra
    cartella, con lo stesso header -- non e' un'altra posa. Le ore le prova `test_local_night.py`;
    qui, senza sito, sono quelle UTC delle pose."""
    gruppi = unnamed_cards(review(pagina))
    assert (gruppi[0]["group"]["first_frame"], gruppi[0]["group"]["last_frame"]) == (
        "2024-03-12T21:00:00+00:00",
        "2024-03-12T21:02:00+00:00",
    )
    assert [_senza_ore(g) for g in gruppi] == [
        _scheda(_chiave(pagina, ROSETTA), 98.0, 4.9, 3, None),
        _scheda(_chiave(pagina, M81), 149.0, 69.0, 2, None),
    ]


def test_a_pose_the_solver_has_not_looked_at_yet_is_not_asked(pagina):
    """Il cielo di quella posa potrebbe ancora arrivare: chiederne l'oggetto adesso sarebbe chiedere
    cio' che l'app sta per sapere da sola."""
    with db(pagina) as conn:
        (in_attesa,) = conn.execute(
            "SELECT p.frame_id FROM positions p WHERE p.rel_path = ?", (f"{ROSETTA}/r_1.fits",)
        ).fetchone()
        stages.set_status(conn, in_attesa, "solve", "pending")
    assert _gruppi(pagina)[_chiave(pagina, ROSETTA)]["frames"] == 2


def test_a_pose_without_sky_is_asked_whatever_identify_has_done_with_it(pagina):
    """Il gruppo si riconosce dalla posa: una posa senza nome e senza cielo si chiede anche se
    `identify` e' stato rimesso in coda."""
    with db(pagina) as conn:
        (frame_id,) = conn.execute(
            "SELECT p.frame_id FROM positions p WHERE p.rel_path = ?", (f"{ROSETTA}/r_1.fits",)
        ).fetchone()
        stages.set_status(conn, frame_id, "identify", "pending")
    assert _gruppi(pagina)[_chiave(pagina, ROSETTA)]["frames"] == 3


def test_an_object_made_only_of_spaces_is_not_a_name(pagina):
    """Se un valore e' un nome lo dice il vocabolario, non il fatto che il campo sia pieno."""
    with db(pagina) as conn:
        (frame_id,) = conn.execute(
            "SELECT frame_id FROM positions WHERE rel_path = ?", (f"{M81}/col_nome.fits",)
        ).fetchone()
        conn.execute("UPDATE frames SET object_raw = '   ' WHERE id = ?", (frame_id,))
        stages.invalidate(conn, [frame_id], "identify")
        list(identify_frames(conn))
    assert _gruppi(pagina)[_chiave(pagina, M81)]["frames"] == 3


def test_a_file_that_is_gone_and_a_retired_folder_do_not_ask_anything(pagina):
    """Su un file sparito o in una cartella ritirata non c'e' niente su cui agire: una domanda li'
    resterebbe aperta per sempre."""
    with db(pagina) as conn:
        conn.execute(
            "UPDATE positions SET status = 'missing' WHERE rel_path = ?", (f"{M81}/m_0.fits",)
        )
    assert _gruppi(pagina)[_chiave(pagina, M81)]["frames"] == 1
    with db(pagina) as conn:
        conn.execute("UPDATE folders SET retired_at = '2026-09-15'")
    assert unnamed_cards(review(pagina)) == []


def test_a_solved_pose_whose_sky_finds_nothing_is_asked_like_the_others(pagina):
    """Risolta, ma nel cono non c'e' niente (qui il catalogo non e' caricato): il cielo non dice
    niente, come per la regola sui nomi, quindi quella posa si chiede."""
    _col_cielo(pagina, ROSETTA, "r_2.fits", 98.0, 4.9)
    assert _gruppi(pagina)[_chiave(pagina, ROSETTA)]["frames"] == 3


def test_a_pose_whose_sky_has_candidates_is_not_asked(db_path_col_catalogo, tmp_path):
    """Dove il cielo ha candidati decide lui: quella posa non si chiede."""
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", i)
    populate(db_path_col_catalogo, root)
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        _col_cielo(c, M81, "m_1.fits", 148.888, 69.065)
        assert _gruppi(c)[_chiave(c, M81)]["frames"] == 1


def test_answering_with_a_name_moves_the_poses_and_the_group_keeps_its_answer(pagina):
    """La risposta arriva allo stadio -- l'Applica lo avvia, e le pose vanno su quell'oggetto -- e
    il gruppo resta in pagina con la risposta, perche' si deve poter cambiare idea."""
    out = apply(pagina, objects=[{"key": _chiave(pagina, ROSETTA), "name": "Nebulosa Rosetta"}])
    assert out["requeued"] == 4  # anche la copia in `calibrate/`: stesso header, stesso gruppo
    assert {o["name"]: o["frames"] for o in all_objects(pagina)}["Nebulosa Rosetta"] == 3
    detta = {"kind": "name", "value": "Nebulosa Rosetta", "name": "Nebulosa Rosetta"}
    assert _senza_ore(_gruppi(pagina)[_chiave(pagina, ROSETTA)]) == _scheda(
        _chiave(pagina, ROSETTA), 98.0, 4.9, 3, detta
    )


def test_an_open_group_counts_and_an_answered_one_does_not(pagina):
    """Un gruppo senza risposta e' una domanda aperta e conta fra le cose da confermare;
    risposta, resta in pagina ma non conta piu'. "Non e' un oggetto": nessun oggetto nasce, quindi
    il conto scende esattamente di uno."""
    prima = review(pagina)["to_confirm"]
    apply(
        pagina,
        objects=[{"key": _chiave(pagina, M81), "not_an_object": True}],
        seen={},  # non ho visto niente: nient'altro si conferma vedendo
    )
    assert review(pagina)["to_confirm"] == prima - 1


def test_the_object_named_by_the_answer_is_not_another_question(pagina):
    """L'oggetto nominato dall'utente non torna in pagina da confermare: l'ha appena detto lui.
    `seen` vuoto -- non ho visto niente -- cosi' nient'altro si conferma vedendo."""
    apply(
        pagina,
        objects=[{"key": _chiave(pagina, M81), "name": "Galassia di Bode"}],
        seen={},
    )
    oggetti = {o["name"]: o for o in all_objects(pagina)}
    assert oggetti["Galassia di Bode"]["confirmed"] is True


def test_not_an_object_is_an_answer_too_and_i_can_change_my_mind(pagina):
    chiave = _chiave(pagina, M81)
    out = apply(pagina, objects=[{"key": chiave, "not_an_object": True}])
    assert out["requeued"] == 2  # le due senza nome: la posa col nome non c'entra
    assert _gruppi(pagina)[chiave]["answer"] == {"kind": "none", "value": None, "name": None}
    apply(pagina, objects=[{"key": chiave, "name": "Galassia di Bode"}])
    assert _gruppi(pagina)[chiave]["answer"] == {
        "kind": "name",
        "value": "Galassia di Bode",
        "name": "Galassia di Bode",
    }


def test_answering_with_a_catalog_entry(db_path_col_catalogo, tmp_path):
    """Lo slug arriva dalla rotta alla risposta; cosa fa alle pose lo prova la regola."""
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", i)
    populate(db_path_col_catalogo, root)
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        chiave = _chiave(c, M81)
        apply(c, objects=[{"key": chiave, "slug": "m-81"}])
        assert _gruppi(c)[chiave]["answer"] == {"kind": "catalog", "value": "m-81", "name": "M 81"}


def test_a_designation_written_by_hand_is_the_catalog_entry(db_path_col_catalogo, tmp_path):
    """Qui non ci sono candidati da cliccare, quindi si scrive: `m 81` e' la voce del catalogo, non
    un oggetto fuori catalogo col nome `m 81` accanto al vero M 81."""
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", i)
    populate(db_path_col_catalogo, root)
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        chiave = _chiave(c, M81)
        apply(c, objects=[{"key": chiave, "name": "m 81"}])
        assert _gruppi(c)[chiave]["answer"] == {"kind": "catalog", "value": "m-81", "name": "M 81"}
        trovati = [o for o in all_objects(c) if o["group"] is None]  # the group card stays too
        assert [(o["slug"], o["frames"]) for o in trovati] == [("m-81", 2)]


def test_a_group_that_is_not_there_is_refused(pagina):
    r = pagina.post(
        "/api/v1/review/apply",
        json={"objects": [{"key": 'frames:["2000-01-01", null]', "name": "M 1"}]},
    )
    assert r.status_code == 404, r.text


def test_a_catalog_entry_that_does_not_exist_is_refused(pagina):
    r = pagina.post(
        "/api/v1/review/apply",
        json={"objects": [{"key": _chiave(pagina, M81), "slug": "non-esiste-123"}]},
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "unknown_target"


@pytest.mark.parametrize(
    "corpo",
    [
        {},  # nessuna risposta
        {"name": "M 81", "slug": "m-81"},  # due bersagli
        {"name": "M 81", "not_an_object": True},  # un oggetto e anche nessuno
        {"not_an_object": False},  # "non e' vero che non e' un oggetto" non dice quale
        {"name": "   "},  # un nome di soli spazi: l'Applica direbbe "fatto" e niente cambierebbe
    ],
)
def test_an_answer_that_says_two_things_or_none_is_refused(pagina, corpo):
    r = pagina.post(
        "/api/v1/review/apply", json={"objects": [{"key": _chiave(pagina, M81), **corpo}]}
    )
    assert r.status_code == 422, r.text
