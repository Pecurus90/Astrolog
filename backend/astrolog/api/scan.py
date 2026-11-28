"""The work lives in the worker, not in the request; the scan itself is the new pipeline's, on
Behind's thread (`scan_door`), and a root a scan holds refuses a second one (`Behind.scanning`)."""

import sqlite3
from collections.abc import Container, Iterable, Sequence
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import State

from ..clock import now_iso
from ..db.connect import connect
from ..db.paths import cache_dir
from ..pipeline.behind import Behind
from ..pipeline.changes import open_receipt
from ..spine import backup, night_moons
from ..spine.run import ORDER, Reading, ScanWork, queue, queue_folders
from ..spine.scan_store import (
    FolderNotFoundError,
    ScanReason,
    ScanStatus,
    discard_run,
    finish_run,
    folder_root,
)
from ..spine.solve import solver_path
from ..spine.stage_run import Factory
from ..worker.worker import Stage, WorkerBusyError
from .deps import get_db
from .models import FolderSkipped, ScanAllStarted, ScanStarted
from .paths import root_readable
from .scan_door import scan_events

router = APIRouter(prefix="/api/v1", tags=["scan"])


def scan_work(state: State) -> ScanWork:
    """The user's scan: the new pipeline's, on Behind's thread, followed by the worker."""
    return lambda conn, folder_id, run_id: scan_events(
        conn, folder_id, run_id, state.behind.scan_now
    )


def start_scan(state: State, conn: sqlite3.Connection, folder_id: int) -> int:
    """Pre-checks, receipt opened, run started; returns `run_id`. HTTPException 404/409 when it
    cannot."""
    try:
        root, retired_at = folder_root(conn, folder_id)
    except FolderNotFoundError as err:
        raise HTTPException(status_code=404, detail={"code": "folder_not_found"}) from err
    if retired_at is not None:
        raise HTTPException(status_code=409, detail={"code": "folder_retired"})
    if not root_readable(root):
        raise HTTPException(status_code=409, detail={"code": "root_unreachable", "path": root})
    if state.behind.scanning(folder_id):
        raise HTTPException(
            status_code=409, detail={"code": "scan_running", "folder_id": folder_id}
        )
    run_id: int | None = None
    previous = (state.last_scan, state.gesture)
    try:
        run_id = open_receipt(conn, folder_id, now_iso())
        _launch(state, [(folder_id, run_id)], _one_folder_stages(state, folder_id, run_id))
        return run_id
    except Exception as err:
        # whatever broke the start, the open receipt will never have a run
        state.last_scan, state.gesture = previous
        if run_id is not None:
            discard_run(conn, run_id)
        if isinstance(err, WorkerBusyError):
            raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
        raise


def _launch(state: State, pairs: Sequence[tuple[int, int]], stages: list[Stage]) -> None:
    """`pairs` are (folder_id, run_id), the first one current."""
    # before the start, and the receipts before the current one: a poll never sees the old run
    state.gesture = pairs[0][1]  # the first placeholder's id is the gesture
    state.last_scan = pairs[0]
    state.worker.start(stages)


def active_folder_ids(conn: sqlite3.Connection) -> list[int]:
    return [
        r[0]
        for r in conn.execute("SELECT id FROM pipeline_roots WHERE retired_at IS NULL ORDER BY id")
    ]


