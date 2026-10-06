"""Leggere TUTTE le cartelle con un gesto solo: e' cio' che fa il pulsante in barra.

La scansione di una cartella sola sta in `test_api_scan.py`, con la sua meccanica (lock,
ricevuta, verbo del pulsante). Qui c'e' quello che cambia quando le cartelle sono piu' d'una:
una corsa sola, una ricevuta per cartella, e cio' che non si e' potuto leggere detto invece
che taciuto.
"""

import threading
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db.connect import connect
from astrolog.spine import run
from astrolog.spine.scan import COUNTS
from astrolog.spine.scan_store import start_run
from astrolog.spine.stages import mark_pending
from astrolog.worker.worker import Stage, WorkerBusyError
from conftest import settle, wait_until, write_light


@pytest.fixture
def app(db_path, tmp_path):
    """Due cartelle vere, tre frame in una e due nell'altra: i conti si distinguono."""
    prima, seconda = tmp_path / "prima", tmp_path / "seconda"
    for i in range(3):
        write_light(prima / f"a{i}.fits", obj=f"M {i + 1}")
    for i in range(2):
        write_light(seconda / f"b{i}.fits", obj=f"NGC {i + 1}")
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        uno = c.post("/api/v1/folders", json={"root_path": str(prima)}).json()["id"]
        due = c.post("/api/v1/folders", json={"root_path": str(seconda)}).json()["id"]
        yield c, uno, due


def scan_all(client):
    """Il gesto della barra. Asserisce il 202: un helper che accettasse anche il rifiuto
    lascerebbe passare in silenzio i test che dopo guardano l'archivio."""
    r = client.post("/api/v1/scan")
    assert r.status_code == 202, r.text
    return r


def status(client):
    return client.get("/api/v1/pipeline/status").json()


def test_one_gesture_reads_every_folder(app):
    """Il pulsante in barra non chiede QUALE cartella: le legge tutte. Una corsa sola -- il
    worker ne accetta una per volta -- con una ricevuta per cartella, perche' una ricevuta e'
    il racconto di una cartella e i suoi numeri non si sommano con quelli di un'altra."""
    client, uno, due = app
    r = scan_all(client)
    assert r.status_code == 202
    avviate = {c["folder_id"]: c["run_id"] for c in r.json()["started"]}
    assert set(avviate) == {uno, due}, "una cartella non e' stata letta"
    assert len(set(avviate.values())) == 2, "due cartelle, due ricevute"

    client.app.state.worker.join(30.0)
    ricevute = client.get("/api/v1/scan-runs").json()["items"]
    per_cartella = {r["folder_id"]: r for r in ricevute}
    assert per_cartella[uno]["found"] == 3
    assert per_cartella[due]["found"] == 2
    assert all(r["status"] == "ok" for r in ricevute)


def test_the_frames_of_every_folder_are_in_the_archive(app):
    """La prova che conta per chi usa l'app: dopo un gesto solo, i frame di **tutte** le
    cartelle sono dentro l'archivio. Guardare le ricevute non basta -- direbbero che la lettura
    e' partita, non che l'archivio e' cresciuto.

    Si contano i **frame** e non gli oggetti: un oggetto nasce due stadi piu' a valle, e nella
    suite il solver non parte (il recinto di `conftest.py` e' il caso "ASTAP non c'e' ancora",
    che e' anche il primo avvio di chiunque). Contare gli oggetti farebbe fallire questa prova
    per una ragione che non c'entra niente con le due cartelle."""
    client, uno, due = app
    scan_all(client)
    client.app.state.worker.join(30.0)
    assert wait_until(lambda: status(client)["worker"]["state"] != "running")

    per_cartella = _frames_per_folder(client)
    assert per_cartella == {uno: 3, due: 2}, "un gesto, e i frame di tutte e due le cartelle"


def test_the_stage_numbers_are_the_sum_of_the_folders(app):
    """La riga dello stadio a schermo e' **una**, e i suoi numeri sono la somma delle cartelle:
    3 + 2 = 5 trovati. Si sommano solo i conteggi veri (`spine/scan.COUNTS`): sommare ogni
    intero prenderebbe anche `done`, che in Python **e'** un intero, e lo stadio direbbe di
    aver finito due volte invece di aver finito."""
    client, _, _ = app
    scan_all(client)
    client.app.state.worker.join(30.0)

    stadio = next(
        s
        for s in client.get("/api/v1/pipeline/status").json()["worker"]["stages"]
        if s["name"] == "scan"
    )
    assert stadio["tally"]["found"] == 5 and stadio["tally"]["new"] == 5


