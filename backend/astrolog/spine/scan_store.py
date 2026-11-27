"""The scan's receipt and its codes. Frames and files come from the new pipeline
(`api/scan_door.py`, `pipeline/frame_row.py`)."""

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from enum import StrEnum
from typing import Any

from ..db.inserted import inserted_id
from ..db.transaction import transaction


class FolderNotFoundError(ValueError):
    """An engine guard, not a user case."""


_FOLDER_ROOT = "SELECT path, retired_at FROM pipeline_roots WHERE id = ?"


def folder_root(conn: sqlite3.Connection, folder_id: int) -> tuple[str, str | None]:
    row = conn.execute(_FOLDER_ROOT, (folder_id,)).fetchone()
    if row is None:
        raise FolderNotFoundError(f"cartella inesistente: id={folder_id}")
    return row[0], row[1]


def start_run(conn: sqlite3.Connection, folder_id: int, now: str, batch: int | None = None) -> int:
    """`batch`: the gesture's first receipt, so the last gesture is read back after a restart."""
    with transaction(conn):
        cursor = conn.execute(
            "INSERT INTO scan_runs(folder_id, batch, started_at) VALUES(?, ?, ?)",
            (folder_id, batch, now),
        )
    return inserted_id(cursor)


# The newest gesture whose receipts have all closed: one still reading, or left open by a dead
# process, does not hide the one before.
_LAST_GESTURE = """
SELECT MAX(ended_at) AS ended_at, SUM(new) AS new, SUM(errors) AS not_read
FROM scan_runs GROUP BY COALESCE(batch, id)
HAVING COUNT(*) = COUNT(ended_at) ORDER BY MAX(id) DESC LIMIT 1
"""


def last_gesture(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(_LAST_GESTURE).fetchone()


def discard_run(conn: sqlite3.Connection, run_id: int) -> None:
    """For a run that never read that folder. Only open rows, so it cannot take away the story of a
    folder already read."""
    conn.execute("DELETE FROM scan_runs WHERE id = ? AND ended_at IS NULL", (run_id,))


# The folder path is what the user recognises. The join is inner because a folder is retired,
# never deleted: `scan_runs.folder_id` references it and the schema stops the delete.
SELECT_RUN = (
    "SELECT r.*, f.path AS folder_path, f.retired_at IS NOT NULL AS folder_retired"
    " FROM scan_runs r JOIN pipeline_roots f ON f.id = r.folder_id"
)


def run_row(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row | None:
    return conn.execute(SELECT_RUN + " WHERE r.id = ?", (run_id,)).fetchone()


def run_outcomes(conn: sqlite3.Connection, run_ids: Iterable[int]) -> list[sqlite3.Row]:
    """Without the unread-file list, which can hold thousands per receipt: it is asked at every
    status poll. Receipts that are gone do not come back."""
    return [
        r
        for r in (
            conn.execute(
                "SELECT id, status, errors, ended_at FROM scan_runs WHERE id = ?", (run_id,)
            ).fetchone()
            for run_id in run_ids
        )
        if r is not None
    ]


class ScanStatus(StrEnum):
    OK = "ok"
    STOPPED = "stopped"
    ABORTED = "aborted"
    ERROR = "error"


class ScanReason(StrEnum):
    ROOT_UNREACHABLE = "root_unreachable"
    STOP_REQUESTED = "stop_requested"
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"


class FileError(StrEnum):
    """Why a file did not enter: the system will not open it, it is not a FITS, its name cannot be
    written, or an unexpected fault (the trace is in the log)."""

    FILE_UNREADABLE = "file_unreadable"
    HEADER_UNREADABLE = "header_unreadable"
    NAME_NOT_UTF8 = "name_not_utf8"
    INTERNAL_ERROR = "internal_error"


class SkipReason(StrEnum):
    CALIBRATION = "calibration"
    REWRITTEN = "rewritten"  # processed elsewhere: calibrated or stacked (ADR 0029)
    NOT_SUPPORTED = "not_supported"  # a program the app does not read (ADR 0029)
    STILL_WRITING = "still_writing"


# The run's counts, each a column of `scan_runs` with the same name.
COUNTS = ("found", "new", "unchanged", "duplicates", "missing", "skipped", "errors", "online_only")
# What the scan leaves out, each carried whole in a `<name>_json` column of `scan_runs`. Unread
# files are not here: they can be thousands, and are read in pages (`errors_detail_json`).
RECEIPT_LISTS = ("unreadable_dirs", "hidden_dirs", "linked_dirs", "skipped_by_reason")


def finish_run(  # noqa: PLR0913
    conn: sqlite3.Connection,
    run_id: int,
    status: ScanStatus,
    reason: ScanReason | None,
    counts: Mapping[str, int],
    left_out: Mapping[str, Sequence[Any]],
    errors: Sequence[Mapping[str, str]],
    now: str,
) -> None:
    """Status, reason and file reasons are closed codes: a sentence or a class name here is a
    programming error."""
    if status not in ScanStatus or (reason is not None and reason not in ScanReason):
        raise ValueError(f"esito fuori dal vocabolario: {status}/{reason}")
    codes = {e["reason"] for e in errors} - set(FileError)
    codes |= {e["reason"] for e in left_out.get("skipped_by_reason", ())} - set(SkipReason)
    if codes:
        raise ValueError(f"motivi fuori dal vocabolario: {sorted(codes)}")
    tallies = "".join(f" {name} = ?," for name in COUNTS)
    lists = ", ".join(f"{name}_json = ?" for name in RECEIPT_LISTS)
    with transaction(conn):
        # S608: columns from constants of ours.
        conn.execute(
            "UPDATE scan_runs SET ended_at = ?, status = ?, reason = ?,"  # noqa: S608
            f"{tallies} errors_detail_json = ?, {lists} WHERE id = ?",
            (
                now,
                status,
                reason,
                *(counts[name] for name in COUNTS),
                _as_json(errors),
                *(_as_json(left_out.get(name)) for name in RECEIPT_LISTS),
                run_id,
            ),
        )
        # The unread-file list stays on a folder's last receipt, and on the last one that reached
        # the end if that did not: the database does not grow at every round of a flaky NAS.
        folder = conn.execute("SELECT folder_id FROM scan_runs WHERE id = ?", (run_id,)).fetchone()
        last_ok = conn.execute(
            "SELECT MAX(id) FROM scan_runs WHERE folder_id = ? AND status = 'ok' AND id < ?",
            (folder[0], run_id),
        ).fetchone()[0]
        conn.execute(
            "UPDATE scan_runs SET errors_detail_json = NULL"
            " WHERE folder_id = ? AND id < ? AND id IS NOT ?",
            (folder[0], run_id, run_id if status == "ok" else last_ok),
        )


def _as_json(items: Sequence[Any] | None) -> str | None:
    """Readable JSON, accents included, or NULL when empty."""
    return json.dumps(items, ensure_ascii=False) if items else None


def home_timezone(conn: sqlite3.Connection) -> str | None:
    """The night zone of a frame that does not say where it was taken."""
    row = conn.execute("SELECT timezone FROM sites WHERE is_default = 1").fetchone()
    return None if row is None else row["timezone"]
