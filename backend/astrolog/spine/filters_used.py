"""Which filters shot something, per night, object or batch of subjects. One home because Nights and
Archive ask it of the same frames: two copies would count the same time two ways."""

import sqlite3
from collections.abc import Collection
from typing import Any

from ..db import idlist
from ..vocab.filters import DISPLAY_ORDER, Passband
from . import counts

_RANK = " ".join(f"WHEN '{band}' THEN {i}" for i, band in enumerate(DISPLAY_ORDER))


def order_by(x: str) -> str:
    """The `ORDER BY` terms for filters aliased `x`, in `DISPLAY_ORDER`, then by name; a band
    outside the vocabulary goes with the unknown."""
    unknown = DISPLAY_ORDER.index(Passband.UNKNOWN)
    return f"CASE {x}.passband {_RANK} ELSE {unknown} END, {x}.name COLLATE NOCASE, {x}.id"


def of(
    conn: sqlite3.Connection,
    subject: counts.Subject,
    ids: Collection[int | str | None],
    *,
    alone: bool = False,
    scope: counts.Scope | None = None,
) -> dict[Any, list[Any]]:
    """`{subject id: [{name, passband, frames, integration_s}]}`, in `DISPLAY_ORDER`; band colours
    the pill. `alone`: frames outside mosaics (`counts.ALONE`); `scope`: the row's frames."""
    column = counts.column_of(subject)  # from a closed list: an unknown key is a KeyError
    narrowed, values = (scope or counts.Scope()).sql
    alone_sql = (f" AND {counts.ALONE}" if alone else "") + narrowed
    sql = f"""
    SELECT f.{column} AS owner, x.name, x.passband, {counts.AGGREGATE}
    FROM frames f JOIN filters x ON x.id = f.filter_id
    WHERE f.{column} IN {{listed}} AND f.copy_of IS NULL{alone_sql}
    GROUP BY f.{column}, x.id
    ORDER BY {order_by("x")}
    """  # noqa: S608 - `column` comes from the closed list, `listed` is a placeholder
    return idlist.grouped(
        conn,
        (sql, values),
        ids,
        "owner",
        lambda r: {
            "name": r["name"],
            "passband": r["passband"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
        },
    )
