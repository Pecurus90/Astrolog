"""Avvia la scansione di una cartella come lavoro di sottofondo (risponde subito con l'id
della ricevuta) e le ricevute delle scansioni passate. L'avanzamento si legge in
`GET /pipeline/status`: un canale solo, per il desktop e per il telefono.

Vincolo non ovvio: il lavoro vive nel worker, non nella richiesta; il lock per cartella si
prende dopo i pre-controlli e lo rilascia il worker a fine CORSA, comunque vada.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..clock import elapsed_s, now_iso
from ..db.connect import connect
from ..spine.run import ORDER, queue, queue_folders
from ..spine.scan import root_readable
from ..spine.scan_store import (
    RECEIPT_LISTS,
    SELECT_RUN,
    FolderNotFoundError,
    discard_run,
    folder_root,
    run_row,
    start_run,
)
from ..worker.states import Stage
from ..worker.worker import WorkerBusyError
from .deps import get_db
from .models import (
    FolderSkipped,
    ScanAllStarted,
    ScanErrorList,
    ScanRunList,
    ScanRunOut,
    ScanStarted,
)
from .models_page import page_of

router = APIRouter(prefix="/api/v1", tags=["scansione"])


def _release(state, folder_id):
    with state.folder_locks_mutex:
        state.folder_locks.discard(folder_id)


def run_out(row):
    """La ricevuta di `scan_runs` nella forma dell'API, una volta sola. Senza i file non letti:
    la pagina la interroga ogni pochi secondi, e quelli si leggono a pagine."""
    lists = {f"{name}_json": name for name in RECEIPT_LISTS}
    apart = {*lists, "errors_detail_json"}
    return ScanRunOut(
        **{k: row[k] for k in row.keys() if k not in apart},  # noqa: SIM118 - Row itera i valori
        **{name: json.loads(row[column] or "[]") for column, name in lists.items()},
        # La durata si **deriva** qui: il database tiene i due istanti, e farla a schermo
        # andrebbe contro la regola che il backend manda cio' che lo schermo mostra.
        duration_s=elapsed_s(row["started_at"], row["ended_at"]),
    )


def start_scan(state, conn, folder_id):
    """Pre-controlli, lock della cartella, ricevuta aperta, corsa avviata. Torna `run_id`.
    HTTPException 404/409 quando non si puo'."""
    try:
        root, retired_at = folder_root(conn, folder_id)
    except FolderNotFoundError as err:
        raise HTTPException(status_code=404, detail={"code": "folder_not_found"}) from err
    if retired_at is not None:
        raise HTTPException(status_code=409, detail={"code": "folder_retired"})
    if not root_readable(root):
        raise HTTPException(status_code=409, detail={"code": "root_unreachable", "path": root})
    with state.folder_locks_mutex:
        if folder_id in state.folder_locks:
            raise HTTPException(
                status_code=409, detail={"code": "scan_running", "folder_id": folder_id}
            )
        state.folder_locks.add(folder_id)
    run_id, previous = None, (state.last_scan, state.scan_runs)
    try:
        run_id = start_run(conn, folder_id, now_iso())
        # Il lock della cartella si rilascia a fine CORSA, non a fine stadio: dopo la lettura
        # dei file la normalizzazione sta ancora lavorando su quei frame. Il worker chiama
        # `finish` di ogni stadio comunque vada, quindi anche uno Stop lo rilascia.
        steps = queue(state.db_path, ORDER, folder_id=folder_id, run_id=run_id)
        stages = []
        for i, (name, factory) in enumerate(steps):
            last = i == len(steps) - 1
            release = (lambda: _release(state, folder_id)) if last else None
            stages.append(Stage(name, factory, on_finish=release))
        # prima dell'avvio, e le ricevute prima della corrente: un poll non vede la corsa vecchia
        state.scan_runs = (run_id,)
        state.last_scan = (folder_id, run_id)
        state.worker.start(stages)
        return run_id
    except WorkerBusyError as err:
        _release(state, folder_id)
        state.last_scan, state.scan_runs = previous
        if run_id is not None:
            discard_run(conn, run_id)  # la ricevuta aperta non avra' mai una corsa
        raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
    except Exception:
        _release(state, folder_id)
        raise


def _pulisci(state, conn, prese, partite):
    """Una corsa che non e' mai partita non lascia niente dietro: ne' cartelle chiuse a chiave
    (non si riaprirebbero fino al riavvio), ne' ricevute aperte che nessuna corsa chiudera'."""
    for c in partite:
        discard_run(conn, c.run_id)
    for folder_id in prese:
        _release(state, folder_id)


def _scarta_le_mai_iniziate(db_path, partite, iniziate):
    """Le ricevute delle cartelle che la corsa non ha fatto in tempo a leggere (uno Stop, un
    guasto). Si apre una connessione propria: qui siamo nel thread del worker, e quella della
    richiesta e' chiusa da un pezzo."""
    orfane = [c.run_id for c in partite if c.run_id not in iniziate]
    if not orfane:
        return
    conn = connect(db_path)
    try:
        for run_id in orfane:
            discard_run(conn, run_id)
    finally:
        conn.close()


