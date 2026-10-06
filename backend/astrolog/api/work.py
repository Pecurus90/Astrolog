"""Before writing, a busy worker is refused so the archive is not left half done; after writing it
is not an error: the frames are queued in the database for the running job or the next Start."""

import logging
from collections.abc import Iterable

from fastapi import HTTPException
from starlette.datastructures import State

from ..spine.run import queue
from ..spine.stage_run import Factory
from ..spine.stages import StageName
from ..worker.worker import Snapshot, Stage, WorkerBusyError

log = logging.getLogger(__name__)


def busy(state: State) -> None:
    """Called before opening the transaction."""
    if state.worker.is_running():
        raise HTTPException(status_code=409, detail={"code": "worker_busy"})


def start(state: State, steps: Iterable[tuple[StageName, Factory]]) -> Snapshot:
    """Raises `WorkerBusyError` while a job runs."""
    return state.worker.start([Stage(n, f) for n, f in steps])


def after(state: State, stages: Iterable[StageName]) -> bool:
    """True if the run started."""
    try:
        start(state, queue(state.db_path, stages))
    except WorkerBusyError:
        log.info("il worker e' occupato: il lavoro resta in coda")
        return False
    return True
