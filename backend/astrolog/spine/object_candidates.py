"""Sky candidates for doubtful objects, rewritten by whoever changes their inputs, so the page only
reads them. Only doubtful ones: a sure object has nothing to click, and the cone costs."""

import sqlite3
from typing import Any

from ..db.replace_table import replace_rows
from . import identify
from . import objects as obj
from .identify_decide import DOUBT

_COLONNE = ("object_id", "rank", "slug", "name", "common_name", "in_frame")


def write(conn: sqlite3.Connection) -> None:
    """Most likely first; all or nothing (`replace_rows`)."""
    righe: list[tuple[Any, ...]] = []
    for (object_id,) in conn.execute(
        "SELECT id FROM objects WHERE identity_confidence = ?", (DOUBT,)
    ).fetchall():
        cielo = obj.a_frame_of(conn, object_id)
        for rank, c in enumerate(identify.candidates(conn, cielo) if cielo else []):
            righe.append(
                (object_id, rank, *(c[k] for k in ("slug", "name", "common_name")),
                 c["in_frame"])
            )  # fmt: skip
    replace_rows(conn, "object_candidates", _COLONNE, righe)