def test_the_end_of_the_run_is_not_a_number(db_path, tmp_path):
    """`done` dice "ho finito", non "quante": in Python **e' un intero** (`True`), quindi una
    somma che prendesse ogni intero lo conterebbe, e la riga finale direbbe `done: 2` con due
    cartelle. Si guarda l'**evento** e non il riassunto dello stadio: quello toglie `done` per
    conto suo (`worker/worker.py`), quindi li' l'errore non si vedrebbe mai."""
    root = tmp_path / "lib"
    write_light(root / "a.fits", obj="M 1")
    with connect(db_path) as conn:
        uno = conn.execute(
            "INSERT INTO folders(root_path, created_at) VALUES(?, 'ora')", (str(root),)
        ).lastrowid
        due = conn.execute(
            "INSERT INTO folders(root_path, created_at) VALUES(?, 'ora')", (str(tmp_path),)
        ).lastrowid
        corse = [
            (uno, start_run(conn, uno, "2026-09-16T10:00:00.000Z")),
            (due, start_run(conn, due, "2026-09-16T10:00:01.000Z")),
        ]
        # solo lo stadio della lettura: gli altri della catena hanno i loro numeri, e l'ultimo
        # evento della corsa sarebbe quello delle notti
        nome, fabbrica = run.queue_folders(db_path, corse)[0]
        assert nome == "scan"
        fine = list(fabbrica())[-1]
    assert fine["done"] is True, f"il segnale di fine e' diventato un numero: {fine['done']!r}"
    interi = {k for k, v in fine.items() if isinstance(v, int) and not isinstance(v, bool)}
    assert interi == set(COUNTS), "nella somma e' entrato qualcosa che non e' un conteggio"


def test_a_folder_lost_while_reading_does_not_look_like_a_clean_run(app, tmp_path):
    """Una cartella che muore **mentre** la si legge -- il NAS che si spegne, non quello gia'
    spento all'avvio -- non passa dal pre-controllo e non finisce fra le saltate. Se anche lo
    stadio dicesse "tutto bene", l'utente leggerebbe *fatto* con una cartella non letta: finche'
    non c'e' la pagina Cartelle, questa e' l'unica cosa che glielo dice."""
    client, uno, due = app
    with mock.patch.object(run, "scan_folder", _cade(tmp_path, "seconda", due)):
        scan_all(client)
        client.app.state.worker.join(30.0)

    stadio = next(
        s
        for s in client.get("/api/v1/pipeline/status").json()["worker"]["stages"]
        if s["name"] == "scan"
    )
    assert stadio["state"] != "completed", (
        "una cartella persa e lo schermo dice che e' andato tutto bene"
    )
    with connect(client.app.state.db_path) as conn:
        righe = {r[0]: r[1] for r in conn.execute("SELECT folder_id, status FROM scan_runs")}
    assert righe[uno] == "ok", "le altre cartelle si leggono lo stesso"


def _cade(tmp_path, cartella, quale):
    """`run.scan_folder` che fa sparire la radice di `quale` appena comincia a leggerla."""
    vero = run.scan_folder

    def cade_la_radice(conn, folder_id, *a, **k):
        if folder_id == quale:
            for f in (tmp_path / cartella).iterdir():
                f.unlink()
            (tmp_path / cartella).rmdir()
        yield from vero(conn, folder_id, *a, **k)

    return cade_la_radice


