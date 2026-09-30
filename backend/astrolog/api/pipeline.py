"""Lo stato della spina in una chiamata: il worker, l'ultimo evento e la ricevuta della
scansione, il residuo per stadio, il verbo del pulsante; e lo Stop.

Vincolo non ovvio: e' l'unico canale di avanzamento (1-3 s mentre gira, 60 s da fermo, zero
a scheda nascosta), uguale per desktop, altra scheda e telefono. La ricevuta viene dal DB,
comunque la corsa sia finita (anche su Stop, dove il generatore non arriva a emetterla). Il
residuo della scansione non e' derivabile dal DB (il denominatore vive sul filesystem):
riprendere e' ri-scansionare. Lo Stop e' cooperativo e risponde sempre 200.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from ..spine.run import ORDER, STAGE_SCAN, queue
from ..spine.scan_store import run_outcomes, run_row
from ..spine.stages import count_pending, pending_by_stage
from ..worker.states import (
    COMPLETED,
    COMPLETED_WITH_ERRORS,
    ERROR,
    RUNNING,
    STOPPED,
    TERMINAL_STATES,
    Stage,
)
from ..worker.worker import WorkerBusyError
from .deps import get_db
from .models import PipelineStatus, ScanEvent, ScanProgress, StageState, WorkerOut
from .scan import run_out, start_scan_all

router = APIRouter(prefix="/api/v1", tags=["spina"])


def action_for(snapshot):
    """Il verbo del pulsante: `stop` mentre gira, `resume` dopo uno Stop (il lavoro resta),
    `start` altrimenti. Deciso qui, cosi' la pagina lo mostra e basta."""
    if snapshot["state"] == RUNNING:
        return "stop"
    if snapshot["state"] == STOPPED:
        return "resume"
    return "start"


# L'esito scritto nelle ricevute, tradotto negli stati del worker, dal piu' grave: una lettura di
# piu' cartelle e' com'e' andata la sua cartella peggiore, e una cartella persa non si copre con
# una letta bene dopo di lei.
_SEVERITY: tuple[StageState, ...] = (ERROR, STOPPED, COMPLETED_WITH_ERRORS, COMPLETED)
_STATE_OF: dict[str, StageState] = {
    "ok": COMPLETED,
    "stopped": STOPPED,
    "aborted": ERROR,
    "error": ERROR,
}


def _state_of(rows) -> StageState:
    def of_row(row) -> StageState:
        if row["status"] == "ok" and row["errors"]:
            return COMPLETED_WITH_ERRORS
        return _STATE_OF.get(row["status"], COMPLETED)

    states = {of_row(r) for r in rows}
    return next(s for s in _SEVERITY if s in states)


def scan_progress(state, conn):
    """L'ultima scansione avviata: l'evento in corso dal worker, l'esito dalle ricevute.

    **Finita, l'esito lo dicono le ricevute di tutte le cartelle del gesto**, non il worker: il
    worker smette di saperlo appena fa ALTRO (una normalizzazione chiesta da Da confermare), e
    l'ultima cartella da sola coprirebbe una persa prima di lei. Mentre gira, lo stato e' del
    worker. La ricevuta che accompagna e' quella dell'ultima cartella."""
    if state.last_scan is None:
        return None
    folder_id, run_id = state.last_scan
    rec = state.worker.stage_record(STAGE_SCAN)
    # quelle delle cartelle mai cominciate si buttano a fine corsa, e non tornano
    rows = run_outcomes(conn, state.scan_runs)
    # senza ricevute (fermata o caduta prima della prima cartella) resta il worker
    closed = bool(rows) and all(r["ended_at"] is not None for r in rows)
    # l'ultima ricevuta si chiude prima della fine dello stadio (lo stacco gira ancora)
    finished = closed and (rec is None or rec["state"] in TERMINAL_STATES)
    row = run_row(conn, run_id) if finished else None
    last = rec["last_event"] if rec is not None else None
    return ScanProgress(
        state=_state_of(rows) if finished else (rec["state"] if rec is not None else "not_run"),
        folder_id=folder_id,
        run_id=run_id,
        last_event=ScanEvent(**last) if last else None,
        receipt=run_out(row) if row is not None else None,
    )


@router.get("/pipeline/status", response_model=PipelineStatus)
def status(request: Request, conn=Depends(get_db)):
    """Lo snapshot del worker, l'avanzamento della scansione, quanti frame mancano a ogni
    stadio, e cosa fa il pulsante."""
    state = request.app.state
    snapshot = state.worker.snapshot()
    return PipelineStatus(
        worker=snapshot,
        scan=scan_progress(state, conn),
        pending=pending_by_stage(conn),
        action=action_for(snapshot),
    )


def _scansione_interrotta(conn, state):
    """Se, a worker fermo, l'ultima lettura non e' arrivata in fondo: una sua ricevuta e'
    `stopped` o ancora aperta, o non ne resta nessuna. Lo dicono le ricevute di tutto il gesto, e
    non il worker: fermato dopo la lettura anche un altro lavoro, il worker non sa piu' che una
    lettura era rimasta a meta'."""
    if state.last_scan is None or state.worker.snapshot()["state"] != STOPPED:
        return False
    rows = run_outcomes(conn, state.scan_runs)
    return not rows or any(r["status"] == "stopped" or r["ended_at"] is None for r in rows)


@router.post("/pipeline/stop", response_model=WorkerOut)
def stop(request: Request):
    """Chiede lo Stop: il worker si ferma entro l'elemento in corso, a transazione chiusa."""
    return WorkerOut(worker=request.app.state.worker.stop())


@router.post("/pipeline/run", response_model=WorkerOut)
def run(request: Request, conn=Depends(get_db)):
    """Avvia il lavoro che aspetta: la normalizzazione dei frame rimasti indietro, il cielo
    delle pose ancora da risolvere, l'oggetto di quelle che non ce l'hanno e le notti di quelle
    che aspettano una sessione.

    E' il pulsante "Avvia"/"Riprendi" della pagina: senza questa rotta il lavoro rimesso in
    coda da una risposta in Da confermare aspetterebbe la prossima scansione, e le pose che
    aspettavano ASTAP non partirebbero mai.

    **Se l'ultima lettura non era arrivata in fondo, Riprendi rilegge le cartelle.** Qui gli
    stadi si chiedono per residuo, e `scan` non e' uno stadio della posa: un file mai letto non
    lascia niente in coda, quindi senza questa riga "Riprendi" riportava il worker a `completed`
    **senza leggere niente**, e chi aveva fermato a meta' restava con l'archivio incompleto e la
    parola "fatto" a schermo. Misurato: 7 frame su 9 fuori, e nessuna traccia (16/9/2026)."""
    state = request.app.state
    if _scansione_interrotta(conn, state):
        start_scan_all(state, conn)
        return WorkerOut(worker=state.worker.snapshot())
    # Cosa ha ancora residuo, e basta: in che ordine vada, e chi tira dietro chi, lo sa `queue`.
    # `scan` non e' uno stadio della posa -- lo chiede solo chi scansiona una cartella.
    da_fare = queue(
        state.db_path,
        [s for s in ORDER if s != STAGE_SCAN and count_pending(conn, s)],
    )
    if not da_fare:
        # niente da fare: occupare il worker farebbe saltare un giro alla cadenza del NAS
        return WorkerOut(worker=state.worker.snapshot())
    try:
        snapshot = state.worker.start([Stage(n, f) for n, f in da_fare])
    except WorkerBusyError as err:
        raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
    return WorkerOut(worker=snapshot)
