"""Da confermare, i frame che non dicono **che file sono**: una domanda per cartella.

Un header senza `IMAGETYP` non dice "light": lo lasciano muto alcuni programmi di ripresa, e
quel file puo' essere una foto del cielo come un dark. Lo dice il cielo; dove non sa dire si
chiede, e finche' non si sa quei frame non hanno un oggetto, quindi non diventano ore e non
finiscono fra i Frame senza nome -- dove la domanda e' "cosa hai ripreso" e non "che file e'". Le
regole stanno in `spine/typeless.py`.
"""

import shutil

import pytest
from fastapi.testclient import TestClient

from astrolog.api import work
from astrolog.api.app import create_app
from astrolog.astap import Reason
from astrolog.spine import typeless, typeless_answer, typeless_folders
from astrolog.spine.declarations import TypeAnswer
from astrolog.spine.frame_folder import folder_key
from astrolog.spine.identify import identify_frames
from astrolog.spine.stages import WAITING_SQL, invalidate, set_status
from conftest import apply, db, populate, review, sky_solved, unnamed_cards, write_fits

DARK, M51, FOTO = "2026-03-14/dark", "2026-03-14/M51", "2026-03-14/foto"


def _muto(path, **header):
    """Un file che non dice `IMAGETYP`, come quelli dei programmi che non lo scrivono (l'elenco
    sta in `astrolog/fits/frame_type.py`). Porta la camera e il
    filtro come ogni file vero: e' proprio leggendoli che `normalize` rimette in coda il frame, ed
    e' li' che un fermo scritto sul frame si perderebbe."""
    card = {"EXPTIME": 300.0, "INSTRUME": "ZWO ASI2600MM", "FILTER": "Ha"}
    return write_fits(path, {**card, **header})


