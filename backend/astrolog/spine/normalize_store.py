"""The writes of `normalize`: static queries, no decisions. Creating a piece, a filter or a rig
lives in `gear_create` and `rigs`, because hand-written answers need them too."""

import sqlite3
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from ..db import idlist
from . import counts
from .rewrite import RewriteMark


def frame(conn: sqlite3.Connection, frame_id: int) -> sqlite3.Row:
    return conn.execute("SELECT * FROM frames WHERE id = ?", (frame_id,)).fetchone()


def none_filter_id(conn: sqlite3.Connection) -> int | None:
    """Found by `is_none`, not by name: the user may have renamed it."""
    row = conn.execute("SELECT id FROM filters WHERE is_none = 1").fetchone()
    return None if row is None else row["id"]


# One row per camera and per what its files say. Every camera is there, even with no frames, so it
# can forget what they said; rewritten copies are not another frame and do not vote.
_CAMERA_VOTES = """
SELECT i.id AS camera_id, i.name AS camera, f.pixel_size_um, f.binning,
       f.bayer_pattern IS NOT NULL AS color, COUNT(f.id) AS n
FROM instruments i
LEFT JOIN rigs r ON r.camera_id = i.id
LEFT JOIN frames f ON f.rig_id = r.id AND f.copy_of IS NULL AND f.id NOT IN {listed}
WHERE i.kind = 'camera'
GROUP BY i.id, f.pixel_size_um, f.binning, color
"""


def camera_votes(conn: sqlite3.Connection, leaving_out: Iterable[int] = ()) -> list[sqlite3.Row]:
    """`leaving_out` are the frames that do not vote with the rig they have now."""
    with idlist.holding(conn, leaving_out) as listed:
        return conn.execute(_CAMERA_VOTES.format(listed=listed)).fetchall()


def camera_colours(conn: sqlite3.Connection) -> dict[int, tuple[str, str | None]]:
    """`{camera id: (name, voted colour)}`, read before a new vote rewrites it."""
    rows = conn.execute("SELECT id, name, camera_type FROM instruments WHERE kind = 'camera'")
    return {r["id"]: (r["name"], r["camera_type"]) for r in rows}


def set_camera_specs(
    conn: sqlite3.Connection, camera_id: int, camera_type: str | None, pixel_size_um: float | None
) -> None:
    conn.execute(
        "UPDATE instruments SET camera_type = ?, pixel_size_um = ?"
        " WHERE id = ? AND (camera_type IS NOT ? OR pixel_size_um IS NOT ?)",
        (camera_type, pixel_size_um, camera_id, camera_type, pixel_size_um),
    )


# Every frame claiming to be the same shot as one given (date, camera, exposure). One without all
# three has no brood: `NULL = NULL` would tie real frames together.
_BROODS = """
SELECT f.id, f.date_obs, f.instrument_raw, f.exposure_s, f.software_raw, f.header_json, f.copy_of
FROM frames f JOIN (
    SELECT DISTINCT date_obs, instrument_raw, exposure_s FROM frames WHERE id IN {listed}
    AND date_obs IS NOT NULL AND instrument_raw IS NOT NULL AND exposure_s IS NOT NULL
) k ON f.date_obs = k.date_obs AND f.instrument_raw = k.instrument_raw
   AND f.exposure_s = k.exposure_s
ORDER BY f.date_obs, f.instrument_raw, f.exposure_s
"""


def broods(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> Iterator[sqlite3.Row]:
    """Row by row, so the headers of the whole queue are never in memory together; the id list
    stays held until the reading ends."""
    with idlist.holding(conn, frame_ids) as listed:
        yield from conn.execute(_BROODS.format(listed=listed))


def pending_focals(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> list[float | None]:
    with idlist.holding(conn, frame_ids) as listed:
        return [
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT focal_mm_raw FROM frames WHERE id IN {listed}"  # noqa: S608
            )
        ]


@dataclass(frozen=True, slots=True)
class Normalized:
    """What `normalize` writes on a frame. `on_frame` holds the carried instruments by kind; column
    `<kind>_id`, kinds from `counts.CARRIED`."""

    filter_id: int | None
    rig_id: int | None
    software: str | None
    copy_of: int | None
    rewrite_mark: RewriteMark | None
    on_frame: Mapping[str, int | None]


def set_normalized(conn: sqlite3.Connection, frame_id: int, row: Normalized) -> None:
    columns = "".join(f", {k}_id = ?" for k in counts.CARRIED)
    # kinds are ours, never user values
    conn.execute(
        "UPDATE frames SET filter_id = ?, rig_id = ?, software = ?, copy_of = ?,"  # noqa: S608
        f" rewrite_mark = ?{columns} WHERE id = ?",
        (
            row.filter_id,
            row.rig_id,
            row.software,
            row.copy_of,
            row.rewrite_mark,
            *(row.on_frame[k] for k in counts.CARRIED),
            frame_id,
        ),
    )
