"""Da confermare, **la scheda dell'oggetto** (ADR 0014, S3): una forma sola al posto di Oggetti e
Senza nome, e una risposta sola -- una voce del catalogo, un nome scritto, "non e' un oggetto".

Regole, e il test che le rompe:

* **Una lista di schede**: un oggetto trovato e' una scheda (`object:` e la sua chiave stabile), un
  gruppo di frame senza nome e senza cielo un'altra (`frames:` e la chiave del gruppo), con zero
  candidati e dove e quando.
* **"Non e' un oggetto" vale anche su un oggetto trovato**: i suoi frame escono dalle ore, la scheda
  resta in pagina con la risposta e i candidati del cielo, e non conta piu'; si cambia idea.
* **"Non e' un oggetto" di un gruppo non scavalca il cielo**: un frame del gruppo che il cielo ha
  riconosciuto non lo prende.
* **Una scheda che non c'e' si rifiuta**, e una risposta che dice due cose o nessuna pure.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import stages, unnamed
from astrolog.spine.identify import identify_frames
from conftest import apply, by_name, db, populate, review, write_fits

ROSETTA, M81 = "2024-03-12_Rosetta/LIGHT", "2024-04-01_M81"
PUNTA = {ROSETTA: (98.0, 4.9), M81: (149.0, 69.0)}
NESSUNO = {"kind": "none", "value": None, "name": None}


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
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", 10 + i)
    _posa(root / M81 / "col_nome.fits", 20, OBJECT="M 81")  # un nome libero: senza catalogo
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


@pytest.fixture
def col_cielo(db_path_col_catalogo, tmp_path):
    """Due frame di M 81 senza nome, che il cielo riconosce."""
    root = tmp_path / "lib"
    for i in range(2):
        _posa(root / M81 / f"m_{i}.fits", i)
    populate(db_path_col_catalogo, root)
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        yield c


def _frame(conn, sotto, nome):
    return conn.execute(
        "SELECT frame_id FROM positions WHERE rel_path = ?", (f"{sotto}/{nome}",)
    ).fetchone()[0]


def _gruppo(client, sotto):
    with db(client) as conn:
        (frame_id,) = conn.execute(
            "SELECT f.id FROM frames f JOIN positions p ON p.frame_id = f.id"
            " WHERE p.rel_path LIKE ? AND f.object_raw IS NULL ORDER BY f.id",
            (f"{sotto}/%",),
        ).fetchone()
        return f"frames:{unnamed.key_of_frame(conn, frame_id)}"


def _col_cielo(client, sotto, nome, ra, dec):
    """Il cielo misurato a (ra, dec) per quel frame, e `identify` rifatto."""
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


def _stato(client, frame_id):
    """`(slug o nome dell'oggetto, stato di identify, motivo)` di quel frame."""
    with db(client) as conn:
        return tuple(
            conn.execute(
                "SELECT COALESCE(o.catalog_slug, n.name), s.status, s.reason FROM frames f"
                " JOIN frame_stages s ON s.frame_id = f.id AND s.stage = 'identify'"
                " LEFT JOIN objects o ON o.id = f.object_id"
                " LEFT JOIN object_names n ON n.object_id = o.id AND n.is_primary = 1"
                " WHERE f.id = ?",
                (frame_id,),
            ).fetchone()
        )


def _schede(client):
    return {s["key"]: s for s in review(client)["objects"]}


def test_found_objects_and_unnamed_groups_are_one_list_of_cards(pagina):
    """Le due sezioni di prima sono una lista: il gruppo porta dove e quando, e nessun candidato;
    l'oggetto trovato porta cosa l'app ha capito. La sezione `unnamed` non c'e' piu'."""
    pagina_letta = review(pagina)
    assert "unnamed" not in pagina_letta
    schede = {s["key"]: s for s in pagina_letta["objects"]}
    rosetta = schede[_gruppo(pagina, ROSETTA)]
    assert (rosetta["name"], rosetta["id"], rosetta["candidates"], rosetta["answer"]) == (
        None,
        None,
        [],
        None,
    )
    assert (rosetta["frames"], rosetta["integration_s"], rosetta["untimed"]) == (3, 360.0, 0)
    assert {k: rosetta["group"][k] for k in ("night", "camera", "ra_deg", "dec_deg")} == {
        "night": "2024-03-12",
        "camera": "Canon EOS 700D",
        "ra_deg": 98.0,
        "dec_deg": 4.9,
    }
    m81 = by_name(pagina_letta["objects"], "M 81")
    assert (m81["key"], m81["group"], m81["answer"], m81["frames"]) == (
        "object:M 81",
        None,
        None,
        1,
    )


