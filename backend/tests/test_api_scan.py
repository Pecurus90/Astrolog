"""La scansione come lavoro di sottofondo: la richiesta risponde subito, l'avanzamento e la
ricevuta stanno in un canale solo (`/pipeline/status`); il lock; nessun avvio da solo; sul
NAS la cadenza; la guardia sull'host e il token del desktop."""

import itertools
import threading
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api import scan as scan_api
from astrolog.api.app import TOKEN_HEADER, create_app
from astrolog.db.connect import connect
from astrolog.pipeline.changes import open_receipt
from astrolog.spine.scan_store import run_outcomes
from astrolog.worker.worker import State
from conftest import add_folder, blocking_reader, receipts, settle, wait_until, write_light

_FEED_BEHIND = scan_api._feed_behind  # the real one, before the suite's fence turns it off


@pytest.fixture
def app(db_path, tmp_path):
    root = tmp_path / "lib"
    for i in range(5):
        write_light(root / f"f{i}.fits", obj=f"M {i + 1}")
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        fid = c.post("/api/v1/folders", json={"root_path": str(root)}).json()["id"]
        yield c, fid, root


def status(client):
    return client.get("/api/v1/pipeline/status").json()


def scans(client):
    return client.get("/api/v1/scans", params={"limit": 200}).json()["items"]


def receipt(client):
    """La scansione dell'ultima corsa, una volta chiusa: la carta del suo gesto in `/scans`."""
    s = status(client)["scan"]
    if s is None or s["state"] in ("running", "not_run"):
        return None
    carta = next((g for g in scans(client) if g["id"] == s["run_id"]), None)
    return carta if carta is not None and carta["duration_s"] is not None else None


def finished(client):
    return receipt(client) is not None


def test_the_new_run_is_visible_before_the_worker_starts(app):
    """La ricevuta della corsa nuova si assegna **prima** dell'avvio: fra le due righe c'e' un
    altro thread, e chi interroga lo stato in quell'istante vedrebbe la corsa VECCHIA come se
    fosse quella appena chiesta -- la pagina mostrerebbe i numeri della scansione di ieri."""
    client, fid, _ = app
    stato = client.app.state
    visto = []
    vero = stato.worker.start

    def spia(stages):
        visto.append(stato.last_scan)  # cosa vedrebbe un poll in questo istante
        return vero(stages)

    stato.worker.start = spia
    try:
        run_id = client.post(f"/api/v1/folders/{fid}/scan").json()["run_id"]
    finally:
        stato.worker.start = vero
    assert visto == [(fid, run_id)], "all'avvio lo stato indicava ancora la corsa precedente"
    assert wait_until(lambda: finished(client))


def test_the_last_scan_says_today_by_the_home_site_clock(app):
    """La riga dell'ultima scansione dice «oggi» (tavola Menu 36-41): il giorno relativo nel fuso
    del sito predefinito arriva dall'API, per la scansione finita e per il worker."""
    client, fid, _ = app
    corpo = {"name": "Vicenza", "latitude": 45.5, "longitude": 11.5, "is_default": True}
    corpo |= {"timezone": "Europe/Rome", "elevation_m": 40}
    assert client.post("/api/v1/sites", json=corpo).status_code == 201
    client.post(f"/api/v1/folders/{fid}/scan")
    assert wait_until(
        lambda: status(client)["last_scan"] is not None and status(client)["worker"]["ended_at"]
    )
    detto = status(client)
    assert detto["last_scan"]["ended_day"] == "today", detto["last_scan"]
    assert detto["worker"]["ended_day"] == "today", detto["worker"]


def test_the_scan_says_the_folder_it_reads(app):
    """La prima scansione dice la cartella in lettura (tavola Dashboard 583, «Cartella
    Dati/Astro»): la rotta la manda col progresso, la pagina non la cerca."""
    client, fid, root = app
    client.post(f"/api/v1/folders/{fid}/scan")
    assert wait_until(lambda: finished(client))
    assert status(client)["scan"]["folder_path"] == str(root)


