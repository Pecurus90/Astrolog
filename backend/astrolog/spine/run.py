"""Which stages run and in what order; stages do not know each other. A stage is `(name, factory)`:
the factory opens and closes its own connection."""

import sqlite3
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

from ..db.connect import connect
from ..db.transaction import transaction
from . import typeless_answer
from .group import group_frames
from .identify import identify_frames
from .normalize import normalize_frames
from .scan import scan_folder
from .scan_store import COUNTS, ScanStatus
from .solve import solve_frames
from .stage_run import Event, Factory, receipt
from .stages import StageName, downstream

ORDER = (
    StageName.SCAN,
    StageName.NORMALIZE,
    StageName.SOLVE,
    StageName.IDENTIFY,
    StageName.GROUP,
)

type Work = Callable[[sqlite3.Connection], Iterable[Event]]
type OnFolder = Callable[[int, int], object]


def _with_conn(db_path: str | Path, work: Work) -> Factory:
    def factory() -> Generator[Event]:
        conn = connect(db_path, check_same_thread=False)
        try:
            yield from work(conn)
        finally:
            conn.close()

    return factory


def _detach_waiting(conn: sqlite3.Connection) -> None:
    """Here because the scan cannot reach the other stages' stores."""
    with transaction(conn):
        typeless_answer.detach_waiting(conn)


def _then_detach(conn: sqlite3.Connection, events: Iterable[Event]) -> Iterator[Event]:
    """The detach runs before `done` (`stage_run.receipt`)."""
    for event in events:
        if event.get("done"):
            _detach_waiting(conn)
        yield event


def _then_normalize(conn: sqlite3.Connection, events: Iterable[Event]) -> Iterator[Event]:
    """The frames the sky sent back to `normalize` (ADR 0016) are redone before `done`: `normalize`
    already ran in this queue, and `identify` waits for it."""
    for event in events:
        if event.get("done"):
            for _ in normalize_frames(conn):
                pass
        yield event


def queue(
    db_path: str | Path,
    stages: Iterable[StageName],
    *,
    folder_id: int | None = None,
    run_id: int | None = None,
    on_folder: OnFolder | None = None,
) -> list[tuple[StageName, Factory]]:
    """The only door: callers say what they need, never the order. Who pulls whom is the graph's
    (`stages.downstream`), so an answer on a filter also requeues names and nights."""
    asked = set(stages)
    jobs: dict[StageName, Work] = {
        StageName.NORMALIZE: normalize_frames,
        StageName.SOLVE: lambda c: _then_normalize(c, solve_frames(c)),
        StageName.IDENTIFY: identify_frames,
        StageName.GROUP: group_frames,
    }
    unknown = asked - set(jobs) - {StageName.SCAN}
    if unknown:  # a stage without work is the caller's mistake, not a shorter queue
        raise ValueError(f"stadi che non esistono: {sorted(map(str, unknown))}")
    if StageName.SCAN in asked:
        if folder_id is None or run_id is None:
            # later it would break inside the generator, in the worker thread, silently
            raise ValueError("scan vuole folder_id e run_id")
        jobs[StageName.SCAN] = lambda c: _then_detach(c, _scan_one(c, folder_id, run_id, on_folder))
    # `measure` is in the graph but has no work yet
    wanted = asked | {d for s in asked for d in downstream(s) if d in jobs}
    return [(s, _with_conn(db_path, jobs[s])) for s in ORDER if s in wanted]


def _scan_one(
    conn: sqlite3.Connection, folder_id: int, run_id: int, on_folder: OnFolder | None
) -> Iterator[Event]:
    if on_folder is not None:
        on_folder(folder_id, run_id)
    yield from scan_folder(conn, folder_id, run_id=run_id)


def queue_folders(
    db_path: str | Path,
    folders: Sequence[tuple[int, int]],
    *,
    on_folder: OnFolder | None = None,
) -> list[tuple[StageName, Factory]]:
    """One `scan` stage reading the `(folder_id, run_id)` pairs in turn, then the chain once: what
    follows works on the database, which knows nothing of folders. `on_folder` precedes each."""
    if not folders:
        raise ValueError("nessuna cartella da leggere")

    def all_folders(conn: sqlite3.Connection) -> Iterator[Event]:
        # one `done` only, after all folders
        counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
        errors: list[dict[str, Any]] = []
        outcomes: list[tuple[Any, Any]] = []
        for folder_id, run_id in folders:
            for event in _scan_one(conn, folder_id, run_id, on_folder):
                if not event.get("done"):
                    yield event
                    continue
                # only the counts: `done` is an int too, and would sum to "done: 2"
                for key in COUNTS:
                    counts[key] += event.get(key, 0)
                errors.extend(event.get("errors_detail", []))
                outcomes.append((event.get("status"), event.get("reason")))
        # ok only if every folder was: a folder dying mid-run must not read as "done"
        failed = [e for e in outcomes if e[0] != ScanStatus.OK]
        status, reason = failed[0] if failed else (ScanStatus.OK, None)
        _detach_waiting(conn)
        yield receipt(status, reason, counts, errors)

    after = [s for s in ORDER if s != StageName.SCAN]
    return [(StageName.SCAN, _with_conn(db_path, all_folders)), *queue(db_path, after)]