@pytest.fixture
def pagina(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(3):
        _muto(root / DARK / f"d_{i}.fits")
    _muto(root / M51 / "a_0.fits", OBJECT="M 51", **{"DATE-OBS": "2026-03-14T21:00:00"})
    write_fits(root / M51 / "detto.fits", {"IMAGETYP": "Light Frame", "EXPTIME": 300.0})
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def _chiave(client, sotto):
    with db(client) as conn:
        radice = conn.execute("SELECT root_path FROM folders").fetchone()[0]
    return folder_key(radice, f"{sotto}/")


def _gruppi(client):
    return {g["key"]: g for g in review(client)["typeless"]}


def _aspetta(client, nome):
    """Se quel file aspetta di sapere che file e': il segno che legge chi decide chi e' pronto."""
    sql = (
        f"SELECT COUNT(*) FROM frames f JOIN positions p ON p.frame_id = f.id"  # noqa: S608
        f" WHERE p.rel_path LIKE ? AND {WAITING_SQL}"
    )
    with db(client) as conn:
        return conn.execute(sql, (f"%{nome}",)).fetchone()[0] > 0


def test_a_question_per_folder_about_which_files_they_are(pagina):
    """Si chiede per cartella: chi riprende tiene dark e flat in cartelle loro, e una risposta
    chiude una cartella intera. Il file che il tipo lo dice non e' una domanda.

    Il gruppo si confronta **intero**, senza togliergli niente: qui non si mostra cio' che il cielo
    ha trovato -- su quei frame il cielo non ha saputo dire -- e un campo che rientrasse deve far
    cadere questo test.

    test-tolto: test_a_question_per_folder_with_the_largest_first -- rinominato: allora quel nome
    ce l'aveva un altro test, e con due omonimi una promessa resterebbe verde per merito
    dell'altro."""
    assert review(pagina)["typeless"] == [
        {"key": _chiave(pagina, DARK), "frames": 3, "answer": None},
        {"key": _chiave(pagina, M51), "frames": 1, "answer": None},
    ]


def test_those_frames_are_not_asked_among_the_unnamed_ones(pagina):
    """La promessa della sezione: finche' non si sa che file sono, quei frame non compaiono fra i
    **Frame senza nome**. Li' la domanda e' "cosa hai ripreso", e rispondere con un oggetto su una
    cartella di dark trasformerebbe una calibrazione in ore -- il buco per cui questa domanda e'
    nata. E lo stesso **frame** non si chiede due volte."""
    pagine = review(pagina)
    assert _chiave(pagina, DARK) in {g["key"] for g in pagine["typeless"]}
    # fra i frame senza nome resta il solo file che il tipo lo dice: il muto no, e i dark nemmeno
    assert [g["frames"] for g in unnamed_cards(pagine)] == [1]


def test_a_frame_that_waits_is_not_work_left_to_do(pagina):
    """Un frame che aspetta una risposta non e' lavoro in coda: il residuo del cielo e di cio' che
    viene dopo resta a zero, anche dopo che la normalizzazione ha rimesso in coda quei frame
    leggendo la loro camera. Altrimenti ogni Avvia ripartirebbe per niente e sul NAS la cadenza
    automatica girerebbe a vuoto per sempre."""
    residuo = pagina.get("/api/v1/pipeline/status")
    assert residuo.status_code == 200, residuo.text
    per_stadio = residuo.json()["pending"]
    # nell'archivio di prova un solo file dice che tipo e': gli altri quattro aspettano, e
    # nessuno stadio del cielo in giu' li conta come lavoro da fare
    assert max(n for s, n in per_stadio.items() if s != "normalize") <= 1


def test_an_unanswered_folder_counts_among_the_things_to_confirm(pagina):
    """Una cartella senza risposta e' una cosa da confermare; con la risposta resta in pagina ma
    non si conta piu'. Senza questa riga il conto direbbe zero mentre l'archivio non ha ancora
    guardato quei frame.

    Il conto si guarda **di quanto** cala, e la risposta si scrive dritta nel DB invece che
    dall'Applica: l'Applica fa partire una corsa, che muove anche le altre domande, e li' "e'
    calato" resta vero pure col segno di questa riga rovesciato (misurato: quel sabotaggio
    sopravviveva).

    test-tolto: test_an_unanswered_folder_does_not_count_yet_among_the_things_to_confirm --
    rinominato quando la riga del conto e' stata riaccesa: prima quella domanda non si poteva
    rispondere e non si contava, ora la sezione c'e' e conta."""
    prima = review(pagina)["to_confirm"]
    aperte = {g["key"] for g in review(pagina)["typeless"] if g["answer"] is None}
    assert len(aperte) == 2
    with db(pagina) as conn:
        typeless.declare(conn, _chiave(pagina, DARK), TypeAnswer.CALIBRATION)
    dopo = review(pagina)
    assert {g["key"] for g in dopo["typeless"] if g["answer"] is None} == aperte - {
        _chiave(pagina, DARK)
    }
    assert dopo["to_confirm"] == prima - 1


def test_saying_calibration_leaves_those_frames_out_of_the_archive(pagina):
    """ "Sono file di calibrazione": restano dove sono, fermi prima dell'oggetto, e non diventano
    ore. La risposta resta in pagina, perche' si deve poter cambiare idea."""
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    assert _gruppi(pagina)[_chiave(pagina, DARK)]["answer"] == "calibration"
    assert _aspetta(pagina, "d_0.fits")


def test_saying_it_is_a_photo_of_the_sky_sends_those_frames_to_the_sky(pagina):
    """ "Sono foto del cielo": da li' in poi fanno la strada di un light, oggetto compreso."""
    apply(pagina, typeless=[{"key": _chiave(pagina, M51), "kind": "light"}])
    assert _gruppi(pagina)[_chiave(pagina, M51)]["answer"] == "light"
    assert not _aspetta(pagina, "a_0.fits")


def test_the_answer_holds_for_the_files_that_arrive_later_in_that_folder(pagina, tmp_path):
    """La dichiarazione si rilegge a ogni giro: un file nuovo che arriva dopo in una cartella gia'
    detta di calibrazione non entra affatto, e la ricevuta lo conta per motivo."""
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    _muto(tmp_path / "lib" / DARK / "d_9.fits")
    r = pagina.post("/api/v1/scan")
    assert r.status_code in (200, 202), r.text
    pagina.app.state.worker.join(20.0)
    with db(pagina) as conn:
        entrati = conn.execute("SELECT COUNT(*) FROM positions WHERE rel_path LIKE '%d_9%'")
        assert entrati.fetchone()[0] == 0


def _cielo(client, sotto, stato, motivo=None):
    """Cio' che il solver avrebbe detto dei frame di quella cartella: la suite non lo lancia."""
    with db(client) as conn:
        for (frame_id,) in conn.execute(
            "SELECT frame_id FROM positions WHERE rel_path LIKE ?", (f"{sotto}/%",)
        ).fetchall():
            if stato == "done":
                sky_solved(conn, frame_id)
            else:
                set_status(conn, frame_id, "solve", stato, reason=motivo)
        typeless_folders.write(conn)  # come a fine cielo
        list(identify_frames(conn))
        conn.commit()


def test_frames_without_stars_are_calibration_and_are_not_asked(pagina):
    """Il cielo non trova stelle: sono file di calibrazione (Marco, 23/9/2026). Non si chiedono,
    non finiscono fra i Frame senza nome, e non diventano ore."""
    _cielo(pagina, DARK, "failed", Reason.NO_STARS)
    pagine = review(pagina)
    assert _chiave(pagina, DARK) not in _gruppi(pagina)
    assert _chiave(pagina, DARK) not in {
        g["key"].removeprefix("frames:") for g in unnamed_cards(pagine)
    }
    assert _aspetta(pagina, "d_0.fits")


def test_a_frame_the_sky_solves_is_a_photo_and_is_not_asked(pagina):
    """Il cielo lo risolve: e' una foto, e fa la strada di un light senza chiedere niente."""
    _cielo(pagina, M51, "done")
    assert _chiave(pagina, M51) not in _gruppi(pagina)
    assert not _aspetta(pagina, "a_0.fits")


def _attaccato(client, nome):
    """Oggetto, notte e sessione di quel frame: cio' che lo fa contare nelle ore."""
    with db(client) as conn:
        riga = conn.execute(
            "SELECT f.object_id, f.night_id, f.session_id FROM frames f"
            " JOIN positions p ON p.frame_id = f.id WHERE p.rel_path LIKE ?",
            (f"%{nome}",),
        ).fetchone()
    return tuple(riga)


def _casa(client):
    """Un sito di casa, perche' i frame abbiano una notte e una sessione."""
    with db(client) as conn:
        conn.execute(
            "INSERT INTO sites(name, latitude, longitude, timezone, is_default, created_at)"
            " VALUES('Casa', 45.4, 11.9, 'Europe/Rome', 1, '2026-01-01T00:00:00Z')"
        )


def _foto_con_le_ore(client):
    """Il file senza tipo di M51 detto "foto del cielo", con le sue ore."""
    _casa(client)
    apply(client, typeless=[{"key": _chiave(client, M51), "kind": "light"}])
    client.app.state.worker.join(20.0)
    assert None not in _attaccato(client, "a_0.fits")


def _rileggi(client, quale):
    """La scansione di tutte le cartelle, o quella di una sola: due strade della corsa."""
    with db(client) as conn:
        (cartella,) = conn.execute("SELECT id FROM folders").fetchone()
    r = client.post("/api/v1/scan" if quale == "tutte" else f"/api/v1/folders/{cartella}/scan")
    assert r.status_code in (200, 202), r.text
    client.app.state.worker.join(20.0)


def _sposta(tmp_path, dove):
    (tmp_path / "lib" / dove).mkdir()
    (tmp_path / "lib" / M51 / "a_0.fits").replace(tmp_path / "lib" / dove / "a_0.fits")


@pytest.mark.parametrize("quale", ["tutte", "una"])
def test_a_frame_moved_where_no_one_answered_waits_again_without_its_hours(pagina, tmp_path, quale):
    """La risposta vale per la cartella: un frame che "foto del cielo" aveva mandato avanti,
    spostato in una cartella che non ha risposto, torna ad aspettare, senza oggetto, notte e
    sessione -- o le sue ore resterebbero attaccate a un oggetto che non rifara' mai i conti.
    Quando la cartella nuova risponde "foto del cielo", li riprende."""
    _foto_con_le_ore(pagina)
    _sposta(tmp_path, "altrove")
    _rileggi(pagina, quale)

    assert _aspetta(pagina, "a_0.fits")
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)

    apply(pagina, typeless=[{"key": _chiave(pagina, "altrove"), "kind": "light"}])
    pagina.app.state.worker.join(20.0)
    assert None not in _attaccato(pagina, "a_0.fits")


