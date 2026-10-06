"""La scansione come lavoro di sottofondo: la richiesta risponde subito, l'avanzamento e la
ricevuta stanno in un canale solo (`/pipeline/status`); il lock; nessun avvio da solo; sul
NAS la cadenza; la guardia sull'host e il token del desktop."""

import itertools
import threading
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import TOKEN_HEADER, create_app
from astrolog.db.connect import connect
from astrolog.spine.scan_store import run_outcomes, start_run
from astrolog.worker.worker import State
from conftest import blocking_reader, settle, wait_until, write_light


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


def finished(client):
    s = status(client)
    return s["scan"] is not None and s["scan"]["receipt"] is not None


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


def test_the_outcome_of_a_reading_does_not_carry_the_files_not_read(conn):
    """Lo stato chiede com'e' finita ogni cartella a ogni interrogazione: la riga porta l'esito e
    basta, non l'elenco dei file non letti, che si legge a pagine quando serve."""
    folder_id = conn.execute(
        "INSERT INTO folders(root_path, created_at) VALUES('D:/Astro', 'ora')"
    ).lastrowid
    run_id = start_run(conn, folder_id, "ora")
    (riga,) = run_outcomes(conn, [run_id, run_id + 1])
    assert set(riga.keys()) == {"id", "status", "errors", "ended_at"}


def open_receipts(db_path: str | Path) -> int:
    with connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM scan_runs WHERE ended_at IS NULL").fetchone()[0]


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
    previous = (state.last_scan, state.scan_runs)
    with (
        mock.patch.object(state.worker, "start", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError),
    ):
        client.post(f"/api/v1/folders/{fid}/scan")
    with connect(state.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] == 0
    assert fid not in state.folder_locks
    assert (state.last_scan, state.scan_runs) == previous


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
    assert "errors_detail" not in status(client)["scan"]["receipt"]
    pagina = client.get(f"/api/v1/scan-runs/{prima}/errors", params={"limit": 1, "offset": 1})
    pagina = pagina.json()
    rotto = {"file": "b_rotto.fits", "reason": "header_unreadable"}
    assert (pagina["total"], pagina["items"]) == (2, [rotto])
    dopo = client.post(f"/api/v1/folders/{fid}/scan").json()["run_id"]
    assert wait_until(lambda: finished(client) and status(client)["scan"]["run_id"] == dopo)
    client.app.state.worker.join(10.0)
    vecchia = client.get(f"/api/v1/scan-runs/{prima}/errors")
    assert vecchia.status_code == 410 and vecchia.json()["detail"]["code"] == "errors_not_kept"
    assert client.get(f"/api/v1/scan-runs/{dopo}/errors").json()["total"] == 2
    assert client.get("/api/v1/scan-runs/99999/errors").status_code == 404
    c = connect(db_path)
    aperta = start_run(c, fid, "now")  # una corsa che non ha ancora scritto la sua ricevuta
    c.close()
    risposta = client.get(f"/api/v1/scan-runs/{aperta}/errors")
    assert risposta.status_code == 409 and risposta.json()["detail"]["code"] == "scan_run_open"


def test_scan_answers_at_once_and_the_receipt_arrives_in_status(app):
    client, fid, root = app
    r = client.post(f"/api/v1/folders/{fid}/scan")
    assert r.status_code == 202
    started = r.json()
    assert started["folder_id"] == fid and started["run_id"] >= 1
    assert wait_until(lambda: finished(client))
    receipt = status(client)["scan"]["receipt"]
    for key in ("status", "found", "new", "unchanged", "duplicates", "missing", "skipped",
                "errors", "unreadable_dirs", "online_only", "hidden_dirs", "linked_dirs", "id",
                "folder_id", "ended_at", "skipped_by_reason"):  # fmt: skip
        assert key in receipt, key
    assert receipt["status"] == "ok" and receipt["new"] == 5
    assert receipt["id"] == started["run_id"]
    runs = client.get("/api/v1/scan-runs").json()["items"]
    assert runs[0]["id"] == started["run_id"] and runs[0]["new"] == 5
    # **Quanto e' durata**, calcolata qui e non a schermo: il database tiene i due istanti, e la
    # differenza e' una derivazione come le altre. Zero secondi e' un valore vero -- una cartella
    # con cinque file si legge in un lampo -- quindi si guarda che sia un numero, non che sia > 0.
    assert isinstance(runs[0]["duration_s"], (int, float))
    # **E di quale cartella parla**, col percorso che l'utente riconosce: con il solo `folder_id`
    # la pagina dovrebbe leggersi le cartelle e appaiarle da se', cioe' fare un lavoro che e' del
    # backend. E' il percorso, come nella sezione Cartelle, non il nome dato alla cartella.
    assert runs[0]["folder_path"].endswith(root.name)
    # **E si possono chiedere quelle di una cartella sola**: e' cosi' che la sezione Cartelle
    # dira' com'e' andata l'ultima volta che ha letto quella li'. Il conto e' della cartella, non
    # dell'archivio, o una pagina che ne mostra venti direbbe "ce ne sono altre" per sempre.
    sola = client.get("/api/v1/scan-runs", params={"folder_id": fid}).json()
    assert [r["id"] for r in sola["items"]] == [started["run_id"]] and sola["total"] == 1
    altrui = client.get("/api/v1/scan-runs", params={"folder_id": fid + 1}).json()
    assert altrui["items"] == [] and altrui["total"] == 0
    client.app.state.worker.join(10.0)
    client.post(f"/api/v1/folders/{fid}/scan")
    assert wait_until(
        lambda: finished(client) and status(client)["scan"]["receipt"]["unchanged"] == 5
    )


