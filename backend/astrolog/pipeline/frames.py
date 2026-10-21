"""A chosen folder scanned end to end: what changed, the new or changed files read, each tied to
its frame. One frame per fingerprint: a copy is a duplicate, a moved file stays its frame."""

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from ..db.transaction import transaction
from .changes import Changes, record_changes
from .scanner import Extracted, Skipped, scan_file


@dataclass
class ScanResult:
    changes: Changes
    frames: int = 0  # frames with at least one file present in the folder
    duplicates: dict[int, list[str]] = field(default_factory=dict)  # frame -> its files
    moved: list[tuple[str, str]] = field(default_factory=list)  # (was, is now)
    skipped: list[Skipped] = field(default_factory=list)  # read, but not a frame


def scan_root(conn: sqlite3.Connection, root_id: int, now: str) -> ScanResult:
    root = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()
    with transaction(conn):  # one with the sync: an interrupted read leaves no file unread
        changes = record_changes(conn, root_id, now)
        result = ScanResult(changes)
        for rel in changes.to_read:
            got = scan_file(Path(root["path"], rel))
            frame_id = _frame_of(conn, got, now) if isinstance(got, Extracted) else None
            if isinstance(got, Skipped):
                result.skipped.append(got)
            conn.execute(
                "UPDATE pipeline_files SET frame_id = ? WHERE root_id = ? AND rel_path = ?",
                (frame_id, root_id, rel),
            )
        result.moved = _moved(conn, root_id, changes)
    result.duplicates = _duplicates(conn, root_id)
    result.frames = conn.execute(
        "SELECT COUNT(DISTINCT frame_id) FROM pipeline_files"
        " WHERE root_id = ? AND state = 'present' AND frame_id IS NOT NULL",
        (root_id,),
    ).fetchone()[0]
    return result


def _frame_of(conn: sqlite3.Connection, got: Extracted, now: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO pipeline_frames (fingerprint, created_at) VALUES (?, ?)",
        (got.fingerprint, now),
    )
    row = conn.execute(
        "SELECT id FROM pipeline_frames WHERE fingerprint = ?", (got.fingerprint,)
    ).fetchone()
    return int(row["id"])


def _moved(conn: sqlite3.Connection, root_id: int, changes: Changes) -> list[tuple[str, str]]:
    """A file new in this scan whose frame lost a file in this same scan, paired one to one: a
    further new file of the same frame is a copy, a duplicate, not a second move."""
    new = set(changes.new)
    rows = conn.execute(
        "SELECT was.rel_path AS was, now.rel_path AS now FROM pipeline_files AS now"
        " JOIN pipeline_files AS was ON was.frame_id = now.frame_id AND was.root_id = now.root_id"
        " WHERE now.root_id = ? AND now.state = 'present' AND was.state = 'gone'"
        " AND was.seen_scan_id = ? ORDER BY was.rel_path, now.rel_path",
        (root_id, changes.scan_id),
    ).fetchall()
    pairs: list[tuple[str, str]] = []
    paired: set[str] = set()
    for row in rows:
        if row["now"] in new and row["was"] not in paired and row["now"] not in paired:
            pairs.append((row["was"], row["now"]))
            paired.update((row["was"], row["now"]))
    return pairs


def _duplicates(conn: sqlite3.Connection, root_id: int) -> dict[int, list[str]]:
    rows = conn.execute(
        "SELECT frame_id, rel_path FROM pipeline_files"
        " WHERE root_id = ? AND state = 'present' AND frame_id IS NOT NULL"
        " AND frame_id IN (SELECT frame_id FROM pipeline_files WHERE root_id = ?"
        " AND state = 'present' GROUP BY frame_id HAVING COUNT(*) > 1)"
        " ORDER BY frame_id, rel_path",
        (root_id, root_id),
    ).fetchall()
    found: dict[int, list[str]] = {}
    for row in rows:
        found.setdefault(row["frame_id"], []).append(row["rel_path"])
    return found
