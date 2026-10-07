"""Registering is permissive: a folder may not answer now (a NAS switched off). `frames` comes
from the database, never the disk: counting on disk is the wizard's explicit `probe`."""

import os
import sqlite3
import threading
import time
from typing import Final

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette.datastructures import State

from ..clock import now_iso
from ..db.inserted import inserted_id
from ..db.transaction import transaction
from ..fits.walk import subfolders, walk_dir
from ..spine import folder_move, typeless_answer
from ..spine.scan import root_readable
from ..spine.stages import StageName, count_pending
from . import work
from .deps import get_db
from .models import (
    BrowseOut,
    FolderCreate,
    FolderEntry,
    FolderList,
    FolderMove,
    FolderOut,
    MoveCheck,
    MovedFrom,
    PathInfo,
    PathProbe,
    ProbeOut,
    RetireOut,
)
from .paths import same_folder, validate_root

router = APIRouter(prefix="/api/v1", tags=["folders"])

# "10 seconds is about the limit for keeping the user's attention focused on the dialogue"
# (Nielsen, *Response Times: The 3 Important Limits*, 1993); checked between folders.
PROBE_SECONDS: Final = 10

_SELECT = (
    "SELECT f.id, f.name, f.root_path, f.created_at,"
    " (SELECT COUNT(*) FROM positions p WHERE p.folder_id = f.id AND p.status = 'present')"
    " AS frames FROM folders f"
)


def _reachable(roots: list[str], deadline: float | None = None) -> dict[str, bool | None]:
    """Every folder asked at once under one deadline: one that has not answered when time is up is
    `None`, and its thread is left behind instead of holding the answer."""
    answers: dict[str, bool] = {}

    def ask(root: str) -> None:
        answers[root] = root_readable(root)

    threads = [threading.Thread(target=ask, args=(r,), daemon=True) for r in set(roots)]
    for thread in threads:
        thread.start()
    if deadline is None:
        deadline = time.monotonic() + PROBE_SECONDS
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
    return {root: answers.get(root) for root in roots}


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
def probe(
    body: PathProbe, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> ProbeOut:
    """Looks at a path without registering it. It also counts the online-only FITS: they are
    there, even if not on the disk, and whoever keeps the archive under OneDrive must not read "0"
    on the folder they have just chosen.

    `moved_from` is the registered folder these files belonged to, when the place is one moved here
    (`moved_check` says why it is missing). Count and recognition share `PROBE_SECONDS`.

    422 when the path is refused, with the reason as its code."""
    canonical = validate_root(body.root_path, request.app.state.data_root)
    if not root_readable(canonical):
        return ProbeOut(
            root_path=canonical,
            reachable=False,
            fits_count=None,
            complete=None,
            moved_from=None,
            moved_check=MoveCheck.PLACE_UNREACHABLE,
        )
    deadline = time.monotonic() + PROBE_SECONDS
    online: list[str] = []
    unvisited: list[str] = []
    found = walk_dir(canonical, online_only=online, deadline=deadline, unvisited=unvisited)
    moved_from, check = _moved_here(conn, canonical, found, deadline)
    return ProbeOut(
        root_path=canonical,
        reachable=True,
        fits_count=len(found) + len(online),
        complete=not unvisited,
        moved_from=moved_from,
        moved_check=check,
    )


def _moved_here(
    conn: sqlite3.Connection, root: str, found: list[str], deadline: float
) -> tuple[MovedFrom | None, MoveCheck]:
    """Only a folder that is gone (retired, or not answering) can have moved: one still reachable
    holding the same files is a copy."""
    rows = conn.execute("SELECT id, root_path, retired_at FROM folders ORDER BY id").fetchall()
    if any(r["root_path"] == root for r in rows):
        return None, MoveCheck.NONE  # already registered: adding it says so
    reach = _reachable([r["root_path"] for r in rows if r["retired_at"] is None], deadline)
    for row in rows:
        # A silent folder with these files may be the original, this its copy: no proposal.
        if row["retired_at"] is None and reach[row["root_path"]] is None:
            same = folder_move.same_files(conn, row["id"], root, found, deadline)
            if same is None or same:
                return None, MoveCheck.OUT_OF_TIME
    for row in rows:
        if row["retired_at"] is None and reach[row["root_path"]] is not False:
            continue
        if time.monotonic() >= deadline:
            return None, MoveCheck.OUT_OF_TIME
        same = folder_move.same_files(conn, row["id"], root, found, deadline)
        if same is None:
            return None, MoveCheck.OUT_OF_TIME
        if same:
            return MovedFrom(id=row["id"], root_path=row["root_path"]), MoveCheck.FOUND
    return None, MoveCheck.NONE


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
    """The active folders (the retired ones do not appear). All are asked at once whether they
    answer, under one deadline of `PROBE_SECONDS`: one that has not answered by then is
    `reachable: false`, so a dead network share cannot hold the list."""
    total = conn.execute("SELECT COUNT(*) FROM folders WHERE retired_at IS NULL").fetchone()[0]
    rows = conn.execute(
        _SELECT + " WHERE f.retired_at IS NULL ORDER BY f.id LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    reach = _reachable([r["root_path"] for r in rows])
    items = [FolderOut(**dict(r), reachable=reach[r["root_path"]] is True) for r in rows]
    return FolderList(items=items, total=total, limit=limit, offset=offset)


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


@router.post("/folders/{folder_id}/move", response_model=FolderOut)
def move_folder(
    folder_id: int, body: FolderMove, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> FolderOut:
    """The folder's files are now at `root_path`: same folder, so frames, scans and the answers
    on its folders follow it. Only to a place with the same files (`folder_move.same_files`); a
    retired folder comes back (`reactivated`).

    404 `folder_not_found`; 409 `folder_exists` with its `folder_id` if the path is registered,
    active or retired; 409 `root_unreachable` with the `path`; 409 `not_the_same_folder`; 422 when
    the path is refused, with the reason as its code."""
    row = conn.execute("SELECT id, retired_at FROM folders WHERE id = ?", (folder_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "folder_not_found"})
    canonical = validate_root(body.root_path, request.app.state.data_root)
    existing = conn.execute("SELECT id FROM folders WHERE root_path = ?", (canonical,)).fetchone()
    if existing is not None:
        raise HTTPException(
            status_code=409, detail={"code": "folder_exists", "folder_id": existing["id"]}
        )
    if not root_readable(canonical):
        raise HTTPException(status_code=409, detail={"code": "root_unreachable", "path": canonical})
    found = walk_dir(canonical, deadline=time.monotonic() + PROBE_SECONDS)
    if not folder_move.same_files(conn, folder_id, canonical, found):
        raise HTTPException(status_code=409, detail={"code": "not_the_same_folder"})
    folder_move.move(conn, folder_id, canonical)
    retired = row["retired_at"] is not None
    if retired:
        _move(conn, request.app.state, folder_id, None)
    return _out(
        conn.execute(_SELECT + " WHERE f.id = ?", (folder_id,)).fetchone(), reactivated=retired
    )


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
        detached, requeued = typeless_answer.detach_waiting(conn)
    # even with nothing detached: a restored folder can make the waiting frames ready again
    if requeued:
        work.after(state, [StageName.SOLVE])
    elif detached or count_pending(conn, StageName.IDENTIFY):
        work.after(state, [StageName.IDENTIFY])
