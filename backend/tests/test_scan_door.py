"""La porta fra la scansione dell'utente e la pipeline nuova (`api/scan_door.py`, passo 40.4): gli
eventi file per file, la ricevuta coi conti della ricevuta vecchia, la chiusura quando la lettura
si ferma o si rompe. FITS veri fabbricati con astropy e un DB nato da schema.sql."""

import sqlite3
import threading
from pathlib import Path

import pytest

from astrolog.api import scan_door
from astrolog.pipeline import changes as pipeline_changes
from astrolog.pipeline import scan as pipeline_scan
from astrolog.pipeline.changes import open_receipt
from astrolog.pipeline.scan import ScanResult, Watch, scan_root
from astrolog.spine import frame_folder, scan_history, typeless
from astrolog.spine.declarations import TypeAnswer
from astrolog.spine.scan_store import COUNTS, TALLIES
from conftest import add_folder, online_only, settle, write_fits, write_light

# by gesture: the scan replaces the placeholder with its own row
_RUN = "SELECT * FROM pipeline_scans WHERE gesture = ? ORDER BY id DESC"
_ROW = "SELECT * FROM pipeline_scans WHERE id = ?"


def _events(conn, db_path, folder_id, runner=None):
    corsa = open_receipt(conn, folder_id, "2026-11-27T10:00:00.000Z")
    return corsa, scan_door.scan_events(conn, folder_id, corsa, runner or scan_door.direct(db_path))


def _truncated(path):
    """Un FITS piu' corto di quanto dice il suo header, scritto da tempo: copia rotta a meta'."""
    write_light(path, obj="M 9")
    path.write_bytes(path.read_bytes()[:2890])
    settle(path)
    return path


def test_each_file_read_says_its_name_and_the_counts_so_far(conn, db_path, tmp_path, monkeypatch):
    """L'evento di un file porta il nome del file senza le cartelle sopra, i conti fin li' --
    trovati compresi quelli che non si rileggono e quelli solo online -- e zero per gli altri: la
    barra della scansione li mostra mentre legge."""
    write_light(tmp_path / "vecchio.fits", obj="M 1")
    fid = add_folder(conn, tmp_path)
    scan_door.scan_once(conn, fid)
    write_light(tmp_path / "notte" / "sotto" / "a.fits", obj="M 2")
    write_light(tmp_path / "notte" / "sotto" / "b.fits", obj="M 3")
    write_light(tmp_path / "nuvola.fits", obj="M 4")
    online_only(monkeypatch, tmp_path / "nuvola.fits")
    monkeypatch.setattr(pipeline_scan, "BATCH", 1)  # a's batch saved before b is read
    _, eventi = _events(conn, db_path, fid)
    letti = list(eventi)[:-1]
    assert [e["file"] for e in letti] == ["a.fits", "b.fits"]
    ultimo = letti[-1]
    assert (ultimo["current"], ultimo["total"], ultimo["folder_id"]) == (2, 2, fid)
    conti = {k: ultimo[k] for k in COUNTS}
    attesi = dict.fromkeys(COUNTS, 0) | {"found": 4, "new": 1, "unchanged": 1, "online_only": 1}
    assert conti == attesi
    assert ultimo["since"].endswith("Z")


def test_the_reading_runs_in_its_own_thread_that_does_not_hold_the_app_open(
    conn, db_path, tmp_path
):
    """La lettura gira in un thread suo, col suo nome (si riconosce in un dump dei thread), che
    non tiene aperta l'app alla chiusura."""
    write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    visto = {}
    vero = scan_door.direct(db_path)

    def guarda(root_id, watch, run_id):
        corrente = threading.current_thread()
        visto.update(name=corrente.name, daemon=corrente.daemon)
        return vero(root_id, watch, run_id)

    _, eventi = _events(conn, db_path, fid, guarda)
    assert list(eventi)[-1]["status"] == "ok"
    assert visto == {"name": "astrolog-scan-door", "daemon": True}