def test_a_frame_moved_into_a_folder_called_calibration_waits_without_its_hours(pagina, tmp_path):
    """La scansione salta alla porta i file senza tipo di una cartella detta di calibrazione, ma un
    frame gia' in archivio ci puo' arrivare spostato: entra, cosi' che lo stacco lo veda.
    Saltato, per l'app sarebbe un file sparito, e un file sparito tiene le ore. Cambiata la
    risposta della cartella in "foto del cielo", le riprende."""
    _foto_con_le_ore(pagina)
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    pagina.app.state.worker.join(20.0)
    (tmp_path / "lib" / M51 / "a_0.fits").replace(tmp_path / "lib" / DARK / "a_0.fits")
    _rileggi(pagina, "tutte")
    assert _aspetta(pagina, "a_0.fits")
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)

    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "light"}])
    pagina.app.state.worker.join(20.0)
    assert None not in _attaccato(pagina, "a_0.fits")


def test_a_frame_moved_back_out_of_calibration_goes_back_to_the_sky(pagina, tmp_path):
    """Lo stacco toglie al frame il cielo trovato. Rimesso dov'era, in una cartella senza risposta,
    aspetta: se non tornasse in fila dal cielo resterebbe fermo per sempre, e nessuno glielo
    chiederebbe -- il cielo lo rimette solo il solver, che ha la sua cache."""
    _risolto_dal_cielo(pagina)
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    pagina.app.state.worker.join(20.0)
    (tmp_path / "lib" / M51 / "a_0.fits").replace(tmp_path / "lib" / DARK / "a_0.fits")
    _rileggi(pagina, "tutte")
    (tmp_path / "lib" / DARK / "a_0.fits").replace(tmp_path / "lib" / M51 / "a_0.fits")
    _rileggi(pagina, "tutte")
    assert _stato_del_cielo(pagina, "a_0.fits") == "pending"


