"""User's scan is the new pipeline's, on Behind's thread (step 40.4): followed per file, closed
with the receipt (`scan_runs`); `positions` written from `pipeline_files` for the old stages."""

import json
import queue
import sqlite3
import threading
from collections import Counter
from collections.abc import Callable, Generator
from pathlib import Path, PurePosixPath
from typing import Any

from ..clock import now_iso
from ..db.connect import connect
from ..db.transaction import transaction
from ..pipeline.scan import MIN_AGE_S, ScanResult, Watch, scan_root
from ..pipeline.scanner import Skip
from ..spine.scan_store import (
    COUNTS,
    FileError,
    ScanReason,
    ScanStatus,
    SkipReason,
    finish_run,
    start_run,
)
from ..spine.stage_run import Event, receipt

type Runner = Callable[[int, Watch], ScanResult]

# Read and not a frame: the receipt's reason for each.
_SKIP_OF = {
    Skip.REWRITTEN: SkipReason.REWRITTEN,
    Skip.NOT_SUPPORTED: SkipReason.NOT_SUPPORTED,
    Skip.INCOMPLETE: SkipReason.STILL_WRITING,
}
_ERROR_OF = {
    Skip.UNREADABLE: FileError.FILE_UNREADABLE,
    Skip.BROKEN: FileError.HEADER_UNREADABLE,
    Skip.FAULT: FileError.INTERNAL_ERROR,
}
_DONE = object()

# SQL out of the functions: mutmut upper-cases a literal in a function, an equivalent mutant
_POSITIONS_SEEN = (
    "INSERT INTO positions (frame_id, folder_id, rel_path, filesize, mtime, status, seen_at)"
    " SELECT pf.frame_id, pf.root_id, pf.rel_path, pf.size, pf.mtime_ns / 1e9, 'present', ?"
    " FROM pipeline_files AS pf JOIN frames AS f ON f.id = pf.frame_id"
    " WHERE pf.root_id = ? AND pf.state = 'present' AND true"  # upsert needs WHERE
    " ON CONFLICT (folder_id, rel_path) DO UPDATE SET frame_id = excluded.frame_id,"
    " filesize = excluded.filesize, mtime = excluded.mtime, status = 'present',"
    " seen_at = excluded.seen_at"
)
_POSITIONS_MISSING = (
    "UPDATE positions SET status = 'missing' WHERE folder_id = ? AND status = 'present'"
    " AND NOT EXISTS (SELECT 1 FROM pipeline_files AS pf"
    " WHERE pf.root_id = positions.folder_id AND pf.rel_path = positions.rel_path"
    " AND pf.state = 'present' AND pf.frame_id = positions.frame_id)"
)
_LEFT_OUT = (
    "SELECT rel_path, skip_reason FROM pipeline_files WHERE root_id = ? AND state = 'present'"
    " AND skip_reason IS NOT NULL ORDER BY rel_path"
)
# a frame of the pipeline, not of the archive; a typeless one without its row: the folder
# said calibration, as frame_row._kept_out and docs/domini/spina-scan.md tell
_CALIBRATION = (
    "SELECT COUNT(*) FROM pipeline_files AS pf JOIN pipeline_cards AS c ON c.file_id = pf.id"
    " WHERE pf.root_id = ? AND pf.state = 'present' AND pf.frame_id IS NOT NULL"
    " AND (c.frame_type NOT IN ('light', 'unknown') OR (c.frame_type = 'unknown'"
    " AND pf.frame_id NOT IN (SELECT id FROM frames)))"
)
# read now, a present file of its frame first: this scan, lower id (two copies born now: one
# duplicate), or earlier and frame not born now (copy of one held out: new only)
_DUPLICATES = (
    "SELECT COUNT(*) FROM pipeline_files AS pf WHERE pf.root_id = ? AND pf.state = 'present'"
    " AND pf.arrived_scan_id = ? AND pf.frame_id IN (SELECT id FROM frames)"
    " AND EXISTS (SELECT 1 FROM pipeline_files AS o WHERE o.frame_id = pf.frame_id"
    "   AND o.state = 'present' AND ((o.arrived_scan_id = pf.arrived_scan_id AND o.id < pf.id)"
    "   OR (o.arrived_scan_id < pf.arrived_scan_id"
    "   AND pf.frame_id NOT IN (SELECT value FROM json_each(?)))))"
)