def test_scan_lock_stop_and_the_button_verb(app):
    client, fid, root = app
    worker = client.app.state.worker
    gate = threading.Event()
    seen = []
    import astrolog.spine.scan as scan_mod

    slow_read = blocking_reader(scan_mod.read_frame, gate, seen)
    with mock.patch.object(scan_mod, "read_frame", side_effect=slow_read):
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
        assert wait_until(lambda: len(seen) >= 2)
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 409
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
    assert s["scan"]["receipt"]["status"] == "stopped"  # dal DB: il generatore non la emette
    assert s["scan"]["receipt"]["new"] >= 1 and s["scan"]["receipt"]["ended_at"]
    assert client.app.state.folder_locks == set()
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
    import astrolog.spine.scan as scan_mod

    slow_read = blocking_reader(scan_mod.read_frame, gate, seen)
    with mock.patch.object(scan_mod, "read_frame", side_effect=slow_read):
        assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 202
        assert wait_until(lambda: len(seen) >= 2)  # la scansione e' ferma sul secondo file
        r = client.post(f"/api/v1/folders/{other_id}/scan")
        assert r.status_code == 409 and r.json()["detail"]["code"] == "worker_busy"
        assert status(client)["scan"]["folder_id"] == fid  # la corsa che gira, non la respinta
        assert open_receipts(client.app.state.db_path) == 1
        gate.set()
        client.app.state.worker.join(10.0)
    assert client.app.state.folder_locks == set()


def test_no_autostart_and_precheck_409s(app):
    client, fid, root = app
    assert client.app.state.worker.snapshot().state == State.IDLE
    assert status(client)["action"] == "start" and status(client)["scan"] is None
    assert client.post("/api/v1/folders/9999/scan").status_code == 404
    for p in root.iterdir():
        p.unlink()
    root.rmdir()
    assert client.post(f"/api/v1/folders/{fid}/scan").status_code == 409
    assert client.app.state.folder_locks == set()


def test_scan_schedule_nas(db_path, tmp_path):
    root = tmp_path / "lib"
    write_light(root / "a.fits")
    with TestClient(create_app(db_path, scan_every_s=0.2), base_url="http://localhost") as c:
        c.post("/api/v1/folders", json={"root_path": str(root)})
        assert wait_until(lambda: c.get("/api/v1/scan-runs").json()["items"] != [])
        assert wait_until(lambda: c.get("/api/v1/scan-runs").json()["items"][0]["status"] == "ok")
        assert c.get("/api/v1/scan-runs").json()["items"][0]["new"] == 1


def test_unknown_hosts_are_refused_and_declared_ones_admitted(db_path):
    with TestClient(create_app(db_path, hosts=["nas.local"]), base_url="http://localhost") as c:
        assert c.get("/api/health", headers={"host": "localhost"}).status_code == 200
        assert c.get("/api/health", headers={"host": "nas.local"}).status_code == 200
        assert c.get("/api/health", headers={"host": "evil.example"}).status_code == 400


def test_desktop_token_is_required_when_set(db_path):
    # noqa qui e non nella configurazione: la presa sui segreti resta accesa sui test, e
    # questo e' l'unico posto dove un token finto e' il soggetto della prova.
    with TestClient(create_app(db_path, token="gettone-1"), base_url="http://localhost") as c:  # noqa: S106
        assert c.get("/api/health").status_code == 401
        assert c.get("/api/health", headers={TOKEN_HEADER: "sbagliato"}).status_code == 401
        assert c.get("/api/health", headers={TOKEN_HEADER: "gettone-1"}).status_code == 200
        assert c.get("/openapi.json").status_code == 200  # consultazione: senza token
        assert c.get("/docs").status_code == 200


def test_the_folder_stays_locked_until_the_whole_run_ends(app):
    """Il lock si rilascia a fine corsa, non a fine lettura: mentre la normalizzazione lavora
    su quei frame, una seconda scansione della stessa cartella sente "gia' in corso"."""
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
        assert r.status_code == 409 and r.json()["detail"]["code"] == "scan_running"
        assert client.app.state.folder_locks == {fid}
        gate.set()
        client.app.state.worker.join(10.0)
    assert client.app.state.folder_locks == set()
