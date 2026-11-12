"""The proofs next to a question of To confirm: the nights and the rigs of a group's frames, read
in one query for every owner, never one per card."""

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FrameRig:
    """Optics and camera of some frames, as the user calls them: either can be missing."""

    optics: str | None
    camera: str | None
    frames: int


@dataclass(slots=True)
class Proofs:
    nights: list[str] = field(default_factory=list)
    rigs: list[FrameRig] = field(default_factory=list)


def _sql(owner: str, source: str, where: str) -> str:
    return f"""
SELECT {owner} AS owner, f.local_night AS night, o.name AS optics, c.name AS camera,
       COUNT(*) AS n
FROM {source} LEFT JOIN rigs g ON g.id = f.rig_id
LEFT JOIN instruments o ON o.id = g.optics_id LEFT JOIN instruments c ON c.id = g.camera_id
WHERE f.copy_of IS NULL AND {owner} IS NOT NULL {where}
GROUP BY owner, night, optics, camera
"""  # noqa: S608 - constant fragments from the caller


def of(
    conn: sqlite3.Connection,
    owner: str,
    *,
    source: str = "frames f",
    where: str = "",
    args: Iterable[Any] = (),
) -> dict[Any, Proofs]:
    """`owner` is a column of `f` (or of `source`); `where` an `AND ...`. Rigs most used first."""
    nights: dict[Any, set[str]] = {}
    rigs: dict[Any, dict[tuple[str | None, str | None], int]] = {}
    for r in conn.execute(_sql(owner, source, where), tuple(args)):
        if r["night"]:
            nights.setdefault(r["owner"], set()).add(r["night"])
        if r["optics"] or r["camera"]:
            pair = rigs.setdefault(r["owner"], {})
            pair[r["optics"], r["camera"]] = pair.get((r["optics"], r["camera"]), 0) + r["n"]
    out: dict[Any, Proofs] = {}
    for key in nights.keys() | rigs.keys():
        pairs = sorted(
            rigs.get(key, {}).items(), key=lambda p: (-p[1], p[0][0] or "", p[0][1] or "")
        )
        out[key] = Proofs(
            nights=sorted(nights.get(key, ())),
            rigs=[FrameRig(optics=o, camera=c, frames=n) for (o, c), n in pairs],
        )
    return out


# A frame back in line for the solver: the sky has not looked at it yet.
_WAITING_SKY = """
SELECT DISTINCT f.object_id FROM frame_stages s JOIN frames f ON f.id = s.frame_id
WHERE s.stage = 'solve' AND s.status = 'pending' AND f.object_id IS NOT NULL
  AND f.copy_of IS NULL
"""


def waiting_for_sky(conn: sqlite3.Connection) -> set[int]:
    """The objects with some frame the solver has not looked at yet."""
    return {r["object_id"] for r in conn.execute(_WAITING_SKY)}