def scan_events(
    conn: sqlite3.Connection, folder_id: int, run_id: int, runner: Runner
) -> Generator[Event]:
    """One event per file read, then the receipt. The scan runs where `runner` puts it; a close
    of this generator (the worker's Stop) stops it between two batches."""
    since = now_iso()
    events: queue.Queue[Any] = queue.Queue()
    stop = threading.Event()
    turn = threading.Semaphore(0)  # one file, then the worker's turn: a Stop lands before the next

    def progress(read: int, total: int, rel: str, seen: ScanResult) -> None:
        changes = seen.changes
        counts = dict.fromkeys(COUNTS, 0) | {
            "found": total + len(changes.unchanged) + len(changes.online_only),
            "new": len(seen.born),
            "unchanged": len(changes.unchanged),
            "online_only": len(changes.online_only),
        }
        events.put({"current": read, "total": total, "file": _shown(PurePosixPath(rel).name),
                    **counts})  # fmt: skip
        if not stop.is_set():  # closed: nobody takes the turn back
            turn.acquire()

    def work() -> None:
        try:
            events.put(runner(folder_id, Watch(stop, progress, min_age_s=MIN_AGE_S)))
        except BaseException as err:  # noqa: BLE001 - raised again in the worker's thread
            events.put(err)
        finally:
            events.put(_DONE)

    thread = threading.Thread(target=work, name="astrolog-scan-door", daemon=True)
    thread.start()
    outcome: ScanResult | BaseException | None = None
    try:
        while (item := events.get()) is not _DONE:
            if isinstance(item, dict):
                yield {**item, "run_id": run_id, "folder_id": folder_id, "since": since}
                turn.release()
            else:
                outcome = item
    finally:
        stop.set()
        turn.release()
        if outcome is None:  # closed while reading: its batches saved stay, said stopped
            _close_closed(conn, folder_id, run_id, events)
        thread.join()
    if isinstance(outcome, BaseException):
        _close_failed(conn, run_id, outcome)
        raise outcome
    assert outcome is not None
    yield close(conn, folder_id, run_id, outcome)


def direct(db_path: str | Path) -> Runner:
    """A runner on its own connection, in the caller's thread: tests and tools, no Behind."""

    def run(root_id: int, watch: Watch) -> ScanResult:
        conn = connect(db_path)  # opened in the scan's own thread, used there only
        try:
            return scan_root(conn, root_id, now_iso(), watch=watch)
        finally:
            conn.close()

    return run


def scan_once(
    conn: sqlite3.Connection, folder_id: int, run_id: int | None = None, min_age_s: float = 0
) -> Event:
    """Same scan, here and now, without events: tests and tools."""
    run_id = run_id if run_id is not None else start_run(conn, folder_id, now_iso())
    watch = Watch(min_age_s=min_age_s)
    return close(conn, folder_id, run_id, scan_root(conn, folder_id, now_iso(), watch=watch))


def close(conn: sqlite3.Connection, folder_id: int, run_id: int, result: ScanResult) -> Event:
    """Positions, then the receipt: the event the worker stops on."""
    changes = result.changes
    status, reason = ScanStatus.OK, None
    if not changes.reachable or result.root_lost:
        status, reason = ScanStatus.ABORTED, ScanReason.ROOT_UNREACHABLE
    elif not result.finished:
        status, reason = ScanStatus.STOPPED, ScanReason.STOP_REQUESTED
    with transaction(conn):
        _positions(conn, folder_id, mark_missing=status == ScanStatus.OK)
        counts, skipped, errors = _counts(conn, result)
    left_out: dict[str, list[Any]] = {
        "unreadable_dirs": list(changes.unreachable),
        "hidden_dirs": list(changes.hidden),
        "linked_dirs": [],  # the new walk follows links, once by real path
        "skipped_by_reason": skipped,
    }
    finish_run(conn, run_id, status, reason, counts, left_out, errors, now_iso())
    return receipt(status, reason, counts, errors, run_id=run_id, folder_id=folder_id, **left_out)


