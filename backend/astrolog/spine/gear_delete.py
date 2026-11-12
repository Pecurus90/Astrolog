"""Deleting a piece or a filter (docs/domini/attrezzatura.md): only one without frames, so no
hour is lost. A chosen part leaves its rigs; the optics or camera of a rig stays."""

import sqlite3

from ..db import idlist
from . import counts, gear_usage
from .declarations import instrument_key
from .rigs import PART_FIELDS, SPACER_FIELD


class InUseError(ValueError):
    """Frames carry it: the route says how many and of which rigs."""

    def __init__(self, frames: int, rigs: list[int]) -> None:
        super().__init__(f"{frames} frame")
        self.frames = frames
        self.rigs = rigs


class InRigError(ValueError):
    """The optics or camera of a rig without frames: the rig is made of it."""

    def __init__(self, rigs: list[int]) -> None:
        super().__init__(f"setup {rigs}")
        self.rigs = rigs


def _users(conn: sqlite3.Connection, frame_ids: set[int]) -> InUseError:
    """Counted as the page counts them, written copies out; refused even on copies alone."""
    with idlist.holding(conn, frame_ids) as listed:
        originals = conn.execute(
            f"SELECT id, rig_id FROM frames WHERE id IN {listed} AND copy_of IS NULL"  # noqa: S608
        ).fetchall()
    rigs = sorted({r["rig_id"] for r in originals if r["rig_id"] is not None})
    return InUseError(len(originals), rigs)


def _instrument_frames(conn: sqlite3.Connection, instrument_id: int) -> set[int]:
    """Every frame holding it, copies too, by the link the hours use: through the rig, the
    columns the frame carries, and the spacers its rig mounts."""
    return {
        r[0]
        for r in conn.execute(
            f"SELECT frame FROM ({counts.PIECE_FRAMES}) WHERE piece = ?",  # noqa: S608
            (instrument_id,),
        )
    }


def delete_instrument(conn: sqlite3.Connection, instrument_id: int) -> None:
    """Its card and its choices on the rigs go with it: born again with the name, it starts empty.
    Raises LookupError, InUseError, InRigError."""
    row = conn.execute(
        "SELECT kind, name FROM instruments WHERE id = ?", (instrument_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"pezzo {instrument_id}")
    frames = _instrument_frames(conn, instrument_id)
    if frames:
        raise _users(conn, frames)
    holding = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM rigs WHERE optics_id = ? OR camera_id = ? ORDER BY id",
            (instrument_id, instrument_id),
        )
    ]
    if holding:
        raise InRigError(holding)
    conn.execute(
        "DELETE FROM declarations WHERE entity_type = 'instrument' AND entity_key = ?",
        (instrument_key(row["kind"], row["name"]),),
    )
    if row["kind"] in PART_FIELDS:
        conn.execute(
            "DELETE FROM declarations WHERE entity_type = 'rig' AND field = ? AND value = ?",
            (row["kind"], row["name"]),
        )
    conn.execute(
        "DELETE FROM declarations WHERE entity_type = 'rig' AND field = ?",
        (SPACER_FIELD + row["name"],),
    )
    _drop(conn, "instrument", "instruments", instrument_id)


def delete_filter(conn: sqlite3.Connection, filter_id: int) -> None:
    """ "No filter" is not a filter you own: not found. Raises LookupError, InUseError."""
    row = conn.execute(
        "SELECT id FROM filters WHERE id = ? AND is_none = 0", (filter_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"filtro {filter_id}")
    frames = {r[0] for r in conn.execute("SELECT id FROM frames WHERE filter_id = ?", (filter_id,))}
    if frames:
        raise _users(conn, frames)
    _drop(conn, "filter", "filters", filter_id)


def _drop(conn: sqlite3.Connection, subject: str, table: str, row_id: int) -> None:
    """The derived rows go too, and the rigs' parts and numbers are written again."""
    conn.execute("DELETE FROM gear_usage WHERE subject = ? AND subject_id = ?", (subject, row_id))
    conn.execute("DELETE FROM gear_numbers WHERE subject = ? AND subject_id = ?", (subject, row_id))
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))  # noqa: S608 - our two tables
    gear_usage.write_bars(conn)
    gear_usage.write_parts(conn)
