"""The work lives in the worker, not in the request: the folder lock is taken after the pre-checks
and the worker releases it at the end of the RUN, however it goes."""

import json
import sqlite3
from collections.abc import Container, Iterable, Sequence
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
from ..spine.stage_run import Factory
from ..worker.worker import Stage, WorkerBusyError
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

router = APIRouter(prefix="/api/v1", tags=["scan"])


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
        _launch(state, [(folder_id, run_id)], _one_folder_stages(state, folder_id, run_id))
        return run_id
    except Exception as err:
        # whatever broke the start, the open receipt will never have a run
        _release(state, folder_id)
        state.last_scan, state.scan_runs = previous
        if run_id is not None:
            discard_run(conn, run_id)
        if isinstance(err, WorkerBusyError):
            raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
        raise


def _launch(state: State, pairs: Sequence[tuple[int, int]], stages: list[Stage]) -> None:
    """`pairs` are (folder_id, run_id), the first one current."""
    # before the start, and the receipts before the current one: a poll never sees the old run
    state.scan_runs = tuple(run_id for _, run_id in pairs)
    state.last_scan = pairs[0]
    state.worker.start(stages)


def active_folder_ids(conn: sqlite3.Connection) -> list[int]:
    return [
        r[0] for r in conn.execute("SELECT id FROM folders WHERE retired_at IS NULL ORDER BY id")
    ]


def _one_folder_stages(state: State, folder_id: int, run_id: int) -> list[Stage]:
    begun: set[int] = set()
    steps = queue(
        state.db_path,
        ORDER,
        folder_id=folder_id,
        run_id=run_id,
        on_folder=lambda _f, r: begun.add(r),
    )
    started = [ScanStarted(run_id=run_id, folder_id=folder_id)]
    return _stages_with_cleanup(state, steps, [folder_id], started, begun)


def _stages_with_cleanup(
    state: State,
    steps: Sequence[tuple[str, Factory]],
    locked: Iterable[int],
    started: Iterable[ScanStarted],
    begun: Container[int],
) -> list[Stage]:
    def at_end() -> None:
        for folder_id in locked:
            _release(state, folder_id)
        _discard_never_begun(state.db_path, started, begun)

    last = len(steps) - 1
    return [
        Stage(name, factory, on_finish=at_end if i == last else None)
        for i, (name, factory) in enumerate(steps)
    ]


def _forget_start(
    state: State, conn: sqlite3.Connection, taken: Iterable[int], opened: Iterable[ScanStarted]
) -> None:
    """A run that never started leaves nothing behind: no locked folders (they would not reopen
    until a restart), no open receipts that no run will close."""
    for c in opened:
        discard_run(conn, c.run_id)
    for folder_id in taken:
        _release(state, folder_id)


def _discard_never_begun(
    db_path: str | Path, opened: Iterable[ScanStarted], begun_runs: Container[int]
) -> None:
    """At the end of a run, its receipts whose reading never began go: no run would ever close them.
    Its own connection: this runs in the worker's thread, the request's one was closed long ago."""
    orphans = [c.run_id for c in opened if c.run_id not in begun_runs]
    if not orphans:
        return
    conn = connect(db_path)
    try:
        for run_id in orphans:
            discard_run(conn, run_id)
    finally:
        conn.close()


def start_scan_all(state: State, conn: sqlite3.Connection) -> ScanAllStarted:
    """A folder that cannot be read is skipped and reported instead of stopping the others: one NAS
    switched off would otherwise stop every scan. The locks are all taken before the start."""
    ids = active_folder_ids(conn)
    if not ids:
        raise HTTPException(status_code=409, detail={"code": "no_folders"})
    opened: list[ScanStarted] = []
    skips: list[FolderSkipped] = []
    taken: list[int] = []
    for folder_id in ids:
        root, _ = folder_root(conn, folder_id)
        if not root_readable(root):
            skips.append(
                FolderSkipped(folder_id=folder_id, root_path=root, reason="root_unreachable")
            )
            continue
        with state.folder_locks_mutex:
            if folder_id in state.folder_locks:
                skips.append(
                    FolderSkipped(folder_id=folder_id, root_path=root, reason="scan_running")
                )
                continue
            state.folder_locks.add(folder_id)
        taken.append(folder_id)
    if not taken:
        raise HTTPException(
            status_code=409,
            detail={"code": "no_readable_folders", "skipped": [s.model_dump() for s in skips]},
        )
    previous = (state.last_scan, state.scan_runs)
    try:
        for folder_id in taken:
            run_id = start_run(conn, folder_id, now_iso())
            opened.append(ScanStarted(run_id=run_id, folder_id=folder_id))
        pairs = [(c.folder_id, c.run_id) for c in opened]
        # the reply carries every receipt, so they all open now
        begun_runs: set[int] = set()

        def follow(folder_id: int, run_id: int) -> None:
            begun_runs.add(run_id)
            state.last_scan = (folder_id, run_id)

        steps = queue_folders(state.db_path, pairs, on_folder=follow)
        _launch(state, pairs, _stages_with_cleanup(state, steps, taken, opened, begun_runs))
        return ScanAllStarted(started=opened, skipped=skips)
    except Exception as err:
        _forget_start(state, conn, taken, opened)
        state.last_scan, state.scan_runs = previous
        if isinstance(err, WorkerBusyError):
            raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
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
