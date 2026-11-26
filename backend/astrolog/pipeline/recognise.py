"""A root met again elsewhere (moved disk, restored backup): the same folder if its first files are
the same shots, fingerprinted as the scan does (step 40.4: one fingerprint, the pipeline's)."""

import json
import os
import sqlite3
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Final

from .scanner import Extracted, scan_file
from .walk import long_path

# Enough to tell a copy of the archive from another one with the same names; each costs a header
# read, which on a NAS is the slow part.
SAMPLE_FILES: Final = 5  # [P ADR 0017]

_KNOWN = (
    "SELECT fr.fingerprint FROM pipeline_files AS f"
    " JOIN pipeline_frames AS fr ON fr.id = f.frame_id"
    " WHERE f.root_id = ? AND f.rel_path = ? AND f.state = 'present'"
)


def _rel(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def same_files(
    conn: sqlite3.Connection,
    root_id: int,
    root: str,
    found: Iterable[str],
    deadline: float | None = None,
) -> bool | None:
    """The first `SAMPLE_FILES` under `root` the root holds a shot for; fewer than it can ask, or
    one different: not it. `None`: `deadline` passed first."""
    sampled = 0
    restored = _restored_sample(conn, root_id)
    for rel, path in sorted((_rel(p, root), p) for p in found):
        known = conn.execute(_KNOWN, (root_id, rel)).fetchone()
        expected = known["fingerprint"] if known is not None else restored.get(rel)
        if expected is None:
            continue
        if deadline is not None and time.monotonic() >= deadline:
            return None
        try:
            size = os.stat(long_path(path)).st_size
        except OSError:
            return False  # unread is unproven
        got = scan_file(Path(path), size)
        if not isinstance(got, Extracted) or got.fingerprint != expected:
            return False
        sampled += 1
        if sampled == SAMPLE_FILES:
            break
    # every file it can ask: one copied elsewhere is not the folder moved
    known_count = conn.execute(
        "SELECT COUNT(DISTINCT rel_path) FROM pipeline_files"
        " WHERE root_id = ? AND state = 'present' AND frame_id IS NOT NULL",
        (root_id,),
    ).fetchone()[0]
    return sampled > 0 and sampled >= min(SAMPLE_FILES, known_count or len(restored))


def _restored_sample(conn: sqlite3.Connection, root_id: int) -> dict[str, str]:
    """The sample a backup brought back (ADR 0017), read only while the root has no shots."""
    if conn.execute(
        "SELECT 1 FROM pipeline_files WHERE root_id = ? AND frame_id IS NOT NULL LIMIT 1",
        (root_id,),
    ).fetchone():
        return {}
    row = conn.execute("SELECT sample_json FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()
    return dict(json.loads(row[0])) if row and row[0] else {}