@pytest.mark.parametrize("prima_fa_altro", [False, True], ids=["subito", "dopo un altro lavoro"])
@pytest.mark.parametrize(
    "guasto, esito",
    [
        ("cartella persa", "error"),
        ("file illeggibile", "completed_with_errors"),
        ("nessuno", "completed"),
    ],
)
def test_the_first_folder_is_not_covered_by_the_last(app, tmp_path, prima_fa_altro, guasto, esito):
    """Com'e' andata una lettura di piu' cartelle lo dicono le ricevute di TUTTE, dalla peggiore:
    un guasto nella prima non lo copre l'ultima letta bene, e resta detto quando il worker passa
    a un altro lavoro -- e' da questo stato che la pagina accende l'avviso della cartella persa."""
    client, uno, _ = app
    lettura = run.scan_folder
    if guasto == "cartella persa":
        lettura = _cade(tmp_path, "prima", uno)
    elif guasto == "file illeggibile":
        (tmp_path / "prima" / "rotto.fits").write_bytes(b"non e' un FITS" * 50)
        settle(tmp_path / "prima" / "rotto.fits")
    with mock.patch.object(run, "scan_folder", lettura):
        scan_all(client)
        client.app.state.worker.join(30.0)
    if prima_fa_altro:  # un lavoro che finisce bene, o lo stato del worker direbbe gia' `error`
        client.app.state.worker.start([Stage("normalize", _un_lavoro_finito)])
        client.app.state.worker.join(5.0)
        assert client.app.state.worker.snapshot().state == "completed"
    assert status(client)["scan"]["state"] == esito


def _un_lavoro_finito():
    yield {"done": True, "total": 0}


def test_a_reading_that_falls_before_the_first_folder_still_answers(app):
    """Una corsa che cade prima di cominciare la prima cartella butta tutte le sue ricevute: lo
    stato risponde lo stesso, col guasto del worker, invece di cadere a ogni interrogazione."""
    client, _, _ = app
    with mock.patch.object(run, "connect", side_effect=OSError("disco staccato")):
        scan_all(client)
        client.app.state.worker.join(10.0)
    r = client.get("/api/v1/pipeline/status")
    assert r.status_code == 200, r.text
    assert r.json()["scan"]["state"] == "error"


def test_while_the_reading_is_being_settled_the_state_is_still_the_workers(app):
    """Chiusa l'ultima ricevuta, lo stadio lavora ancora (lo stacco di chi torna ad aspettare):
    finche' non ha finito lo stato e' quello del worker, e la ricevuta non si mostra."""
    client, _, _ = app
    gate, dentro = threading.Event(), threading.Event()
    vero = run._detach_waiting

    def lento(conn):
        dentro.set()
        gate.wait(10.0)
        vero(conn)

    try:
        with mock.patch.object(run, "_detach_waiting", lento):
            scan_all(client)
            assert dentro.wait(10.0)
            scan = status(client)["scan"]
    finally:
        gate.set()
        client.app.state.worker.join(30.0)
    assert (scan["state"], scan["receipt"]) == ("running", None)


def test_a_folder_that_cannot_be_read_does_not_stop_the_others(app, tmp_path):
    """Una cartella su un disco staccato non ferma le altre: si leggono quelle che si possono
    leggere, e quella saltata **si dice**, col suo motivo. Fallire tutto perche' un NAS e'
    spento vorrebbe dire non scansionare piu' niente finche' non lo si riattacca."""
    client, uno, _ = app
    sparita = tmp_path / "sparita"
    sparita.mkdir()
    terza = client.post("/api/v1/folders", json={"root_path": str(sparita)}).json()["id"]
    sparita.rmdir()

    r = scan_all(client)
    assert r.status_code == 202
    assert terza not in {c["folder_id"] for c in r.json()["started"]}
    saltate = {c["folder_id"]: (c["reason"], c["root_path"]) for c in r.json()["skipped"]}
    assert saltate == {terza: ("root_unreachable", str(sparita))}, (
        "la cartella saltata porta il suo percorso: e' cio' che l'utente riconosce"
    )
    assert uno in {c["folder_id"] for c in r.json()["started"]}


def test_with_nothing_to_read_it_says_so_instead_of_starting(db_path):
    """A mani vuote -- nessuna cartella indicata -- il pulsante non finge una corsa: risponde
    che non c'e' niente da leggere. Una corsa a vuoto lascerebbe una ricevuta che racconta
    zero file e un utente convinto di aver scansionato qualcosa."""
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        r = client.post("/api/v1/scan")
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "no_folders"
        assert client.get("/api/v1/scan-runs").json()["items"] == []


