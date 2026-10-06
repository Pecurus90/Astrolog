"""The user's answer on a typeless folder: what it requeues and what it detaches. Apart from the
question because the scan reads the question, and must not reach the stores of other stages."""

import sqlite3

from ..db.row import Row
from ..fits.frame_type import FrameType
from . import (
    camera_sky,
    gear_usage,
    group_store,
    identify_store,
    mosaic,
    object_candidates,
    solve_store,
    typeless,
    typeless_folders,
)
from . import frame_folder as folder
from .declarations import TypeAnswer
from .stages import FOLDER_SAYS, WAITING_FROM, WAITING_SQL, StageName, invalidate


def detach(conn: sqlite3.Connection, frame_ids: list[int]) -> None:
    """Object, night, session, measured sky and mosaic panel. The stages that would redo them no
    longer take these frames, so without this their hours would stay for good."""
    if not frame_ids:
        return
    identify_store.detach(conn, frame_ids)
    group_store.detach(conn, frame_ids)
    # The solver looks for a sky already found for the same `OBJECT`: a calibration frame keeping
    # its WCS would go on telling the others where to point.
    solve_store.detach(conn, frame_ids)
    # without a sky the frame is in no panel or mosaic, and the mosaics it leaves are reweighed
    mosaic.settle(conn, mosaic.leave(conn, frame_ids))


def apply_answer(
    conn: sqlite3.Connection, row: Row, now: str | None = None, *, rewrite: bool = True
) -> list[int]:
    """Returns the requeued frames. "Photos" go on, and those an earlier "calibration" detached go
    back to the sky, which restores it from its cache; "calibration" stops and detaches them."""
    # `rewrite=False` leaves the derived tables to one `rewrite_derived` after many answers
    frames = typeless.frames_of(conn, row)
    if row["answer"] == TypeAnswer.LIGHT:
        invalidate(conn, solve_store.lost_sky(conn, frames), StageName.SOLVE, now)
    else:
        _stop(conn, frames, now, rewrite=rewrite)
    return frames


# What it carries, not the state of `identify`: an `invalidate` meanwhile makes it pending without
# detaching anything. Without a live folder nothing is detached: nobody could answer.
_WAITING_AND_ATTACHED = f"""
SELECT f.id FROM frames f
WHERE {WAITING_SQL} AND (f.object_id IS NOT NULL OR f.night_id IS NOT NULL)
  AND ({folder.KEY_OF_FRAME}) IS NOT NULL
"""  # noqa: S608 - constant fragments of the spine


# Lost its sky to a detach, in a live folder not answered "calibration": only the solver's cache
# puts it back. Without a live folder, or in one answered "calibration", it stays as it is.
_TYPELESS = f"SELECT f.id FROM frames f WHERE f.image_type = '{FrameType.UNKNOWN}'"  # noqa: S608 - constants
_LET_GO = (
    f"SELECT ({folder.KEY_OF_FRAME}) IS NOT NULL"  # noqa: S608 - constant fragments of the spine
    f" AND IFNULL({FOLDER_SAYS}, '') <> '{TypeAnswer.CALIBRATION}' FROM frames f WHERE f.id = ?"
)


def detach_waiting(conn: sqlite3.Connection, now: str | None = None) -> tuple[list[int], list[int]]:
    """For whoever changes a frame's folder: it reads the waiting mark they already rewrote.
    Returns the frames stopped and detached, and those requeued from the sky."""
    frames = [r[0] for r in conn.execute(_WAITING_AND_ATTACHED)]
    if frames:
        _stop(conn, frames, now)
    lost = solve_store.lost_sky(conn, [r[0] for r in conn.execute(_TYPELESS)])
    requeued = [i for i in lost if conn.execute(_LET_GO, (i,)).fetchone()[0]]
    invalidate(conn, requeued, StageName.SOLVE, now)
    typeless_folders.write(conn)
    return frames, requeued


def _stop(
    conn: sqlite3.Connection, frames: list[int], now: str | None, *, rewrite: bool = True
) -> None:
    invalidate(conn, frames, WAITING_FROM, now)
    detach(conn, frames)
    if rewrite:
        rewrite_derived(conn)


def rewrite_derived(conn: sqlite3.Connection) -> None:
    """No stage works stopped frames any more, so the derived tables they moved are rewritten
    here: whole, so once after many answers gives what once per answer gave."""
    camera_sky.write(conn)
    gear_usage.write(conn)
    object_candidates.write(conn)
