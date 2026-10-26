"""The only progress channel, the same for every device. The scan's remainder cannot be derived
from the database: its denominator is the folders on disk."""

import json
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import State

from ..clock import parse_iso
from ..db.row import Row
from ..spine.run import ORDER, queue
from ..spine.scan_store import run_outcomes, run_row
from ..spine.stages import StageName, count_pending, pending_by_stage
from ..worker.worker import TERMINAL_STATES, Snapshot, WorkerBusyError
from ..worker.worker import State as WorkerState
from . import work
from .deps import get_db
from .models import (
    PipelineAction,
    PipelineStatus,
    ScanEvent,
    ScanProgress,
    StageState,
    WorkerOut,
    WorkerSnapshot,
)
from .scan import run_out, start_scan_all

router = APIRouter(prefix="/api/v1", tags=["pipeline"])


def _shown(snapshot: Snapshot) -> WorkerSnapshot:
    return WorkerSnapshot.model_validate(asdict(snapshot))


def action_for(snapshot: Snapshot) -> PipelineAction:
    """`resume` after a Stop, because the work is still there."""
    if snapshot.state == WorkerState.RUNNING:
        return "stop"
    if snapshot.state == WorkerState.STOPPED:
        return "resume"
    return "start"


# Worst first: several folders read together end like their worst one, and a lost folder is not
# covered by one read well after it.
_SEVERITY = (
    WorkerState.ERROR,
    WorkerState.STOPPED,
    WorkerState.COMPLETED_WITH_ERRORS,
    WorkerState.COMPLETED,
)
_STATE_OF = {
    "ok": WorkerState.COMPLETED,
    "stopped": WorkerState.STOPPED,
    "aborted": WorkerState.ERROR,
    "error": WorkerState.ERROR,
}


def _state_of(rows: Iterable[Row]) -> WorkerState:
    def of_row(row: Row) -> WorkerState:
        if row["status"] == "ok" and row["errors"]:
            return WorkerState.COMPLETED_WITH_ERRORS
        return _STATE_OF.get(row["status"], WorkerState.COMPLETED)

    states = {of_row(r) for r in rows}
    return next(s for s in _SEVERITY if s in states)


# The pace of the first files is not the real one yet. [P docs/domini/navigazione.md]
ETA_AFTER_S = 60


def remaining_s(current: int, total: int, elapsed_s: float) -> int | None:
    """What is left at the pace so far: the files still to read divided by the files read per
    second. `None` in the first minute, before any file, and once all are read."""
    if current <= 0 or current >= total or elapsed_s < ETA_AFTER_S:
        return None
    return round(elapsed_s * (total - current) / current)


# A folder of the gesture never read to the end outside it: a reading stopped or broken does not
# count as one, so Stop then Resume is still the first reading of what was not read.
_NEVER_READ = (
    "SELECT 1 FROM scan_runs AS cur WHERE cur.id IN (SELECT value FROM json_each(:runs))"
    " AND NOT EXISTS (SELECT 1 FROM scan_runs AS prev WHERE prev.folder_id = cur.folder_id"
    " AND prev.status = 'ok' AND prev.id NOT IN (SELECT value FROM json_each(:runs))) LIMIT 1"
)


def is_first_scan(conn: sqlite3.Connection, run_ids: Iterable[int]) -> bool:
    """The gesture reads at least one folder for the first time: its counts are still growing. A
    folder added to a read archive is a first reading too, of that folder."""
    return conn.execute(_NEVER_READ, {"runs": json.dumps(list(run_ids))}).fetchone() is not None


def _remaining(last: Mapping[str, Any] | None) -> int | None:
    """The estimate of the folder being read, from when its reading began: the receipts of a
    gesture all open together, so theirs would count the folders read before."""
    started = parse_iso(last.get("since")) if last is not None else None
    if last is None or started is None:
        return None
    elapsed = (datetime.now(UTC) - started).total_seconds()
    return remaining_s(last["current"], last["total"], elapsed)


