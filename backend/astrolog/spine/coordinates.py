"""Frames whose site is unclear, grouped by coordinates, shared by the `group` stage and the review.
An answered place stays listed with its answer: a wrong click attributes hundreds of frames."""

import sqlite3
from typing import Any

from ..place import coordinates_key
from . import declarations as decl
from . import group_store as store
from . import objects as obj

# Each way in (stopped there, or in a declared night) uses its index, unioned: an `OR` across two
# tables walks every frame. The id breaks ties so the coordinates do not depend on the plan.
_ROWS = f"""
SELECT f.id, f.local_night, f.site_lat, f.site_lon, {obj.SUBJECT} AS subject
FROM frames f
{obj.SUBJECT_JOIN}
WHERE f.copy_of IS NULL AND f.site_lat IS NOT NULL AND f.site_lon IS NOT NULL AND f.id IN (
  SELECT s.frame_id FROM frame_stages s
  WHERE s.stage = 'group' AND s.status = 'skipped' AND s.reason = ?
  UNION
  SELECT d.id FROM nights n JOIN frames d ON d.night_id = n.id WHERE n.site_source = 'declared')
ORDER BY f.date_obs, f.id
"""  # noqa: S608 - constant spine fragments, not user values


def _rows(conn: sqlite3.Connection, reason: str) -> list[sqlite3.Row]:
    """The stopped frames, and those an answer already settled: the answer must stay changeable."""
    return conn.execute(_ROWS, (reason,)).fetchall()


def unclear_coordinates(conn: sqlite3.Connection, reason: str) -> list[dict[str, Any]]:
    """One row per place, never per frame: the answer is a fact about the place, valid for every
    night shot there, including future ones. Nights are in the zone of those coordinates."""
    gruppi: dict[str | None, dict[str, Any]] = {}
    for r in _rows(conn, reason):
        chiave = coordinates_key(r["site_lat"], r["site_lon"])
        posto = gruppi.setdefault(
            chiave,
            {
                "key": chiave,
                "latitude": r["site_lat"],
                "longitude": r["site_lon"],
                "frames": 0,
                "nights": set(),
            },
        )
        posto["frames"] += 1
        obj.count_subject(posto, r["subject"], 1)
        if r["local_night"]:
            posto["nights"].add(r["local_night"])
    return [
        {**p, "nights": sorted(p["nights"]), "site": _answered(conn, p["key"])}
        for p in obj.subjects(conn, gruppi.values())
    ]


def _answered(conn: sqlite3.Connection, key: str) -> str | None:
    """Only if that site still exists, found the way the stage finds it: renamed or deleted, the
    answer no longer hooks, and the stage, the page and the counter ask again."""
    detto = decl.site_for_coordinates(conn, key)
    return detto if detto and store.site_by_name(conn, detto) else None


def frames_at(conn: sqlite3.Connection, coordinates: str, reason: str) -> list[int]:
    """Including those a previous answer settled, or changing one's mind would move nothing."""
    return [
        r["id"]
        for r in _rows(conn, reason)
        if coordinates_key(r["site_lat"], r["site_lon"]) == coordinates
    ]
