"""The scan's writes: folder, receipt, frames, positions. Nothing is decided here: it writes what
`scan.py` decided, and a new frame is born with every stage `pending`."""

import json
import sqlite3
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import Any

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from .stages import mark_pending, refresh_waiting

FRAME_COLUMNS = (
    "image_type",
    "date_obs",
    "exposure_s",
    "gain",
    "offset",
    "ccd_temp_c",
    "naxis1",
    "naxis2",
    "binning",
    "pixel_size_um",
    "bayer_pattern",
    "focal_mm_raw",
    "filter_raw",
    "object_raw",
    "telescope_raw",
    "instrument_raw",
    "filter_wheel_raw",
    "focuser_raw",
    "guide_camera_raw",
    "software_raw",
    "asks_camera",
    "asks_filter",
    "names_optics",
    "ra_hint_deg",
    "dec_hint_deg",
    "site_lat",
    "site_lon",
    "site_elev_m",
)
_FIELD_OF = {"focal_mm_raw": "focal_mm", "ra_hint_deg": "ra_deg", "dec_hint_deg": "dec_deg"}


class FolderNotFoundError(ValueError):
    """An engine guard, not a user case."""


def folder_root(conn: sqlite3.Connection, folder_id: int) -> tuple[str, str | None]:
    row = conn.execute(
        "SELECT root_path, retired_at FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if row is None:
        raise FolderNotFoundError(f"cartella inesistente: id={folder_id}")
    return row["root_path"], row["retired_at"]


def start_run(conn: sqlite3.Connection, folder_id: int, now: str) -> int:
    with transaction(conn):
        cursor = conn.execute(
            "INSERT INTO scan_runs(folder_id, started_at) VALUES(?, ?)", (folder_id, now)
        )
    return inserted_id(cursor)


def discard_run(conn: sqlite3.Connection, run_id: int) -> None:
    """For a run that never read that folder. Only open rows, so it cannot take away the story of a
    folder already read."""
    conn.execute("DELETE FROM scan_runs WHERE id = ? AND ended_at IS NULL", (run_id,))


# The folder path is what the user recognises. The join is inner because a folder is retired,
# never deleted: `scan_runs.folder_id` references it and the schema stops the delete.
SELECT_RUN = (
    "SELECT r.*, f.root_path AS folder_path, f.retired_at IS NOT NULL AS folder_retired"
    " FROM scan_runs r JOIN folders f ON f.id = r.folder_id"
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


STATUSES = ("ok", "stopped", "aborted", "error")
REASONS = (None, "root_unreachable", "stop_requested", "internal_error", "database_error")
# Why a file did not enter: the system will not open it, it is not a FITS, its name cannot be
# written, or an unexpected fault (the trace is in the log).
FILE_ERRORS = ("file_unreadable", "header_unreadable", "name_not_utf8", "internal_error")
SKIP_REASONS = ("calibration", "stack", "still_writing")


# What the scan leaves out, each carried whole in a `<name>_json` column of `scan_runs`. Unread
# files are not here: they can be thousands, and are read in pages (`errors_detail_json`).
RECEIPT_LISTS = ("unreadable_dirs", "hidden_dirs", "linked_dirs", "skipped_by_reason")


def finish_run(  # noqa: PLR0913
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    reason: str | None,
    counts: Mapping[str, int],
    left_out: Mapping[str, Sequence[Any]],
    errors: Sequence[Mapping[str, str]],
    now: str,
) -> None:
    """Status, reason and file reasons are closed codes: a sentence or a class name here is a
    programming error."""
    if status not in STATUSES or reason not in REASONS:
        raise ValueError(f"esito fuori dal vocabolario: {status}/{reason}")
    codes = {e["reason"] for e in errors} - set(FILE_ERRORS)
    codes |= {e["reason"] for e in left_out.get("skipped_by_reason", ())} - set(SKIP_REASONS)
    if codes:
        raise ValueError(f"motivi fuori dal vocabolario: {sorted(codes)}")
    columns = ", ".join(f"{name}_json = ?" for name in RECEIPT_LISTS)
    with transaction(conn):
        # S608: columns from a constant of ours.
        conn.execute(
            "UPDATE scan_runs SET ended_at = ?, status = ?, reason = ?,"  # noqa: S608
            " found = ?, new = ?, unchanged = ?, duplicates = ?, missing = ?, skipped = ?,"
            " errors = ?, online_only = ?,"
            f" errors_detail_json = ?, {columns} WHERE id = ?",
            (
                now,
                status,
                reason,
                counts["found"],
                counts["new"],
                counts["unchanged"],
                counts["duplicates"],
                counts["missing"],
                counts["skipped"],
                counts["errors"],
                counts["online_only"],
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


def position(conn: sqlite3.Connection, folder_id: int, rel_path: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, frame_id, filesize, mtime, status FROM positions"
        " WHERE folder_id = ? AND rel_path = ?",
        (folder_id, rel_path),
    ).fetchone()


def set_position_present(conn: sqlite3.Connection, position_id: int, now: str) -> None:
    with transaction(conn):
        conn.execute(
            "UPDATE positions SET status = 'present', seen_at = ? WHERE id = ?", (now, position_id)
        )
        refresh_waiting(conn, [_frame_of(conn, position_id)])


def _frame_of(conn: sqlite3.Connection, position_id: int) -> int:
    return conn.execute("SELECT frame_id FROM positions WHERE id = ?", (position_id,)).fetchone()[0]


def home_timezone(conn: sqlite3.Connection) -> str | None:
    """The night zone of a frame that does not say where it was taken."""
    row = conn.execute("SELECT timezone FROM sites WHERE is_default = 1").fetchone()
    return None if row is None else row["timezone"]


def frame_id_by_hash(conn: sqlite3.Connection, frame_hash: str) -> int | None:
    row = conn.execute("SELECT id FROM frames WHERE frame_hash = ?", (frame_hash,)).fetchone()
    return row["id"] if row else None


# (night, zone, instant) of a frame, as `local_night`, `local_tz`, `night_instant`.
LocalNight = tuple[str | None, str | None, str]


def insert_frame(  # noqa: PLR0913
    conn: sqlite3.Connection,
    fields: Mapping[str, Any],
    frame_hash: str,
    header_json: str,
    now: str,
    night: LocalNight,
) -> int:
    """Inside a transaction opened by the caller."""
    values = [fields.get(_FIELD_OF.get(c, c)) for c in FRAME_COLUMNS]
    cols = ", ".join(f'"{c}"' for c in FRAME_COLUMNS)
    marks = ", ".join("?" for _ in FRAME_COLUMNS)  # segnaposto-ok: the columns, not the rows
    # S608: fixed columns.
    sql = (
        "INSERT INTO frames(frame_hash, header_json, created_at,"  # noqa: S608
        f" local_night, local_tz, night_instant, {cols}) VALUES(?, ?, ?, ?, ?, ?, {marks})"
    )
    frame_id = inserted_id(conn.execute(sql, [frame_hash, header_json, now, *night, *values]))
    mark_pending(conn, frame_id, now)
    return frame_id


def upsert_position(  # noqa: PLR0913
    conn: sqlite3.Connection,
    frame_id: int,
    folder_id: int,
    rel_path: str,
    filesize: int,
    mtime: float,
    now: str,
) -> None:
    """A different file at the same path takes the position over, and the frame before may have
    lost the folder that answered its type."""
    prima = position(conn, folder_id, rel_path)
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, status, seen_at)"
        " VALUES(?, ?, ?, ?, ?, 'present', ?)"
        " ON CONFLICT(folder_id, rel_path) DO UPDATE SET frame_id = excluded.frame_id,"
        " filesize = excluded.filesize, mtime = excluded.mtime, status = 'present',"
        " seen_at = excluded.seen_at",
        (frame_id, folder_id, rel_path, filesize, mtime, now),
    )
    refresh_waiting(conn, {frame_id} | ({prima["frame_id"]} if prima else set()))


def mark_missing(
    conn: sqlite3.Connection,
    folder_id: int,
    seen: Collection[str],
    untouched: Collection[str],
    now: str,
) -> int:
    """Never deleted; positions under an `untouched` subfolder (it would not open) stay as they
    were."""
    missing = 0
    with transaction(conn):
        for r in conn.execute(
            "SELECT id, frame_id, rel_path FROM positions"
            " WHERE folder_id = ? AND status = 'present'",
            (folder_id,),
        ).fetchall():
            if any(r["rel_path"].startswith(prefix + "/") for prefix in untouched):
                continue
            if r["rel_path"] not in seen:
                conn.execute(
                    "UPDATE positions SET status = 'missing', seen_at = ? WHERE id = ?",
                    (now, r["id"]),
                )
                refresh_waiting(conn, [r["frame_id"]])
                missing += 1
    return missing