def test_a_stop_does_not_leave_receipts_open_forever(app):
    """Una corsa fermata a meta' non lascia dietro ricevute di cartelle che nessuno ha letto.

    Le righe si aprono tutte subito (la risposta le deve gia' portare), ma se lo Stop arriva
    alla prima cartella la seconda non verra' mai letta: senza buttarla, `GET /scan-runs`
    mostrerebbe per sempre una corsa "mai finita" su una cartella intatta, e ogni gesto ne
    aggiungerebbe un'altra.

    Lo Stop si chiede **da dentro la prima cartella**, non subito dopo il 202: chiesto da fuori
    puo' arrivare a lettura gia' finita, e allora la prova resterebbe verde anche cancellando
    la riparazione -- una guardia che non morde."""
    client, uno, due = app
    with _stops_while_reading(client, uno):
        scan_all(client)
        client.app.state.worker.join(30.0)

    assert client.get("/api/v1/pipeline/status").json()["worker"]["state"] == "stopped"
    with connect(client.app.state.db_path) as conn:
        righe = {r[0]: r[1] for r in conn.execute("SELECT folder_id, status FROM scan_runs")}
    assert righe.get(uno) == "stopped", "la cartella letta a meta' racconta di essere stata fermata"
    assert due not in righe, "ricevuta orfana su una cartella che nessuno ha letto"


def test_resume_after_a_stop_reads_the_files_that_were_left(app):
    """**Riprendi deve riprendere davvero.** Gli stadi si chiedono per residuo, ma un file mai
    letto non lascia niente in coda: senza una riga apposta, Riprendi riportava il worker a
    "completato" **senza leggere niente**, e chi aveva fermato a meta' restava con l'archivio
    incompleto e la parola "fatto" a schermo. Misurato prima della riparazione: 7 frame su 9
    fuori, e nessuna traccia.

    E' il difetto peggiore di tutta la fetta, perche' l'app **dice** una parola e ne fa un'altra:
    trovato eseguendo, non leggendo."""
    client, uno, due = app
    with _stops_while_reading(client, uno):
        scan_all(client)
        client.app.state.worker.join(30.0)
    assert client.get("/api/v1/pipeline/status").json()["action"] == "resume"

    client.post("/api/v1/pipeline/run")
    client.app.state.worker.join(30.0)
    per_cartella = _frames_per_folder(client)
    assert per_cartella == {uno: 3, due: 2}, "Riprendi ha detto fatto senza leggere i file rimasti"


def _stops_while_reading(client, folder_id):
    """`run.scan_folder` che preme Stop appena ha letto un file di `folder_id`: da dentro la
    lettura, perche' chiesto da fuori lo Stop puo' arrivare a lettura gia' finita."""
    vero = run.scan_folder

    def ferma_appena_legge(conn, fid, *a, **k):
        for evento in vero(conn, fid, *a, **k):
            yield evento
            if fid == folder_id and not evento.get("done"):
                client.post("/api/v1/pipeline/stop")

    return mock.patch.object(run, "scan_folder", ferma_appena_legge)


def _holding(stage):
    """Sostituisce `stage` di `run` con uno che aspetta la porta: si guarda o si ferma la corsa
    mentre aspetta. Torna la sostituzione, la porta e l'elenco che dice se e' cominciato."""
    porta, visto = threading.Event(), []
    vero = getattr(run, stage)

    def lenta(conn):
        visto.append(1)
        porta.wait(10.0)
        yield from vero(conn)

    return mock.patch.object(run, stage, lenta), porta, visto


def _frames_per_folder(client):
    with connect(client.app.state.db_path) as conn:
        return dict(
            conn.execute(
                "SELECT p.folder_id, COUNT(DISTINCT f.id) FROM frames f"
                " JOIN positions p ON p.frame_id = f.id GROUP BY p.folder_id"
            )
        )


def test_resume_reads_even_when_the_stop_came_before_the_first_folder(app):
    """Fermata prima di cominciare la prima cartella, la lettura non lascia nessuna ricevuta
    `stopped` -- quelle mai iniziate si buttano -- ma e' ferma lo stesso: Riprendi rilegge,
    invece di restare su Riprendi senza fare niente."""
    client, uno, due = app
    worker = client.app.state.worker
    # lo Stop arriva fra l'avvio e il primo passo: `start` azzera uno Stop premuto prima
    worker._stop_requested = lambda: True
    try:
        scan_all(client)
        worker.join(30.0)
    finally:
        del worker._stop_requested
    assert status(client)["action"] == "resume"
    assert _frames_per_folder(client) == {}

    client.post("/api/v1/pipeline/run")
    worker.join(30.0)
    assert _frames_per_folder(client) == {uno: 3, due: 2}