def test_a_scan_feeds_the_new_pipeline_behind_the_scenes(app, db_path, monkeypatch):
    """Dopo la lettura la pipeline nuova legge la stessa cartella sul suo thread: intanto l'app e'
    libera (Avvia, una seconda scansione accettata), e senza ASTAP (il recinto) non rompe niente."""
    import astrolog.pipeline.run as run_module

    monkeypatch.setattr(scan_api, "_feed_behind", _FEED_BEHIND)
    client, fid, _ = app
    gate, real = threading.Event(), run_module.run_roots

    def held(*args):
        gate.wait(10.0)
        yield from real(*args)

    monkeypatch.setattr(run_module, "run_roots", held)
    client.post(f"/api/v1/folders/{fid}/scan")
    client.app.state.worker.join(20.0)
    during = status(client)
    again = client.post(f"/api/v1/folders/{fid}/scan")
    client.app.state.worker.join(20.0)
    gate.set()
    client.app.state.behind.join(20.0)
    with connect(db_path) as conn:
        files = conn.execute("SELECT count(*) FROM pipeline_files").fetchone()[0]
    assert during["action"] == "start" and again.status_code == 202, again.text
    assert files == 5


def test_the_outcome_of_a_reading_does_not_carry_the_files_not_read(conn):
    """Lo stato chiede com'e' finita ogni cartella a ogni interrogazione: la riga porta l'esito e
    basta, non l'elenco dei file non letti, che si legge a pagine quando serve."""
    folder_id = add_folder(conn, "D:/Astro")
    run_id = open_receipt(conn, folder_id, "ora")
    (riga,) = run_outcomes(conn, run_id)
    assert set(riga.keys()) == {"id", "root_id", "status", "errors", "ended_at"}


def open_receipts(db_path: str | Path) -> int:
    with connect(db_path) as conn:
        return len(receipts(conn, "ended_at IS NULL"))


@pytest.mark.parametrize("stop_from_check", [1, 2])
def test_resume_reads_one_folder_stopped_before_it_began(app, stop_from_check):
    """A single folder stopped before it began, even after its stage was handed out, leaves no
    receipt open forever (as with many folders), and Resume reads it again."""
    client, fid, _ = app
    worker = client.app.state.worker
    checks = itertools.count(1)
    worker._stop_requested = lambda: next(checks) >= stop_from_check
    try:
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
        worker.join(10.0)
    finally:
        del worker._stop_requested

    def pose():
        with connect(client.app.state.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]

    db_path = client.app.state.db_path
    assert (status(client)["action"], pose(), open_receipts(db_path)) == ("resume", 0, 0)
    client.post("/api/v1/pipeline/run")
    worker.join(30.0)
    assert pose() == 5


def test_a_start_that_breaks_unexpectedly_leaves_nothing_behind(app):
    """Not only a busy worker: any failure after the receipt opened discards it, frees the folder
    and puts back the previous run, as the scan of every folder does."""
    client, fid, _ = app
    state = client.app.state
    # a run before, so "put back" and "reset" give different states
    assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
    state.worker.join(30.0)
    previous = (state.last_scan, state.gesture)
    assert previous[0] is not None
    with (
        mock.patch.object(state.worker, "start", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError),
    ):
        client.post(f"/api/v1/folders/{fid}/scan")
    with connect(state.db_path) as conn:
        assert len(receipts(conn)) == 1
    assert not state.behind.scanning(fid)
    assert (state.last_scan, state.gesture) == previous


def test_the_files_not_read_are_listed_a_page_at_a_time(app, db_path):
    """La ricevuta nello stato porta i numeri; i file non letti si leggono a pagine, perche'
    possono essere migliaia e la pagina interroga lo stato ogni pochi secondi. L'elenco lo tiene
    l'ultima scansione della cartella, e se non e' arrivata in fondo anche l'ultima che ci e'
    arrivata (Marco, 2026-09-11): delle altre lo dice un codice."""
    client, fid, root = app
    for nome in ("a_rotto.fits", "b_rotto.fits"):
        (root / nome).write_bytes(b"non e' un FITS\x00" * 50)
        settle(root / nome)
    prima = client.post(f"/api/v1/folders/{fid}/scan").json()["run_id"]
    assert wait_until(lambda: finished(client))
    client.app.state.worker.join(10.0)
    assert "errors_detail" not in str(status(client)["scan"])
    pagina = client.get(f"/api/v1/scans/{prima}/unread", params={"limit": 1, "offset": 1})
    pagina = pagina.json()
    rotto = {"file": "b_rotto.fits", "reason": "header_unreadable"}
    assert (pagina["total"], pagina["items"]) == (2, [rotto])
    dopo = client.post(f"/api/v1/folders/{fid}/scan").json()["run_id"]
    assert wait_until(lambda: finished(client) and status(client)["scan"]["run_id"] == dopo)
    client.app.state.worker.join(10.0)
    vecchia = client.get(f"/api/v1/scans/{prima}/unread")
    assert vecchia.status_code == 410 and vecchia.json()["detail"]["code"] == "errors_not_kept"
    assert client.get(f"/api/v1/scans/{dopo}/unread").json()["total"] == 2
    assert client.get("/api/v1/scans/99999/unread").status_code == 404


