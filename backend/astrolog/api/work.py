"""**Il lavoro in corso, visto da una rotta che scrive**: le due meta' dello stesso fatto.

Prima di scrivere, **un lavoro alla volta**: col worker in corsa si rifiuta, perche' meglio
dirlo che lasciare l'archivio a meta'. Dopo aver scritto, invece, **il worker occupato non e'
un errore**: le pose sono gia' segnate da rilavorare nel database, quindi le raccoglie la corsa
in corso o il prossimo *Avvia*, e fallire li' direbbe a chi ha risposto che la sua risposta e'
andata persa. Due risposte opposte alla stessa domanda, e la differenza e' **quando** si chiede.
"""

import logging

from fastapi import HTTPException

from ..spine.run import queue
from ..worker.states import Stage
from ..worker.worker import WorkerBusyError

log = logging.getLogger(__name__)


def busy(state):
    """Rifiuta se il worker sta gia' lavorando. Si chiama **prima** di aprire la transazione."""
    if state.worker.is_running():
        raise HTTPException(status_code=409, detail={"code": "worker_busy"})


def after(state, stages):
    """Avvia gli stadi che quella risposta tocca. Torna se la corsa e' partita."""
    try:
        state.worker.start([Stage(n, f) for n, f in queue(state.db_path, stages)])
    except WorkerBusyError:
        log.info("il worker e' occupato: il lavoro resta in coda")
        return False
    return True