def test_a_frame_moved_from_calibration_into_a_photo_folder_goes_back_to_the_sky(pagina, tmp_path):
    """Una cartella detta "foto del cielo" lo lascia andare: senza tornare in fila dal cielo,
    `identify` lo riprenderebbe col cielo vuoto e il nome dell'header."""
    _risolto_dal_cielo(pagina)
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    pagina.app.state.worker.join(20.0)
    (tmp_path / "lib" / M51 / "a_0.fits").replace(tmp_path / "lib" / DARK / "a_0.fits")
    _rileggi(pagina, "tutte")
    with db(pagina) as conn:
        typeless.declare(conn, _chiave(pagina, FOTO), TypeAnswer.LIGHT)
    (tmp_path / "lib" / FOTO).mkdir()
    (tmp_path / "lib" / DARK / "a_0.fits").replace(tmp_path / "lib" / FOTO / "a_0.fits")
    _rileggi(pagina, "tutte")
    assert _stato_del_cielo(pagina, "a_0.fits") == "pending"


@pytest.mark.parametrize("come", ["file sparito", "cartella tolta"])
def test_a_detached_frame_left_without_a_live_folder_keeps_waiting(pagina, tmp_path, come):
    """Un frame che il cielo aveva risolto, fermato in una cartella detta di calibrazione, tiene lo
    stato che aveva quando resta senza cartella viva: aspetta, senza ore, e non torna in fila dal
    cielo. Il cielo che lo stacco gli ha tolto non conta come riconosciuto, o `identify` lo
    riprenderebbe con un cielo vuoto e il nome dell'header."""
    _risolto_dal_cielo(pagina)
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    pagina.app.state.worker.join(20.0)
    (tmp_path / "lib" / M51 / "a_0.fits").replace(tmp_path / "lib" / DARK / "a_0.fits")
    _rileggi(pagina, "tutte")
    if come == "file sparito":
        (tmp_path / "lib" / DARK / "a_0.fits").unlink()
        _rileggi(pagina, "tutte")
    else:
        with db(pagina) as conn:
            (cartella,) = conn.execute("SELECT id FROM folders").fetchone()
        assert pagina.delete(f"/api/v1/folders/{cartella}").status_code == 200
        pagina.app.state.worker.join(20.0)
    assert _aspetta(pagina, "a_0.fits")
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)
    assert _stato_del_cielo(pagina, "a_0.fits") == "done"


