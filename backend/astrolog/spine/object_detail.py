"""An Archive row for its window, read: its nights as the Nights page has them with what the row
took in each, the setups that took it, what the catalog says of it. The row is `archive.page`'s."""

import sqlite3
from typing import Any

from . import counts
from .night_detail import distance, rigs_with

_FACTS = (
    *("common_name", "type_code", "constellation", "distance", "extent_ly", "distance_pc"),
    *("size_arcmin", "moon"),
)


def frames_of(row: dict[str, Any], scope: counts.Scope) -> tuple[str, list[Any]]:
    """`(" AND ...", values)` on frames `f`: a mosaic its frames, an object those outside mosaics,
    as the Archive counts them."""
    narrowed, values = scope.sql
    if row["mosaic_key"]:
        return " AND f.mosaic_key = ?" + narrowed, [row["mosaic_key"], *values]
    return f" AND f.object_id = ? AND {counts.ALONE}" + narrowed, [row["id"], *values]


def detail(conn: sqlite3.Connection, row: dict[str, Any], scope: counts.Scope) -> dict[str, Any]:
    """`nights` are `[(night id, its counts)]` in shooting order: the caller reads the nights."""
    where, values = frames_of(row, scope)
    taken = conn.execute(
        f"SELECT f.night_id, n.night_date, s.name AS site, {counts.AGGREGATE}, {counts.UNTIMED}"  # noqa: S608
        " FROM frames f JOIN nights n ON n.id = f.night_id JOIN sites s ON s.id = n.site_id"
        f" WHERE f.copy_of IS NULL{where}"
        " GROUP BY f.night_id ORDER BY n.night_date, f.night_id",
        values,
    ).fetchall()
    rigs = conn.execute(
        f"SELECT f.rig_id, {counts.AGGREGATE}, {counts.UNTIMED} FROM frames f"  # noqa: S608
        f" WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL{where}"
        f" GROUP BY f.rig_id {counts.ORDER_BY_TIME}, f.rig_id",
        values,
    )
    return {
        "nights": [(t["night_id"], _counted(t)) for t in taken],
        "first_night": taken[0]["night_date"] if taken else None,
        "last_night": taken[-1]["night_date"] if taken else None,
        "sites": list(dict.fromkeys(t["site"] for t in taken)),
        "rigs": rigs_with(conn, rigs),
        "facts": facts(conn, row, _panel_slug(conn, scope.panel) if scope.panel else None),
    }


def _panel_slug(conn: sqlite3.Connection, panel: int) -> str | None:
    """The catalog of a panel's object, if one only; else None, and the mosaic's speaks."""
    slugs = conn.execute(
        "SELECT DISTINCT o.catalog_slug FROM frames f JOIN objects o ON o.id = f.object_id"
        " JOIN catalog_entries e ON e.slug = o.catalog_slug"
        " WHERE f.panel_id = ? AND f.copy_of IS NULL",
        (panel,),
    ).fetchall()
    return slugs[0][0] if len(slugs) == 1 else None


def _counted(t: sqlite3.Row) -> dict[str, Any]:
    return {"frames": t["frames"], "integration_s": t["integration_s"], "untimed": t["untimed"]}


def facts(conn: sqlite3.Connection, row: dict[str, Any], slug: str | None = None) -> dict[str, Any]:
    """As `catalog/load.py` wrote them, of `slug` or the row's; all null outside the catalog."""
    entry = conn.execute(
        "SELECT common_name, type_code, constellation, distance_ly, extent_ly, distance_pc,"
        " size_major_arcmin, moon_compare, moon_count FROM catalog_entries WHERE slug = ?",
        (slug or row["catalog_slug"],),
    ).fetchone()
    if entry is None:
        return {"key": row["key"], **dict.fromkeys(_FACTS)}
    moon = entry["moon_compare"]
    return {
        "key": row["key"],
        "common_name": entry["common_name"],
        "type_code": entry["type_code"],
        "constellation": entry["constellation"],
        "distance": distance(entry["distance_ly"]),
        "extent_ly": entry["extent_ly"],
        "distance_pc": entry["distance_pc"],
        "size_arcmin": entry["size_major_arcmin"],
        "moon": {"compare": moon, "moons": entry["moon_count"]} if moon else None,
    }
