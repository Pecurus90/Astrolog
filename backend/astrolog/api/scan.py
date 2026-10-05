"""The work lives in the worker, not in the request: the folder lock is taken after the pre-checks
and the worker releases it at the end of the RUN, however it goes."""

import json
import sqlite3
from collections.abc import Container, Iterable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.datastructures import State

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


def _release(state: State, folder_id: int) -> None:
    with state.folder_locks_mutex:
        state.folder_locks.discard(folder_id)


def run_out(row: sqlite3.Row) -> ScanRunOut:
    """Without the unread files: the page polls the receipt every few seconds, and those are read
    in pages."""
    lists = {f"{name}_json": name for name in RECEIPT_LISTS}
    apart = {*lists, "errors_detail_json"}
    return ScanRunOut(
        # iterating a Row yields its values, so keys() is needed
        **{k: row[k] for k in row.keys() if k not in apart},  # noqa: SIM118
        **{name: json.loads(row[column] or "[]") for column, name in lists.items()},
        # derived here: the database keeps the two instants, and the screen only formats
        duration_s=elapsed_s(row["started_at"], row["ended_at"]),
    )


def start_scan(state: State, conn: sqlite3.Connection, folder_id: int) -> int:
    """Pre-checks, folder lock, receipt opened, run started; returns `run_id`. HTTPException
    404/409 when it cannot."""
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
    run_id: int | None = None
    previous = (state.last_scan, state.scan_runs)
    try:
        run_id = start_run(conn, folder_id, now_iso())
        # The folder lock is released at the end of the RUN, not of the stage: normalize still works
        # on those frames after the reading; every stage's `finish` runs however it goes, Stop too.
        steps = queue(state.db_path, ORDER, folder_id=folder_id, run_id=run_id)
        stages: list[Stage] = []
        for i, (name, factory) in enumerate(steps):
            last = i == len(steps) - 1
            release = (lambda: _release(state, folder_id)) if last else None
            stages.append(Stage(name, factory, on_finish=release))
        # before the start, and the receipts before the current one: a poll never sees the old run
        state.scan_runs = (run_id,)
        state.last_scan = (folder_id, run_id)
        state.worker.start(stages)
        return run_id
    except WorkerBusyError as err:
        _release(state, folder_id)
        state.last_scan, state.scan_runs = previous
        if run_id is not None:
            discard_run(conn, run_id)  # the open receipt will never have a run
        raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
    except Exception:
        _release(state, folder_id)
        raise


def _pulisci(
    state: State, conn: sqlite3.Connection, prese: Iterable[int], partite: Iterable[ScanStarted]
) -> None:
    """A run that never started leaves nothing behind: no locked folders (they would not reopen
    until a restart), no open receipts that no run will close."""
    for c in partite:
        discard_run(conn, c.run_id)
    for folder_id in prese:
        _release(state, folder_id)


def _scarta_le_mai_iniziate(
    db_path: str | Path, partite: Iterable[ScanStarted], iniziate: Container[int]
) -> None:
    """Its own connection: this runs in the worker's thread, and the request's connection was
    closed long ago."""
    orfane = [c.run_id for c in partite if c.run_id not in iniziate]
    if not orfane:
        return
    conn = connect(db_path)
    try:
        for run_id in orfane:
            discard_run(conn, run_id)
    finally:
        conn.close()


def start_scan_all(state: State, conn: sqlite3.Connection) -> ScanAllStarted:  # noqa: C901
    """A folder that cannot be read is skipped and reported instead of stopping the others: one NAS
    switched off would otherwise stop every scan. The locks are all taken before the start."""
    ids = [
        r[0] for r in conn.execute("SELECT id FROM folders WHERE retired_at IS NULL ORDER BY id")
    ]
    if not ids:
        raise HTTPException(status_code=409, detail={"code": "no_folders"})
    partite: list[ScanStarted] = []
    saltate: list[FolderSkipped] = []
    prese: list[int] = []
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
        # The reply carries every receipt, so they all open now; those a stopped run never reaches
        # are discarded at its end, or `GET /scan-runs` would show them open forever.
        iniziate: set[int] = set()

        def segui(folder_id: int, run_id: int) -> None:
            iniziate.add(run_id)
            state.last_scan = (folder_id, run_id)

        def a_fine_corsa() -> None:
            for folder_id in prese:
                _release(state, folder_id)
            _scarta_le_mai_iniziate(state.db_path, partite, iniziate)

        steps = queue_folders(state.db_path, coppie, on_folder=segui)
        stages: list[Stage] = []
        for i, (name, factory) in enumerate(steps):
            last = i == len(steps) - 1
            # as for a single folder: the locks are released at the end of the RUN
            stages.append(Stage(name, factory, on_finish=a_fine_corsa if last else None))
        # before the start, and the receipts before the current one: a poll never sees the old run
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
def scan_all(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> ScanAllStarted:
    """Reads all the registered folders that are not retired, in one run, and replies at once;
    the progress is in `GET /pipeline/status`.

    409 `no_folders` when there is none; 409 `no_readable_folders` with the `skipped` folders
    when none can be started; 409 `worker_busy`."""
    return start_scan_all(request.app.state, conn)


@router.post("/folders/{folder_id}/scan", response_model=ScanStarted, status_code=202)
def scan(
    folder_id: int, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> ScanStarted:
    """Starts the scan and replies at once; the progress is in `GET /pipeline/status`.

    404 `folder_not_found`; 409 `folder_retired`, `root_unreachable` with the `path`,
    `scan_running` with the `folder_id`, or `worker_busy`."""
    run_id = start_scan(request.app.state, conn, folder_id)
    return ScanStarted(run_id=run_id, folder_id=folder_id)


@router.get("/scan-runs", response_model=ScanRunList)
def scan_runs(
    folder_id: int | None = None,
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> ScanRunList:
    """The receipts, newest first."""
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
    conn: sqlite3.Connection = Depends(get_db),
) -> ScanErrorList:
    """The files the scan did not read, each with its reason, in pages. The list is kept by the
    last scan of each folder and, if that one did not reach the end, also by the last one that did
    (`spine/scan_store.finish_run`): of the others only the numbers remain, and an open one has no
    list yet; the reply says so with its code instead of an empty list.

    404 `scan_run_not_found`; 409 `scan_run_open`; 410 `errors_not_kept`."""
    row = run_row(conn, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "scan_run_not_found"})
    if row["ended_at"] is None:
        raise HTTPException(status_code=409, detail={"code": "scan_run_open"})
    if row["errors"] and row["errors_detail_json"] is None:
        raise HTTPException(status_code=410, detail={"code": "errors_not_kept"})
    items = json.loads(row["errors_detail_json"] or "[]")
    return ScanErrorList(**page_of(items, limit, offset))
