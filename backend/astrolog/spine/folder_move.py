"""Old tables when a root changes (row: `pipeline/roots.py`): positions and whole-path folder
answers follow (recognition: `pipeline/recognise.py`). Dies with positions (step 40.4)."""

import os
import sqlite3

from . import typeless_folders
from .declarations import EntityType
from .frame_folder import folder_key

# SQL out of the functions: mutmut upper-cases a literal in a function, an equivalent mutant
_FRAMES = "SELECT COUNT(*) FROM positions WHERE folder_id = ? AND status = 'present'"
_ROOTS = "SELECT id, root_key, written_key, retired_at FROM pipeline_roots"
# IGNORE: a file two nested folders both held is one position of the outer one
_TAKE = "UPDATE OR IGNORE positions SET folder_id = ?, rel_path = ? || rel_path WHERE folder_id = ?"
_DROP = "DELETE FROM positions WHERE folder_id = ?"
# IGNORE: a file the folder holds already stays its; the outer copy goes
_GIVE = (
    "UPDATE OR IGNORE positions SET folder_id = ?, rel_path = substr(rel_path, ?)"
    " WHERE folder_id = ? AND substr(rel_path, 1, ?) = ?"
)
_DROP_GIVEN = "DELETE FROM positions WHERE folder_id = ? AND substr(rel_path, 1, ?) = ?"
_ROOT_KEY = "SELECT root_key FROM pipeline_roots WHERE id = ?"
# OR REPLACE: a stale answer of another folder on the new key yields to this folder's
_FOLLOW = (
    "UPDATE OR REPLACE declarations SET entity_key = ? || substr(entity_key, ?)"
    " WHERE entity_type = ? AND (entity_key = ? OR substr(entity_key, 1, ?) = ?)"
    " AND NOT EXISTS (SELECT 1 FROM pipeline_roots o WHERE o.id <> ? AND o.retired_at IS NULL"
    "  AND substr(o.root_key, 1, ?) = ?"
    "  AND (entity_key = o.root_key OR substr(entity_key, 1, length(o.root_key) + 1)"
    "       = o.root_key || '/'))"
)


def frames(conn: sqlite3.Connection, folder_id: int) -> int:
    """Present positions: what the user sees the folder hold."""
    return int(conn.execute(_FRAMES, (folder_id,)).fetchone()[0])


def inside(child: str, parent: str) -> bool:
    """Copy of `pipeline/roots._inside` (spine does not import the new pipeline): the same roots
    follow. Dies with positions (step 40.4)."""
    return child.startswith(parent if parent.endswith(os.sep) else parent + os.sep)


def absorb(conn: sqlite3.Connection, outer_id: int) -> None:
    """In caller's transaction, after `roots.absorb`, same rule on positions: roots inside,
    retired too, give theirs prefixed; a retired one around gives back those under it."""
    rows = [tuple(r) for r in conn.execute(_ROOTS)]
    _, outer, outer_written, _ = next(r for r in rows if r[0] == outer_id)
    for inner_id, inner, inner_written, retired_at in rows:
        if inner_id == outer_id:
            continue
        if retired_at is not None and inside(outer_written, inner_written):
            _give_back(conn, inner, inner_id, outer, outer_id)
        if not inside(inner_written, outer_written):
            continue
        conn.execute(_TAKE, (outer_id, inner[len(outer) + 1 :] + "/", inner_id))
        conn.execute(_DROP, (inner_id,))
    typeless_folders.write(conn)


def _give_back(
    conn: sqlite3.Connection, around: str, around_id: int, root: str, root_id: int
) -> None:
    """Positions of `around` under `root` pass to it, prefix cut: same rows, frames."""
    prefix = root[len(around) + 1 :] + "/"
    args = (around_id, len(prefix), prefix)
    conn.execute(_GIVE, (root_id, len(prefix) + 1, *args))
    conn.execute(_DROP_GIVEN, args)


def follow_answers(conn: sqlite3.Connection, folder_id: int, old_root: str) -> None:
    """In caller's transaction, after `roots.move` (answer triggers match `root_key`): answers
    under old root take the new prefix; a folder registered inside did not move, its stay."""
    old_key = folder_key(old_root)
    new_key = conn.execute(_ROOT_KEY, (folder_id,)).fetchone()[0]
    after = len(old_key) + 1
    conn.execute(
        _FOLLOW,
        (new_key, after, EntityType.FOLDER, old_key, after, old_key + "/",
         folder_id, after, old_key + "/"),
    )  # fmt: skip
    typeless_folders.write(conn)