def test_the_errors_of_an_unknown_reading_are_a_404_with_its_code(client_vuoto):
    """Una ricevuta che non c'e' si dice col suo codice, non con una lista vuota."""
    r = client_vuoto.get("/api/v1/scans/99999/unread")
    assert r.status_code == 404, r.text
    assert r.json()["detail"]["code"] == "scan_not_found"


def test_stop_with_nothing_running_still_answers(client_vuoto):
    """Stop a worker fermo: 200 con lo stato com'e', non un errore."""
    r = client_vuoto.post("/api/v1/pipeline/stop")
    assert r.status_code == 200, r.text
    assert r.json()["worker"]["state"] == "idle"


def test_scan_answers_at_once_and_the_receipt_arrives_in_status(app):
    client, fid, root = app
    r = client.post(f"/api/v1/folders/{fid}/scan")
    assert r.status_code == 202
    started = r.json()
    assert started["folder_id"] == fid and started["run_id"] >= 1
    assert wait_until(lambda: finished(client))
    carta = receipt(client)
    for key in ("id", "outcome", "reason", "folders", "new", "left_out", "dirs_left_out",
                "unread", "unread_files", "duration_s"):  # fmt: skip
        assert key in carta, key
    assert carta["outcome"] == "completed" and carta["new"] == 5
    assert carta["id"] == started["run_id"]
    assert scans(client)[0]["id"] == started["run_id"]
    # **Quanto e' durata**, calcolata qui e non a schermo: il database tiene i due istanti, e la
    # differenza e' una derivazione come le altre. Zero secondi e' un valore vero -- una cartella
    # con cinque file si legge in un lampo -- quindi si guarda che sia un numero, non che sia > 0.
    assert isinstance(carta["duration_s"], (int, float))
    # **E di quale cartella parla**, col percorso che l'utente riconosce: con il solo `folder_id`
    # la pagina dovrebbe leggersi le cartelle e appaiarle da se', cioe' fare un lavoro che e' del
    # backend. E' il percorso, come nella sezione Cartelle, non il nome dato alla cartella.
    assert [f.endswith(root.name) for f in carta["folders"]] == [True]
    client.app.state.worker.join(10.0)
    client.post(f"/api/v1/folders/{fid}/scan")

    def invariati():
        carta = receipt(client)
        return carta is not None and {"reason": "unchanged", "count": 5} in carta["left_out"]

    assert wait_until(invariati)


def test_scan_lock_stop_and_the_button_verb(app):
    client, fid, root = app
    worker = client.app.state.worker
    gate = threading.Event()
    seen = []
    import astrolog.pipeline.scan as scan_mod

    slow_read = blocking_reader(scan_mod.scan_file, gate, seen)
    with mock.patch.object(scan_mod, "scan_file", side_effect=slow_read):
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
        assert wait_until(lambda: len(seen) >= 2)
        r = client.post(f"/api/v1/folders/{fid}/scan")
        assert r.status_code == 409
        assert r.json()["detail"] == {"code": "scan_running", "folder_id": fid}
        s = status(client)
        assert s["worker"]["state"] == "running" and s["action"] == "stop"
        assert s["scan"]["state"] == "running" and s["scan"]["folder_id"] == fid
        assert s["scan"]["last_event"]["run_id"] >= 1
        client.post("/api/v1/pipeline/stop")
        gate.set()
        worker.join(10.0)
    assert worker.snapshot().state == State.STOPPED
    s = status(client)
    assert s["action"] == "resume" and s["scan"]["folder_id"] == fid  # cosa riprendere
    carta = receipt(client)
    assert carta["outcome"] == "stopped"  # dal DB: il generatore non la emette
    assert carta["new"] >= 1 and carta["duration_s"] is not None
    assert not client.app.state.behind.scanning(fid)
    assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202  # si riparte


