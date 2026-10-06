"""Folders to frames, reading the header and `FINGERPRINT_BYTES` of pixels from the centre, never
the rest. An unreadable file is counted among the errors and named in the receipt, never fatal."""

import logging
import os
import sqlite3
import time
from collections.abc import Callable, Generator, Iterator, Mapping
from dataclasses import asdict, dataclass, field
from functools import partial
from typing import Any, TypeGuard

from ..clock import night_date, night_instant, now_iso
from ..db.transaction import transaction
from ..fits.frame_type import CALIBRATION_TYPES, FrameType
from ..fits.header_fields import extract_fields
from ..fits.header_read import HeaderReadError, frame_fingerprint, header_to_json, read_frame
from ..fits.walk import long_path, walk_dir
from ..place import timezone_of_frame
from . import header_asks, typeless
from . import scan_store as store
from .scan_store import COUNTS, FileError, ScanReason, ScanStatus, SkipReason
from .stage_run import Event, receipt

log = logging.getLogger(__name__)

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


@dataclass(frozen=True, slots=True)
class _Run:
    """One folder's read: what every file shares, and what the receipt gathers."""

    conn: sqlite3.Connection
    folder_id: int
    root: str
    run_id: int
    min_age_s: float
    now_fn: Callable[[], float]
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(COUNTS, 0))
    left_out: dict[str, list[Any]] = field(
        default_factory=lambda: {name: [] for name in store.RECEIPT_LISTS}
    )
    errors: list[dict[str, str]] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)
    # exception types already traced in the log
    traced: set[type[BaseException]] = field(default_factory=set)


def _receipt(run: _Run, status: ScanStatus, reason: ScanReason | None) -> Event:
    lists = {name: list(run.left_out[name]) for name in store.RECEIPT_LISTS}
    return receipt(
        status, reason, run.counts, run.errors, run_id=run.run_id, folder_id=run.folder_id, **lists
    )


def _finish(run: _Run, status: ScanStatus, reason: ScanReason | None) -> None:
    store.finish_run(
        run.conn, run.run_id, status, reason, run.counts, run.left_out, run.errors, now_iso()
    )


