"""Each frame's status in each stage, and the graph of who depends on whom. Resuming means "what is
missing"; `running` never reaches the DB, so a dead process leaves no stuck rows."""

import sqlite3
from collections.abc import Collection, Iterable
from enum import StrEnum

from ..clock import now_iso
from . import declarations as decl
from . import frame_folder as folder


class StageName(StrEnum):
    """What the worker runs. `scan` reads folders and has no row in `frame_stages`."""

    SCAN = "scan"
    SOLVE = "solve"
    NORMALIZE = "normalize"
    IDENTIFY = "identify"
    GROUP = "group"
    MEASURE = "measure"


# The stages with a row per frame, the words of the `frame_stages.stage` CHECK.
STAGES = (
    StageName.SOLVE,
    StageName.NORMALIZE,
    StageName.IDENTIFY,
    StageName.GROUP,
    StageName.MEASURE,
)


class StageStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


# stage -> the stages it needs
DEPENDS: dict[StageName, tuple[StageName, ...]] = {
    StageName.SOLVE: (),
    StageName.NORMALIZE: (),
    StageName.IDENTIFY: (StageName.SOLVE, StageName.NORMALIZE),
    StageName.GROUP: (StageName.NORMALIZE, StageName.IDENTIFY),
    StageName.MEASURE: (StageName.SOLVE,),
}


def downstream(stage: StageName) -> tuple[StageName, ...]:
    """The stage and every stage that depends on it, directly or not."""
    out, frontier = {stage}, [stage]
    while frontier:
        s = frontier.pop()
        for other, needs in DEPENDS.items():
            if s in needs and other not in out:
                out.add(other)
                frontier.append(other)
    return tuple(s for s in STAGES if s in out)


# `identify` takes a frame the solver gave up on, not one it will retry; `group` stops frames
# `identify` skipped with their reason, else they stay pending and the residue never reaches zero.
SETTLED = {
    (StageName.IDENTIFY, StageName.SOLVE): (StageStatus.DONE, StageStatus.FAILED),
    (StageName.GROUP, StageName.IDENTIFY): (StageStatus.DONE, StageStatus.SKIPPED),
}

# An unknown-type frame waits before `identify` until a solved sky or a folder `light` answer frees
# it (a `calibration` answer keeps it waiting), or a dark would become hours.
WAITING_FROM = StageName.IDENTIFY
WAITING_STAGES = frozenset(downstream(StageName.SOLVE)) - {StageName.SOLVE}


# The answer of a frame's folder; the waiting rule itself is the `frame_waits` view in `schema.sql`.
FOLDER_SAYS = f"""(
  SELECT dc.value FROM declarations dc WHERE dc.entity_type = '{decl.FOLDER}'
    AND dc.field = '{decl.FOLDER_TYPE}'
    AND dc.entity_key = ({folder.KEY_OF_FRAME}))"""  # noqa: S608 - constants
# a mark on the frame, since `invalidate` resets stage rows; the schema's triggers rewrite it on
# every write to an input of the rule
WAITING_SQL = "f.asks_type = 1"


def ready(
    conn: sqlite3.Connection,
    stage: StageName,
    limit: int | None = None,
    frame_id: int | None = None,
) -> list[int]:
    """Settled upstream, oldest first; in `WAITING_STAGES` none waiting for a type. `frame_id` asks
    if that one is still ready: removing a folder mid-run can send it back."""
    needs = DEPENDS[stage]
    sql = (
        "SELECT s.frame_id FROM frame_stages s JOIN frames f ON f.id = s.frame_id"
        " WHERE s.stage = ? AND s.status = 'pending'"
    )
    args: list[str | int] = [stage]
    if frame_id is not None:
        sql += " AND s.frame_id = ?"
        args.append(frame_id)
    if stage in WAITING_STAGES:
        sql += f" AND NOT ({WAITING_SQL})"
    for dep in needs:
        settled = SETTLED.get((stage, dep), (StageStatus.DONE,))
        marks = ",".join("?" * len(settled))  # segnaposto-ok: two statuses, not one per frame
        # S608: only placeholders, the statuses are bound
        sql += (
            " AND EXISTS (SELECT 1 FROM frame_stages d WHERE d.frame_id = s.frame_id"  # noqa: S608
            f" AND d.stage = ? AND d.status IN ({marks}))"
        )
        args.append(dep)
        args.extend(settled)
    sql += " ORDER BY f.id"
    if limit is not None:
        sql += " LIMIT ?"
        args.append(limit)
    return [r[0] for r in conn.execute(sql, args)]


def mark_pending(conn: sqlite3.Connection, frame_id: int, now: str | None = None) -> None:
    now = now or now_iso()
    conn.executemany(
        "INSERT OR IGNORE INTO frame_stages(frame_id, stage, status, updated_at)"
        " VALUES(?, ?, 'pending', ?)",
        [(frame_id, s, now) for s in STAGES],
    )


def set_status(  # noqa: PLR0913
    conn: sqlite3.Connection,
    frame_id: int,
    stage: StageName,
    status: StageStatus,
    reason: str | None = None,
    now: str | None = None,
) -> None:
    if status not in StageStatus:
        raise ValueError(f"stato sconosciuto: {status}")
    conn.execute(
        "INSERT INTO frame_stages(frame_id, stage, status, reason, updated_at)"
        " VALUES(?, ?, ?, ?, ?)"
        " ON CONFLICT(frame_id, stage) DO UPDATE SET status = excluded.status,"
        " reason = excluded.reason, updated_at = excluded.updated_at",
        (frame_id, stage, status, reason, now or now_iso()),
    )


def invalidate(
    conn: sqlite3.Connection,
    frame_ids: Collection[int],
    from_stage: StageName,
    now: str | None = None,
) -> None:
    """The only way back to `pending`, for the stage and everything downstream: every user
    declaration calls it, and the later stages redo themselves."""
    now = now or now_iso()
    stages = downstream(from_stage)
    conn.executemany(
        "UPDATE frame_stages SET status = 'pending', reason = NULL, updated_at = ?"
        " WHERE frame_id = ? AND stage = ?",
        [(now, frame_id, s) for frame_id in frame_ids for s in stages],
    )


# The same predicate as `WAITING_SQL`, or `ready` and this count would disagree. `CROSS JOIN`
# starts from the marked frames, not from every queued stage row.
_WAITING_BY_STAGE = f"""
SELECT s.stage, COUNT(*) FROM frames f CROSS JOIN frame_stages s ON s.frame_id = f.id
WHERE {WAITING_SQL} AND s.status = 'pending' GROUP BY s.stage
"""  # noqa: S608 - the same constant fragment
_PENDING = "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'pending'"


def _waiting_by_stage(conn: sqlite3.Connection) -> dict[str, int]:
    return {r[0]: r[1] for r in conn.execute(_WAITING_BY_STAGE)}


def count_pending(conn: sqlite3.Connection, stage: StageName) -> int:
    return pending_by_stage(conn, (stage,))[stage]


def pending_by_stage(
    conn: sqlite3.Connection, stages: Iterable[StageName] = STAGES
) -> dict[str, int]:
    """Frames waiting for an answer are not work: counted, the residue would never reach zero and
    every run would restart for nothing."""
    # one count per stage on the `frame_stages_pending` index, not one GROUP BY sweep
    totals = {s: conn.execute(_PENDING, (s,)).fetchone()[0] for s in stages}
    waiting = _waiting_by_stage(conn) if WAITING_STAGES.intersection(totals) else {}
    return {s: n - (waiting.get(s, 0) if s in WAITING_STAGES else 0) for s, n in totals.items()}