def scan_progress(state: State, conn: sqlite3.Connection) -> ScanProgress | None:
    """The outcome is read from the receipts, not the worker: the worker forgets it as soon as it
    does something else."""
    if state.last_scan is None:
        return None
    folder_id, run_id = state.last_scan
    rec = state.worker.stage_record(StageName.SCAN)
    # receipts of folders never started are discarded at the end of the run
    rows = run_outcomes(conn, state.scan_runs)
    closed = bool(rows) and all(r["ended_at"] is not None for r in rows)
    # the last receipt closes before the stage ends (the detach is still running)
    finished = closed and (rec is None or rec.state in TERMINAL_STATES)
    row = run_row(conn, run_id) if finished else None
    last = rec.last_event if rec is not None else None
    stage_state = (
        _state_of(rows) if finished else (rec.state if rec is not None else WorkerState.NOT_RUN)
    )
    return ScanProgress(
        # `StageState` repeats the worker `State` as a `Literal` on purpose (`models_tonight`).
        state=cast(StageState, stage_state),
        folder_id=folder_id,
        run_id=run_id,
        last_event=ScanEvent(**last) if last else None,
        receipt=run_out(row) if row is not None else None,
        remaining_s=None if finished else _remaining(last),
        first=is_first_scan(conn, state.scan_runs),
    )


@router.get("/pipeline/status", response_model=PipelineStatus)
def status(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> PipelineStatus:
    """The worker snapshot, the progress of the last scan started (`null` until one has started),
    how many frames each stage still lacks, and what the button does (`action`).

    Once the scan has finished, however it finished (a Stop included), `state` combines the
    receipts of every folder of the gesture (worst first); while it runs, it is the worker's.
    `receipt`, like `folder_id` and `run_id`, is the last started folder's, present once the scan
    has finished. If it stopped or fell before the first folder, no receipt is left: `receipt` is
    `null` and the state is the worker's (`not_run` when the worker has no record of the scan)."""
    state = request.app.state
    snapshot = state.worker.snapshot()
    return PipelineStatus(
        worker=_shown(snapshot),
        scan=scan_progress(state, conn),
        # the stages that run: one in the graph without work would stay "to do" for ever
        pending=pending_by_stage(conn, [s for s in ORDER if s != StageName.SCAN]),
        action=action_for(snapshot),
    )


def _reading_cut_short(conn: sqlite3.Connection, state: State) -> bool:
    """True when, with the worker stopped, the last read did not end (a receipt `stopped` or open,
    or none). Asked of the receipts: after another stopped job the worker no longer knows."""
    if state.last_scan is None or state.worker.snapshot().state != WorkerState.STOPPED:
        return False
    rows = run_outcomes(conn, state.scan_runs)
    return not rows or any(r["status"] == "stopped" or r["ended_at"] is None for r in rows)


@router.post("/pipeline/stop", response_model=WorkerOut)
def stop(request: Request) -> WorkerOut:
    """Asks for the Stop and returns the worker snapshot. Cooperative: the worker stops within the
    item in progress, with the transaction closed. Always 200, even with nothing running. The new
    pipeline behind the scenes stops too: its ASTAP killed."""
    snapshot = request.app.state.worker.stop()  # first: a scan ending now kicks nothing after
    request.app.state.behind.stop()
    return WorkerOut(worker=_shown(snapshot))


@router.post("/pipeline/run", response_model=WorkerOut)
def run(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> WorkerOut:
    """Starts the waiting work: the normalisation of frames left behind, the sky of frames still
    to solve, the object of those without one, and the nights of those waiting for a session.
    Returns the worker snapshot.

    It is the page's "Start"/"Resume" button: without this route the work requeued by an answer
    in To confirm would wait for the next scan, and frames waiting for ASTAP would never start.

    **If the last read did not reach the end, Resume reads the folders again.** Stages are asked
    for by remainder here, and `scan` is not a frame stage: a file never read leaves nothing in the
    queue, so otherwise Resume would bring the worker to `completed` without reading anything.

    With nothing to do it starts nothing and returns the snapshot as it is, even mid-run, so the
    NAS cadence does not skip a round.

    409 `worker_busy` if there is work to start while a job is already running. When Resume
    reads the folders again it answers with the `skipped` ones, like `POST /scan`, and with its
    409s: `no_folders` if no active folder is left, `no_readable_folders` (or `worker_busy` when
    some are already being read) with the `skipped` folders when none can be started."""
    state = request.app.state
    if _reading_cut_short(conn, state):
        started = start_scan_all(state, conn)
        return WorkerOut(worker=_shown(state.worker.snapshot()), skipped=started.skipped)
    # Only what has a remainder: the order and who pulls whom is `queue`'s.
    steps = queue(
        state.db_path,
        [s for s in ORDER if s != StageName.SCAN and count_pending(conn, s)],
    )
    if not steps:
        return WorkerOut(worker=_shown(state.worker.snapshot()))
    try:
        snapshot = work.start(state, steps)
    except WorkerBusyError as err:
        raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
    return WorkerOut(worker=_shown(snapshot))