def test_a_file_still_being_written_waits_for_the_next_scan(conn, db_path, tmp_path):
    """Un file appena scritto (meno di 30 secondi) si salta come "ancora in scrittura": la copia
    dal telescopio puo' essere ancora in corso."""
    settle(write_light(tmp_path / "fresco.fits"), 0)
    _, eventi = _events(conn, db_path, add_folder(conn, tmp_path))
    fine = list(eventi)[-1]
    assert (fine["new"], fine["skipped"]) == (0, 1)
    assert fine["skipped_by_reason"] == [{"reason": "still_writing", "count": 1}]


@pytest.mark.parametrize(
    ("guasto", "motivo"),
    [(sqlite3.OperationalError("database or disk is full (mock)"), "database_error"),
     (ValueError("un guasto che nessuno aspettava (mock)"), "internal_error")],
)  # fmt: skip
def test_a_reading_that_breaks_closes_its_receipt_with_the_reason(
    conn, db_path, tmp_path, guasto, motivo
):
    """Una lettura che si rompe chiude la sua ricevuta col motivo -- il database che non risponde
    non e' un guasto qualsiasi -- e zero in ogni conto, poi l'errore risale al worker."""
    fid = add_folder(conn, tmp_path)

    def rompe(_root_id, _watch, _run_id):
        raise guasto

    corsa, eventi = _events(conn, db_path, fid, rompe)
    with pytest.raises(type(guasto)):
        list(eventi)
    riga = conn.execute(_RUN, (corsa,)).fetchone()
    assert (riga["status"], riga["reason"], riga["root_id"]) == ("error", motivo, fid)
    assert [riga[k] for k in TALLIES] == [0] * len(TALLIES)
    assert riga["ended_at"] is not None and riga["errors_detail"] is None
    assert not conn.in_transaction


def test_a_reading_stopped_then_broken_says_stopped_and_keeps_its_poses(conn, db_path, tmp_path):
    """Fermata dall'utente, una lettura che poi si rompe resta "fermata su richiesta", coi conti a
    zero: le pose lette fin li' restano, e un file sparito non si dice "non trovato", perche' la
    cartella non e' stata vista tutta."""
    write_light(tmp_path / "a.fits", obj="M 1")
    write_light(tmp_path / "b.fits", obj="M 2")
    fid = add_folder(conn, tmp_path)
    scan_door.scan_once(conn, fid)
    (tmp_path / "a.fits").unlink()
    write_light(tmp_path / "c.fits", obj="M 3")
    vero = scan_door.direct(db_path)

    def legge_poi_rompe(root_id, watch, run_id):
        vero(root_id, watch, run_id)
        raise ValueError("dopo lo Stop (mock)")

    corsa, eventi = _events(conn, db_path, fid, legge_poi_rompe)
    next(eventi)
    eventi.close()
    riga = conn.execute(_RUN, (corsa,)).fetchone()
    assert (riga["status"], riga["reason"]) == ("stopped", "stop_requested")
    assert [riga[k] for k in (*TALLIES, "unchanged")] == [0] * (len(TALLIES) + 1)
    pose = dict(
        conn.execute(
            "SELECT rel_path, state FROM pipeline_files WHERE root_id = ?"
            " AND frame_id IN (SELECT id FROM frames)",
            (fid,),
        )
    )
    assert pose == {"a.fits": "present", "b.fits": "present", "c.fits": "present"}


def test_a_reading_broken_after_its_judgement_shows_nothing_left_out(conn, db_path, tmp_path):
    """Una lettura che si rompe dopo aver guardato la cartella non mostra a meta' cio' che aveva
    visto: in Scansioni niente "gia' in archivio" e nessuna cartella lasciata fuori, come prima."""
    write_light(tmp_path / "a.fits", obj="M 1")
    write_light(tmp_path / "b.fits", obj="M 2")
    write_light(tmp_path / "sotto" / ".cestino" / "x.fits", obj="M 3")
    fid = add_folder(conn, tmp_path)
    scan_door.scan_once(conn, fid)
    vero = scan_door.direct(db_path)

    def legge_poi_rompe(root_id, watch, run_id):
        vero(root_id, watch, run_id)
        raise ValueError("dopo il giudizio (mock)")

    corsa, eventi = _events(conn, db_path, fid, legge_poi_rompe)
    with pytest.raises(ValueError, match="dopo il giudizio"):
        list(eventi)
    gesto = scan_history.one(conn, corsa, None)
    assert gesto is not None and (gesto.outcome, gesto.reason) == ("blocked", "internal_error")
    assert (gesto.left_out, gesto.dirs_left_out) == ([], [])


