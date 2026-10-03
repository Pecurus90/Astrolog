"""The "which optics was it" question, once per camera and focal, for frames whose files do not name
the optics. The answer sits on the optics-less rig key, field `optics`, with the optics NAME."""

import json
import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

from ..units import same_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import telescope_is_mount
from . import counts
from . import frame_folder as folder
from . import objects as obj
from .declarations import rig_key, rig_key_parts, values_of, write_declaration
from .stages import invalidate

OPTICS = "optics"

# Live frames per rig and object, among those whose file does not name the optics.
_BY_RIG = f"""
SELECT f.rig_id, {obj.SUBJECT} AS subject,
       c.name AS camera, g.focal_mm, o.name AS optics, {counts.AGGREGATE}, {counts.UNTIMED}
FROM frames f {folder.JOIN}
JOIN rigs g ON g.id = f.rig_id JOIN instruments c ON c.id = g.camera_id
LEFT JOIN instruments o ON o.id = g.optics_id
{obj.SUBJECT_JOIN}
WHERE f.copy_of IS NULL AND f.names_optics = 0
GROUP BY f.rig_id, subject
"""  # noqa: S608 - constant fragments

# Copies included: they have a rig too.
_POSES_OF_RIGS = """
SELECT id, telescope_raw, software FROM frames
WHERE rig_id IN (SELECT value FROM json_each(?))
"""


def names_the_optics(software: str | None, telescope_raw: str | None) -> bool:
    """`TELESCOP` written, by a software that does not put the mount there: the same reading as
    `normalize_rig.rig_for_frame`."""
    return not telescope_is_mount(software) and bool(normalize_header_value(telescope_raw))


def _answer_for(
    answers: Iterable[sqlite3.Row], camera: str | None, focal_mm: float | None
) -> tuple[str, str, float | None] | None:
    """(key, optics, focal); the focal compares with the rigs' rule, so 800 mm answers for 803."""
    for chiave, ottica in answers:
        letta = rig_key_parts(chiave)
        if letta is not None and letta[1] == camera and same_focal(letta[2], focal_mm):
            return chiave, ottica, letta[2]
    return None


def declared(
    conn: sqlite3.Connection, camera: str | None, focal_mm: float | None
) -> tuple[str, str] | None:
    """(key, optics). The key is the optics-less rig's: whoever uses it finds there the name and
    mount given to it."""
    trovata = _answer_for(values_of(conn, "rig", OPTICS), camera, focal_mm)
    return None if trovata is None else trovata[:2]


def by_rig(conn: sqlite3.Connection, only: str | None = None) -> list[dict[str, Any]]:
    """Most shot first. A rig with optics from another answer (the camera one) is not asked; once
    answered, the question stays with its answer. `only` keeps one: the answerer's row."""
    risposte = values_of(conn, "rig", OPTICS)
    domande: dict[str, dict[str, Any]] = {}
    for r in conn.execute(_BY_RIG):
        trovata = _answer_for(risposte, r["camera"], r["focal_mm"])
        if trovata is None and r["optics"] is not None:
            continue
        chiave = trovata[0] if trovata else rig_key(None, r["camera"], r["focal_mm"])
        if only is not None and chiave != only:
            continue
        chiave, ottica, focale = trovata or (chiave, None, r["focal_mm"])
        domanda = domande.setdefault(chiave, {
            "key": chiave, "camera": r["camera"], "focal_mm": focale,
            "frames": 0, "integration_s": 0.0, "untimed": 0, "answer": ottica, "rigs": set(),
        })  # fmt: skip
        for campo in ("frames", "integration_s", "untimed"):
            domanda[campo] += r[campo] or 0
        obj.count_subject(domanda, r["subject"], r["frames"])
        domanda["rigs"].add(r["rig_id"])
    out = obj.subjects(conn, list(domande.values()))
    return sorted(out, key=lambda d: (-d["frames"], d["key"]))


def row_of(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return next(iter(by_rig(conn, only=key)), None)


def declare(conn: sqlite3.Connection, key: str, optics: str, now: str | None = None) -> None:
    """The NAME is written: the piece is born from it on the next pass, as from a header
    (`normalize_rig.instrument_named`)."""
    write_declaration(conn, "rig", key, OPTICS, optics, now)


def requeue(conn: sqlite3.Connection, row: Mapping[str, Any]) -> list[int]:
    """Only the frames of its rigs that do not name the optics: those that write it stay put."""
    pose = conn.execute(_POSES_OF_RIGS, (json.dumps(sorted(row["rigs"])),)).fetchall()
    frames = [p["id"] for p in pose if not names_the_optics(p["software"], p["telescope_raw"])]
    invalidate(conn, frames, "normalize")
    return frames
