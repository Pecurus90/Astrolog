"""Mosaics as the review page shows them: read, never computed, so the import contract keeps the
geometry out. The answer goes by mosaic key, stable across a camera change."""

import sqlite3
from typing import Any

from . import counts
from . import declarations as decl
from . import object_answer as risposta
from . import objects as obj

# A single panel is a subject shot normally. The rule for readers, answerers and the key sweep.
LIVE = """
SELECT p.mosaic_id, COUNT(DISTINCT f.panel_id) AS panels
FROM panels p JOIN frames f ON f.panel_id = p.id AND f.copy_of IS NULL
WHERE p.mosaic_id IS NOT NULL AND p.counts_in_mosaic = 1
GROUP BY p.mosaic_id HAVING COUNT(DISTINCT f.panel_id) > 1
"""

_MOSAICS = f"""
SELECT m.id, m.key, m.ra_deg, m.dec_deg, m.proposed, d.value, r.panels,
       {counts.counts_on("proposal")}
FROM mosaics m
JOIN ({LIVE}) r ON r.mosaic_id = m.id
LEFT JOIN declarations d ON d.entity_type = ? AND d.entity_key = m.key AND d.field = ?
ORDER BY m.id
"""  # noqa: S608 - constant fragments

# Each panel frames a different part of the complex, identified as a different object.
_SUBJECTS = obj.subjects_sql(
    "p.mosaic_id",
    "panels p JOIN frames f ON f.panel_id = p.id",
    "AND p.mosaic_id IS NOT NULL AND p.counts_in_mosaic = 1",
)


def candidates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Oldest first, with the answer given and the name the user said; an answered one stays, so
    one can change one's mind. Keys are the page's (`MosaicCandidate`)."""
    soggetti = obj.subjects_of(conn.execute(_SUBJECTS))
    righe = []
    for r in conn.execute(_MOSAICS, (decl.MOSAIC, decl.MOSAIC_FIELD)):
        valore = r["value"]
        parola = risposta.mosaic_word(valore)
        detto = risposta.shown_target(conn, valore) if parola == decl.MOSAIC_YES else None
        nomi = soggetti.get(r["id"], [])
        righe.append(
            {
                "key": r["key"],
                "ra_deg": r["ra_deg"],
                "dec_deg": r["dec_deg"],
                "object": obj.together(nomi),
                "panels": r["panels"],
                "frames": r["frames"],
                "integration_s": r["integration_s"],
                "untimed": r["untimed"],
                "answer": parola,
                "answer_name": None if detto is None else detto[2],
                "names": sorted({*nomi, r["proposed"]} - {""}),
                "proposed": r["proposed"],
            }
        )
    return righe
