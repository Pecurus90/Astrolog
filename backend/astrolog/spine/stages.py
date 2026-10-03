"""Each frame's status in each stage, and the graph of who depends on whom. Resuming means "what is
missing"; `running` never reaches the DB, so a dead process leaves no stuck rows."""

import sqlite3
from collections.abc import Collection, Iterable

from ..clock import now_iso
from ..fits.frame_type import UNKNOWN
from . import declarations as decl
from . import frame_folder as folder

STAGES = ("solve", "normalize", "identify", "group", "measure")
STATUSES = ("pending", "done", "failed", "skipped")

# stage -> the stages it needs
DEPENDS = {
    "solve": (),
    "normalize": (),
    "identify": ("solve", "normalize"),
    "group": ("normalize", "identify"),
    "measure": ("solve",),
}


def downstream(stage: str) -> tuple[str, ...]:
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
SETTLED = {("identify", "solve"): ("done", "failed"), ("group", "identify"): ("done", "skipped")}

# An unknown-type frame waits before `identify` until a solved sky or a folder `light` answer frees
# it (a `calibration` answer keeps it waiting), or a dark would become hours.
WAITING_FROM = "identify"
WAITING_STAGES = frozenset(downstream("solve")) - {"solve"}


# read once per frame: composing the key is the costly part
FOLDER_SAYS = f"""(
  SELECT dc.value FROM declarations dc WHERE dc.entity_type = '{decl.FOLDER}'
    AND dc.field = '{decl.FOLDER_TYPE}' AND dc.entity_key = ({folder.KEY_OF_FRAME}))"""  # noqa: S608
# solved and with the sky still there: a detach keeps the stage done, and `identify` would name the
# frame from its header
_SKY_SOLVED = """(EXISTS (
  SELECT 1 FROM frame_stages sv WHERE sv.frame_id = f.id AND sv.stage = 'solve'
    AND sv.status = 'done') AND EXISTS (SELECT 1 FROM frame_wcs w WHERE w.frame_id = f.id))"""
WAITING_RULE = f"""
f.image_type = '{UNKNOWN}' AND CASE {FOLDER_SAYS}
  WHEN '{decl.TYPE_LIGHT}' THEN 0 WHEN '{decl.TYPE_CALIBRATION}' THEN 1 ELSE NOT {_SKY_SOLVED} END
"""  # noqa: S608 - spine constants, no user values
# a mark on the frame, since `invalidate` resets stage rows: whoever changes an input of the rule
# calls `refresh_waiting` at once, or a stale 0 sends a typeless dark to `identify`
WAITING_SQL = "f.asks_type = 1"
_REFRESH = f"UPDATE frames AS f SET asks_type = ({WAITING_RULE})"  # noqa: S608 - constants


def refresh_waiting(conn: sqlite3.Connection, frame_ids: Iterable[int] | None = None) -> None:
    """Without ids every typeless frame: a changed answer or folder can touch any of them."""
    if frame_ids is None:
        conn.execute(_REFRESH + " WHERE f.image_type = ?", (UNKNOWN,))
    else:
        conn.executemany(_REFRESH + " WHERE f.id = ?", [(i,) for i in frame_ids])


def ready(
    conn: sqlite3.Connection, stage: str, limit: int | None = None, frame_id: int | None = None
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
        settled = SETTLED.get((stage, dep), ("done",))
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
    stage: str,
    status: str,
    reason: str | None = None,
    now: str | None = None,
) -> None:
    if status not in STATUSES:
        raise ValueError(f"stato sconosciuto: {status}")
    conn.execute(
        "INSERT INTO frame_stages(frame_id, stage, status, reason, updated_at)"
        " VALUES(?, ?, ?, ?, ?)"
        " ON CONFLICT(frame_id, stage) DO UPDATE SET status = excluded.status,"
        " reason = excluded.reason, updated_at = excluded.updated_at",
        (frame_id, stage, status, reason, now or now_iso()),
    )
    if stage == "solve":
        refresh_waiting(conn, [frame_id])


def invalidate(
    conn: sqlite3.Connection, frame_ids: Collection[int], from_stage: str, now: str | None = None
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
    if "solve" in stages:
        refresh_waiting(conn, frame_ids)


# The same predicate as `WAITING_SQL`, or `ready` and this count would disagree and the residue
# never reach zero. `CROSS JOIN` starts from the marked frames, not from every queued stage row.
_WAITING_BY_STAGE = f"""
SELECT s.stage, COUNT(*) FROM frames f CROSS JOIN frame_stages s ON s.frame_id = f.id
WHERE {WAITING_SQL} AND s.status = 'pending' GROUP BY s.stage
"""  # noqa: S608 - the same constant fragment


def _waiting_by_stage(conn: sqlite3.Connection) -> dict[str, int]:
    return {r[0]: r[1] for r in conn.execute(_WAITING_BY_STAGE)}


def count_pending(conn: sqlite3.Connection, stage: str) -> int:
    """Frames waiting for an answer are not work: counted, the residue would never reach zero and
    every run would restart for nothing."""
    quanti = conn.execute(
        "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'pending'", (stage,)
    ).fetchone()[0]
    if stage not in WAITING_STAGES:
        return quanti
    return quanti - _waiting_by_stage(conn).get(stage, 0)


def pending_by_stage(conn: sqlite3.Connection) -> dict[str, int]:
    """Pending per stage minus the frames waiting for an answer, these read in one query for all
    stages instead of one per stage."""
    totali = {
        s: conn.execute(
            "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'pending'", (s,)
        ).fetchone()[0]
        for s in STAGES
    }  # five counts on the `frame_stages_pending` index, not one GROUP BY sweep
    aspettano = _waiting_by_stage(conn)
    return {s: totali[s] - (aspettano.get(s, 0) if s in WAITING_STAGES else 0) for s in STAGES}
