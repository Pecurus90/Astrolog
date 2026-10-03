"""Which filters shot something, per night, object or batch of subjects. One home because Nights and
Archive ask it of the same frames: two copies would count the same time two ways."""

import sqlite3
from collections.abc import Collection
from typing import Any

from ..db import idlist
from . import counts


def of(
    conn: sqlite3.Connection,
    soggetto: str,
    ids: Collection[int | str | None],
    *,
    alone: bool = False,
) -> dict[Any, list[Any]]:
    """`{subject id: [{name, passband, frames, integration_s}]}`, most time first; the band travels
    because it colours the pill. `alone` keeps frames outside confirmed mosaics (`counts.ALONE`)."""
    dove = counts.column_of(soggetto)  # from a closed list: an unknown key is a KeyError
    solo = f" AND {counts.ALONE}" if alone else ""
    sql = f"""
    SELECT f.{dove} AS soggetto, x.name, x.passband, {counts.AGGREGATE}
    FROM frames f JOIN filters x ON x.id = f.filter_id
    WHERE f.{dove} IN {{dentro}} AND f.copy_of IS NULL{solo}
    GROUP BY f.{dove}, x.id
    {counts.ORDER_BY_TIME}, x.id
    """  # noqa: S608 - `dove` comes from the closed list, `dentro` is a placeholder
    return idlist.grouped(
        conn,
        sql,
        ids,
        "soggetto",
        lambda r: {
            "name": r["name"],
            "passband": r["passband"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
        },
    )
