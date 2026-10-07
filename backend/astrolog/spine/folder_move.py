"""A folder moved elsewhere stays the same row: positions are relative and frames are known by their
fingerprint, so only the folder answers, keyed on the whole path, have to follow."""

import json
import sqlite3
import time
from collections.abc import Iterable
from typing import Final

from ..db.transaction import transaction
from ..fits.header_read import HeaderReadError, frame_fingerprint, read_frame
from ..fits.walk import long_path
from . import typeless_folders
from .declarations import EntityType
from .frame_folder import folder_key
from .scan import rel_path

# Enough to tell a copy of the archive from another one with the same names; each costs a header
# read, which on a NAS is the slow part.
SAMPLE_FILES: Final = 5

_KNOWN = (
    "SELECT f.frame_hash FROM positions p JOIN frames f ON f.id = p.frame_id"
    " WHERE p.folder_id = ? AND p.rel_path = ?"
)


def same_files(
    conn: sqlite3.Connection,
    folder_id: int,
    root: str,
    found: Iterable[str],
    deadline: float | None = None,
) -> bool | None:
    """The first `SAMPLE_FILES` under `root` the folder has a position for, fingerprinted as the
    scan does; zero, or one different: not it. `None`: `deadline` passed first, unknown."""
    sampled = 0
    restored = _restored_sample(conn, folder_id)
    for rel, path in sorted((rel_path(p, root), p) for p in found):
        known = conn.execute(_KNOWN, (folder_id, rel)).fetchone()
        expected = known["frame_hash"] if known is not None else restored.get(rel)
        if expected is None:
            continue
        if deadline is not None and time.monotonic() >= deadline:
            return None
        try:
            header, block = read_frame(long_path(path))
            fingerprint = frame_fingerprint(long_path(path), header, block)
        except (HeaderReadError, OSError):
            return False  # unread is unproven
        if fingerprint != expected:
            return False
        sampled += 1
        if sampled == SAMPLE_FILES:
            break
    return sampled > 0


def _restored_sample(conn: sqlite3.Connection, folder_id: int) -> dict[str, str]:
    """The sample a backup brought back (ADR 0017), read only while the folder has no frames."""
    if conn.execute("SELECT 1 FROM positions WHERE folder_id = ? LIMIT 1", (folder_id,)).fetchone():
        return {}
    row = conn.execute("SELECT sample_json FROM folders WHERE id = ?", (folder_id,)).fetchone()
    return dict(json.loads(row[0])) if row and row[0] else {}


def move(conn: sqlite3.Connection, folder_id: int, new_root: str) -> None:
    """Same id, new `root_path`; the folder answers under the old root take the new prefix."""
    old_key = conn.execute("SELECT root_key FROM folders WHERE id = ?", (folder_id,)).fetchone()[0]
    new_key = folder_key(new_root)
    after = len(old_key) + 1
    with transaction(conn):
        # Root first: the answer triggers match the new key against `root_key`.
        conn.execute("UPDATE folders SET root_path = ? WHERE id = ?", (new_root, folder_id))
        # OR REPLACE: a stale answer of another folder on the new key yields to this folder's.
        conn.execute(
            "UPDATE OR REPLACE declarations SET entity_key = ? || substr(entity_key, ?)"
            " WHERE entity_type = ? AND (entity_key = ? OR substr(entity_key, 1, ?) = ?)",
            (new_key, after, EntityType.FOLDER, old_key, after, old_key + "/"),
        )
        typeless_folders.write(conn)
