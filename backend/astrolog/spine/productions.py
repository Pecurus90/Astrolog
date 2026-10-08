"""The productions of an Archive row: the same object shot with the same optics and the same
camera, until projects exist (`docs/domini/archivio.md`)."""

import sqlite3
from collections.abc import Collection
from typing import Any

from ..db import idlist
from . import counts, filters_used

# Optics and camera come through the rig. LEFT JOIN: a frame that does not say its rig, or a rig
# that knows half of itself, is a production too, and says so with a null.
_RIG = "LEFT JOIN rigs pr ON pr.id = f.rig_id"


def of(
    conn: sqlite3.Connection,
    subject: counts.Subject,
    ids: Collection[int | str | None],
    *,
    alone: bool = False,
    scope: counts.Scope | None = None,
) -> dict[Any, list[dict[str, Any]]]:
    """`{subject id: [{optics, camera, frames, integration_s, untimed, filters}]}`, most time
    first. `alone`: frames outside mosaics; `scope`: the row's frames."""
    # Grouped on optics and camera, not on the rig: a reducer changes the focal length and the
    # rig, not the production. Two queries for the whole page: the productions, their filters.
    column = counts.column_of(subject)  # from a closed list: an unknown key is a KeyError
    narrowed, values = (scope or counts.Scope()).sql
    where = (
        f"f.{column} IN {{listed}} AND f.copy_of IS NULL"
        + (f" AND {counts.ALONE}" if alone else "")
        + narrowed
    )
    sql = f"""
    SELECT f.{column} AS owner, pr.optics_id, pr.camera_id, o.name AS optics, c.name AS camera,
           {counts.AGGREGATE}, {counts.UNTIMED}
    FROM frames f {_RIG}
    LEFT JOIN instruments o ON o.id = pr.optics_id
    LEFT JOIN instruments c ON c.id = pr.camera_id
    WHERE {where}
    GROUP BY f.{column}, pr.optics_id, pr.camera_id
    {counts.ORDER_BY_TIME}, o.name COLLATE NOCASE, c.name COLLATE NOCASE
    """  # noqa: S608 - `column` comes from the closed list, `listed` is a placeholder
    by_filter = f"""
    SELECT f.{column} AS owner, pr.optics_id, pr.camera_id, x.name, x.passband,
           {counts.AGGREGATE}
    FROM frames f {_RIG} JOIN filters x ON x.id = f.filter_id
    WHERE {where}
    GROUP BY f.{column}, pr.optics_id, pr.camera_id, x.id
    ORDER BY {filters_used.order_by("x")}
    """  # noqa: S608 - as above
    filters = idlist.grouped(conn, (by_filter, values), ids, "owner", dict)
    out = idlist.grouped(conn, (sql, values), ids, "owner", dict)
    for owner, rows in out.items():
        theirs = filters.get(owner, [])
        for row in rows:
            rig = (row.pop("optics_id"), row.pop("camera_id"))
            del row["owner"]
            row["filters"] = [
                {k: f[k] for k in ("name", "passband", "frames", "integration_s")}
                for f in theirs
                if (f["optics_id"], f["camera_id"]) == rig
            ]
    return out
