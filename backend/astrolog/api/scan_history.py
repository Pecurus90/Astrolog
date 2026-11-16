"""Impostazioni > Scansioni: the scans as the user made them, newest first, each with what entered,
what was left out and why (`spine/scan_history`)."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.datastructures import State

from ..clock import elapsed_s, relative_day
from ..site_of import home_site
from ..spine import scan_history
from ..spine.stages import StageName
from ..worker.worker import State as WorkerState
from .deps import get_db
from .models import (
    DirLeftOut,
    FileNotRead,
    LeftOutCount,
    ScanErrorList,
    ScanList,
    ScanOut,
    ScanProgressOut,
)
from .models_page import page_of

router = APIRouter(prefix="/api/v1", tags=["scan"])


def _live(state: State) -> set[int]:
    running = state.worker.snapshot().state == WorkerState.RUNNING
    return set(state.scan_runs) if running else set()


def _progress(state: State, g: scan_history.Gesture) -> ScanProgressOut | None:
    rec = state.worker.stage_record(StageName.SCAN)
    if g.outcome != scan_history.Outcome.RUNNING or rec is None:
        return None
    if rec.current is None or not rec.total:
        return None
    return ScanProgressOut(
        read=rec.current, total=rec.total, pct=round(100 * rec.current / rec.total)
    )


def _out(state: State, g: scan_history.Gesture, zone: str | None, newest: bool) -> ScanOut:
    idle = state.worker.snapshot().state != WorkerState.RUNNING
    return ScanOut(
        id=g.id,
        started_at=g.started_at,
        started_day=relative_day(g.started_at, zone),
        duration_s=elapsed_s(g.started_at, g.ended_at),
        outcome=g.outcome.value,
        reason=g.reason,  # type: ignore[arg-type] - the closed codes of scan_store and LEFT_OPEN
        reason_folder=g.reason_folder,
        folders=g.folders,
        new=g.new,
        left_out=[LeftOutCount(reason=r.value, count=n) for r, n in g.left_out],
        dirs_left_out=[DirLeftOut(path=p, why=w.value) for p, w in g.dirs_left_out],
        unread=g.unread,
        unread_files=[FileNotRead.model_validate(f) for f in g.unread_files],
        unread_kept=g.unread_kept,
        progress=_progress(state, g),
        can_retry=newest and idle and g.outcome == scan_history.Outcome.BLOCKED,
    )


@router.get("/scans", response_model=ScanList)
def scans(
    request: Request,
    limit: int = Query(20, ge=1, le=200),  # [T]
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> ScanList:
    """The scans, newest first: one per gesture (Scansiona reads every folder in one scan).
    Days by the home site's clock."""
    state = request.app.state
    home = home_site(conn)
    zone = home.timezone if home else None
    gestures = scan_history.page(conn, limit, offset, _live(state))
    return ScanList(
        items=[_out(state, g, zone, offset == 0 and i == 0) for i, g in enumerate(gestures)],
        total=scan_history.count(conn),
        limit=limit,
        offset=offset,
    )


@router.get("/scans/{scan_id}/unread", response_model=ScanErrorList)
def scan_unread(
    scan_id: int,
    limit: int = Query(100, ge=1, le=1000),  # [T]
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> ScanErrorList:
    """Every file the scan could not read, each with its reason, in pages.

    404 `scan_not_found`; 410 `errors_not_kept` when a folder's list is no longer kept (only the
    last scan of each folder keeps it)."""
    if scan_history.one(conn, scan_id, set()) is None:
        raise HTTPException(status_code=404, detail={"code": "scan_not_found"})
    files = scan_history.unread_files(conn, scan_id)
    if files is None:
        raise HTTPException(status_code=410, detail={"code": "errors_not_kept"})
    return ScanErrorList(**page_of(files, limit, offset))