def test_a_reading_stopped_keeps_the_poses_of_its_folder(conn, db_path, tmp_path):
    """Fermata a meta', la lettura chiude con cio' che ha letto: le pose dei file letti sono della
    cartella, e la ricevuta dice "fermata"."""
    for i in range(3):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    fid = add_folder(conn, tmp_path)
    corsa, eventi = _events(conn, db_path, fid)
    next(eventi)
    eventi.close()
    assert conn.execute("SELECT status FROM pipeline_scans WHERE gesture = ?", (corsa,)).fetchone()[
        0
    ] == ("stopped")
    righe = conn.execute(
        "SELECT root_id, rel_path FROM pipeline_files WHERE frame_id IN (SELECT id FROM frames)"
    ).fetchall()
    assert [tuple(r) for r in righe] == [(fid, "f0.fits")]


def test_the_receipt_names_what_it_left_out_and_whose_it_is(conn, tmp_path):
    """La ricevuta dice di chi e' (corsa e cartella), le cartelle lasciate fuori per tipo -- i
    collegamenti la lettura nuova li segue, quindi nessuno -- e il motivo di una cartella che non
    risponde, anche nella riga salvata."""
    write_light(tmp_path / "sotto" / ".cestino" / "buttata.fits")
    fid = add_folder(conn, tmp_path)
    corsa = open_receipt(conn, fid, "2026-11-27T10:00:00.000Z")
    fine = scan_door.scan_once(conn, fid, corsa)
    # run_id: la riga che ha preso il posto del segnaposto, del gesto della corsa
    riga = conn.execute(_ROW, (fine["run_id"],)).fetchone()
    assert (riga["gesture"], riga["root_id"], fine["folder_id"]) == (corsa, fid, fid)
    assert (fine["hidden_dirs"], fine["unreadable_dirs"]) == (["sotto/.cestino"], [])
    assert "linked_dirs" not in fine
    spenta = add_folder(conn, tmp_path / "spenta")
    fine = scan_door.scan_once(conn, spenta)
    assert (fine["status"], fine["reason"]) == ("aborted", "root_unreachable")
    riga = conn.execute(_ROW, (fine["run_id"],)).fetchone()
    assert (riga["status"], riga["reason"]) == ("aborted", "root_unreachable")


def test_found_counts_every_file_the_walk_saw(conn, tmp_path, monkeypatch):
    """ "Trovati" e' ogni file che la lettura ha visto: nuovi, cambiati, da rileggere, uguali, non
    guardati e solo online. Un file che non si e' potuto guardare e' fra i non letti; uno ancora
    corto si rilegge e resta "ancora in scrittura", con quelli appena scritti."""
    write_light(tmp_path / "uguale.fits", obj="M 1")
    write_light(tmp_path / "cambia.fits", obj="M 2")
    _truncated(tmp_path / "corto.fits")
    fid = add_folder(conn, tmp_path)
    scan_door.scan_once(conn, fid)
    write_light(tmp_path / "cambia.fits", obj="M 22", age_s=300)
    write_light(tmp_path / "nuovo.fits", obj="M 3")
    settle(write_light(tmp_path / "fresco.fits", obj="M 4"), 0)
    write_light(tmp_path / "fantasma.fits", obj="M 5")
    write_light(tmp_path / "nuvola.fits", obj="M 6")
    online_only(monkeypatch, tmp_path / "nuvola.fits")
    vero = pipeline_changes.is_text
    monkeypatch.setattr(pipeline_changes, "is_text", lambda p: "fantasma" not in p and vero(p))
    fine = scan_door.scan_once(conn, fid, min_age_s=30)
    # nuovi 2 (uno fresco), cambiato 1, da rileggere 1, uguale 1, non guardato 1, online 1
    assert fine["found"] == 7
    assert fine["errors_detail"] == [{"file": "fantasma.fits", "reason": "file_unreadable"}]
    assert {e["reason"]: e["count"] for e in fine["skipped_by_reason"]} == {"still_writing": 2}


