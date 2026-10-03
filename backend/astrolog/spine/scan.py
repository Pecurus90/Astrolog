"""Folders to frames, reading the header and `FINGERPRINT_BYTES` of pixels from the centre, never
the rest. An unreadable file is counted among the errors and named in the receipt, never fatal."""

import logging
import os
import sqlite3
import time
from collections.abc import Callable, Generator, Iterable, Mapping
from functools import partial
from typing import Any, TypeGuard

from ..clock import night_date, night_instant, now_iso
from ..db.transaction import transaction
from ..fits.frame_type import CALIBRATION_TYPES, UNKNOWN
from ..fits.header_fields import extract_fields
from ..fits.header_read import HeaderReadError, frame_fingerprint, header_to_json, read_frame
from ..fits.walk import long_path, walk_dir
from ..place import timezone_of_frame
from . import header_asks, typeless
from . import scan_store as store
from .stage_run import Event, receipt

log = logging.getLogger(__name__)

COUNTS = ("found", "new", "unchanged", "duplicates", "missing", "skipped", "errors", "online_only")
DEFAULT_MIN_AGE_S = 30  # a file written more recently is still being written: seen next time


class _RootLostError(Exception):
    """The root vanished, between the pre-check and the walk or mid-run."""


def root_readable(root: str) -> bool:
    """`isdir` is not enough: a dropped share can exist as a folder and not answer. The spine's
    only reachability check."""
    try:
        os.scandir(long_path(root)).close()
    except OSError:
        return False
    return True


def rel_path(abs_path: str, root: str) -> str:
    """With `/` on every system: it is the key of `positions`."""
    return os.path.relpath(abs_path, root).replace(os.sep, "/")


# a NAS remounted with another precision truncates mtime to the millisecond: not a modification
MTIME_TOLERANCE_S = 0.001


def is_unchanged(known: sqlite3.Row | None, size: int, mtime: float) -> TypeGuard[sqlite3.Row]:
    return (
        known is not None
        and known["filesize"] == size
        and abs(known["mtime"] - mtime) < MTIME_TOLERANCE_S
    )


def _receipt(  # noqa: PLR0913
    status: str,
    reason: str | None,
    run_id: int,
    folder_id: int,
    counts: dict[str, int],
    left_out: Mapping[str, Iterable[Any]] | None = None,
    errors: Iterable[dict[str, str]] = (),
) -> Event:
    lists = {name: list((left_out or {}).get(name, ())) for name in store.RECEIPT_LISTS}
    return receipt(status, reason, counts, errors, run_id=run_id, folder_id=folder_id, **lists)