def test_a_copy_in_a_folder_called_calibration_keeps_the_hours_of_the_original(pagina, tmp_path):
    """Una COPIA di un frame gia' in archivio entra anche li', come copia, ma la cartella di una
    posa e' quella della sua prima posizione presente in una cartella non tolta
    (`spine/frame_folder.py`): finche' l'originale resta dov'era, le ore restano."""
    _foto_con_le_ore(pagina)
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    pagina.app.state.worker.join(20.0)
    shutil.copy2(tmp_path / "lib" / M51 / "a_0.fits", tmp_path / "lib" / DARK / "a_0.fits")
    _rileggi(pagina, "tutte")
    with db(pagina) as conn:
        dove = conn.execute("SELECT COUNT(*) FROM positions WHERE rel_path LIKE '%a_0.fits'")
        assert dove.fetchone()[0] == 2
    assert None not in _attaccato(pagina, "a_0.fits")


def test_a_frame_already_back_in_line_is_detached_all_the_same(pagina, tmp_path):
    """Lo stacco guarda cio' che il frame porta, non lo stato dei suoi stadi: una risposta su un
    filtro lo rimette in coda senza staccargli niente, e spostato cosi' terrebbe le ore per sempre,
    perche' chi aspetta non e' pronto per nessuno."""
    _foto_con_le_ore(pagina)
    with db(pagina) as conn:
        (frame_id,) = conn.execute(
            "SELECT frame_id FROM positions WHERE rel_path LIKE '%a_0.fits'"
        ).fetchone()
        invalidate(conn, [frame_id], "normalize")
    _sposta(tmp_path, "altrove")
    _rileggi(pagina, "tutte")
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)


def _risolto_dal_cielo(pagina):
    _casa(pagina)
    _cielo(pagina, M51, "done")
    _rileggi(pagina, "tutte")
    assert None not in _attaccato(pagina, "a_0.fits")


def test_a_frame_the_sky_recognised_keeps_its_hours_where_no_one_said_calibration(pagina, tmp_path):
    """Un file che il cielo ha risolto e' una foto anche in una cartella che non ha risposto:
    spostato li' non aspetta."""
    _risolto_dal_cielo(pagina)
    _sposta(tmp_path, "altrove")
    _rileggi(pagina, "tutte")
    assert None not in _attaccato(pagina, "a_0.fits")


def test_a_frame_the_sky_recognised_moved_into_calibration_waits_without_its_hours(
    pagina, tmp_path
):
    """La parola dell'utente vale anche dove il cielo ha risolto (`spine/typeless.py`): spostato
    in una cartella detta di calibrazione, anche un frame che il cielo ha riconosciuto aspetta, e
    le sue ore escono dall'archivio. Il cielo che lo stacco gli toglie non si rifa': li' la
    cartella lo ferma comunque."""
    _risolto_dal_cielo(pagina)
    apply(pagina, typeless=[{"key": _chiave(pagina, DARK), "kind": "calibration"}])
    pagina.app.state.worker.join(20.0)
    (tmp_path / "lib" / M51 / "a_0.fits").replace(tmp_path / "lib" / DARK / "a_0.fits")
    _rileggi(pagina, "tutte")
    assert _aspetta(pagina, "a_0.fits")
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)
    assert _stato_del_cielo(pagina, "a_0.fits") == "done"


def test_a_file_that_is_gone_keeps_its_hours(pagina, tmp_path):
    """Un file sparito non ha una cartella viva, e nessuno potrebbe rispondere: tiene le sue ore
    come ogni altro frame dell'archivio."""
    _foto_con_le_ore(pagina)
    (tmp_path / "lib" / M51 / "a_0.fits").unlink()
    _rileggi(pagina, "tutte")
    assert None not in _attaccato(pagina, "a_0.fits")


