"""Old tables when a root changes (row: `pipeline/roots.py`): positions and whole-path folder
answers follow; recognition by frame_hash. Dies with positions (step 40.4)."""

import json
import os
import sqlite3
import time
from collections.abc import Iterable
from typing import Final

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
    row = conn.execute(
        "SELECT sample_json FROM pipeline_roots WHERE id = ?", (folder_id,)
    ).fetchone()
    return dict(json.loads(row[0])) if row and row[0] else {}


def frames(conn: sqlite3.Connection, folder_id: int) -> int:
    """Present positions: what the user sees the folder hold."""
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM positions WHERE folder_id = ? AND status = 'present'",
            (folder_id,),
        ).fetchone()[0]
    )


def _inside(child: sqlite3.Row, parent: sqlite3.Row) -> bool:
    """Same test as `pipeline/roots.py`, on `written_key`: the same roots follow."""
    key = parent["written_key"]
    return bool(child["written_key"].startswith(key if key.endswith(os.sep) else key + os.sep))


def absorb(conn: sqlite3.Connection, outer_id: int) -> None:
    """In caller's transaction, after `roots.absorb`, same rule on positions: roots inside, retired
    too, give theirs prefixed; a retired one around gives back those under it."""
    rows = conn.execute(
        "SELECT id, root_key, written_key, retired_at FROM pipeline_roots"
    ).fetchall()
    outer_row = next(r for r in rows if r["id"] == outer_id)
    outer = outer_row["root_key"]
    for inner in rows:
        if inner["id"] == outer_id:
            continue
        if inner["retired_at"] is not None and _inside(outer_row, inner):
            _give_back(conn, inner["root_key"], inner["id"], outer, outer_id)
        if not _inside(inner, outer_row):
            continue
        prefix = inner["root_key"][len(outer) + 1 :] + "/"
        # IGNORE: a file two nested folders both held is one position of the outer one
        conn.execute(
            "UPDATE OR IGNORE positions SET folder_id = ?, rel_path = ? || rel_path"
            " WHERE folder_id = ?",
            (outer_id, prefix, inner["id"]),
        )
        conn.execute("DELETE FROM positions WHERE folder_id = ?", (inner["id"],))
    typeless_folders.write(conn)


def _give_back(
    conn: sqlite3.Connection, around: str, around_id: int, root: str, root_id: int
) -> None:
    """Positions of `around` under `root` pass to it, prefix cut: same rows, frames."""
    prefix = root[len(around) + 1 :] + "/"
    args = (around_id, len(prefix), prefix)
    # IGNORE: a file the folder holds already stays its; the outer copy goes
    conn.execute(
        "UPDATE OR IGNORE positions SET folder_id = ?, rel_path = substr(rel_path, ?)"
        " WHERE folder_id = ? AND substr(rel_path, 1, ?) = ?",
        (root_id, len(prefix) + 1, *args),
    )
    conn.execute("DELETE FROM positions WHERE folder_id = ? AND substr(rel_path, 1, ?) = ?", args)


def follow_answers(conn: sqlite3.Connection, folder_id: int, old_root: str) -> None:
    """In caller's transaction, after `roots.move` (answer triggers match `root_key`): answers
    under old root take the new prefix; a folder registered inside did not move, its stay."""
    old_key = folder_key(old_root)
    new_key = conn.execute(
        "SELECT root_key FROM pipeline_roots WHERE id = ?", (folder_id,)
    ).fetchone()[0]
    after = len(old_key) + 1
    # OR REPLACE: a stale answer of another folder on the new key yields to this folder's.
    conn.execute(
        "UPDATE OR REPLACE declarations SET entity_key = ? || substr(entity_key, ?)"
        " WHERE entity_type = ? AND (entity_key = ? OR substr(entity_key, 1, ?) = ?)"
        " AND NOT EXISTS (SELECT 1 FROM pipeline_roots o WHERE o.id <> ? AND o.retired_at IS NULL"
        "  AND substr(o.root_key, 1, ?) = ?"
        "  AND (entity_key = o.root_key OR substr(entity_key, 1, length(o.root_key) + 1)"
        "       = o.root_key || '/'))",
        (new_key, after, EntityType.FOLDER, old_key, after, old_key + "/",
         folder_id, after, old_key + "/"),
    )  # fmt: skip
    typeless_folders.write(conn)
