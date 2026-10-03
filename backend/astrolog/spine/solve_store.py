"""The queries of the `solve` stage, all static: no decision lives here, so `solve.py` reads
without opening this file."""

import sqlite3
from collections.abc import Collection, Iterable

from ..db import idlist


def frame(conn: sqlite3.Connection, frame_id: int) -> sqlite3.Row:
    """With its first present position; all `missing` gives a `None` path: a detached disk, not
    an error."""
    return conn.execute(
        "SELECT f.*,"
        " (SELECT d.root_path FROM positions p JOIN folders d ON d.id = p.folder_id"
        "   WHERE p.frame_id = f.id AND p.status = 'present' ORDER BY p.id LIMIT 1) AS root_path,"
        " (SELECT p.rel_path FROM positions p"
        "   WHERE p.frame_id = f.id AND p.status = 'present' ORDER BY p.id LIMIT 1) AS rel_path"
        " FROM frames f WHERE f.id = ?",
        (frame_id,),
    ).fetchone()


# Not the glossary's session (that is `group`'s): only a queue, so the raw object is enough and
# `M31` vs `M 31` costs one more solve. The night is `scan`'s, the same as `clock.night_date`.
SOLVE_ORDER_KEY = (
    "COALESCE(object_raw, '') || '|' || COALESCE(local_night, '')"
    " || '|' || COALESCE(telescope_raw, '') || '|' || COALESCE(instrument_raw, '')"
)


def first_per_order_key(conn: sqlite3.Connection, frame_ids: Collection[int]) -> list[int]:
    if not frame_ids:
        return []
    with idlist.holding(conn, frame_ids) as listed:
        return [
            r[0]
            for r in conn.execute(
                # S608: `listed` is `idlist.IN_LIST` and the key is this module's constant
                f"SELECT MIN(id) FROM frames WHERE id IN {listed}"  # noqa: S608
                f" GROUP BY {SOLVE_ORDER_KEY}"
            )
        ]


def newest_first(conn: sqlite3.Connection, frame_ids: Collection[int]) -> list[int]:
    """Undated frames go last: they are not pretended to be today's."""
    if not frame_ids:
        return []
    with idlist.holding(conn, frame_ids) as listed:
        return [
            r[0]
            for r in conn.execute(
                # S608: `listed` is `idlist.IN_LIST`, not a user value
                f"SELECT id FROM frames WHERE id IN {listed}"  # noqa: S608
                " ORDER BY date_obs IS NULL, date_obs DESC, id DESC"
            )
        ]


def sister_solution(conn: sqlite3.Connection, frame: sqlite3.Row) -> sqlite3.Row | None:
    """By named object, not by session: a session key with empty pieces would join two frames
    without `OBJECT` pointing at different places, and send the solver to the wrong one."""
    if not frame["object_raw"]:
        return None
    return conn.execute(
        "SELECT w.ra_deg, w.dec_deg FROM frame_wcs w JOIN frames f ON f.id = w.frame_id"
        " WHERE f.object_raw = ? AND f.id != ? LIMIT 1",
        (frame["object_raw"], frame["id"]),
    ).fetchone()


def has_metrics(conn: sqlite3.Connection, frame_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT 1 FROM frame_metrics WHERE frame_id = ?", (frame_id,)).fetchone()


def save_wcs(  # noqa: PLR0913
    conn: sqlite3.Connection,
    frame_id: int,
    *,
    ra_deg: float | None,
    dec_deg: float | None,
    scale: float | None,
    rotation: float | None,
    width: float | None,
    height: float | None,
    now: str,
) -> None:
    conn.execute(
        "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, rotation_deg,"
        " width_deg, height_deg, solved_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(frame_id) DO UPDATE SET ra_deg = excluded.ra_deg,"
        " dec_deg = excluded.dec_deg, scale_arcsec_px = excluded.scale_arcsec_px,"
        " rotation_deg = excluded.rotation_deg, width_deg = excluded.width_deg,"
        " height_deg = excluded.height_deg, solved_at = excluded.solved_at",
        (frame_id, ra_deg, dec_deg, scale, rotation, width, height, now),
    )


def detach(conn: sqlite3.Connection, frame_ids: Collection[int]) -> None:
    """The sky found and the stars counted: the result of a pass that no longer holds."""
    if not frame_ids:
        return
    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(f"DELETE FROM frame_wcs WHERE frame_id IN {listed}")  # noqa: S608 - an id list
        conn.execute(f"DELETE FROM frame_metrics WHERE frame_id IN {listed}")  # noqa: S608


# The `+` before `stage` turns off the queued-stages index: without it the search would start from
# every solved frame in the archive instead of the list, even an empty list.
LOST_SKY = (
    # S608: `IN_LIST` is a constant
    f"SELECT frame_id FROM frame_stages s WHERE frame_id IN {idlist.IN_LIST}"  # noqa: S608
    " AND +stage = 'solve' AND status = 'done'"
    " AND NOT EXISTS (SELECT 1 FROM frame_wcs w WHERE w.frame_id = s.frame_id)"
)


def lost_sky(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> list[int]:
    """Solved but detached (`detach`): only the solver puts the sky back."""
    with idlist.holding(conn, frame_ids):
        return [r[0] for r in conn.execute(LOST_SKY)]


def save_metrics(
    conn: sqlite3.Connection, frame_id: int, *, hfd_px: float | None, stars: int | None, now: str
) -> None:
    """The other columns belong to `measure`: a number nobody measured is not written."""
    conn.execute(
        "INSERT INTO frame_metrics(frame_id, hfd_px, stars, source, measured_at)"
        " VALUES(?, ?, ?, 'astap', ?)"
        " ON CONFLICT(frame_id) DO UPDATE SET hfd_px = excluded.hfd_px,"
        " stars = excluded.stars, source = excluded.source, measured_at = excluded.measured_at",
        (frame_id, hfd_px, stars, now),
    )
