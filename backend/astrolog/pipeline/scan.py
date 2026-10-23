"""Chosen folder scanned: changed files read, each tied to its frame, header stored.
One frame per fingerprint: copy is duplicate, moved file stays its frame."""

import json
import os
import sqlite3
import threading
from collections import Counter
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path

from ..db.transaction import transaction
from .card import Card, Conditions, read_card, read_conditions
from .changes import Changes, finish_scan, record_changes
from .filters import resolve
from .scanner import Extracted, Skip, Skipped, scan_file
from .walk import long_path

_ROOTS_GUARD = threading.Lock()
_RUNNING: dict[int, threading.Lock] = {}  # app is one process: a lock per root
BATCH = 100  # files saved per transaction: short lock, small loss if stopped
UNKNOWN_KEPT = 100  # no convention, product choice: receipt stays small, readable on screen
UNKNOWN_TRACKED = 10_000  # memory bound on distinct keys counted; past it unknown_more = at least


class ScanRunningError(RuntimeError):
    """Same root already scanning in this process: second would mark first's files gone."""


@dataclass
class ScanResult:
    changes: Changes
    frames: int = 0  # frames with at least one file present in folder
    duplicates: dict[int, list[str]] = field(default_factory=dict)  # frame -> its files
    moved: list[tuple[str, str]] = field(default_factory=list)  # (was, is now)
    skipped: list[Skipped] = field(default_factory=list)  # read, but not a frame


def scan_root(conn: sqlite3.Connection, root_id: int, now: str) -> ScanResult:
    """One scan per root at a time (ScanRunningError); other roots run side by side."""
    with _ROOTS_GUARD:
        running = _RUNNING.setdefault(root_id, threading.Lock())
    if not running.acquire(blocking=False):
        raise ScanRunningError(root_id)
    try:
        return _scan_root(conn, root_id, now)
    finally:
        running.release()


def _scan_root(conn: sqlite3.Connection, root_id: int, now: str) -> ScanResult:
    """Files opened outside any transaction, saved per batch: lock held only to write; stopped
    scan keeps saved batches, unread files keep old size and date, so read next time."""
    changes = record_changes(conn, root_id, now)
    result = ScanResult(changes)
    to_read = changes.to_read
    reasons: Counter[str] = Counter()
    unknown: Counter[str] = Counter()
    vanished: set[str] = set()
    for start in range(0, len(to_read), BATCH):
        read = [
            (rel, scan_file(Path(changes.root, rel), changes.stat[rel][0]))  # size already stat-ed
            for rel in to_read[start : start + BATCH]
        ]
        batch = [(rel, got) for rel, got in read if not _vanished(got)]
        vanished.update(rel for rel, got in read if _vanished(got))
        skipped = [got for _, got in batch if isinstance(got, Skipped)]
        reasons.update(got.reason for got in skipped)
        _count_unknown(unknown, [got for _, got in batch if isinstance(got, Extracted)])
        with transaction(conn, immediate=True):
            for rel, got in batch:
                _store(conn, changes, rel, got, now)
            conn.execute(  # running totals: a stopped scan keeps what its saved batches saw
                "UPDATE pipeline_scans SET skipped = ?, unknown_keys = ?, unknown_more = ?"
                " WHERE id = ?",
                (
                    json.dumps(reasons),
                    json.dumps(dict(sorted(unknown.items(), key=_by_count)[:UNKNOWN_KEPT])),
                    max(0, len(unknown) - UNKNOWN_KEPT),
                    changes.scan_id,
                ),
            )
        result.skipped.extend(skipped)
    _left_unread(changes, vanished)
    with transaction(conn, immediate=True):  # gone and moves together: a crash loses neither
        finish_scan(conn, changes)
        result.moved = _moved(conn, root_id, changes)
        conn.execute(  # name no card carries any more: nothing left to ask
            "DELETE FROM pipeline_filter_spellings WHERE written NOT IN"
            " (SELECT filter FROM pipeline_cards WHERE filter IS NOT NULL)"
        )
    result.duplicates = _duplicates(conn, root_id)
    result.frames = conn.execute(
        "SELECT COUNT(DISTINCT frame_id) FROM pipeline_files"
        " WHERE root_id = ? AND state = 'present' AND frame_id IS NOT NULL",
        (root_id,),
    ).fetchone()[0]
    return result


def _left_unread(changes: Changes, vanished: set[str]) -> None:
    """Gone before read: not looked at, said once in receipt, not also new or changed."""
    for listed in (changes.new, changes.changed, changes.reread):
        listed[:] = [rel for rel in listed if rel not in vanished]
    changes.unlooked = sorted(set(changes.unlooked) | vanished)


def _count_unknown(unknown: Counter[str], read: list[Extracted]) -> None:
    """Keys by name: same keys tracked every run. New key past UNKNOWN_TRACKED not counted."""
    for got in read:
        for key in sorted(got.unknown):
            if key in unknown or len(unknown) < UNKNOWN_TRACKED:
                unknown[key] += 1


def _by_count(item: tuple[str, int]) -> tuple[int, str]:
    """Most files first; same count: by name, never by hash order."""
    return -item[1], item[0]


def _vanished(got: Extracted | Skipped) -> bool:
    """Gone between walk and read (folder renamed meanwhile): nothing stored, row keeps its
    frame, next scan finds it gone and pairs the move."""
    return (
        isinstance(got, Skipped)
        and got.reason is Skip.UNREADABLE
        and not os.path.lexists(long_path(got.path))
    )