def test_a_second_folder_finds_the_worker_busy_and_leaves_no_open_receipt(app, tmp_path):
    """Il lock e' per cartella, il worker e' uno: la cartella B mentre gira A riceve 409 e la
    sua ricevuta appena aperta sparisce."""
    client, fid, _ = app
    other = tmp_path / "altra"
    write_light(other / "b.fits", obj="M 2")
    other_id = client.post("/api/v1/folders", json={"root_path": str(other)}).json()["id"]
    gate = threading.Event()
    seen = []
    import astrolog.pipeline.scan as scan_mod

    slow_read = blocking_reader(scan_mod.scan_file, gate, seen)
    with mock.patch.object(scan_mod, "scan_file", side_effect=slow_read):
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
        assert wait_until(lambda: len(seen) >= 2)  # la scansione e' ferma sul secondo file
        r = client.post(f"/api/v1/folders/{other_id}/scan")
        assert r.status_code == 409 and r.json()["detail"]["code"] == "worker_busy"
        assert status(client)["scan"]["folder_id"] == fid  # la corsa che gira, non la respinta
        assert open_receipts(client.app.state.db_path) == 1
        gate.set()
        client.app.state.worker.join(10.0)
    assert not client.app.state.behind.scanning(fid)


def test_no_autostart_and_precheck_409s(app):
    client, fid, root = app
    assert client.app.state.worker.snapshot().state == State.IDLE
    assert status(client)["action"] == "start" and status(client)["scan"] is None
    assert client.post("/api/v1/folders/9999/scan").status_code == 404
    scritta = client.get("/api/v1/folders").json()["items"][0]["root_path"]
    for p in root.iterdir():
        p.unlink()
    root.rmdir()
    r = client.post(f"/api/v1/folders/{fid}/scan")
    assert r.status_code == 409
    assert r.json()["detail"] == {"code": "root_unreachable", "path": scritta}
    assert not client.app.state.behind.scanning(fid)


def test_the_end_of_a_run_hands_its_folders_on_unless_stopped(db_path, monkeypatch):
    """A corsa finita -- l'ultimo stadio della catena, non uno in mezzo -- le cartelle lette passano
    alla pipeline nuova; fermata dall'utente, no: lo Stop vale anche li'."""
    monkeypatch.setattr(scan_api, "_feed_behind", _FEED_BEHIND)
    date = []
    fermato = [False]
    stato = mock.Mock(db_path=db_path)
    stato.worker.stop_requested = lambda: fermato[0]
    stato.behind.kick = date.append
    passi = [(nome, mock.Mock()) for nome in ("scan", "normalize", "identify")]
    stadi = scan_api._stages_with_cleanup(stato, passi, iter([3, 5]), [], set())
    assert [s.on_finish is not None for s in stadi] == [False, False, True]
    stadi[-1].on_finish()
    assert date == [[3, 5]]
    fermato[0] = True
    stadi[-1].on_finish()
    assert date == [[3, 5]]


def test_scan_schedule_nas(db_path, tmp_path):
    root = tmp_path / "lib"
    write_light(root / "a.fits")
    with TestClient(create_app(db_path, scan_every_s=0.2), base_url="http://localhost") as c:
        c.post("/api/v1/folders", json={"root_path": str(root)})
        assert wait_until(lambda: scans(c) != [])
        assert wait_until(lambda: scans(c)[0]["outcome"] == "completed")
        # a later round may end before this read and find nothing new: the file is new once
        assert sum(run["new"] for run in scans(c)) == 1


def test_a_locked_database_skips_one_round_of_the_schedule_not_all(db_path, tmp_path):
    """Sul NAS un'altra scrittura tiene il database per un attimo: quel giro salta, la cadenza
    resta viva e il giro dopo legge la cartella."""
    import sqlite3

    import astrolog.api.scan as scan_api

    root = tmp_path / "lib"
    write_light(root / "a.fits")
    vero = scan_api.active_folder_ids
    giri = itertools.count()

    def bloccato_al_primo(conn):
        if next(giri) == 0:
            raise sqlite3.OperationalError("database is locked")
        return vero(conn)

    with mock.patch.object(scan_api, "active_folder_ids", bloccato_al_primo):
        app = create_app(db_path, scan_every_s=0.2)
        with TestClient(app, base_url="http://localhost") as c:
            c.post("/api/v1/folders", json={"root_path": str(root)})
            assert wait_until(lambda: scans(c) != [])


