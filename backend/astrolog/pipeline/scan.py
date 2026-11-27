"""Chosen folder scanned: changed files read, each tied to its frame, header stored.
One frame per fingerprint: copy is duplicate, moved file stays its frame."""

import json
import logging
import os
import sqlite3
import threading
import time
from collections import Counter
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from . import frame_card, frame_row
from .card import Card, Conditions, read_card, read_conditions
from .changes import PASSING, Changes, finish_scan, record_changes
from .filters import resolve
from .scanner import Extracted, Skip, Skipped, scan_file
from .walk import long_path

log = logging.getLogger(__name__)
_ROOTS_GUARD = threading.Lock()
_RUNNING: dict[int, threading.Lock] = {}  # app is one process: a lock per root
BATCH = 100  # [T] write lock short, a stop loses one batch at most
UNKNOWN_KEPT = 100  # [P ADR 0038] receipt stays small, readable on screen
UNKNOWN_TRACKED = 10_000  # [T] memory bound on distinct keys; past it unknown_more = at least


class ScanRunningError(RuntimeError):
    """Same root already scanning or solving in this process: a second scan would mark the
    first's files gone, a second solve pass would launch ASTAP twice on each shot."""


@contextmanager
def busy(root_id: int) -> Generator[None]:
    """One scan or solve pass per root at a time; other roots run side by side."""
    with _ROOTS_GUARD:
        running = _RUNNING.setdefault(root_id, threading.Lock())
    if not running.acquire(blocking=False):
        raise ScanRunningError(root_id)
    try:
        yield
    finally:
        running.release()


@dataclass
class ScanResult:
    changes: Changes
    frames: int = 0  # frames with at least one file present in folder
    duplicates: dict[int, list[str]] = field(default_factory=dict)  # frame -> its files
    moved: list[tuple[str, str]] = field(default_factory=list)  # (was, is now)
    skipped: list[Skipped] = field(default_factory=list)  # read, but not a frame
    born: set[int] = field(default_factory=set)  # frames that entered the archive now
    still_writing: list[str] = field(default_factory=list)  # too young: read next scan
    finished: bool = False


# A copy may preallocate the final size: header whole, pixels still zero. Young file waits. [T]
MIN_AGE_S = 30
type Progress = Callable[[int, int, str, ScanResult], object]  # read, to read, file, so far


@dataclass(frozen=True, slots=True)
class Watch:
    """What the caller follows: stop between batches, a call per file read, the clock. The app's
    scans wait MIN_AGE_S; a bare call (tests, tools) reads at once."""

    stop: threading.Event = field(default_factory=threading.Event)
    progress: Progress | None = None
    now_s: Callable[[], float] = time.time
    min_age_s: float = 0


def scan_root(
    conn: sqlite3.Connection,
    root_id: int,
    now: str,
    *,
    stop: threading.Event | None = None,
    watch: Watch | None = None,
) -> ScanResult:
    """One scan per root at a time (ScanRunningError, `busy`); a stop ends it between batches."""
    watch = watch or Watch(stop or threading.Event())
    with busy(root_id):
        return _scan_root(conn, root_id, now, watch)


def _young(changes: Changes, watch: Watch) -> list[str]:
    """Written in the last seconds (either side: float rounding of the clock): not read now, row
    keeps old size and date. Date further ahead (camera PC, NAS clock) says nothing: read."""
    if watch.min_age_s <= 0:
        return []
    now_ns = watch.now_s() * 1e9
    span_ns = watch.min_age_s * 1e9
    return [rel for rel in changes.to_read if abs(changes.stat[rel][1] - now_ns) < span_ns]


