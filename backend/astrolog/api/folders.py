"""Registering is permissive: a folder may not answer now (a NAS switched off). `frames` comes
from the database, never the disk: counting on disk is the wizard's explicit `probe`."""

import os
import sqlite3
import time
from typing import Final

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.datastructures import State

from ..clock import now_iso
from ..db.inserted import inserted_id
from ..db.transaction import transaction
from ..fits.walk import subfolders, walk_dir
from ..spine import typeless_answer
from ..spine.run import STAGE_IDENTIFY, STAGE_SOLVE
from ..spine.scan import root_readable
from ..spine.stages import count_pending, refresh_waiting
from . import work
from .deps import get_db
from .models import (
    BrowseOut,
    FolderCreate,
    FolderEntry,
    FolderList,
    FolderOut,
    PathInfo,
    PathProbe,
    ProbeOut,
    RetireOut,
)
from .paths import same_folder, validate_root

router = APIRouter(prefix="/api/v1", tags=["cartelle"])

# "10 seconds is about the limit for keeping the user's attention focused on the dialogue"
# (Nielsen, *Response Times: The 3 Important Limits*, 1993); checked between folders.
PROBE_SECONDS: Final = 10

_SELECT = (
    "SELECT f.id, f.name, f.root_path, f.created_at,"
    " (SELECT COUNT(*) FROM positions p WHERE p.folder_id = f.id AND p.status = 'present')"
    " AS frames FROM folders f"
)


def _out(row: sqlite3.Row, *, reactivated: bool = False) -> FolderOut:
    return FolderOut(
        **dict(row), reachable=root_readable(row["root_path"]), reactivated=reactivated
    )


@router.get("/folders/path-info", response_model=PathInfo)
def path_info(request: Request) -> PathInfo:
    """How paths are shaped on THIS machine, and whether there is a confined data root."""
    return PathInfo(
        family="windows" if os.name == "nt" else "posix", data_root=request.app.state.data_root
    )


@router.post("/folders/probe", response_model=ProbeOut)
def probe(body: PathProbe, request: Request) -> ProbeOut:
    """Looks at a path without registering it. It also counts the online-only FITS: they are
    there, even if not on the disk, and whoever keeps the archive under OneDrive must not read "0"
    on the folder they have just chosen.

    422 when the path is refused, with the reason as its code."""
    canonical = validate_root(body.root_path, request.app.state.data_root)
    if not root_readable(canonical):
        return ProbeOut(root_path=canonical, reachable=False, fits_count=None, complete=None)
    online: list[str] = []
    unvisited: list[str] = []
    found = walk_dir(
        canonical,
        online_only=online,
        deadline=time.monotonic() + PROBE_SECONDS,
        unvisited=unvisited,
    )
    return ProbeOut(
        root_path=canonical,
        reachable=True,
        fits_count=len(found) + len(online),
        complete=not unvisited,
    )


@router.get("/folders/browse", response_model=BrowseOut)
def browse(request: Request, path: str | None = None) -> BrowseOut:
    """The subfolders to choose from inside the data root: on a NAS in Docker the user does not
    know which path the folder has inside the container, and picks it instead of typing it.
    Without a root (the desktop) nothing is listed: 409 `no_data_root`. No pages: these are the
    subfolders of a single folder, not the archive.

    409 `root_unreachable` with the `path` when it cannot be listed; 422 when the path is refused,
    with the reason as its code."""
    root = request.app.state.data_root
    if root is None:
        raise HTTPException(status_code=409, detail={"code": "no_data_root"})
    where = validate_root(path or root, root)
    try:
        names = subfolders(where)
    except OSError as err:
        raise HTTPException(
            status_code=409, detail={"code": "root_unreachable", "path": where}
        ) from err
    return BrowseOut(
        path=where,
        parent=None if same_folder(os.path.realpath(where), root) else os.path.dirname(where),
        folders=[FolderEntry(name=n, path=os.path.join(where, n)) for n in names],
    )


@router.get("/folders", response_model=FolderList)
def list_folders(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> FolderList:
    """The active folders (the retired ones do not appear)."""
    total = conn.execute("SELECT COUNT(*) FROM folders WHERE retired_at IS NULL").fetchone()[0]
    rows = conn.execute(
        _SELECT + " WHERE f.retired_at IS NULL ORDER BY f.id LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return FolderList(items=[_out(r) for r in rows], total=total, limit=limit, offset=offset)


@router.post("/folders", response_model=FolderOut, status_code=201)
def create_folder(
    body: FolderCreate, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> FolderOut:
    """Registers a folder; registering a retired one again reactivates it.

    409 `folder_exists` with its `folder_id` if it is already active; 422 when the path is
    refused, with the reason as its code."""
    canonical = validate_root(body.root_path, request.app.state.data_root)
    existing = conn.execute(
        "SELECT id, retired_at FROM folders WHERE root_path = ?", (canonical,)
    ).fetchone()
    if existing is not None:
        if existing["retired_at"] is None:
            raise HTTPException(
                status_code=409, detail={"code": "folder_exists", "folder_id": existing["id"]}
            )
        _move(conn, request.app.state, existing["id"], None)
        row = conn.execute(_SELECT + " WHERE f.id = ?", (existing["id"],)).fetchone()
        return _out(row, reactivated=True)
    folder_id = inserted_id(
        conn.execute(
            "INSERT INTO folders(root_path, name, created_at) VALUES(?, ?, ?)",
            (canonical, body.name, now_iso()),
        )
    )
    return _out(conn.execute(_SELECT + " WHERE f.id = ?", (folder_id,)).fetchone())


@router.delete("/folders/{folder_id}", response_model=RetireOut)
def retire_folder(
    folder_id: int, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> RetireOut:
    """Retires: the app stops looking there. The frames stay. Idempotent.

    404 `folder_not_found` if it is unknown."""
    row = conn.execute("SELECT id, retired_at FROM folders WHERE id = ?", (folder_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "folder_not_found"})
    kept = conn.execute(
        "SELECT COUNT(*) FROM positions WHERE folder_id = ?", (folder_id,)
    ).fetchone()[0]
    if row["retired_at"] is not None:
        return RetireOut(folder_id=folder_id, retired=False, kept_frames=kept)
    _move(conn, request.app.state, folder_id, now_iso())
    return RetireOut(folder_id=folder_id, retired=True, kept_frames=kept)


def _move(conn: sqlite3.Connection, state: State, folder_id: int, retired_at: str | None) -> None:
    """Waiting marks are rewritten in the retirement's transaction: one written with stale marks
    cannot be repaired by repeating it, which returns early as already retired."""
    # Not refused while the worker runs: re-adding goes through Add, used while scanning, and
    # removing must always work; `identify` and `group` recheck every frame before working it.
    with transaction(conn):
        conn.execute("UPDATE folders SET retired_at = ? WHERE id = ?", (retired_at, folder_id))
        refresh_waiting(conn)  # a frame's folder changed without going through the positions
        detached, requeued = typeless_answer.detach_waiting(conn)
    # even with nothing detached: a restored folder can make the waiting frames ready again
    if requeued:
        work.after(state, [STAGE_SOLVE])
    elif detached or count_pending(conn, STAGE_IDENTIFY):
        work.after(state, [STAGE_IDENTIFY])