def start_scan_all(state, conn):  # noqa: C901
    """Legge **tutte** le cartelle attive in una corsa sola. Torna cosa e' partito e cosa no.

    Le cartelle si prendono qui e non le sceglie chi chiama: il pulsante in barra non chiede
    quale, e "tutte" vuol dire quelle non ritirate. Una che non si puo' leggere -- un disco
    staccato, un NAS spento -- **non ferma le altre**: si salta e si dice, perche' altrimenti
    basterebbe un NAS spento per non scansionare piu' niente.

    I lock si prendono tutti **prima** di avviare, e se il worker e' occupato si rilasciano
    tutti: una cartella lasciata chiusa a chiave da una corsa che non e' mai partita non si
    riaprirebbe piu' fino al riavvio."""
    ids = [
        r[0] for r in conn.execute("SELECT id FROM folders WHERE retired_at IS NULL ORDER BY id")
    ]
    if not ids:
        raise HTTPException(status_code=409, detail={"code": "no_folders"})
    partite, saltate, prese = [], [], []
    for folder_id in ids:
        root, _ = folder_root(conn, folder_id)
        if not root_readable(root):
            saltate.append(
                FolderSkipped(folder_id=folder_id, root_path=root, reason="root_unreachable")
            )
            continue
        with state.folder_locks_mutex:
            if folder_id in state.folder_locks:
                saltate.append(
                    FolderSkipped(folder_id=folder_id, root_path=root, reason="scan_running")
                )
                continue
            state.folder_locks.add(folder_id)
        prese.append(folder_id)
    if not prese:
        raise HTTPException(
            status_code=409,
            detail={"code": "no_readable_folders", "skipped": [s.model_dump() for s in saltate]},
        )
    previous = (state.last_scan, state.scan_runs)
    try:
        for folder_id in prese:
            run_id = start_run(conn, folder_id, now_iso())
            partite.append(ScanStarted(run_id=run_id, folder_id=folder_id))
        coppie = [(c.folder_id, c.run_id) for c in partite]
        # Le ricevute si aprono tutte SUBITO, perche' la risposta le deve gia' portare; ma una
        # corsa fermata a meta' non arrivera' mai alle ultime cartelle, e le loro righe
        # resterebbero aperte per sempre -- `GET /scan-runs` le mostrerebbe come corse mai
        # finite, su cartelle che nessuno ha letto. Si tiene il conto di quelle davvero
        # iniziate, e a fine corsa le altre si buttano.
        iniziate = set()

        def segui(folder_id, run_id):
            iniziate.add(run_id)
            state.last_scan = (folder_id, run_id)

        def a_fine_corsa():
            for folder_id in prese:
                _release(state, folder_id)
            _scarta_le_mai_iniziate(state.db_path, partite, iniziate)

        steps = queue_folders(state.db_path, coppie, on_folder=segui)
        stages = []
        for i, (name, factory) in enumerate(steps):
            last = i == len(steps) - 1
            # Come per una cartella sola: i lock si rilasciano a fine CORSA, non a fine stadio
            # -- dopo la lettura dei file la catena sta ancora lavorando su quei frame.
            stages.append(Stage(name, factory, on_finish=a_fine_corsa if last else None))
        # prima dell'avvio, e le ricevute prima della corrente: un poll non vede la corsa vecchia
        state.scan_runs = tuple(run_id for _, run_id in coppie)
        state.last_scan = coppie[0]
        state.worker.start(stages)
        return ScanAllStarted(started=partite, skipped=saltate)
    except WorkerBusyError as err:
        _pulisci(state, conn, prese, partite)
        state.last_scan, state.scan_runs = previous
        raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
    except Exception:
        _pulisci(state, conn, prese, partite)
        state.last_scan, state.scan_runs = previous
        raise


@router.post("/scan", response_model=ScanAllStarted, status_code=202)
def scan_all(request: Request, conn=Depends(get_db)):
    """Legge tutte le cartelle indicate; l'avanzamento sta in `GET /pipeline/status`."""
    return start_scan_all(request.app.state, conn)


@router.post("/folders/{folder_id}/scan", response_model=ScanStarted, status_code=202)
def scan(folder_id: int, request: Request, conn=Depends(get_db)):
    """Avvia la scansione e risponde subito; l'avanzamento sta in `GET /pipeline/status`."""
    run_id = start_scan(request.app.state, conn, folder_id)
    return ScanStarted(run_id=run_id, folder_id=folder_id)


@router.get("/scan-runs", response_model=ScanRunList)
def scan_runs(
    folder_id: int | None = None,
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db),
):
    """Le ricevute, dalla piu' recente."""
    if folder_id is None:
        total = conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0]
        rows = conn.execute(
            SELECT_RUN + " ORDER BY r.id DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
    else:
        total = conn.execute(
            "SELECT COUNT(*) FROM scan_runs WHERE folder_id = ?", (folder_id,)
        ).fetchone()[0]
        rows = conn.execute(
            SELECT_RUN + " WHERE r.folder_id = ? ORDER BY r.id DESC LIMIT ? OFFSET ?",
            (folder_id, limit, offset),
        ).fetchall()
    return ScanRunList(items=[run_out(r) for r in rows], total=total, limit=limit, offset=offset)


@router.get("/scan-runs/{run_id}/errors", response_model=ScanErrorList)
def scan_run_errors(
    run_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db),
):
    """I file che la scansione non ha letto, ognuno col suo motivo, a pagine. L'elenco lo tiene
    l'ultima scansione di ogni cartella, e se non e' arrivata in fondo anche l'ultima che ci e'
    arrivata (`spine/scan_store.finish_run`): delle altre restano i numeri, e di una ancora aperta
    non c'e' ancora; la risposta lo dice col suo codice invece di un elenco vuoto."""
    row = run_row(conn, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "scan_run_not_found"})
    if row["ended_at"] is None:
        raise HTTPException(status_code=409, detail={"code": "scan_run_open"})
    if row["errors"] and row["errors_detail_json"] is None:
        raise HTTPException(status_code=410, detail={"code": "errors_not_kept"})
    items = json.loads(row["errors_detail_json"] or "[]")
    return ScanErrorList(**page_of(items, limit, offset))
