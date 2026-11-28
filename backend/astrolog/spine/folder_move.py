"""Old tables when a root changes (files follow in `pipeline/roots.py`): whole-path folder answers
follow (recognition: `pipeline/recognise.py`), and the typeless folders are written again."""

import sqlite3

from . import typeless_folders
from .declarations import EntityType
from .frame_folder import folder_key

# SQL out of the functions: mutmut upper-cases a literal in a function, an equivalent mutant
_FRAMES = (
    "SELECT COUNT(*) FROM pipeline_files WHERE root_id = ? AND state = 'present'"
    " AND frame_id IN (SELECT id FROM frames)"
)
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
    """Present files of a frame: what the user sees the folder hold."""
    return int(conn.execute(_FRAMES, (folder_id,)).fetchone()[0])


def absorb(conn: sqlite3.Connection) -> None:
    """In caller's transaction, after `roots.absorb` moved the files: the typeless folders."""
    typeless_folders.write(conn)


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
