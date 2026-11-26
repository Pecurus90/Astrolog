"""Three judgements on raw header, from file and vocab only; review filters them in SQL. Scan has
no vocab: `fill` writes them at the start of `normalize`, nobody rewrites them."""

import sqlite3
from collections.abc import Mapping
from typing import Any

from ..db.transaction import transaction
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from .night_rig import asks_camera
from .unfiltered import says_no_filter


def names_the_optics(software: str | None, telescope_raw: str | None) -> bool:
    """`TELESCOP` written, by a software that does not put the mount there: the same reading as
    `normalize_rig.rig_for_frame`."""
    return not telescope_is_mount(software) and bool(normalize_header_value(telescope_raw))


_RAW = "software_raw, instrument_raw, filter_raw, telescope_raw"


def fill(conn: sqlite3.Connection) -> None:
    """Frames the scan left unjudged (NULL), or whose header it rewrote."""
    rows = conn.execute(
        f"SELECT id, {_RAW} FROM frames WHERE asks_camera IS NULL"  # noqa: S608 - constant
        " OR asks_filter IS NULL OR names_optics IS NULL"
    ).fetchall()
    with transaction(conn):
        conn.executemany(
            "UPDATE frames SET asks_camera = :asks_camera, asks_filter = :asks_filter,"
            " names_optics = :names_optics WHERE id = :id",
            [{**of(dict(row)), "id": row["id"]} for row in rows],
        )


def of(fields: Mapping[str, Any]) -> dict[str, int]:
    software = normalize_software(fields.get("software_raw"))
    return {
        "asks_camera": int(asks_camera(fields.get("instrument_raw"))),
        "asks_filter": int(says_no_filter(fields.get("filter_raw"))),
        "names_optics": int(names_the_optics(software, fields.get("telescope_raw"))),
    }
