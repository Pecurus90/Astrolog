"""Frames whose header does not say where follow home's zone, night and unnamed group. Answers
carry no night, so none moves (contract: `domini/spina.md`)."""

import json
import sqlite3

from ..clock import NIGHT_SQL, night_date
from ..place import timezone_of_frame
from . import unnamed
from .scan_store import home_timezone
from .stages import invalidate

_PLACES = "SELECT DISTINCT site_lat, site_lon FROM frames WHERE local_tz IS NOT ?"
_OF_PLACE = """
SELECT f.id, f.local_night, f.night_instant, f.unnamed_key
FROM frames f WHERE f.local_tz IS NOT ? AND f.site_lat IS ? AND f.site_lon IS ?
"""
_REWRITE = "UPDATE frames SET local_night = ?, local_tz = ? WHERE id = ?"
_OF_NIGHTS = f"""
SELECT f.id FROM frames f WHERE {NIGHT_SQL} IN (SELECT value FROM json_each(?))
"""  # noqa: S608 - constant fragments


def follow_home(conn: sqlite3.Connection) -> None:
    """Into home's zone now (UTC without a home), only where the header's coordinates give no zone;
    comparing with the written zone makes a second call a no-op. Touched nights are redone."""
    casa = home_timezone(conn)
    moved: list[tuple[sqlite3.Row, str | None]] = []
    riscritte: list[tuple[str | None, str | None, int]] = []
    for lat, lon in conn.execute(_PLACES, (casa,)).fetchall():
        if timezone_of_frame(lat, lon, casa) != casa:
            continue  # the zone comes from the coordinates
        for r in conn.execute(_OF_PLACE, (casa, lat, lon)).fetchall():
            notte = night_date(r["night_instant"], casa)
            riscritte.append((notte, casa, r["id"]))
            if notte != r["local_night"]:
                moved.append((r, notte))
    conn.executemany(_REWRITE, riscritte)
    if not moved:
        return
    # The group is written on the frame, so it is chosen again in the new night, where it may
    # land in a group already there.
    toccati = sorted(r["id"] for r, _ in moved if r["unnamed_key"])
    conn.executemany("UPDATE frames SET unnamed_key = NULL WHERE id = ?", [(i,) for i in toccati])
    for frame_id in toccati:
        unnamed.assign(conn, frame_id)
    notti = json.dumps(
        sorted({n for _, n in moved} | {r["local_night"] for r, _ in moved}, key=str)
    )
    invalidate(conn, [r["id"] for r in conn.execute(_OF_NIGHTS, (notti,))], "normalize")
