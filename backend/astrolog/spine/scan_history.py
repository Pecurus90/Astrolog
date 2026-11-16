"""The scans as the user made them: one gesture is one scan, however many folders it read.
Its receipts are the rows of `scan_runs` sharing `COALESCE(batch, id)`."""

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from .scan_store import SELECT_RUN, SkipReason


class Outcome(StrEnum):
    COMPLETED = "completed"
    STOPPED = "stopped"  # by the user
    BLOCKED = "blocked"  # by a fault, or left open by a process that died
    RUNNING = "running"


class LeftOut(StrEnum):
    """Why files found did not become frames, in the order the page lists them."""

    UNCHANGED = "unchanged"
    DUPLICATES = "duplicates"
    CALIBRATION = SkipReason.CALIBRATION.value
    STACK = SkipReason.STACK.value
    STILL_WRITING = SkipReason.STILL_WRITING.value
    ONLINE_ONLY = "online_only"


class DirLeftOut(StrEnum):
    UNREADABLE = "unreadable"
    HIDDEN = "hidden"
    LINKED = "linked"


# The reason a gesture closed without a receipt saying why: the process died while it read.
LEFT_OPEN = "left_open"
# Files unread shown with the scan; the rest on request, they can be thousands. [T]
UNREAD_SHOWN = 5


@dataclass
class Gesture:
    id: int
    started_at: str
    ended_at: str | None
    outcome: Outcome
    reason: str | None
    reason_folder: str | None
    folders: list[str]
    new: int
    left_out: list[tuple[LeftOut, int]]
    dirs_left_out: list[tuple[str, DirLeftOut]]
    unread: int
    unread_files: list[dict[str, str]] = field(default_factory=list)
    unread_kept: bool = True
    run_ids: list[int] = field(default_factory=list)


_GESTURES = """
SELECT COALESCE(batch, id) AS g FROM scan_runs GROUP BY g ORDER BY g DESC LIMIT ? OFFSET ?
"""


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(DISTINCT COALESCE(batch, id)) FROM scan_runs").fetchone()[0]


def page(conn: sqlite3.Connection, limit: int, offset: int, live: set[int]) -> list[Gesture]:
    """Newest first. `live`: the receipts the worker is still reading, so an open one among them
    is running and any other open one was left by a process that died."""
    ids = [r["g"] for r in conn.execute(_GESTURES, (limit, offset))]
    return [g for g in (one(conn, i, live) for i in ids) if g is not None]


def one(conn: sqlite3.Connection, gesture_id: int, live: set[int]) -> Gesture | None:
    rows = conn.execute(
        SELECT_RUN + " WHERE COALESCE(r.batch, r.id) = ? ORDER BY r.id", (gesture_id,)
    ).fetchall()
    return _gesture(gesture_id, rows, live) if rows else None


def unread_files(conn: sqlite3.Connection, gesture_id: int) -> list[dict[str, str]] | None:
    """Every unread file of the gesture, folder by folder; None when a receipt with unread files
    no longer keeps their list (only the last scan of each folder does)."""
    rows = conn.execute(
        "SELECT errors, errors_detail_json FROM scan_runs WHERE COALESCE(batch, id) = ?"
        " ORDER BY id",
        (gesture_id,),
    ).fetchall()
    if any(r["errors"] and r["errors_detail_json"] is None for r in rows):
        return None
    return [f for r in rows for f in json.loads(r["errors_detail_json"] or "[]")]


def _outcome(rows: Sequence[sqlite3.Row], live: set[int]) -> tuple[Outcome, sqlite3.Row | None]:
    """Worst first, as `pipeline._state_of`: a lost folder is not covered by one read well."""
    for r in rows:
        if r["status"] in ("aborted", "error"):
            return Outcome.BLOCKED, r
    open_rows = [r for r in rows if r["ended_at"] is None]
    if any(r["id"] in live for r in open_rows):
        return Outcome.RUNNING, None
    if open_rows:
        return Outcome.BLOCKED, open_rows[0]
    if any(r["status"] == "stopped" for r in rows):
        return Outcome.STOPPED, None
    return Outcome.COMPLETED, None


def _left_out(rows: Sequence[sqlite3.Row]) -> list[tuple[LeftOut, int]]:
    total: dict[LeftOut, int] = dict.fromkeys(LeftOut, 0)
    for r in rows:
        total[LeftOut.UNCHANGED] += r["unchanged"]
        total[LeftOut.DUPLICATES] += r["duplicates"]
        total[LeftOut.ONLINE_ONLY] += r["online_only"]
        for s in json.loads(r["skipped_by_reason_json"] or "[]"):
            total[LeftOut(s["reason"])] += s["count"]
    return [(k, n) for k, n in total.items() if n]


def _dirs(rows: Sequence[sqlite3.Row]) -> list[tuple[str, DirLeftOut]]:
    kinds = (
        ("unreadable_dirs_json", DirLeftOut.UNREADABLE),
        ("hidden_dirs_json", DirLeftOut.HIDDEN),
        ("linked_dirs_json", DirLeftOut.LINKED),
    )
    return [(p, why) for col, why in kinds for r in rows for p in json.loads(r[col] or "[]")]


def _gesture(gesture_id: int, rows: Sequence[sqlite3.Row], live: set[int]) -> Gesture:
    outcome, cause = _outcome(rows, live)
    ends = [r["ended_at"] for r in rows]
    unread = sum(r["errors"] for r in rows)
    kept = not any(r["errors"] and r["errors_detail_json"] is None for r in rows)
    files = [f for r in rows for f in json.loads(r["errors_detail_json"] or "[]")]
    return Gesture(
        id=gesture_id,
        started_at=min(r["started_at"] for r in rows),
        ended_at=None if None in ends else max(ends),
        outcome=outcome,
        reason=None if cause is None else (cause["reason"] or LEFT_OPEN),
        reason_folder=None if cause is None else cause["folder_path"],
        folders=list(dict.fromkeys(r["folder_path"] for r in rows)),
        new=sum(r["new"] for r in rows),
        left_out=_left_out(rows),
        dirs_left_out=_dirs(rows),
        unread=unread,
        unread_files=files[:UNREAD_SHOWN],
        unread_kept=kept,
        run_ids=[r["id"] for r in rows],
    )