def scan_folder(  # noqa: C901
    conn: sqlite3.Connection,
    folder_id: int,
    *,
    run_id: int | None = None,
    min_age_s: float = DEFAULT_MIN_AGE_S,
    now_fn: Callable[[], float] = time.time,
) -> Generator[Event, None, None]:
    """One event per file, then the receipt. `run_id` is the `scan_runs` row the caller already
    opened to answer with its id at once, or None to open it here."""
    root, _retired = store.folder_root(conn, folder_id)
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    online, seen, errors, traced = [], set(), [], set()
    left_out: dict[str, list[Any]] = {name: [] for name in store.RECEIPT_LISTS}
    skipped, unreadable = left_out["skipped_by_reason"], left_out["unreadable_dirs"]
    if run_id is None:
        run_id = store.start_run(conn, folder_id, now_iso())
    log.info("scan: inizio", extra={"scan_run_id": run_id, "folder_id": folder_id, "root": root})
    if not root_readable(root):
        log.warning("scan: radice irraggiungibile", extra={"scan_run_id": run_id, "root": root})
        store.finish_run(
            conn, run_id, "aborted", "root_unreachable", counts, left_out, errors, now_iso()
        )
        yield _receipt("aborted", "root_unreachable", run_id, folder_id, counts)
        return

    status, reason = "ok", None
    try:
        files = walk_dir(
            root,
            unreadable=unreadable,
            hidden=left_out["hidden_dirs"],
            online_only=online,
            linked=left_out["linked_dirs"],
        )
        if any(os.path.normpath(d) == os.path.normpath(root) for d in unreadable):
            raise _RootLostError  # dropped between the check and the walk
        for dirs in (unreadable, left_out["hidden_dirs"], left_out["linked_dirs"]):
            # from the root down, like unread files: the receipt already names the folder; a
            # name that is not UTF-8 cannot be written
            dirs[:] = [_shown(rel_path(d, root)) for d in dirs]
        total = len(files)
        counts["found"] = total + len(online)
        net = (conn, folder_id, root, counts, errors, seen, run_id, traced)
        for abs_path in online:
            rel = rel_path(abs_path, root)
            _safely(*net, rel, partial(_not_on_disk, conn, folder_id, rel, counts, seen))
        for i, abs_path in enumerate(files, start=1):
            rel = rel_path(abs_path, root)
            one = (conn, folder_id, root, abs_path, rel, counts, skipped, seen, min_age_s, now_fn)
            _safely(*net, rel, partial(_one_file, *one))
            yield {
                "current": i,
                "total": total,
                "file": _shown(os.path.basename(abs_path)),
                "run_id": run_id,
                "folder_id": folder_id,
                **counts,
            }
        # Files under a folder that would not open have not vanished: nobody knows. Their
        # positions stay as they were.
        counts["missing"] = store.mark_missing(conn, folder_id, seen, unreadable, now_iso())
    except GeneratorExit:
        status, reason = "stopped", "stop_requested"
        raise
    except _RootLostError:
        # the root dropped: stop without marking as missing files that are there
        status, reason = "aborted", "root_unreachable"
        log.warning("scan: radice caduta", extra={"scan_run_id": run_id})
    except Exception as err:
        # a database that does not answer (disk full, busy) is not an unreadable file
        status = "error"
        reason = "database_error" if isinstance(err, sqlite3.Error) else "internal_error"
        log.exception("scan: errore di sistema", extra={"scan_run_id": run_id})
        raise
    finally:
        # a fault mid-write: if the database answers, the receipt closes anyway
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        store.finish_run(conn, run_id, status, reason, counts, left_out, errors, now_iso())
        log.info("scan: fine", extra={"scan_run_id": run_id, "status": status, **counts})

    yield _receipt(status, reason, run_id, folder_id, counts, left_out, errors)


def _shown(name: str) -> str:
    """Python carries the bytes of a non-UTF-8 name as surrogates, which sqlite3 and JSON refuse:
    they become `?`."""
    return name.encode("utf-8", "replace").decode("utf-8")


def _safely(  # noqa: PLR0913
    conn: sqlite3.Connection,
    folder_id: int,
    root: str,
    counts: dict[str, int],
    errors: list[dict[str, str]],
    seen: set[str],
    run_id: int,
    traced: set[type[BaseException]],
    rel: str,
    work: Callable[[], None],
) -> None:
    code = "name_not_utf8" if _shown(rel) != rel else _failure(work, root, run_id, traced)
    if code is not None:
        _count_error(conn, folder_id, rel, code, counts, errors, seen, run_id)


def _failure(
    work: Callable[[], None], root: str, run_id: int, traced: set[type[BaseException]]
) -> str | None:
    """The system says why it cannot open a file with an errno; astropy says "not a FITS" with an
    errno-less `OSError`. A dropped root or a silent database is not a file: it stops the run."""
    try:
        work()
    except (HeaderReadError, OSError) as err:
        cause = err.cause if isinstance(err, HeaderReadError) else err
        if isinstance(cause, OSError) and not root_readable(root):
            raise _RootLostError from err  # in the stat or inside the header read
        if isinstance(cause, OSError) and cause.errno is not None:
            return "file_unreadable"
        return "header_unreadable"
    except Exception as err:
        if isinstance(err, sqlite3.Error):
            raise
        # The trace goes to the log once per type: the same fault on a thousand files would fill
        # the log.
        if type(err) not in traced:
            traced.add(type(err))
            log.exception("scan: errore imprevisto", extra={"scan_run_id": run_id})
        return "internal_error"
    return None


def _not_on_disk(
    conn: sqlite3.Connection, folder_id: int, rel: str, counts: dict[str, int], seen: set[str]
) -> None:
    """Opening an online-only FITS would download it. If it was already archived it has not
    vanished: it is there, only not on disk."""
    counts["online_only"] += 1
    pos = store.position(conn, folder_id, rel)
    if pos is not None:
        seen.add(rel)
        if pos["status"] != "present":
            store.set_position_present(conn, pos["id"], now_iso())