def test_a_closed_app_starts_no_folder_of_its_round(db_path, tmp_path):
    """La cadenza aspetta la cartella in corso: chiusa l'app, non passa alla dopo (Issue #14)."""
    import time

    import astrolog.api.scan as scan_api
    from astrolog.worker.worker import Stage

    partite = []

    def senza_fine(state, folder_id, run_id):
        partite.append(folder_id)

        def passi():
            while True:
                time.sleep(0.01)
                yield {"current": 0, "total": 1}

        return [Stage("scan", passi)]

    for nome in ("a", "b"):
        write_light(tmp_path / nome / "a.fits")
    with mock.patch.object(scan_api, "_one_folder_stages", senza_fine):
        with TestClient(create_app(db_path), base_url="http://localhost") as c:
            for nome in ("a", "b"):
                c.post("/api/v1/folders", json={"root_path": str(tmp_path / nome)})
        app = create_app(db_path, scan_every_s=0.05)
        with TestClient(app, base_url="http://localhost"):
            assert wait_until(lambda: partite != [])
        time.sleep(0.5)
    assert len(partite) == 1 and not app.state.worker.is_running()


def test_a_folder_starting_while_the_app_closes_is_stopped_too(db_path, tmp_path):
    """La chiusura arriva fra il controllo della cadenza e l'avvio: l'avvio cancellerebbe lo stop,
    e la chiusura aspetterebbe la cartella intera."""
    import time

    import astrolog.api.scan as scan_api
    from astrolog.worker.worker import Stage

    def senza_fine(state, folder_id, run_id):
        def passi():
            while True:
                time.sleep(0.01)
                yield {"current": 0, "total": 1}

        return [Stage("scan", passi)]

    vero, entrata, chiusa = scan_api.start_scan, threading.Event(), threading.Event()

    def in_ritardo(state, conn, folder_id):
        entrata.set()
        time.sleep(0.5)
        return vero(state, conn, folder_id)

    write_light(tmp_path / "a" / "a.fits")
    with mock.patch.object(scan_api, "_one_folder_stages", senza_fine):
        with TestClient(create_app(db_path), base_url="http://localhost") as c:
            c.post("/api/v1/folders", json={"root_path": str(tmp_path / "a")})
        app = create_app(db_path, scan_every_s=0.05)

        def apri_e_chiudi():
            with TestClient(app, base_url="http://localhost"):
                entrata.wait(10.0)
            chiusa.set()

        with mock.patch.object(scan_api, "start_scan", in_ritardo):
            threading.Thread(target=apri_e_chiudi, daemon=True).start()
            chiusa_in_tempo = chiusa.wait(10.0)
            app.state.worker.stop()  # red: free the stuck closing before the patches go
            chiusa.wait(10.0)
    assert chiusa_in_tempo and not app.state.worker.is_running()


def test_unknown_hosts_are_refused_and_declared_ones_admitted(db_path):
    with TestClient(create_app(db_path, hosts=["nas.local"]), base_url="http://localhost") as c:
        assert c.get("/api/health", headers={"host": "localhost"}).status_code == 200
        assert c.get("/api/health", headers={"host": "nas.local"}).status_code == 200
        assert c.get("/api/health", headers={"host": "evil.example"}).status_code == 400


def test_desktop_token_is_required_when_set(db_path):
    # Esenzione qui e non nella configurazione: la presa sui segreti resta accesa sui test, e
    # questo e' l'unico posto dove un token finto e' il soggetto della prova.
    with TestClient(create_app(db_path, token="gettone-1"), base_url="http://localhost") as c:  # noqa: S106
        assert c.get("/api/health").status_code == 401
        assert c.get("/api/health", headers={TOKEN_HEADER: "sbagliato"}).status_code == 401
        assert c.get("/api/health", headers={TOKEN_HEADER: "gettone-1"}).status_code == 200
        assert c.get("/openapi.json").status_code == 200  # consultazione: senza token
        assert c.get("/docs").status_code == 200


def test_the_folder_stays_locked_until_the_whole_run_ends(app):
    """Finche' la corsa non e' finita, non solo la lettura: mentre la normalizzazione lavora su
    quei frame, una seconda scansione della stessa cartella e' rifiutata (il worker e' uno:
    "occupato"); a fine corsa nessuna cartella resta tenuta (passo 40.4, `Behind.scanning`)."""
    client, fid, _ = app
    gate = threading.Event()
    seen = []
    import astrolog.spine.run as run_mod

    real = run_mod.normalize_frames

    def slow(conn):
        seen.append(1)
        gate.wait(10.0)
        yield from real(conn)

    with mock.patch.object(run_mod, "normalize_frames", slow):
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
        assert wait_until(lambda: seen != [])
        r = client.post(f"/api/v1/folders/{fid}/scan")
        assert r.status_code == 409 and r.json()["detail"]["code"] == "worker_busy"
        gate.set()
        client.app.state.worker.join(10.0)
    assert not client.app.state.behind.scanning(fid)