def test_two_copies_of_a_frame_read_together_are_one_new_and_one_duplicate(conn, tmp_path):
    """Due copie dello stesso file lette nella stessa scansione sono un frame nuovo e un doppione,
    come diceva la ricevuta vecchia (`test_scan_duplicate_header`); una terza copia arrivata dopo
    e' un altro doppione."""
    a = Path(write_light(tmp_path / "a" / "x.fits", obj="M 51"))
    for copia in ("b/copia.fits", "c/terza.fits"):
        (tmp_path / copia).parent.mkdir()
    (tmp_path / "b" / "copia.fits").write_bytes(a.read_bytes())
    settle(tmp_path / "b" / "copia.fits")
    fid = add_folder(conn, tmp_path)
    fine = scan_door.scan_once(conn, fid)
    assert (fine["new"], fine["duplicates"]) == (1, 1)
    (tmp_path / "c" / "terza.fits").write_bytes(a.read_bytes())
    settle(tmp_path / "c" / "terza.fits")
    fine = scan_door.scan_once(conn, fid)
    assert (fine["new"], fine["duplicates"]) == (0, 1)


def test_a_copy_of_a_file_held_out_elsewhere_is_new_not_a_duplicate(conn, tmp_path):
    """Un file senza tipo tenuto fuori in una cartella detta calibrazione non e' in archivio: se
    la risposta cambia e una sua copia arriva in un'altra cartella, la copia e' un frame nuovo e
    basta -- un file solo non si conta due volte."""
    a, b = tmp_path / "a", tmp_path / "b"
    write_fits(a / "x.fits", {"OBJECT": "M 13", "EXPTIME": 60.0, "DATE-OBS": "2024-05-17T21:00:00"})
    cartella_a = add_folder(conn, a)
    typeless.declare(conn, frame_folder.folder_key(str(a)), TypeAnswer.CALIBRATION)
    assert scan_door.scan_once(conn, cartella_a)["new"] == 0
    typeless.declare(conn, frame_folder.folder_key(str(a)), TypeAnswer.LIGHT)
    b.mkdir()
    (b / "x.fits").write_bytes((a / "x.fits").read_bytes())
    settle(b / "x.fits")
    fine = scan_door.scan_once(conn, add_folder(conn, b))
    assert (fine["found"], fine["new"], fine["duplicates"]) == (1, 1, 0)


def test_a_name_that_is_not_text_is_said_readable_with_its_own_reason():
    """Un nome non UTF-8 (una condivisione Linux scritta da un sistema vecchio) si mostra con `?`
    al posto dei caratteri storti e si dice "nome non scrivibile"; un nome buono non guardato e'
    un file non leggibile."""
    assert scan_door._shown("M31_\udce9.fits") == "M31_?.fits"
    assert scan_door._unlooked("M31_\udce9.fits") == "name_not_utf8"
    assert scan_door._unlooked("M31.fits") == "file_unreadable"


def test_a_closed_result_without_a_finish_is_said_stopped(conn, tmp_path):
    """Una lettura che torna senza essere arrivata in fondo e' "fermata", col suo motivo."""
    fid = add_folder(conn, tmp_path)
    corsa = open_receipt(conn, fid, "2026-11-27T10:00:00.000Z")
    risultato = scan_root(conn, fid, "2026-11-27T10:00:01.000Z", watch=Watch(), receipt=corsa)
    risultato = ScanResult(risultato.changes, finished=False)
    fine = scan_door.close(conn, fid, corsa, risultato)
    assert (fine["status"], fine["reason"]) == ("stopped", "stop_requested")
    riga = conn.execute(_RUN, (corsa,)).fetchone()
    assert (riga["status"], riga["reason"]) == ("stopped", "stop_requested")
