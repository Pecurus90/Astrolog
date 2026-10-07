"""A folder moved elsewhere stays the same row: positions are relative and frames are known by their
fingerprint, so only the folder answers, keyed on the whole path, have to follow."""

import sqlite3
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


def same_files(conn: sqlite3.Connection, folder_id: int, root: str, found: Iterable[str]) -> bool:
    """The first `SAMPLE_FILES` under `root`, by path, that the folder has a position for (no
    calibration file has one), fingerprinted as the scan does. None, or one different: not it."""
    sampled = 0
    for rel, path in sorted((rel_path(p, root), p) for p in found):
        known = conn.execute(_KNOWN, (folder_id, rel)).fetchone()
        if known is None:
            continue
        try:
            header, block = read_frame(long_path(path))
            fingerprint = frame_fingerprint(long_path(path), header, block)
        except (HeaderReadError, OSError):
            return False  # unread is unproven
        if fingerprint != known["frame_hash"]:
            return False
        sampled += 1
        if sampled == SAMPLE_FILES:
            break
    return sampled > 0


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