def _anche_altrove_poi_via_la_prima(pagina, tmp_path):
    """Il frame detto "foto del cielo" anche in una seconda cartella registrata, senza risposta;
    poi la prima si toglie. Torna la seconda radice."""
    _foto_con_le_ore(pagina)
    altra = tmp_path / "lib2"
    (altra / "altrove").mkdir(parents=True)
    shutil.copy2(tmp_path / "lib" / M51 / "a_0.fits", altra / "altrove" / "a_0.fits")
    r = pagina.post("/api/v1/folders", json={"root_path": str(altra), "name": "Altra"})
    assert r.status_code == 201, r.text
    assert pagina.post(f"/api/v1/folders/{r.json()['id']}/scan").status_code == 202
    pagina.app.state.worker.join(20.0)
    assert None not in _attaccato(pagina, "a_0.fits")
    with db(pagina) as conn:
        (prima,) = conn.execute("SELECT id FROM folders ORDER BY id").fetchone()
    assert pagina.delete(f"/api/v1/folders/{prima}").status_code == 200
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)
    pagina.app.state.worker.join(20.0)
    return altra


def _rimetti_la_prima(pagina, tmp_path):
    r = pagina.post("/api/v1/folders", json={"root_path": str(tmp_path / "lib"), "name": "Lib"})
    assert r.status_code == 201, r.text
    pagina.app.state.worker.join(20.0)


def _stato_del_cielo(client, nome):
    with db(client) as conn:
        return conn.execute(
            "SELECT s.status FROM frame_stages s JOIN positions p ON p.frame_id = s.frame_id"
            " WHERE p.rel_path LIKE ? AND s.stage = 'solve'",
            (f"%{nome}",),
        ).fetchone()[0]


def test_putting_back_a_folder_sends_a_frame_that_lost_its_sky_back_to_the_sky(
    pagina, tmp_path, monkeypatch
):
    """Ritirata la prima cartella, il frame risolto dal cielo e' della sua copia in una cartella
    detta di calibrazione, e perde il cielo; rimessa la prima, la cartella non lo ferma piu' e
    torna in fila dal cielo -- e la corsa che parte deve cominciare da li', o nessuno lo
    riprenderebbe."""
    _risolto_dal_cielo(pagina)
    altra = tmp_path / "lib2"
    (altra / "altrove").mkdir(parents=True)
    shutil.copy2(tmp_path / "lib" / M51 / "a_0.fits", altra / "altrove" / "a_0.fits")
    with db(pagina) as conn:
        typeless.declare(conn, folder_key(str(altra), "altrove/"), TypeAnswer.CALIBRATION)
    r = pagina.post("/api/v1/folders", json={"root_path": str(altra), "name": "Altra"})
    assert r.status_code == 201, r.text
    assert pagina.post(f"/api/v1/folders/{r.json()['id']}/scan").status_code == 202
    pagina.app.state.worker.join(20.0)
    with db(pagina) as conn:
        (prima,) = conn.execute("SELECT id FROM folders ORDER BY id").fetchone()
    assert pagina.delete(f"/api/v1/folders/{prima}").status_code == 200
    pagina.app.state.worker.join(20.0)
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)

    chiesti = []
    monkeypatch.setattr(work, "after", lambda state, stadi: chiesti.append(stadi))
    _rimetti_la_prima(pagina, tmp_path)
    assert _stato_del_cielo(pagina, "a_0.fits") == "pending"
    assert ["solve"] in chiesti


