"""Whether a panel counts in its mosaic: an uncentred meridian flip opens a second panel of a few
frames, while a real mosaic has every panel shot at length."""

import json
import sqlite3
from collections.abc import Iterable

# Equal time per panel or seams show (Astrophotography Magazine, Mosaic Images; Smart Scope Tonight,
# Mosaic Mode Explained; Chaotic Nebula). No number given: 25% of the longest panel doubles noise.
MIN_SHARE = 0.25

_WORK = """
SELECT p.id, p.mosaic_id, COUNT(f.id) AS frames, COALESCE(SUM(f.exposure_s), 0) AS seconds,
       SUM(f.exposure_s IS NULL) AS untimed
FROM panels p JOIN frames f ON f.panel_id = p.id AND f.copy_of IS NULL
WHERE p.mosaic_id IN (SELECT value FROM json_each(?))
GROUP BY p.id
"""


def weigh(conn: sqlite3.Connection, mosaic_ids: Iterable[int]) -> None:
    """Time is weighed, frames only when one frame in the mosaic lacks its time, or a panel of
    such frames would weigh zero."""
    per_mosaico: dict[int, list[sqlite3.Row]] = {}
    for r in conn.execute(_WORK, (json.dumps(sorted(mosaic_ids)),)):
        per_mosaico.setdefault(r["mosaic_id"], []).append(r)
    for pannelli in per_mosaico.values():
        misura = "untimed" if any(p["untimed"] for p in pannelli) else "seconds"
        lavoro = {p["id"]: p["frames"] if misura == "untimed" else p["seconds"] for p in pannelli}
        soglia = MIN_SHARE * max(lavoro.values())
        conn.executemany(
            "UPDATE panels SET counts_in_mosaic = ? WHERE id = ?",
            [(int(peso >= soglia), pid) for pid, peso in lavoro.items()],
        )
