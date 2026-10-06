"""Where a night's upper wind falls against its site's usual: a position, not a threshold. It says
whether the night is unusual for the place, not whether it is good."""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any


def percentiles(conn: sqlite3.Connection, site: Mapping[str, Any]) -> list[float] | None:
    """`None` when missing or measured elsewhere: a moved site is not held to its old usual."""
    row = conn.execute(
        "SELECT latitude, longitude, percentiles_json FROM weather_climate WHERE site_id = ?",
        (site["id"],),
    ).fetchone()
    if row is None or (row["latitude"], row["longitude"]) != (
        site["latitude"],
        site["longitude"],
    ):
        return None
    return json.loads(row["percentiles_json"])


def tenths_below(usual: Sequence[float], value: float) -> int:
    """How many nights in ten of the last year had less wind than `value`."""
    below = sum(p < value for p in usual)
    return round(below / len(usual) * 10)