def test_not_an_object_on_a_found_object_takes_its_frames_out_and_the_card_stays(pagina):
    """Il frame esce dalle ore e da ogni oggetto; la scheda resta in pagina con la risposta, cosi'
    si cambia idea, e non conta piu' fra le cose da confermare."""
    prima = review(pagina)["to_confirm"]
    with db(pagina) as conn:
        frame_id = _frame(conn, M81, "col_nome.fits")
    out = apply(pagina, objects=[{"key": "object:M 81", "not_an_object": True}], seen={})
    assert out["requeued"] == 1
    assert _stato(pagina, frame_id) == (None, "skipped", "not_an_object")
    scheda = _schede(pagina)["object:M 81"]
    assert (scheda["answer"], scheda["frames"], scheda["id"]) == (NESSUNO, 1, None)
    assert review(pagina)["to_confirm"] == prima - 1

    apply(pagina, objects=[{"key": "object:M 81", "name": "Galassia di Bode"}])
    assert _stato(pagina, frame_id) == ("Galassia di Bode", "done", None)
    assert "object:M 81" not in _schede(pagina)


def test_changing_ones_mind_brings_back_the_frames_a_group_answer_had_linked(pagina):
    """I frame senza nome ne' cielo stanno sull'oggetto per la risposta del loro gruppo: messi fuori
    con la scheda dell'oggetto, restano sotto la sua chiave e tornano tutti cambiando idea."""
    gruppo = _gruppo(pagina, M81)
    apply(pagina, objects=[{"key": gruppo, "name": "M 81"}])
    with db(pagina) as conn:
        frames = [_frame(conn, M81, n) for n in ("m_0.fits", "m_1.fits", "col_nome.fits")]
    assert {_stato(pagina, f) for f in frames} == {("M 81", "done", None)}

    apply(pagina, objects=[{"key": "object:M 81", "not_an_object": True}])
    assert {_stato(pagina, f) for f in frames} == {(None, "skipped", "not_an_object")}
    assert _schede(pagina)["object:M 81"]["frames"] == 3

    apply(pagina, objects=[{"key": "object:M 81", "name": "M 81"}])
    assert {_stato(pagina, f) for f in frames} == {("M 81", "done", None)}
    assert _schede(pagina)[gruppo]["answer"] == {"kind": "name", "value": "M 81", "name": "M 81"}


def test_the_card_of_frames_put_out_keeps_the_sky_candidates(col_cielo):
    """Fuori dalle ore, la scheda tiene cosa il cielo ha trovato: si cambia idea cliccando."""
    frame_id = _col_cielo(col_cielo, M81, "m_0.fits", 148.888, 69.065)
    assert _stato(col_cielo, frame_id)[0] == "m-81"
    apply(col_cielo, objects=[{"key": "object:m-81", "not_an_object": True}])
    assert _stato(col_cielo, frame_id) == (None, "skipped", "not_an_object")
    scheda = _schede(col_cielo)["object:m-81"]
    assert scheda["answer"] == NESSUNO
    assert "m-81" in [c["slug"] for c in scheda["candidates"]]

    apply(col_cielo, objects=[{"key": "object:m-81", "slug": "m-81"}])
    assert _stato(col_cielo, frame_id) == ("m-81", "done", None)


def test_not_an_object_said_for_a_group_does_not_reach_a_frame_the_sky_recognised(col_cielo):
    """Il frame col cielo sta ancora nel gruppo (la chiave e' scritta), ma la domanda del gruppo
    non lo riguarda: dove il cielo ha candidati decide lui."""
    gruppo = _gruppo(col_cielo, M81)
    col_m81 = _col_cielo(col_cielo, M81, "m_1.fits", 148.888, 69.065)
    apply(col_cielo, objects=[{"key": gruppo, "not_an_object": True}])
    assert _stato(col_cielo, col_m81) == ("m-81", "done", None)
    assert _schede(col_cielo)[gruppo]["answer"] == NESSUNO


def test_a_sky_that_comes_after_the_group_answer_still_decides(col_cielo):
    """L'ordine inverso: il gruppo risponde quando il frame non ha cielo, il cielo arriva dopo coi
    candidati e decide lui."""
    gruppo = _gruppo(col_cielo, M81)
    apply(col_cielo, objects=[{"key": gruppo, "not_an_object": True}])
    col_m81 = _col_cielo(col_cielo, M81, "m_1.fits", 148.888, 69.065)
    assert _stato(col_cielo, col_m81) == ("m-81", "done", None)


@pytest.mark.parametrize(
    "chiave", ["object:non esiste", 'frames:["2000-01-01", null, null, null, null]', "M 81"]
)
def test_a_card_that_is_not_there_is_refused(pagina, chiave):
    r = pagina.post(
        "/api/v1/review/apply", json={"objects": [{"key": chiave, "not_an_object": True}]}
    )
    assert r.status_code == 404, r.text


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
    r = pagina.post("/api/v1/review/apply", json={"objects": [{"key": "object:M 81", **corpo}]})
    assert r.status_code == 422, r.text
