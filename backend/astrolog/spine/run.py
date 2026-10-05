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
from .scan import COUNTS, scan_folder
from .solve import solve_frames
from .stage_run import Event, Factory, receipt
from .stages import downstream

STAGE_SCAN = "scan"
STAGE_NORMALIZE = "normalize"
STAGE_SOLVE = "solve"
STAGE_IDENTIFY = "identify"
STAGE_GROUP = "group"

ORDER = (STAGE_SCAN, STAGE_NORMALIZE, STAGE_SOLVE, STAGE_IDENTIFY, STAGE_GROUP)

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


def _then_detach(conn: sqlite3.Connection, eventi: Iterable[Event]) -> Iterator[Event]:
    """The detach runs before `done`, because the worker stops there."""
    for evento in eventi:
        if evento.get("done"):
            _detach_waiting(conn)
        yield evento


def queue(
    db_path: str | Path,
    stages: Iterable[str],
    *,
    folder_id: int | None = None,
    run_id: int | None = None,
    on_folder: OnFolder | None = None,
) -> list[tuple[str, Factory]]:
    """The only door: callers say what they need, never the order. Who pulls whom is the graph's
    (`stages.downstream`), so an answer on a filter also requeues names and nights."""
    chiesti = set(stages)
    lavoro: dict[str, Work] = {
        STAGE_NORMALIZE: normalize_frames,
        STAGE_SOLVE: solve_frames,
        STAGE_IDENTIFY: identify_frames,
        STAGE_GROUP: group_frames,
    }
    ignoti = chiesti - set(lavoro) - {STAGE_SCAN}
    if ignoti:  # a stage without work is the caller's mistake, not a shorter queue
        raise ValueError(f"stadi che non esistono: {sorted(ignoti)}")
    if STAGE_SCAN in chiesti:
        if folder_id is None or run_id is None:
            # later it would break inside the generator, in the worker thread, silently
            raise ValueError("scan vuole folder_id e run_id")
        lavoro[STAGE_SCAN] = lambda c: _then_detach(c, _scan_one(c, folder_id, run_id, on_folder))
    # `measure` is in the graph but has no work yet
    voluti = chiesti | {d for s in chiesti for d in downstream(s) if d in lavoro}
    return [(s, _with_conn(db_path, lavoro[s])) for s in ORDER if s in voluti]


def _scan_one(
    conn: sqlite3.Connection, folder_id: int, run_id: int, on_folder: OnFolder | None
) -> Iterator[Event]:
    if on_folder is not None:
        on_folder(folder_id, run_id)
    yield from scan_folder(conn, folder_id, run_id=run_id)


def queue_folders(
    db_path: str | Path,
    cartelle: Sequence[tuple[int, int]],
    *,
    on_folder: OnFolder | None = None,
) -> list[tuple[str, Factory]]:
    """One `scan` stage reading the `(folder_id, run_id)` pairs in turn, then the chain once: what
    follows works on the database, which knows nothing of folders. `on_folder` precedes each."""
    if not cartelle:
        raise ValueError("nessuna cartella da leggere")

    def molte(conn: sqlite3.Connection) -> Iterator[Event]:
        # one `done` only, after all folders: the worker stops at the first one it sees
        conti: dict[str, int] = dict.fromkeys(COUNTS, 0)
        errori: list[dict[str, Any]] = []
        esiti: list[tuple[Any, Any]] = []
        for folder_id, run_id in cartelle:
            for evento in _scan_one(conn, folder_id, run_id, on_folder):
                if not evento.get("done"):
                    yield evento
                    continue
                # only the counts: `done` is an int too, and would sum to "done: 2"
                for chiave in COUNTS:
                    conti[chiave] += evento.get(chiave, 0)
                errori.extend(evento.get("errors_detail", []))
                esiti.append((evento.get("status"), evento.get("reason")))
        # ok only if every folder was: a folder dying mid-run must not read as "done"
        storte = [e for e in esiti if e[0] != "ok"]
        stato, motivo = storte[0] if storte else ("ok", None)
        _detach_waiting(conn)
        yield receipt(stato, motivo, conti, errori)

    dopo = [s for s in ORDER if s != STAGE_SCAN]
    return [(STAGE_SCAN, _with_conn(db_path, molte)), *queue(db_path, dopo)]
