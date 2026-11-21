"""Archive rows with nothing narrowing, written by whoever writes (ADR 0048): hours, productions,
filters, totals, frames no row took, objects' nights. Instruments and filters: ids, names live."""

import sqlite3
from collections.abc import Collection
from typing import Any

from ..db import idlist
from . import archive, counts, filters_used, productions

# (table, columns, SELECT): each written whole, from the frames, as the live reads count them.
_PER_PRODUCTION = "pr.optics_id, pr.camera_id"
_FROM_SHOT = f"FROM frames f LEFT JOIN rigs pr ON pr.id = f.rig_id WHERE {archive.SHOT}"
_TABLES = (
    (
        "archive_rows",
        (*archive.ROW_COLUMNS, *archive.STAT_COLUMNS),
        f"SELECT {archive.BASE}, {archive.stats('')} FROM {archive.ROWS}",  # noqa: S608
    ),
    (
        "archive_productions",
        ("row_key", "optics_id", "camera_id", "frames", "integration_s", "untimed"),
        f"SELECT {archive.ROW_OF_FRAME}, {_PER_PRODUCTION}, {counts.AGGREGATE}, {counts.UNTIMED}"
        f" {_FROM_SHOT} GROUP BY 1, 2, 3",
    ),
    (
        "archive_production_filters",
        ("row_key", "optics_id", "camera_id", "filter_id", "frames", "integration_s"),
        f"SELECT {archive.ROW_OF_FRAME}, {_PER_PRODUCTION}, f.filter_id, {counts.AGGREGATE}"
        f" {_FROM_SHOT} AND f.filter_id IS NOT NULL GROUP BY 1, 2, 3, 4",
    ),
    (
        "archive_row_filters",
        ("row_key", "filter_id", "frames", "integration_s"),
        f"SELECT {archive.ROW_OF_FRAME}, f.filter_id, {counts.AGGREGATE} FROM frames f"  # noqa: S608
        f" WHERE {archive.SHOT} AND f.filter_id IS NOT NULL GROUP BY 1, 2"
        f" UNION ALL SELECT NULL, f.filter_id, {counts.AGGREGATE} FROM frames f"
        f" WHERE {archive.UNRESOLVED} AND f.filter_id IS NOT NULL GROUP BY 2",
    ),
    (
        "archive_whole",
        ("frames", "integration_s", "untimed", "nights",
         "left_frames", "left_integration_s", "left_untimed"),
        f"SELECT t.*, l.* FROM ({archive.TOTALS}) t, ({archive.LEFT}) l",  # noqa: S608
    ),
    (
        "archive_object_nights",
        ("object_id", "night_id"),
        "SELECT DISTINCT f.object_id, f.night_id FROM frames f WHERE f.copy_of IS NULL"
        " AND f.object_id IS NOT NULL AND f.night_id IS NOT NULL",
    ),
)  # fmt: skip


def write(conn: sqlite3.Connection) -> None:
    """Every table whole; the caller holds BEGIN IMMEDIATE and leaves the sign after."""
    for table, columns, select in _TABLES:
        conn.execute(f"DELETE FROM {table}")  # noqa: S608 - constants of this file
        conn.execute(f"INSERT INTO {table}({', '.join(columns)}) {select}")


# Ties broken by the ids, as the live query's grouping leaves them.
_PRODUCTIONS = """
SELECT p.row_key AS owner, p.optics_id, p.camera_id, o.name AS optics, c.name AS camera,
       p.frames, p.integration_s, p.untimed
FROM archive_productions p
LEFT JOIN instruments o ON o.id = p.optics_id
LEFT JOIN instruments c ON c.id = p.camera_id
WHERE p.row_key IN {listed}
ORDER BY p.integration_s DESC, p.frames DESC, o.name COLLATE NOCASE, c.name COLLATE NOCASE,
         p.optics_id, p.camera_id"""
_PRODUCTION_FILTERS = f"""
SELECT q.row_key AS owner, q.optics_id, q.camera_id, x.name, x.passband, q.frames, q.integration_s
FROM archive_production_filters q JOIN filters x ON x.id = q.filter_id
WHERE q.row_key IN {{listed}}
ORDER BY {filters_used.order_by("x")}"""  # noqa: S608 - constant fragments
_ROW_FILTERS = f"""
SELECT a.row_key AS owner, x.name, x.passband, a.frames, a.integration_s
FROM archive_row_filters a JOIN filters x ON x.id = a.filter_id
WHERE a.row_key IN {{listed}}
ORDER BY {filters_used.order_by("x")}"""  # noqa: S608 - constant fragments


def productions_of(conn: sqlite3.Connection, keys: Collection[str]) -> dict[str, list[Any]]:
    """As `productions.of`, by row key, read from what is written."""
    filters = idlist.grouped(conn, _PRODUCTION_FILTERS, keys, "owner", dict)
    out = idlist.grouped(conn, _PRODUCTIONS, keys, "owner", dict)
    return productions.with_filters(out, filters)


def filters_of(conn: sqlite3.Connection, keys: Collection[str]) -> dict[str, list[Any]]:
    """As `filters_used.of`, by row key, read from what is written."""
    keep = ("name", "passband", "frames", "integration_s")
    return idlist.grouped(conn, _ROW_FILTERS, keys, "owner", lambda r: {k: r[k] for k in keep})
