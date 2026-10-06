"""The night of frames whose header does not say where they were shot follows home's zone, and so
do the unnamed groups keyed by it; gear answers carry no night (contract: `domini/spina.md`)."""

import json
import sqlite3

from ..clock import NIGHT_SQL, night_date
from ..place import timezone_of_frame
from . import declarations as decl
from . import unnamed
from .scan_store import home_timezone
from .stages import invalidate

# A frame and its new night.
type Move = tuple[sqlite3.Row, str | None]
# `{new key: old keys}` of a per-group answer.
type Towards = dict[str, set[str]]

_PLACES = "SELECT DISTINCT site_lat, site_lon FROM frames WHERE local_tz IS NOT ?"
_OF_PLACE = """
SELECT f.id, f.local_night, f.night_instant, f.unnamed_key
FROM frames f WHERE f.local_tz IS NOT ? AND f.site_lat IS ? AND f.site_lon IS ?
"""
_REWRITE = "UPDATE frames SET local_night = ?, local_tz = ? WHERE id = ?"
_OF_NIGHTS = f"""
SELECT f.id, {NIGHT_SQL} AS night, f.unnamed_key
FROM frames f WHERE {NIGHT_SQL} IN (SELECT value FROM json_each(?))
"""  # noqa: S608 - constant fragments


def follow_home(conn: sqlite3.Connection) -> None:
    """Into home's zone now (UTC without a home), only where the header's coordinates give no zone;
    comparing with the written zone makes a second call a no-op. Touched nights are redone."""
    casa = home_timezone(conn)
    moved: list[Move] = []
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
    notti = json.dumps(
        sorted({n for _, n in moved} | {r["local_night"] for r, _ in moved}, key=str)
    )
    spostati = {r["id"] for r, _ in moved}
    fermi = [r for r in conn.execute(_OF_NIGHTS, (notti,)) if r["id"] not in spostati]
    oggetto_fermi = {r["unnamed_key"] for r in fermi}
    _carry(conn, decl.GROUP_OBJECT, _unnamed_moves(conn, moved), oggetto_fermi)
    invalidate(conn, [r["id"] for r in conn.execute(_OF_NIGHTS, (notti,))], "normalize")


def _unnamed_moves(conn: sqlite3.Connection, moved: list[Move]) -> Towards:
    """The key is written on the frame, so it is chosen again in the new night (`unnamed.assign`),
    where it may land in a group already there."""
    toccati = sorted(((r["id"], r["unnamed_key"]) for r, _ in moved if r["unnamed_key"]))
    conn.executemany(
        "UPDATE frames SET unnamed_key = NULL WHERE id = ?", [(i,) for i, _ in toccati]
    )
    verso: Towards = {}
    for frame_id, vecchia in toccati:
        verso.setdefault(unnamed.assign(conn, frame_id), set()).add(vecchia)
    return verso


def _carry(conn: sqlite3.Connection, field: str, verso: Towards, fermi: set[str]) -> None:
    """`fermi` are keys still carried by frames that stayed: their answer holds for newcomers too.
    All is read before writing, because one group's old key may be another's new one."""
    tutte = set(verso).union(*verso.values())
    prima = {k: decl.declared(conn, decl.FRAME_GROUP, k, field) for k in tutte}
    for nuova, vecchie in verso.items():
        fonti = vecchie | ({nuova} if nuova in fermi else set())
        dette = {prima[k] for k in fonti} - {None}
        if len(dette) == 1:
            decl.write_declaration(conn, decl.FRAME_GROUP, nuova, field, dette.pop())
        else:
            # Two different answers fall and the question reopens: picking one would invent it.
            decl.forget(conn, decl.FRAME_GROUP, nuova, field)
    # An answer left with no frames would hold for other frames arriving later with the same key.
    for vecchia in tutte - set(verso) - fermi:
        decl.forget(conn, decl.FRAME_GROUP, vecchia, field)