def _scan_root(conn: sqlite3.Connection, root_id: int, now: str, watch: Watch) -> ScanResult:
    """Files opened outside any transaction, saved per batch: lock held only to write; stopped
    scan keeps saved batches, unread files keep old size and date, so read next time."""
    stop = watch.stop
    changes = record_changes(conn, root_id, now)
    result = ScanResult(changes)
    result.still_writing = _young(changes, watch)
    young = set(result.still_writing)
    to_read = [rel for rel in changes.to_read if rel not in young]
    reasons: Counter[str] = Counter()
    unknown: Counter[str] = Counter()
    vanished: set[str] = set()
    traced: set[type[Exception]] = set()
    for start in range(0, len(to_read), BATCH):
        if stop.is_set():  # as interrupted: not finished, nothing judged gone
            return result
        read: list[tuple[str, Read]] = []
        for number, rel in enumerate(to_read[start : start + BATCH], start + 1):
            if stop.is_set():  # between two files: what was read is saved, the rest waits
                break
            path = Path(changes.root, rel)
            read.append((rel, _read(path, changes.stat[rel][0], traced)))
            if watch.progress is not None:
                watch.progress(number, len(to_read), rel, result)
        batch = [(rel, got) for rel, got in read if not _vanished(got.got)]
        vanished.update(rel for rel, got in read if _vanished(got.got))
        skipped = [got.got for _, got in batch if isinstance(got.got, Skipped)]
        reasons.update(got.reason for got in skipped)
        _count_unknown(unknown, [got.got for _, got in batch if isinstance(got.got, Extracted)])
        with transaction(conn):
            touched: set[int] = set()
            for rel, got in batch:
                touched |= _store(conn, changes, rel, got, now)
            touched |= frame_card.settle(conn, touched)
            result.born |= frame_row.write(conn, touched)
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
        if stop.is_set():  # stopped inside the batch: saved, not finished
            return result
    _left_unread(changes, vanished)
    with transaction(conn):  # gone and moves together: a crash loses neither
        finish_scan(conn, changes)
        result.moved = _moved(conn, root_id, changes)
        frame_card.follow_moves(conn, root_id, changes.scan_id, result.moved)
        again = frame_card.settle_stale(conn) | frame_row.left_out(conn, root_id)
        result.born |= frame_row.write(conn, again)
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
    result.finished = True
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


@dataclass(frozen=True, slots=True)
class Read:
    """A file read: header, and its card and conditions when it is a frame."""

    got: Extracted | Skipped
    card: Card | None = None
    conditions: Conditions | None = None


def _read(path: Path, size: int, traced: set[type[Exception]]) -> Read:
    """Unexpected fault skips this file, never the scan, read again next time; log gets one
    trace per type per run, not a thousand (docs/domini/spina-scan.md)."""
    try:
        got = scan_file(path, size)
        if isinstance(got, Skipped):
            return Read(got)
        return Read(got, read_card(got.program, got.values), read_conditions(got.values))
    except Exception as err:  # any fault of one file, by contract
        if type(err) not in traced:
            traced.add(type(err))
            log.exception("scansione: guasto imprevisto leggendo un file (%s)", path.name)
        return Read(Skipped(path, Skip.FAULT))


def _store(conn: sqlite3.Connection, changes: Changes, rel: str, read: Read, now: str) -> set[int]:
    """File's size and date written with its read, frame and header together: skipped file
    loses both, unless passing skip (locked) of file read before. Returns shots touched."""
    got = read.got
    skipped = isinstance(got, Skipped)
    shot = None if skipped else _frame_of(conn, got, now)
    was = _row_for(conn, changes.root_id, rel, shot)
    before = was["frame_id"] if was is not None else None
    held = skipped and got.reason in PASSING and before is not None  # locked: keeps its shot
    frame_id = (before if held else None) if skipped else shot
    file_id = _write_file(conn, changes, rel, was, (frame_id, got.reason if skipped else None))
    touched = {shot for shot in (before, frame_id) if shot is not None}
    if before is not None and before != frame_id:
        _drop_if_unused(conn, before, frame_id)
    if skipped:
        if not held:
            conn.execute("DELETE FROM pipeline_headers WHERE file_id = ?", (file_id,))
        return touched
    conn.execute(
        "INSERT OR REPLACE INTO pipeline_headers (file_id, program, header) VALUES (?, ?, ?)",
        (file_id, got.program, json.dumps(got.values, allow_nan=False)),
    )
    card, conditions = read.card, read.conditions
    assert card is not None  # a frame read always has its card (_read)
    _insert(conn, "pipeline_cards", file_id, card)
    if conditions is not None:
        _insert(conn, "pipeline_conditions", file_id, conditions)
    if card.filter is not None:
        resolve(conn, card.filter)
    return touched