def scan_folder(
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
    if run_id is None:
        run_id = store.start_run(conn, folder_id, now_iso())
    run = _Run(conn, folder_id, root, run_id, min_age_s, now_fn)
    log.info("scan: inizio", extra={"scan_run_id": run_id, "folder_id": folder_id, "root": root})
    if not root_readable(root):
        log.warning("scan: radice irraggiungibile", extra={"scan_run_id": run_id, "root": root})
        _finish(run, ScanStatus.ABORTED, ScanReason.ROOT_UNREACHABLE)
        yield _receipt(run, ScanStatus.ABORTED, ScanReason.ROOT_UNREACHABLE)
        return

    status, reason = ScanStatus.OK, None
    try:
        yield from _walk(run)
    except GeneratorExit:
        status, reason = ScanStatus.STOPPED, ScanReason.STOP_REQUESTED
        raise
    except _RootLostError:
        # the root dropped: stop without marking as missing files that are there
        status, reason = ScanStatus.ABORTED, ScanReason.ROOT_UNREACHABLE
        log.warning("scan: radice caduta", extra={"scan_run_id": run_id})
    except Exception as err:
        # a database that does not answer (disk full, busy) is not an unreadable file
        status = ScanStatus.ERROR
        reason = (
            ScanReason.DATABASE_ERROR
            if isinstance(err, sqlite3.Error)
            else ScanReason.INTERNAL_ERROR
        )
        log.exception("scan: errore di sistema", extra={"scan_run_id": run_id})
        raise
    finally:
        # a fault mid-write: if the database answers, the receipt closes anyway
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        _finish(run, status, reason)
        log.info("scan: fine", extra={"scan_run_id": run_id, "status": status, **run.counts})

    yield _receipt(run, status, reason)


def _walk(run: _Run) -> Iterator[Event]:
    online: list[str] = []
    unreadable = run.left_out["unreadable_dirs"]
    files = walk_dir(
        run.root,
        unreadable=unreadable,
        hidden=run.left_out["hidden_dirs"],
        online_only=online,
        linked=run.left_out["linked_dirs"],
    )
    if any(os.path.normpath(d) == os.path.normpath(run.root) for d in unreadable):
        raise _RootLostError  # dropped between the check and the walk
    for dirs in (unreadable, run.left_out["hidden_dirs"], run.left_out["linked_dirs"]):
        # from the root down, like unread files: the receipt already names the folder; a name
        # that is not UTF-8 cannot be written
        dirs[:] = [_shown(rel_path(d, run.root)) for d in dirs]
    total = len(files)
    run.counts["found"] = total + len(online)
    for abs_path in online:
        rel = rel_path(abs_path, run.root)
        _safely(run, rel, partial(_not_on_disk, run, rel))
    for i, abs_path in enumerate(files, start=1):
        rel = rel_path(abs_path, run.root)
        _safely(run, rel, partial(_one_file, run, abs_path, rel))
        yield {
            "current": i,
            "total": total,
            "file": _shown(os.path.basename(abs_path)),
            "run_id": run.run_id,
            "folder_id": run.folder_id,
            **run.counts,
        }
    # Files under a folder that would not open have not vanished: nobody knows. Their positions
    # stay as they were.
    run.counts["missing"] = store.mark_missing(
        run.conn, run.folder_id, run.seen, unreadable, now_iso()
    )


def _shown(name: str) -> str:
    """Python carries the bytes of a non-UTF-8 name as surrogates, which sqlite3 and JSON refuse:
    they become `?`."""
    return name.encode("utf-8", "replace").decode("utf-8")


def _safely(run: _Run, rel: str, work: Callable[[], None]) -> None:
    code = FileError.NAME_NOT_UTF8 if _shown(rel) != rel else _failure(run, work)
    if code is not None:
        _count_error(run, rel, code)


def _failure(run: _Run, work: Callable[[], None]) -> FileError | None:
    """The system says why it cannot open a file with an errno; astropy says "not a FITS" with an
    errno-less `OSError`. A dropped root or a silent database is not a file: it stops the run."""
    try:
        work()
    except (HeaderReadError, OSError) as err:
        cause = err.cause if isinstance(err, HeaderReadError) else err
        if isinstance(cause, OSError) and not root_readable(run.root):
            raise _RootLostError from err  # in the stat or inside the header read
        if isinstance(cause, OSError) and cause.errno is not None:
            return FileError.FILE_UNREADABLE
        return FileError.HEADER_UNREADABLE
    except Exception as err:
        if isinstance(err, sqlite3.Error):
            raise
        # The trace goes to the log once per type: the same fault on a thousand files would fill
        # the log.
        if type(err) not in run.traced:
            run.traced.add(type(err))
            log.exception("scan: errore imprevisto", extra={"scan_run_id": run.run_id})
        return FileError.INTERNAL_ERROR
    return None


def _not_on_disk(run: _Run, rel: str) -> None:
    """Opening an online-only FITS would download it. If it was already archived it has not
    vanished: it is there, only not on disk."""
    run.counts["online_only"] += 1
    pos = store.position(run.conn, run.folder_id, rel)
    if pos is not None:
        run.seen.add(rel)
        if pos["status"] != "present":
            store.set_position_present(run.conn, pos["id"], now_iso())


def _count_error(run: _Run, rel: str, code: FileError) -> None:
    run.counts["errors"] += 1
    run.errors.append({"file": _shown(rel), "reason": code})
    # a name that cannot be written has no position, and asking the DB with it would fail
    if code != FileError.NAME_NOT_UTF8 and store.position(run.conn, run.folder_id, rel) is not None:
        run.seen.add(rel)  # the file is there even if unreadable: not missing
    log.warning(
        "scan: file non letto",
        extra={"scan_run_id": run.run_id, "file": _shown(rel), "error": code},
    )


def _one_file(run: _Run, abs_path: str, rel: str) -> None:
    conn = run.conn
    st = os.stat(long_path(abs_path))
    size, mtime = st.st_size, st.st_mtime
    pos = store.position(conn, run.folder_id, rel)
    now = now_iso()
    if is_unchanged(pos, size, mtime):
        run.seen.add(rel)
        run.counts["unchanged"] += 1
        if pos["status"] != "present":
            store.set_position_present(conn, pos["id"], now)
        return
    if run.now_fn() - mtime < run.min_age_s:
        _skip(run, rel, SkipReason.STILL_WRITING, pos)
        return
    header, block = read_frame(long_path(abs_path))
    if os.stat(long_path(abs_path)).st_size != size:
        _skip(run, rel, SkipReason.STILL_WRITING, pos)  # grew while being read
        return
    fields = extract_fields(header, abs_path)
    kind = fields.image_type
    if kind in CALIBRATION_TYPES or kind == FrameType.STACK:
        why = SkipReason.STACK if kind == FrameType.STACK else SkipReason.CALIBRATION
        _skip(run, rel, why, pos)
        return
    # A typeless file in a folder the user called calibration is skipped like a calibration; one
    # already a frame still enters, or after a move it would look vanished and keep its hours.
    folder_says = typeless.answer_at(conn, run.root, rel) if kind == FrameType.UNKNOWN else None
    fingerprint = frame_fingerprint(long_path(abs_path), header, block)
    if folder_says == typeless.CALIBRATION and store.frame_id_by_hash(conn, fingerprint) is None:
        _skip(run, rel, SkipReason.CALIBRATION, pos)
        return
    with transaction(conn):
        frame_id = store.frame_id_by_hash(conn, fingerprint)
        if frame_id is None:
            columns = asdict(fields)
            night = night_of(conn, columns, mtime)
            judged = {**columns, **header_asks.of(columns)}
            new = store.NewFrame(judged, fingerprint, header_to_json(header), night)
            frame_id = store.insert_frame(conn, new, now)
            run.counts["new"] += 1
        elif pos is not None and pos["frame_id"] == frame_id:
            run.counts["unchanged"] += 1  # touched on disk (the header, perhaps), same pixels
        else:
            run.counts["duplicates"] += 1
        store.upsert_position(conn, frame_id, run.folder_id, rel, size, mtime, now)
    run.seen.add(rel)


def night_of(conn: sqlite3.Connection, fields: Mapping[str, Any], mtime: float) -> store.LocalNight:
    """Written on entry, by the rules of `clock.night_date` and `place.timezone_of_frame`."""
    zone = timezone_of_frame(
        fields.get("site_lat"), fields.get("site_lon"), store.home_timezone(conn)
    )
    instant = night_instant(fields.get("date_obs"), mtime)
    return store.LocalNight(night_date(instant, zone), zone, instant)


def _skip(run: _Run, rel: str, why: SkipReason, pos: sqlite3.Row | None) -> None:
    """Counted by reason, not by name."""
    run.counts["skipped"] += 1
    skipped = run.left_out["skipped_by_reason"]
    entry = next((e for e in skipped if e["reason"] == why), None)
    if entry is None:
        entry = {"reason": why, "count": 0}
        skipped.append(entry)
    entry["count"] += 1
    if pos is not None:
        run.seen.add(rel)