def test_every_folder_stays_locked_until_the_whole_run_ends(app):
    """I lock si rilasciano a fine CORSA, non a fine lettura: mentre la catena lavora su quei
    frame, chiedere di nuovo il gesto sente "gia' in corso" su **tutte** le cartelle.

    Rilasciarli a fine lettura sembrerebbe funzionare -- la lettura e' finita davvero -- ma
    lascerebbe passare una seconda corsa sopra frame che la prima sta ancora normalizzando."""
    client, uno, due = app
    blocco, porta, visto = _holding("normalize_frames")
    with blocco:
        scan_all(client)
        assert wait_until(lambda: visto != [])
        assert client.app.state.folder_locks == {uno, due}, "lock lasciati a fine lettura"
        r = client.post("/api/v1/scan")
        assert r.status_code == 409 and r.json()["detail"]["code"] == "no_readable_folders"
        porta.set()
        client.app.state.worker.join(30.0)
    assert client.app.state.folder_locks == set(), "lock mai rilasciati"


def test_resume_does_not_re_read_when_the_reading_had_finished(app):
    """Riprendi rilegge le cartelle **solo** se l'ultima lettura non era arrivata in fondo. Finita
    quella, e fermato il lavoro a valle -- la normalizzazione chiesta da Da confermare, il cielo --
    rileggere i file sarebbe una passata su tutto l'archivio che nessuno ha chiesto, e sul NAS si
    sente."""
    client, _, _ = app
    scan_all(client)
    client.app.state.worker.join(30.0)
    prima = len(client.get("/api/v1/scan-runs").json()["items"])

    blocco, porta, visto = _holding("identify_frames")
    with blocco:
        client.post("/api/v1/review/apply", json={})  # rimette in coda il lavoro a valle
        client.post("/api/v1/pipeline/run")
        assert wait_until(lambda: visto != [])
        client.post("/api/v1/pipeline/stop")
        porta.set()
        client.app.state.worker.join(30.0)

    client.post("/api/v1/pipeline/run")
    client.app.state.worker.join(30.0)
    assert len(client.get("/api/v1/scan-runs").json()["items"]) == prima, (
        "Riprendi ha riletto le cartelle per un lavoro che non era una lettura"
    )


def test_resume_after_a_stop_in_the_same_run_after_the_reading_does_not_re_read(app):
    """La lettura e' finita e lo Stop colpisce la normalizzazione della stessa corsa: le ricevute
    sono tutte chiuse bene, e Riprendi fa girare il resto senza rileggere le cartelle."""
    client, _, _ = app
    blocco, porta, visto = _holding("normalize_frames")
    with blocco:
        scan_all(client)
        assert wait_until(lambda: visto != [])
        client.post("/api/v1/pipeline/stop")
        porta.set()
        client.app.state.worker.join(30.0)
    prima = len(client.get("/api/v1/scan-runs").json()["items"])
    client.post("/api/v1/pipeline/run")
    client.app.state.worker.join(30.0)
    assert len(client.get("/api/v1/scan-runs").json()["items"]) == prima


def test_resume_reads_a_stopped_reading_even_after_another_stopped_job(app):
    """Una lettura fermata a meta', poi un altro lavoro fermato anche lui (quello che rimette in
    coda Da confermare): Riprendi torna sulle cartelle che la lettura non aveva finito."""
    client, uno, due = app
    with _stops_while_reading(client, uno):
        scan_all(client)
        client.app.state.worker.join(30.0)
    porta = threading.Event()

    def un_altro_lavoro():
        porta.wait(10.0)
        yield {"current": 1, "total": 1}
        yield {"done": True, "total": 1}

    worker = client.app.state.worker
    worker.start([Stage("normalize", un_altro_lavoro)])
    worker.stop()
    porta.set()
    worker.join(10.0)
    assert status(client)["action"] == "resume"
    client.post("/api/v1/pipeline/run")
    client.app.state.worker.join(30.0)
    assert _frames_per_folder(client) == {uno: 3, due: 2}


