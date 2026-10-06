"""What a change of the declared sites requeues: only what the change can change, the rest would
come back the same (`docs/domini/sito.md`)."""

import json
import sqlite3
from collections.abc import Collection, Iterable

from .. import place
from ..db import idlist
from .declarations import COORDINATES_SITE
from .group import SAME_PLACE_KM, GroupReason
from .stages import StageName, invalidate


def requeue_waiting(
    conn: sqlite3.Connection,
    *,
    near: Collection[tuple[float | None, float | None]] = (),
    names: Iterable[str] = (),
    homeless: bool = False,
) -> None:
    """Frames stopped on their place: near a touched point, answered with a renamed site, waiting
    for a home, and always those of a site without a zone, which a moved site may give one."""
    named_keys = {
        r[0]
        for r in conn.execute(
            "SELECT entity_key FROM declarations WHERE entity_type = 'coordinates'"
            " AND field = ? AND value IN (SELECT value FROM json_each(?))",
            (COORDINATES_SITE, json.dumps(list(names))),
        )
    }
    frames = []
    for r in conn.execute(
        "SELECT s.frame_id, s.reason, f.site_lat, f.site_lon FROM frame_stages s"
        " JOIN frames f ON f.id = s.frame_id WHERE s.stage = 'group' AND s.status = 'skipped'"
        " AND s.reason IN (?, ?, ?)",
        (GroupReason.SITE_UNCLEAR, GroupReason.NO_ACTIVE_SITE, GroupReason.SITE_NO_TIMEZONE),
    ):
        is_near = any(
            (km := place.distance_km(r["site_lat"], r["site_lon"], *point)) is not None
            and km <= SAME_PLACE_KM
            for point in near
        )
        named = place.coordinates_key(r["site_lat"], r["site_lon"]) in named_keys
        no_zone = r["reason"] == GroupReason.SITE_NO_TIMEZONE
        if is_near or named or no_zone or (homeless and r["reason"] == GroupReason.NO_ACTIVE_SITE):
            frames.append(r["frame_id"])
    invalidate(conn, frames, StageName.GROUP)


def requeue_nights_of(conn: sqlite3.Connection, site_id: int) -> None:
    """The nights the app gave that site: moved, their coordinates may no longer fall there."""
    frames = [
        r[0]
        for r in conn.execute(
            "SELECT f.id FROM frames f JOIN nights n ON n.id = f.night_id"
            " WHERE n.site_id = ? AND n.site_source = 'detected'",
            (site_id,),
        )
    ]
    invalidate(conn, frames, StageName.GROUP)


def adopt_nights(conn: sqlite3.Connection, site_id: int, old_home: int) -> None:
    """The app's guesses follow the new home; declared nights are answers and stay. So does a date
    the new site already has: failing the move would be worse, and that night moves by hand."""
    # one date at a time: two detected nights of a date on two sites would collide moving together
    to_move = [
        r[0]
        for r in conn.execute(
            "SELECT MIN(id) FROM nights WHERE site_source = 'detected' AND site_id = ?"
            " AND night_date NOT IN (SELECT night_date FROM nights WHERE site_id = ?)"
            " GROUP BY night_date",
            (old_home, site_id),
        )
    ]
    if not to_move:
        return
    with idlist.holding(conn, to_move) as listed:
        conn.execute(
            f"UPDATE nights SET site_id = ? WHERE id IN {listed}",  # noqa: S608 - our constant
            (site_id,),
        )
        # the new zone may cut the nights elsewhere, and only `group` knows how to recut them
        frames = [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE night_id IN {listed}"  # noqa: S608 - our constant
            )
        ]
    invalidate(conn, frames, StageName.GROUP)
