"""The answers' backup (ADR 0017): the file is rewritten after every write of the user's, and a
database with no answer is offered the one it finds beside it."""

import re
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import Response

from ..db.connect import connect
from ..spine import backup
from .deps import get_db
from .models_site import BackupCounts, BackupStatus

router = APIRouter(prefix="/api/v1", tags=["settings"])

# What the user says, not what the app does on its own: scans, the pipeline, the weather
# refresh and the probe are left out. A rule, not a list of routes, as `app._is_open`.
_USER_WRITES = re.compile(
    r"^/api/v1/(review/apply|gear/.+|settings|settings/wizard-done|weather/meteoblue-key"
    r"|sites(/\d+(/default)?)?|folders|folders/\d+(/move)?|backup/(restore|import))$"
)


def is_user_write(method: str, path: str) -> bool:
    return method != "GET" and _USER_WRITES.match(path) is not None


def rewrite(db_path: str) -> None:
    """Its own connection: the request's is closed by the time the answer is out."""
    conn = connect(db_path)
    try:
        backup.write_quietly(conn, db_path)
    finally:
        conn.close()


def _status(request: Request) -> BackupStatus:
    path = backup.path_for(request.app.state.db_path)
    try:
        data = backup.read(path)
        unreadable = False
    except backup.BackupError:
        data, unreadable = None, True
    offered = request.app.state.backup_offer and data is not None
    return BackupStatus(
        offer="found" if offered else "none",
        last=BackupCounts(**backup.summary(data)) if data else None,
        unreadable=unreadable,
        path=str(path),
    )


@router.get("/backup", response_model=BackupStatus)
def backup_status(request: Request) -> BackupStatus:
    """The answers' file next to the database: when it was last written and what it carries.

    `offer` is `found` when the database holds no answer (new, or recreated) and the file is
    there: the page asks whether to put the answers back. It stays
    `found` until `POST /backup/restore` or `POST /backup/decline`."""
    return _status(request)


@router.post("/backup/restore", response_model=BackupStatus)
def restore_backup(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> BackupStatus:
    """Puts back the answers of the file beside the database: settings, sites, folders, the
    pieces and filters written by hand, the names learnt and every answer of Da confermare.
    Nothing derived is in the file: the next scan rebuilds frames, rigs and nights.

    409 `no_backup_offered` unless the database held no answer at start and the file is there."""
    if _status(request).offer != "found":
        raise HTTPException(status_code=409, detail={"code": "no_backup_offered"})
    data = backup.read(backup.path_for(request.app.state.db_path))
    assert data is not None  # the status just said found
    backup.restore(conn, data)
    request.app.state.backup_offer = False
    return _status(request)


@router.post("/backup/decline", response_model=BackupStatus)
def decline_backup(request: Request) -> BackupStatus:
    """Starts from scratch: the offer is not made again while the app runs, and the first answer
    rewrites the file, after which a database with answers is never offered one."""
    request.app.state.backup_offer = False
    return _status(request)


@router.get("/backup/export")
def export_backup(conn: sqlite3.Connection = Depends(get_db)) -> Response:
    """The answers as a file to take to another computer, **without the service keys**: whoever
    has the file does not get them; nor the solver path, wrong on another computer. Import it
    there with `POST /backup/import`."""
    body = backup.json_text(backup.collect(conn, this_machine=False))
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{backup.FILE_NAME}"'},
    )


@router.post("/backup/import", response_model=BackupStatus)
def import_backup(
    request: Request,
    content: dict[str, Any] = Body(...),
    conn: sqlite3.Connection = Depends(get_db),
) -> BackupStatus:
    """Puts back the answers of a file exported elsewhere, sent as its JSON content: adds and
    updates, deletes nothing, so it is safe on a database already in use.

    422 `not_a_backup` when the content is not an answers' file of this version."""
    try:
        data = backup.checked(content)
    except backup.BackupError as e:
        raise HTTPException(status_code=422, detail={"code": "not_a_backup"}) from e
    try:
        backup.restore(conn, data)
    except (KeyError, TypeError, ValueError, sqlite3.Error) as e:
        raise HTTPException(status_code=422, detail={"code": "not_a_backup"}) from e
    request.app.state.backup_offer = False
    return _status(request)


def offered_on_start(db_path: str | Path) -> bool:
    """Offered while the database holds no answer: new, or recreated by `tools/reset_db.py`
    before the app started. On one with answers the file is its own."""
    if not backup.path_for(db_path).exists():
        return False
    conn = connect(db_path)
    try:
        return not backup.has_answers(backup.collect(conn, this_machine=True))
    finally:
        conn.close()
