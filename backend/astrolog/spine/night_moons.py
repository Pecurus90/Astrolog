"""The Moon and dark of every archive night, written by who writes (ADR 0047); Nights reads
the rows and computes nothing."""

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from ..clock import midnight_of, night_window
from ..db import config
from ..ephemeris import bodies, moon

# Raised when the Moon or the dark of a night is computed another way: every row is rewritten.
VERSION = 1

COLUMNS = (
    "night_id", "version", "night_date", "latitude", "longitude", "timezone", "floor_deg",
    "phase_key", "illumination_pct", "dark_s", "moonless_dark_s",
)  # fmt: skip

# A row that is missing, or was computed for another formula, place, zone, date or rule floor.
_STALE = """
SELECT n.id, n.night_date, s.timezone, s.latitude, s.longitude
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN night_moons m ON m.night_id = n.id
WHERE m.night_id IS NULL OR m.version != :version OR m.night_date != n.night_date
   OR m.latitude != s.latitude OR m.longitude != s.longitude
   OR m.timezone IS NOT s.timezone OR m.floor_deg != :floor
"""


@dataclass(frozen=True, slots=True)
class _Night:
    id: int
    night_date: str
    timezone: str | None
    latitude: float
    longitude: float


def refresh(conn: sqlite3.Connection) -> int:
    """Only the stale rows, all at once; how many were written. Nothing stale costs one query."""
    floor = config.moon_rule(config.read(conn)).floor_deg
    stale = [_Night(*r) for r in conn.execute(_STALE, {"version": VERSION, "floor": floor})]
    if not stale:
        return 0
    phases = _phases(stale)
    darks = _darks([n for n in stale if n.id in phases], floor)
    rows = [
        (
            n.id,
            VERSION,
            n.night_date,
            n.latitude,
            n.longitude,
            n.timezone,
            floor,
            *phases.get(n.id, (None, None)),
            *darks.get(n.id, (None, None)),
        )  # fmt: skip
        for n in stale
    ]
    marks = ", ".join("?" * len(COLUMNS))  # segnaposto-ok: the columns, not the rows
    # a savepoint: in a caller's transaction it nests, alone it is one write for all the rows
    conn.execute("SAVEPOINT night_moons")
    try:
        conn.executemany(
            f"INSERT OR REPLACE INTO night_moons({', '.join(COLUMNS)}) VALUES({marks})",
            rows,
        )
    except Exception:
        conn.execute("ROLLBACK TO night_moons")
        conn.execute("RELEASE night_moons")
        raise
    conn.execute("RELEASE night_moons")
    return len(rows)


def _phases(nights: Sequence[_Night]) -> dict[int, tuple[str, int]]:
    """One call to the sky, at midnight in the site's zone; without a zone, or outside DE421 (a
    header's wrong clock), no Moon."""
    when = {n.id: midnight_of(n.night_date, n.timezone) for n in nights}
    known = {i: q for i, q in when.items() if q is not None and bodies.covers(q)}
    return {
        i: (p.phase_key.value, p.illumination_pct)
        for i, p in zip(known, moon.phases(list(known.values())), strict=True)
    }


def _darks(nights: Sequence[_Night], floor_deg: float) -> dict[int, tuple[int, int]]:
    """Dark and dark without the Moon over the floor, one call per site."""
    by_site: dict[tuple[float, float], list[_Night]] = {}
    for n in nights:
        by_site.setdefault((n.latitude, n.longitude), []).append(n)
    out = {}
    for (lat, lon), mine in by_site.items():
        windows = [(n.night_date, *night_window(n.night_date, n.timezone)) for n in mine]
        for n, dark in zip(mine, moon.dark_seconds(windows, lat, lon, floor_deg), strict=True):
            out[n.id] = dark
    return out