def _store(
    conn: sqlite3.Connection, changes: Changes, rel: str, got: Extracted | Skipped, now: str
) -> None:
    """File's size and date written with its read, frame and header together: skipped file
    loses both, even if read before."""
    size, mtime_ns = changes.stat[rel]
    was = conn.execute(
        "SELECT frame_id FROM pipeline_files WHERE root_id = ? AND rel_path = ?",
        (changes.root_id, rel),
    ).fetchone()
    file_id = conn.execute(
        "INSERT INTO pipeline_files"
        " (root_id, rel_path, size, mtime_ns, state, seen_scan_id, arrived_scan_id)"
        " VALUES (?, ?, ?, ?, 'present', ?, ?)"
        " ON CONFLICT (root_id, rel_path) DO UPDATE SET size = excluded.size,"
        " mtime_ns = excluded.mtime_ns, seen_scan_id = excluded.seen_scan_id,"
        " arrived_scan_id = CASE WHEN state = 'gone' THEN excluded.arrived_scan_id"
        " ELSE arrived_scan_id END, state = 'present', gone_scan_id = NULL RETURNING id",
        (changes.root_id, rel, size, mtime_ns, changes.scan_id, changes.scan_id),
    ).fetchone()["id"]
    skipped = isinstance(got, Skipped)
    frame_id = None if skipped else _frame_of(conn, got, now)
    conn.execute(
        "UPDATE pipeline_files SET frame_id = ?, skip_reason = ? WHERE id = ?",
        (frame_id, got.reason if skipped else None, file_id),
    )
    if was is not None and was["frame_id"] not in (None, frame_id):
        _drop_if_unused(conn, was["frame_id"])
    if skipped:
        conn.execute("DELETE FROM pipeline_headers WHERE file_id = ?", (file_id,))
        return
    conn.execute(
        "INSERT OR REPLACE INTO pipeline_headers (file_id, program, header) VALUES (?, ?, ?)",
        (file_id, got.program, json.dumps(got.values, allow_nan=False)),
    )
    card = read_card(got.program, got.values)
    _insert(conn, "pipeline_cards", file_id, card)
    conditions = read_conditions(got.values)
    if conditions is not None:
        _insert(conn, "pipeline_conditions", file_id, conditions)
    if card.filter is not None:
        resolve(conn, card.filter)


def _insert(conn: sqlite3.Connection, table: str, file_id: int, row: Card | Conditions) -> None:
    """Columns named as dataclass fields (tests)."""
    names = [f.name for f in fields(row)]
    conn.execute(
        f"INSERT OR REPLACE INTO {table} (file_id, {', '.join(names)})"  # noqa: S608
        f" VALUES (?{', ?' * len(names)})",
        (file_id, *(_column(getattr(row, name)) for name in names)),
    )


def _column(value: object) -> object:
    """Start as fixed-form text: order and equality on text (schema)."""
    return value.isoformat(timespec="microseconds") if isinstance(value, datetime) else value


def _drop_if_unused(conn: sqlite3.Connection, frame_id: int) -> None:
    """Frame left by every file, present or gone: phantom shot. Gone file keeps its own."""
    conn.execute(
        "DELETE FROM pipeline_frames WHERE id = ?"
        " AND NOT EXISTS (SELECT 1 FROM pipeline_files WHERE frame_id = ?)",
        (frame_id, frame_id),
    )


def _frame_of(conn: sqlite3.Connection, got: Extracted, now: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO pipeline_frames (fingerprint, created_at) VALUES (?, ?)",
        (got.fingerprint, now),
    )
    row = conn.execute(
        "SELECT id FROM pipeline_frames WHERE fingerprint = ?", (got.fingerprint,)
    ).fetchone()
    return int(row["id"])


MOVED = (  # by frame inside root: index pipeline_files_frame, else quadratic on big moves
    "SELECT was.rel_path AS was, now.rel_path AS now,"
    " now.size = was.size AND now.mtime_ns = was.mtime_ns AS kept FROM pipeline_files AS now"
    " JOIN pipeline_files AS was ON was.frame_id = now.frame_id AND was.root_id = now.root_id"
    " WHERE now.root_id = ? AND now.state = 'present' AND was.state = 'gone'"
    " AND was.gone_scan_id = ? AND now.arrived_scan_id > was.seen_scan_id"
)  # no ORDER BY: it would steer planner to path index; few rows, sorted in Python


def _moved(conn: sqlite3.Connection, root_id: int, changes: Changes) -> list[tuple[str, str]]:
    """Gone this scan, paired one to one with file of same frame arrived after gone one was last
    seen: holds across stopped scans and silent roots. Further arrival: copy (duplicate)."""
    rows = sorted(  # a move keeps size and date, a copy may too: every kept pair first
        conn.execute(MOVED, (root_id, changes.scan_id)),
        key=lambda r: (not r["kept"], r["was"], r["now"]),
    )
    pairs: list[tuple[str, str]] = []
    paired: set[str] = set()
    for row in rows:
        if row["was"] not in paired and row["now"] not in paired:
            pairs.append((row["was"], row["now"]))
            paired.update((row["was"], row["now"]))
    pairs.sort()
    conn.executemany(
        "INSERT INTO pipeline_moves (scan_id, was_path, now_path) VALUES (?, ?, ?)",
        [(changes.scan_id, was, now) for was, now in pairs],
    )
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
