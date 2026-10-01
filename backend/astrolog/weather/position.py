"""Where a night's upper wind falls against its site's usual: a position, not a threshold. It says
whether the night is unusual for the place, not whether it is good."""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any


def percentiles(conn: sqlite3.Connection, site: Mapping[str, Any]) -> list[float] | None:
    """`None` when missing or measured elsewhere: a moved site is not held to its old usual."""
    riga = conn.execute(
        "SELECT latitude, longitude, percentiles_json FROM weather_climate WHERE site_id = ?",
        (site["id"],),
    ).fetchone()
    if riga is None or (riga["latitude"], riga["longitude"]) != (
        site["latitude"],
        site["longitude"],
    ):
        return None
    return json.loads(riga["percentiles_json"])


def tenths_below(percentili: Sequence[float], valore: float) -> int:
    """How many nights in ten of the last year had less wind than `valore`."""
    sotto = sum(p < valore for p in percentili)
    return round(sotto / len(percentili) * 10)