def _count_error(  # noqa: PLR0913
    conn: sqlite3.Connection,
    folder_id: int,
    rel: str,
    code: str,
    counts: dict[str, int],
    errors: list[dict[str, str]],
    seen: set[str],
    run_id: int,
) -> None:
    counts["errors"] += 1
    errors.append({"file": _shown(rel), "reason": code})
    # a name that cannot be written has no position, and asking the DB with it would fail
    if code != "name_not_utf8" and store.position(conn, folder_id, rel) is not None:
        seen.add(rel)  # the file is there even if unreadable: not missing
    log.warning(
        "scan: file non letto", extra={"scan_run_id": run_id, "file": _shown(rel), "error": code}
    )


def _one_file(  # noqa: PLR0913
    conn: sqlite3.Connection,
    folder_id: int,
    root: str,
    abs_path: str,
    rel: str,
    counts: dict[str, int],
    skipped: list[dict[str, Any]],
    seen: set[str],
    min_age_s: float,
    now_fn: Callable[[], float],
) -> None:
    st = os.stat(long_path(abs_path))
    size, mtime = st.st_size, st.st_mtime
    pos = store.position(conn, folder_id, rel)
    now = now_iso()
    if is_unchanged(pos, size, mtime):
        seen.add(rel)
        counts["unchanged"] += 1
        if pos["status"] != "present":
            store.set_position_present(conn, pos["id"], now)
        return
    if now_fn() - mtime < min_age_s:
        _skip(rel, "still_writing", counts, skipped, seen, pos)
        return
    header, block = read_frame(long_path(abs_path))
    if os.stat(long_path(abs_path)).st_size != size:
        _skip(rel, "still_writing", counts, skipped, seen, pos)  # grew while being read
        return
    fields = extract_fields(header, abs_path)
    kind = fields["image_type"]
    if kind in CALIBRATION_TYPES or kind == "stack":
        _skip(rel, "stack" if kind == "stack" else "calibration", counts, skipped, seen, pos)
        return
    # A typeless file in a folder the user called calibration is skipped like a calibration; one
    # already a frame still enters, or after a move it would look vanished and keep its hours.
    detto = typeless.answer_at(conn, root, rel) if kind == UNKNOWN else None
    fingerprint = frame_fingerprint(long_path(abs_path), header, block)
    if detto == typeless.CALIBRATION and store.frame_id_by_hash(conn, fingerprint) is None:
        _skip(rel, "calibration", counts, skipped, seen, pos)
        return
    with transaction(conn):
        frame_id = store.frame_id_by_hash(conn, fingerprint)
        if frame_id is None:
            notte = night_of(conn, fields, mtime)
            giudicati = {**fields, **header_asks.of(fields)}
            frame_id = store.insert_frame(
                conn, giudicati, fingerprint, header_to_json(header), now, notte
            )
            counts["new"] += 1
        elif pos is not None and pos["frame_id"] == frame_id:
            counts["unchanged"] += 1  # touched on disk (the header, perhaps), same pixels
        else:
            counts["duplicates"] += 1
        store.upsert_position(conn, frame_id, folder_id, rel, size, mtime, now)
    seen.add(rel)


def night_of(conn: sqlite3.Connection, fields: Mapping[str, Any], mtime: float) -> store.LocalNight:
    """Written on entry: noon to noon in the zone of the header coordinates, or of the home
    site, or UTC (zone `None`)."""
    fuso = timezone_of_frame(
        fields.get("site_lat"), fields.get("site_lon"), store.home_timezone(conn)
    )
    istante = night_instant(fields.get("date_obs"), mtime)
    return night_date(istante, fuso), fuso, istante


def _skip(  # noqa: PLR0913
    rel: str,
    why: str,
    counts: dict[str, int],
    skipped: list[dict[str, Any]],
    seen: set[str],
    pos: sqlite3.Row | None,
) -> None:
    """Counted by reason, not by name."""
    counts["skipped"] += 1
    entry = next((e for e in skipped if e["reason"] == why), None)
    if entry is None:
        entry = {"reason": why, "count": 0}
        skipped.append(entry)
    entry["count"] += 1
    if pos is not None:
        seen.add(rel)