def test_resume_without_any_scan_behind_does_not_look_for_one(db_path, tmp_path):
    """Riprendi dopo uno Stop **senza che ci sia mai stata una scansione**: il lavoro a valle
    puo' essere fermato anche da solo (lo rimette in coda una risposta in Da confermare), e li'
    non c'e' nessuna corsa a cui tornare. Senza la guardia si andrebbe a cercare la ricevuta di
    una scansione che non esiste, e Riprendi risponderebbe con un guasto."""
    with TestClient(create_app(db_path), base_url="http://localhost") as client:
        with connect(db_path) as conn:
            frame_id = conn.execute(
                "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
                " VALUES('a-mano', 'light', '[]', '2026-09-16T00:00:00Z')"
            ).lastrowid
            mark_pending(conn, frame_id, "2026-09-16T00:00:00Z")

        blocco, porta, visto = _holding("normalize_frames")
        with blocco:
            client.post("/api/v1/pipeline/run")
            assert wait_until(lambda: visto != [])
            client.post("/api/v1/pipeline/stop")
            porta.set()
            client.app.state.worker.join(30.0)

        r = client.post("/api/v1/pipeline/run")
        assert r.status_code == 200, r.text
        assert client.get("/api/v1/scan-runs").json()["items"] == [], (
            "ha cercato una scansione da riprendere che non c'e' mai stata"
        )


def test_a_folder_already_being_read_is_skipped_and_said(app):
    """Se una cartella e' gia' sotto le mani di un'altra corsa non si legge due volte, e il
    perche' si dice: e' il secondo motivo che il contratto dichiara, accanto al disco staccato."""
    client, uno, due = app
    with client.app.state.folder_locks_mutex:
        client.app.state.folder_locks.add(uno)
    try:
        r = scan_all(client)
        assert {c["folder_id"] for c in r.json()["started"]} == {due}
        saltata = r.json()["skipped"]
        assert [(s["folder_id"], s["reason"]) for s in saltata] == [(uno, "scan_running")]
        assert saltata[0]["root_path"]
    finally:
        client.app.state.worker.join(30.0)
        with client.app.state.folder_locks_mutex:
            client.app.state.folder_locks.discard(uno)


def test_when_no_folder_can_be_read_it_says_which_ones(app, tmp_path):
    """Se **nessuna** cartella si riesce a leggere non si avvia niente, e la risposta porta
    l'elenco di quelle saltate: "non ho potuto" con le ragioni, invece di una corsa a vuoto."""
    client, uno, due = app
    for nome in ("prima", "seconda"):
        for f in (tmp_path / nome).iterdir():
            f.unlink()
        (tmp_path / nome).rmdir()

    r = client.post("/api/v1/scan")
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "no_readable_folders"
    assert {s["folder_id"] for s in detail["skipped"]} == {uno, due}
    with connect(client.app.state.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] == 0


def test_a_busy_worker_leaves_no_folder_locked(app):
    """Il worker occupato rifiuta il gesto, e non deve lasciare **niente** dietro: una cartella
    chiusa a chiave da una corsa mai partita non si riaprirebbe fino al riavvio dell'app, e le
    ricevute aperte racconterebbero corse che non esistono."""
    client, _, _ = app
    with mock.patch.object(client.app.state.worker, "start", side_effect=WorkerBusyError("gia")):
        r = client.post("/api/v1/scan")
    assert r.status_code == 409 and r.json()["detail"]["code"] == "worker_busy"
    with client.app.state.folder_locks_mutex:
        assert client.app.state.folder_locks == set(), "cartelle chiuse a chiave per sempre"
    with connect(client.app.state.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] == 0


def test_a_retired_folder_is_not_read(app):
    """Una cartella ritirata resta fuori: ritirarla vuol dire "non guardarla piu'", e i suoi
    frame restano in archivio. Senza questa riga il gesto in barra la riporterebbe dentro."""
    client, uno, due = app
    client.delete(f"/api/v1/folders/{due}")
    r = scan_all(client)
    assert {c["folder_id"] for c in r.json()["started"]} == {uno}
