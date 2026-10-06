"""Sky candidates for the cards that ask, written by whoever changes their inputs: doubtful objects,
and frames put out as "not an object", to click back. A sure object has nothing to click."""

import sqlite3
from typing import Any

from ..db.replace_table import replace_rows
from . import identify
from . import objects as obj
from .identify_decide import DOUBT

_COLONNE = ("object_key", "rank", "slug", "name", "common_name", "in_frame")

# One measured sky per key: its frames look at the same patch.
_OUT_SKIES = """
SELECT f.found_key AS key, w.ra_deg, w.dec_deg, w.scale_arcsec_px, w.rotation_deg, w.width_deg,
  w.height_deg
FROM frames f JOIN frame_wcs w ON w.frame_id = f.id
WHERE f.found_key IS NOT NULL AND f.object_id IS NULL
  AND f.id = (SELECT MIN(g.id) FROM frames g JOIN frame_wcs v ON v.frame_id = g.id
              WHERE g.found_key = f.found_key AND g.object_id IS NULL)
"""


def write(conn: sqlite3.Connection) -> None:
    """Most likely first; all or nothing (`replace_rows`)."""
    cieli: dict[str, dict[str, Any]] = {}
    for r in conn.execute(_OUT_SKIES).fetchall():
        cieli[r["key"]] = {k: r[k] for k in r.keys() if k != "key"}  # noqa: SIM118 - a Row
    for riga in obj.identities(conn):
        if riga["identity_confidence"] == DOUBT and (cielo := obj.a_frame_of(conn, riga["id"])):
            cieli[obj.stable_key(riga)] = cielo
    righe: list[tuple[Any, ...]] = []
    for chiave, cielo in cieli.items():
        for rank, c in enumerate(identify.candidates(conn, cielo)):
            righe.append(
                (chiave, rank, *(c[k] for k in ("slug", "name", "common_name")), c["in_frame"])
            )
    replace_rows(conn, "object_candidates", _COLONNE, righe)
