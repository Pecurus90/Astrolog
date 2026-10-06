"""Mosaics as the review page shows them: read, never computed, so the import contract keeps the
geometry out. The answer goes by mosaic key, stable across a camera change."""

import sqlite3
from dataclasses import dataclass

from . import counts, object_answer
from . import declarations as decl
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
       {counts.counts_on(counts.Subject.PROPOSAL)}
FROM mosaics m
JOIN ({LIVE}) r ON r.mosaic_id = m.id
LEFT JOIN declarations d ON d.entity_type = ? AND d.entity_key = m.key AND d.field = ?
ORDER BY m.id
"""  # noqa: S608 - constant fragments

# The frames of the panels that count: whom a mosaic touches, and whom `mosaic_describe` names it
# after when the catalog has nothing.
PANEL_FRAMES = "panels p JOIN frames f ON f.panel_id = p.id"
COUNTING = "p.counts_in_mosaic = 1"

# Each panel frames a different part of the complex, identified as a different object.
_SUBJECTS = obj.subjects_sql(
    "p.mosaic_id", PANEL_FRAMES, f"AND p.mosaic_id IS NOT NULL AND {COUNTING}"
)


@dataclass(frozen=True, slots=True)
class Proposal:
    """A mosaic as the page proposes it: the fields of `MosaicCandidate`."""

    key: str
    ra_deg: float
    dec_deg: float
    object: str
    panels: int
    frames: int
    integration_s: float
    untimed: int
    answer: str | None
    answer_name: str | None
    names: list[str]
    proposed: str


def candidates(conn: sqlite3.Connection) -> list[Proposal]:
    """Oldest first, with the answer given and the name the user said; an answered one stays, so
    one can change one's mind."""
    subjects = obj.subjects_of(conn.execute(_SUBJECTS))
    rows = []
    for r in conn.execute(_MOSAICS, (decl.EntityType.MOSAIC, decl.MOSAIC_FIELD)):
        value = r["value"]
        word = object_answer.mosaic_word(value)
        said = object_answer.shown_target(conn, value) if word == decl.MosaicAnswer.YES else None
        names = subjects.get(r["id"], [])
        rows.append(
            Proposal(
                key=r["key"],
                ra_deg=r["ra_deg"],
                dec_deg=r["dec_deg"],
                object=obj.together(names),
                panels=r["panels"],
                frames=r["frames"],
                integration_s=r["integration_s"],
                untimed=r["untimed"],
                answer=word,
                answer_name=None if said is None else said.name,
                names=sorted({*names, r["proposed"]} - {""}),
                proposed=r["proposed"],
            )
        )
    return rows
