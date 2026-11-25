"""A folder moved elsewhere stays the same row: positions are relative and frames are known by their
fingerprint, so only the folder answers, keyed on the whole path, have to follow."""

import json
import os
import sqlite3
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from ..clock import now_iso
from ..db.transaction import transaction
from ..fits.header_read import HeaderReadError, frame_fingerprint, read_frame
from ..fits.walk import long_path
from . import typeless_folders
from .declarations import EntityType
from .frame_folder import folder_key
from .scan import rel_path

# Enough to tell a copy of the archive from another one with the same names; each costs a header
# read, which on a NAS is the slow part.
SAMPLE_FILES: Final = 5  # [P ADR 0017]

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
    scan does; fewer than it can ask, or one different: not it. `None`: `deadline` passed first."""
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
    # every file it can ask: one copied elsewhere is not the folder moved
    known = conn.execute(
        "SELECT COUNT(DISTINCT rel_path) FROM positions WHERE folder_id = ? AND status = 'present'",
        (folder_id,),
    ).fetchone()[0]
    return sampled > 0 and sampled >= min(SAMPLE_FILES, known or len(restored))


def _restored_sample(conn: sqlite3.Connection, folder_id: int) -> dict[str, str]:
    """The sample a backup brought back (ADR 0017), read only while the folder has no frames."""
    if conn.execute("SELECT 1 FROM positions WHERE folder_id = ? LIMIT 1", (folder_id,)).fetchone():
        return {}
    row = conn.execute("SELECT sample_json FROM folders WHERE id = ?", (folder_id,)).fetchone()
    return dict(json.loads(row[0])) if row and row[0] else {}


@dataclass(frozen=True)
class Registered:
    """A registered folder another one overlaps, with its present frames."""

    id: int
    root_path: str
    frames: int


def _compared(root_path: str) -> str:
    """Key form in this system's case rule: `D:\\Astro\\` and `d:/astro` are one on Windows."""
    return os.path.normcase(folder_key(root_path))


def _inside(child: str, parent: str) -> bool:
    """Strictly inside, on key text: `D:/Astro2` is not in `D:/Astro`."""
    return _compared(child).startswith(_compared(parent) + os.path.normcase("/"))


_REGISTERED = (
    "SELECT f.id, f.root_path, (SELECT COUNT(*) FROM positions p WHERE p.folder_id = f.id"
    " AND p.status = 'present') FROM folders f WHERE ? OR f.retired_at IS NULL ORDER BY f.id"
)


def _registered(conn: sqlite3.Connection, *, active: bool) -> list[Registered]:
    return [Registered(*r) for r in conn.execute(_REGISTERED, (not active,)).fetchall()]


def held(conn: sqlite3.Connection, root_path: str) -> list[Registered]:
    """The active folders `root_path` would hold: adding it replaces them, when the user says so."""
    return [r for r in _registered(conn, active=True) if _inside(r.root_path, root_path)]


def holder(conn: sqlite3.Connection, root_path: str) -> Registered | None:
    """The active folder `root_path` is inside: its files are read already."""
    return next(
        (r for r in _registered(conn, active=True) if _inside(root_path, r.root_path)), None
    )


def absorb(conn: sqlite3.Connection, outer_id: int) -> None:
    """In the caller's transaction. Each folder inside, retired too, gives its positions prefixed
    (same rows, frames) and retires; answers keyed on the whole path hold as they are."""
    outer = conn.execute("SELECT root_path FROM folders WHERE id = ?", (outer_id,)).fetchone()[0]
    after = len(folder_key(outer)) + 1
    for inner in _registered(conn, active=False):
        if inner.id == outer_id or not _inside(inner.root_path, outer):
            continue
        prefix = folder_key(inner.root_path)[after:] + "/"
        # IGNORE: a file two nested folders both held is one position of the outer one
        conn.execute(
            "UPDATE OR IGNORE positions SET folder_id = ?, rel_path = ? || rel_path"
            " WHERE folder_id = ?",
            (outer_id, prefix, inner.id),
        )
        conn.execute("DELETE FROM positions WHERE folder_id = ?", (inner.id,))
        conn.execute(
            "UPDATE folders SET retired_at = ? WHERE id = ? AND retired_at IS NULL",
            (now_iso(), inner.id),
        )
    typeless_folders.write(conn)


def move(conn: sqlite3.Connection, folder_id: int, new_root: str) -> None:
    """Same id, new `root_path`; the folder answers under the old root take the new prefix."""
    old_key = conn.execute("SELECT root_key FROM folders WHERE id = ?", (folder_id,)).fetchone()[0]
    new_key = folder_key(new_root)
    after = len(old_key) + 1
    with transaction(conn):
        # Root first: the answer triggers match the new key against `root_key`.
        conn.execute("UPDATE folders SET root_path = ? WHERE id = ?", (new_root, folder_id))
        # OR REPLACE: a stale answer of another folder on the new key yields to this folder's.
        # A folder registered inside this one did not move: its answers stay.
        conn.execute(
            "UPDATE OR REPLACE declarations SET entity_key = ? || substr(entity_key, ?)"
            " WHERE entity_type = ? AND (entity_key = ? OR substr(entity_key, 1, ?) = ?)"
            " AND NOT EXISTS (SELECT 1 FROM folders o WHERE o.id <> ? AND o.retired_at IS NULL"
            "  AND substr(o.root_key, 1, ?) = ?"
            "  AND (entity_key = o.root_key OR substr(entity_key, 1, length(o.root_key) + 1)"
            "       = o.root_key || '/'))",
            (new_key, after, EntityType.FOLDER, old_key, after, old_key + "/",
             folder_id, after, old_key + "/"),
        )  # fmt: skip
        typeless_folders.write(conn)