def test_retiring_a_folder_moves_a_frame_that_is_also_elsewhere(pagina, tmp_path):
    """Lo stesso file in due cartelle registrate: ritirata la prima, la sua cartella e' l'altra, e
    se l'altra non ha risposto il frame torna ad aspettare senza ore, anche senza una scansione.
    Riattivata la prima, la sua cartella torna quella di prima, e vale la risposta di li'."""
    altra = _anche_altrove_poi_via_la_prima(pagina, tmp_path)
    with db(pagina) as conn:  # l'oggetto rimasto senza frame non resta in archivio a zero
        assert conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 0

    apply(pagina, typeless=[{"key": folder_key(str(altra), "altrove/"), "kind": "light"}])
    pagina.app.state.worker.join(20.0)
    assert None not in _attaccato(pagina, "a_0.fits")
    with db(pagina) as conn:  # la cartella ritirata non si chiede: la risposta si scrive dritta
        typeless.declare(conn, _chiave(pagina, M51), TypeAnswer.CALIBRATION)
    _rimetti_la_prima(pagina, tmp_path)
    assert _attaccato(pagina, "a_0.fits") == (None, None, None)


def test_a_retire_that_fails_leaves_the_folder_where_it_was(pagina, monkeypatch):
    """Il ritiro e il segno dell'attesa entrano insieme o non entrano: un ritiro scritto coi segni
    vecchi non si ripara ripetendolo, perche' una cartella gia' ritirata non si ritira di nuovo."""

    def cade(conn, now=None):
        raise RuntimeError("database occupato")

    monkeypatch.setattr(typeless_answer, "detach_waiting", cade)
    with db(pagina) as conn:
        (prima,) = conn.execute("SELECT id FROM folders ORDER BY id").fetchone()
    with pytest.raises(RuntimeError):
        pagina.delete(f"/api/v1/folders/{prima}")
    with db(pagina) as conn:
        riga = conn.execute("SELECT retired_at FROM folders WHERE id = ?", (prima,)).fetchone()
    assert riga["retired_at"] is None


def test_putting_back_a_folder_that_said_photo_gives_the_hours_back(pagina, tmp_path):
    """Rimessa la cartella che aveva detto "foto del cielo", il frame che aspettava altrove torna
    pronto, e la corsa parte da se': senza, le ore tornerebbero solo al prossimo Avvia."""
    _anche_altrove_poi_via_la_prima(pagina, tmp_path)
    _rimetti_la_prima(pagina, tmp_path)
    assert None not in _attaccato(pagina, "a_0.fits")


def test_retiring_the_folder_keeps_the_hours(pagina):
    """Ritirare una cartella non cancella niente: i suoi frame senza tipo tengono le ore."""
    _foto_con_le_ore(pagina)
    with db(pagina) as conn:
        (cartella,) = conn.execute("SELECT id FROM folders").fetchone()
    assert pagina.delete(f"/api/v1/folders/{cartella}").status_code == 200
    assert None not in _attaccato(pagina, "a_0.fits")


def test_a_frame_that_waits_does_not_ask_for_the_filter(db_path, tmp_path):
    """Finche' non si sa che file e', un file senza filtro non fa chiedere il filtro della sua
    camera: puo' essere un dark, e la domanda sui filtri riguarda le foto del cielo. Detto "foto
    del cielo", la domanda arriva."""
    root = tmp_path / "lib"
    _muto(root / "boh" / "x.fits", FILTER=None)
    populate(db_path, root)
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        assert [g for g in review(c)["gear"] if g["asks_filter"]] == []
        apply(c, typeless=[{"key": _chiave(c, "boh"), "kind": "light"}])
        c.app.state.worker.join(20.0)
        filtro = [(g["camera"], g["frames"]) for g in review(c)["gear"] if g["asks_filter"]]
        assert filtro == [("ZWO ASI2600MM", 1)]


def test_a_folder_that_is_not_there_is_refused(pagina):
    """Una risposta verso una cartella che non chiede niente non si scrive: resterebbe li' per
    sempre senza che nessuno la veda."""
    r = pagina.post(
        "/api/v1/review/apply", json={"typeless": [{"key": "D:/mai/vista", "kind": "light"}]}
    )
    assert r.status_code == 404, r.text


def test_an_answer_that_is_not_one_of_the_two_words_is_refused(pagina):
    """Le risposte sono due: una foto del cielo o un file di calibrazione. Una terza parola e'
    una richiesta malformata, non una risposta da interpretare."""
    r = pagina.post(
        "/api/v1/review/apply",
        json={"typeless": [{"key": _chiave(pagina, DARK), "kind": "forse"}]},
    )
    assert r.status_code == 422, r.text