def _one_folder_stages(state: State, folder_id: int, run_id: int) -> list[Stage]:
    begun: set[int] = set()
    steps = queue(
        state.db_path,
        ORDER,
        folder_id=folder_id,
        run_id=run_id,
        scan=Reading(scan_work(state), lambda _f, r: begun.add(r)),
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
        _discard_never_begun(state.db_path, started, begun)
        _backup_new_samples(state.db_path)
        if not state.worker.stop_requested():
            _feed_behind(state, locked)

    last = len(steps) - 1
    return [
        Stage(name, factory, on_finish=at_end if i == last else None)
        for i, (name, factory) in enumerate(steps)
    ]


def behind(db_path: str | Path) -> Behind:
    """The new pipeline behind the app's scans, on its own thread, never shown: it learns on the
    real archive until the pages are ported (ADR 0030); the app's Stop kills its ASTAP."""
    return Behind(db_path, cache_dir() / "astap", solver_path, night_moons.refresh)


def sky_follows(request: Request) -> None:
    """After a write that moves where frames go (sites, coordinates, a backup): the sites' sky from
    the frames is written again behind, through the one door (docs/domini/sito.md)."""
    request.app.state.behind.refresh_sky()


def _feed_behind(state: State, folder_ids: Iterable[int]) -> None:
    """A folder is a pipeline root (one row, step 40.3): its id is enough."""
    state.behind.kick(list(folder_ids))


def _backup_new_samples(db_path: str | Path) -> None:
    """The folders' samples into the backup when a scan changed one (`spine/backup.py`). Its own
    connection: this runs in the worker's thread."""
    conn = connect(db_path)
    try:
        backup.write_if_new_sample(conn, db_path)
    finally:
        conn.close()


def _forget_start(conn: sqlite3.Connection, opened: Iterable[ScanStarted]) -> None:
    """A run that never started leaves no open receipts that no run will close."""
    for c in opened:
        discard_run(conn, c.run_id)


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


def _unreachable_receipts(
    conn: sqlite3.Connection, skips: Iterable[FolderSkipped], batch: int
) -> None:
    """A folder that did not answer is in the gesture, blocked with its reason (Impostazioni,
    Scansioni): a closed receipt, as when the root drops while it is read."""
    for s in skips:
        if s.reason != "root_unreachable":
            continue
        now = now_iso()
        run_id = open_receipt(conn, s.folder_id, now, batch)
        finish_run(
            conn, run_id, batch, ScanStatus.ABORTED, ScanReason.ROOT_UNREACHABLE, {}, {}, [], now
        )


def start_scan_all(state: State, conn: sqlite3.Connection) -> ScanAllStarted:
    """A folder that cannot be read is skipped and reported instead of stopping the others: one NAS
    switched off would otherwise stop every scan; one a scan already holds, too."""
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
        if state.behind.scanning(folder_id):
            skips.append(FolderSkipped(folder_id=folder_id, root_path=root, reason="scan_running"))
            continue
        taken.append(folder_id)
    if not taken:
        # a folder being read is not unreachable: a double click says busy
        busy = any(s.reason == "scan_running" for s in skips)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "worker_busy" if busy else "no_readable_folders",
                "skipped": [s.model_dump() for s in skips],
            },
        )
    previous = (state.last_scan, state.gesture)
    try:
        for folder_id in taken:
            batch = opened[0].run_id if opened else None
            run_id = open_receipt(conn, folder_id, now_iso(), batch)
            opened.append(ScanStarted(run_id=run_id, folder_id=folder_id))
        pairs = [(c.folder_id, c.run_id) for c in opened]
        # the reply carries every receipt, so they all open now
        begun_runs: set[int] = set()

        def follow(folder_id: int, run_id: int) -> None:
            begun_runs.add(run_id)
            state.last_scan = (folder_id, run_id)

        steps = queue_folders(state.db_path, pairs, scan_work(state), on_folder=follow)
        _launch(state, pairs, _stages_with_cleanup(state, steps, taken, opened, begun_runs))
    except Exception as err:
        _forget_start(conn, opened)
        state.last_scan, state.gesture = previous
        if isinstance(err, WorkerBusyError):
            raise HTTPException(status_code=409, detail={"code": "worker_busy"}) from err
        raise
    _unreachable_receipts(conn, skips, opened[0].run_id)
    return ScanAllStarted(started=opened, skipped=skips)


# [C RFC 9110 15.3.3: 202 Accepted]
@router.post("/scan", response_model=ScanAllStarted, status_code=202)
def scan_all(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> ScanAllStarted:
    """Reads all the registered folders that are not retired, in one run, and replies at once;
    the progress is in `GET /pipeline/status`.

    A folder that does not answer is `skipped` and gets a closed receipt `aborted` /
    `root_unreachable` in the gesture, so `GET /scans` says it blocked. With none readable nothing
    starts and no receipt is left: the 409 is said at once.

    409 `no_folders` when there is none; 409 `no_readable_folders` with the `skipped` folders
    when none can be started; 409 `worker_busy` when a job runs, also with the `skipped` folders
    when some are already being read."""
    return start_scan_all(request.app.state, conn)


# [C RFC 9110 15.3.3: 202 Accepted]
@router.post("/folders/{folder_id}/scan", response_model=ScanStarted, status_code=202)
def scan(
    folder_id: int, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> ScanStarted:
    """Starts the scan and replies at once; the progress is in `GET /pipeline/status`.

    404 `folder_not_found`; 409 `folder_retired`, `root_unreachable` with the `path`,
    `scan_running` with the `folder_id`, or `worker_busy`."""
    run_id = start_scan(request.app.state, conn, folder_id)
    return ScanStarted(run_id=run_id, folder_id=folder_id)