def _row_for(
    conn: sqlite3.Connection, root_id: int, rel: str, shot: int | None
) -> sqlite3.Row | None:
    """Present row of path; else gone one of same shot (back; shotless row of still-copying
    file gives way). Gone with another shot: history, new file gets own row."""
    rows = conn.execute(
        "SELECT id, frame_id, state, arrived_scan_id FROM pipeline_files"
        " WHERE root_id = ? AND rel_path = ?",
        (root_id, rel),
    ).fetchall()
    present = [row for row in rows if row["state"] == "present"]
    back = [row for row in rows if shot is not None and row["frame_id"] == shot]
    if back and present and present[0]["frame_id"] is None:
        unread = present[0]
        conn.execute("DELETE FROM pipeline_headers WHERE file_id = ?", (unread["id"],))
        conn.execute("DELETE FROM pipeline_files WHERE id = ?", (unread["id"],))
        conn.execute(  # arrived when copy began, not now: no false move
            "UPDATE pipeline_files SET state = 'present', gone_scan_id = NULL,"
            " arrived_scan_id = ? WHERE id = ?",
            (unread["arrived_scan_id"], back[0]["id"]),
        )
        return back[0]
    return (present or back or [None])[0]


def _write_file(
    conn: sqlite3.Connection,
    changes: Changes,
    rel: str,
    was: sqlite3.Row | None,
    read: tuple[int | None, str | None],
) -> int:
    """`read`: frame, skip reason. Back from gone: arrived now, so move pairing sees it."""
    size, mtime_ns = changes.stat[rel]
    frame_id, skip_reason = read
    if was is None:
        return inserted_id(
            conn.execute(
                "INSERT INTO pipeline_files (root_id, rel_path, size, mtime_ns, state,"
                " seen_scan_id, arrived_scan_id, frame_id, skip_reason)"
                " VALUES (?, ?, ?, ?, 'present', ?, ?, ?, ?)",
                (changes.root_id, rel, size, mtime_ns, changes.scan_id, changes.scan_id,
                 frame_id, skip_reason),
            )
        )  # fmt: skip
    conn.execute(
        "UPDATE pipeline_files SET size = ?, mtime_ns = ?, seen_scan_id = ?,"
        " arrived_scan_id = CASE WHEN state = 'gone' THEN ? ELSE arrived_scan_id END,"
        " state = 'present', gone_scan_id = NULL, frame_id = ?, skip_reason = ? WHERE id = ?",
        (size, mtime_ns, changes.scan_id, changes.scan_id, frame_id, skip_reason, was["id"]),
    )
    return int(was["id"])


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


def _drop_if_unused(conn: sqlite3.Connection, frame_id: int, heir: int | None) -> None:
    """Frame left by every file, present or gone: phantom shot. Gone file keeps its own. A file
    rewritten in place (header fixed: new fingerprint) hands the user's answers to its heir."""
    old = conn.execute(
        "SELECT fingerprint FROM pipeline_frames WHERE id = ?"
        " AND NOT EXISTS (SELECT 1 FROM pipeline_files WHERE frame_id = ?)",
        (frame_id, frame_id),
    ).fetchone()
    if old is None:
        return
    if heir is not None:
        conn.execute(  # declarations keyed on the frame's fingerprint (schema: declarations)
            "UPDATE OR IGNORE declarations SET entity_key ="
            " (SELECT fingerprint FROM pipeline_frames WHERE id = ?)"
            " WHERE entity_type IN ('frame', 'mosaic') AND entity_key = ?",
            (heir, old["fingerprint"]),
        )
    conn.execute("DELETE FROM pipeline_frames WHERE id = ?", (frame_id,))  # frames: cascade


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