def _close_closed(
    conn: sqlite3.Connection, folder_id: int, run_id: int, events: queue.Queue[Any]
) -> None:
    outcome: Any = None
    while (item := events.get()) is not _DONE:
        outcome = item if not isinstance(item, dict) else outcome
    if isinstance(outcome, ScanResult):
        close(conn, folder_id, run_id, outcome)
    else:
        _close_stopped(conn, folder_id, run_id)


def _close_stopped(conn: sqlite3.Connection, folder_id: int, run_id: int) -> None:
    conn.rollback()
    with transaction(conn):
        _positions(conn, folder_id, mark_missing=False)
    _close_empty(conn, run_id, ScanStatus.STOPPED, ScanReason.STOP_REQUESTED)


def _close_failed(conn: sqlite3.Connection, run_id: int, err: BaseException) -> None:
    """A database that does not answer is not an unreadable file."""
    conn.rollback()
    why = ScanReason.DATABASE_ERROR if isinstance(err, sqlite3.Error) else ScanReason.INTERNAL_ERROR
    _close_empty(conn, run_id, ScanStatus.ERROR, why)


def _close_empty(
    conn: sqlite3.Connection, run_id: int, status: ScanStatus, reason: ScanReason
) -> None:
    finish_run(conn, run_id, status, reason, dict.fromkeys(COUNTS, 0), {}, [], now_iso())


def _positions(conn: sqlite3.Connection, folder_id: int, *, mark_missing: bool) -> None:
    """The archive's files of this folder as the old stages read them, until they read
    `pipeline_files` (step 40.4, third commit)."""
    conn.execute(_POSITIONS_SEEN, (now_iso(), folder_id))
    if mark_missing:
        conn.execute(_POSITIONS_MISSING, (folder_id,))


def _counts(
    conn: sqlite3.Connection, result: ScanResult
) -> tuple[dict[str, int], list[dict[str, Any]], list[dict[str, str]]]:
    """The old receipt's counts from the new scan (step 40.4: each its definition in the plan)."""
    changes = result.changes
    # what is left out is the folder's state, read now or before: a broken file is not read again,
    # and the receipt says it at every scan, as the old one did
    left = [(rel, Skip(why)) for rel, why in conn.execute(_LEFT_OUT, (changes.root_id,))]
    reasons: Counter[str] = Counter(_SKIP_OF[why] for _, why in left if why in _SKIP_OF)
    reasons[SkipReason.STILL_WRITING] += len(result.still_writing)
    reasons[SkipReason.CALIBRATION] = conn.execute(_CALIBRATION, (changes.root_id,)).fetchone()[0]
    born = json.dumps(sorted(result.born))
    duplicates = conn.execute(_DUPLICATES, (changes.root_id, changes.scan_id, born)).fetchone()[0]
    errors = [
        {"file": _shown(rel), "reason": _ERROR_OF[why]} for rel, why in left if why in _ERROR_OF
    ]
    errors += [
        {"file": _shown(rel), "reason": _unlooked(rel)}
        for rel in changes.unlooked
    ]  # fmt: skip
    counts = {
        "found": len(changes.new) + len(changes.changed) + len(changes.reread)
        + len(changes.unchanged) + len(changes.unlooked) + len(changes.online_only),
        "new": len(result.born),
        "unchanged": len(changes.unchanged),
        "duplicates": duplicates,
        "missing": len(changes.gone),
        "skipped": sum(reasons.values()),
        "errors": len(errors),
        "online_only": len(changes.online_only),
    }  # fmt: skip
    skipped = [{"reason": r, "count": n} for r, n in sorted(reasons.items()) if n]
    return counts, skipped, errors


def _unlooked(rel: str) -> FileError:
    return FileError.NAME_NOT_UTF8 if _shown(rel) != rel else FileError.FILE_UNREADABLE


def _shown(name: str) -> str:
    """Python carries a non-UTF-8 name as surrogates, which sqlite3 and JSON refuse: `?`."""
    return name.encode(errors="replace").decode()
