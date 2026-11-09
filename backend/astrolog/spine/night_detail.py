"""A night for its window, read: when it was shot in the site's zone, its setups, what the catalog
says of its objects. The night itself is `nights.page`'s row; nothing is recomputed here."""

import sqlite3
from collections.abc import Iterable
from typing import Any

from ..clock import local_iso
from . import counts, inventory
from . import objects as obj

MILLION = 1_000_000  # from here a distance reads in millions [D tavola v76, Riepilogo:130]
WHOLE_MILLIONS = 10_000_000  # from here without the decimal [D tavola v76, Riepilogo:130]

# The last end is a start plus its exposure; one without exposure ends where it starts.
_HOURS = """
SELECT s.timezone, MIN(f.date_obs) AS first_start,
       MAX(datetime(f.date_obs, '+' || COALESCE(f.exposure_s, 0) || ' seconds')) AS last_end
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN frames f ON f.night_id = n.id AND f.copy_of IS NULL AND f.date_obs IS NOT NULL
WHERE n.id = ?
GROUP BY n.id
"""

_RIGS = f"""
SELECT f.rig_id, {counts.AGGREGATE}, {counts.UNTIMED}
FROM frames f WHERE f.night_id = ? AND f.copy_of IS NULL AND f.rig_id IS NOT NULL
GROUP BY f.rig_id
{counts.ORDER_BY_TIME}, f.rig_id
"""  # noqa: S608 - constant fragments of the spine

_OBJECTS = f"""
SELECT o.id, o.catalog_slug, {obj.NAME_COLUMNS}, e.common_name, e.type_code, e.constellation,
       e.distance_ly,
       e.extent_ly, {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id
LEFT JOIN catalog_entries e ON e.slug = o.catalog_slug
WHERE f.night_id = ? AND f.copy_of IS NULL
GROUP BY o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - constant fragments of the spine; the Nights page's order


def detail(conn: sqlite3.Connection, night_id: int) -> dict[str, Any] | None:
    """None: no such night. `night` is left to the caller, who reads it as the list does."""
    hours = conn.execute(_HOURS, (night_id,)).fetchone()
    if hours is None:
        return None
    zone = hours["timezone"]
    return {
        "first_start": local_iso(hours["first_start"], zone),
        "last_end": local_iso(hours["last_end"], zone),
        "rigs": _rigs(conn, night_id),
        "objects": [_facts(r) for r in conn.execute(_OBJECTS, (night_id,))],
    }


def _rigs(conn: sqlite3.Connection, night_id: int) -> list[dict[str, Any]]:
    return rigs_with(conn, conn.execute(_RIGS, (night_id,)))


def rigs_with(conn: sqlite3.Connection, taken: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    """The rig as the Gear page reads it, with what it took: rows of `rig_id`, `counts.AGGREGATE`
    and `counts.UNTIMED`, in the order to show."""
    used = {r["rig_id"]: r for r in taken}
    whole = {r["id"]: r for r in inventory.rigs(conn) if r["id"] in used}
    return [
        {
            **{k: whole[i][k] for k in ("id", "name", "optics", "camera", "focal_mm", "parts")},
            **{k: whole[i][k] for k in ("scale_arcsec_px", "width_deg", "height_deg")},
            "frames": u["frames"],
            "integration_s": u["integration_s"],
            "untimed": u["untimed"],
        }
        for i, u in used.items()
    ]


def _facts(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "key": obj.stable_key(r),
        "common_name": r["common_name"],
        "type_code": r["type_code"],
        "constellation": r["constellation"],
        "distance": distance(r["distance_ly"]),
        "extent_ly": r["extent_ly"],
    }


def distance(ly: float | None) -> dict[str, Any] | None:
    """Light years whole, or millions with a decimal up to ten million."""
    if ly is None:
        return None
    if ly < MILLION:
        return {"value": float(round(ly)), "unit": "ly"}
    digits = 1 if ly < WHOLE_MILLIONS else 0
    return {"value": round(ly / MILLION, digits), "unit": "million_ly"}
