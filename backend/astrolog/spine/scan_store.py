"""The scan's receipt and its codes: the user's rows of `pipeline_scans` (gesture not NULL), a
placeholder per folder at the gesture (`changes.open_receipt`) that the scan replaces."""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from enum import StrEnum

from ..db.transaction import transaction


class FolderNotFoundError(ValueError):
    """An engine guard, not a user case."""


_FOLDER_ROOT = "SELECT path, retired_at FROM pipeline_roots WHERE id = ?"


def folder_root(conn: sqlite3.Connection, folder_id: int) -> tuple[str, str | None]:
    row = conn.execute(_FOLDER_ROOT, (folder_id,)).fetchone()
    if row is None:
        raise FolderNotFoundError(f"cartella inesistente: id={folder_id}")
    return row[0], row[1]


# The newest gesture whose receipts have all closed: one still reading, or left open by a dead
# process, does not hide the one before.
_LAST_GESTURE = """
SELECT MAX(ended_at) AS ended_at, SUM(born) AS new, SUM(errors) AS not_read
FROM pipeline_scans WHERE gesture IS NOT NULL GROUP BY gesture
HAVING COUNT(*) = COUNT(ended_at) ORDER BY MAX(id) DESC LIMIT 1
"""


def last_gesture(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(_LAST_GESTURE).fetchone()


def discard_run(conn: sqlite3.Connection, run_id: int) -> None:
    """For a placeholder whose folder was never read. Only placeholders still open, so it cannot
    take away the story of a folder already read."""
    conn.execute(
        "DELETE FROM pipeline_scans WHERE id = ? AND reachable IS NULL AND ended_at IS NULL",
        (run_id,),
    )


# The folder path is what the user recognises. The join is inner because a folder is retired,
# never deleted: `pipeline_scans.root_id` references it and the schema stops the delete.
SELECT_RUN = (
    "SELECT r.*, f.path AS folder_path, f.retired_at IS NOT NULL AS folder_retired"
    " FROM pipeline_scans r JOIN pipeline_roots f ON f.id = r.root_id"
)


def gesture_of(conn: sqlite3.Connection, run_id: int) -> int:
    """The gesture of a receipt: of the placeholder before its scan, which replaces it, then of
    the scan's row."""
    row = conn.execute("SELECT gesture FROM pipeline_scans WHERE id = ?", (run_id,)).fetchone()
    if row is None or row[0] is None:
        raise ValueError(f"ricevuta inesistente: id={run_id}")
    return row[0]


def run_outcomes(conn: sqlite3.Connection, gesture: int | None) -> list[sqlite3.Row]:
    """Without the unread-file list, which can hold thousands per receipt: it is asked at every
    status poll. Placeholders discarded do not come back."""
    return conn.execute(
        "SELECT id, root_id, status, errors, ended_at FROM pipeline_scans WHERE gesture = ?"
        " ORDER BY id",
        (gesture,),
    ).fetchall()


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


# The run's counts, as the worker's events carry them (`spine/run` sums them per gesture).
COUNTS = ("found", "new", "unchanged", "duplicates", "missing", "skipped", "errors", "online_only")
# What only the receipt writes; the scan's own columns (unchanged, gone, left_out) stay its own.
TALLIES = ("found", "born", "same", "duplicates", "errors", "online_only")

# The row a close writes: the placeholder if the folder was never read, else the one row of the
# gesture being read (one folder at a time), whatever root a merge moved it to.
_TARGET = (
    "SELECT id, root_id FROM pipeline_scans WHERE gesture = :g AND ended_at IS NULL"
    " AND (id = :p OR (reachable IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pipeline_scans"
    "  WHERE id = :p AND reachable IS NULL))) ORDER BY id DESC LIMIT 1"
)
_KEEP_UNREAD = "SELECT MAX(id) FROM pipeline_scans WHERE root_id = ? AND status = 'ok' AND id < ?"
_DROP_UNREAD = (
    "UPDATE pipeline_scans SET errors_detail = NULL WHERE root_id = ? AND id < ? AND id IS NOT ?"
)


def finish_run(  # noqa: PLR0913
    conn: sqlite3.Connection,
    run_id: int,
    gesture: int,
    status: ScanStatus,
    reason: ScanReason | None,
    tallies: Mapping[str, int],
    skipped: Mapping[str, int],
    errors: Sequence[Mapping[str, str]],
    now: str,
) -> int | None:
    """`run_id`: the folder's placeholder, gone once its scan began (`gesture` read before). Returns
    the row closed (None: already closed). Status, reason and file reasons are closed codes."""
    if status not in ScanStatus or (reason is not None and reason not in ScanReason):
        raise ValueError(f"esito fuori dal vocabolario: {status}/{reason}")
    codes = {e["reason"] for e in errors} - set(FileError)
    codes |= set(skipped) - set(SkipReason)
    if codes:
        raise ValueError(f"motivi fuori dal vocabolario: {sorted(codes)}")
    with transaction(conn):
        row = conn.execute(_TARGET, {"g": gesture, "p": run_id}).fetchone()
        if row is None:
            return None
        # S608: columns from a constant of ours.
        conn.execute(
            "UPDATE pipeline_scans SET ended_at = ?, status = ?, reason = ?,"  # noqa: S608
            f"{''.join(f' {name} = ?,' for name in TALLIES)} skipped_by_reason = ?,"
            " errors_detail = ? WHERE id = ?",
            (
                now,
                status,
                reason,
                *(tallies.get(name, 0) for name in TALLIES),
                json.dumps(dict(sorted(skipped.items()))),
                json.dumps(errors, ensure_ascii=False) if errors else None,
                row["id"],
            ),
        )
        # The unread-file list stays on a folder's last receipt, and on the last one that reached
        # the end if that did not: the database does not grow at every round of a flaky NAS.
        last_ok = conn.execute(_KEEP_UNREAD, (row["root_id"], row["id"])).fetchone()[0]
        kept = row["id"] if status == "ok" else last_ok
        conn.execute(_DROP_UNREAD, (row["root_id"], row["id"], kept))
    return row["id"]


# what the page shows of a scan's own judgement: unchanged, and the paths left out
_BLANK = (
    "UPDATE pipeline_scans SET unchanged = 0, left_out = (SELECT json_group_object(key, json('[]'))"
    " FROM json_each(pipeline_scans.left_out)) WHERE id = ? AND left_out IS NOT NULL"
)


def blank_judgement(conn: sqlite3.Connection, row_id: int) -> None:
    """A reading that broke or stopped with no result shows nothing it had seen: only its
    reason, as the receipt always said."""
    with transaction(conn):
        conn.execute(_BLANK, (row_id,))


def home_timezone(conn: sqlite3.Connection) -> str | None:
    """The night zone of a frame that does not say where it was taken."""
    row = conn.execute("SELECT timezone FROM sites WHERE is_default = 1").fetchone()
    return None if row is None else row["timezone"]
