"""Two spellings of one camera, asked and never merged alone: the criterion, the direction and the
no live in `docs/domini/spina.md`, *Due grafie della stessa camera sono una domanda*."""

import json
import re
import sqlite3
from collections.abc import Collection, Iterable
from typing import Any

from ..spine import counts, gear
from ..spine import declarations as decl
from ..vocab.header_value import normalize_header_value
from . import instrument_answer
from .models_review import LookalikeOut
from .models_review_apply import LookalikeEdit

# Real frames per camera, matched as the Gear page does (`counts.of`): a rewritten copy is not
# another frame. The rigs are in the `FROM`: a sub-select would search them per (frame, camera).
_CAMERAS = f"""
SELECT i.id, COUNT(f.id) AS frames
FROM instruments i
LEFT JOIN (frames f LEFT JOIN rigs g ON g.id = f.rig_id)
       ON f.copy_of IS NULL AND {counts.of(counts.Subject.INSTRUMENT, rigs_joined=True)}
WHERE i.id IN (SELECT value FROM json_each(?))
GROUP BY i.id
"""  # noqa: S608 - a fragment of the spine, not user values


def _frames_of(conn: sqlite3.Connection, ids: Iterable[int]) -> dict[int, int]:
    return {r["id"]: r["frames"] for r in conn.execute(_CAMERAS, (json.dumps(sorted(ids)),))}


def lookalikes(conn: sqlite3.Connection) -> list[LookalikeOut]:
    """On a tie of frames the first come is kept."""
    specs = gear.camera_specs(conn)
    distinct = _answered_no(conn)
    by_key: dict[tuple[str, float, str], list[dict[str, Any]]] = {}
    for r in conn.execute("SELECT id, name FROM instruments WHERE kind = 'camera'"):
        p = {**dict(r), **specs.get(r["id"], {})}
        name = _bare_name(p["name"])
        if name and p["pixel_size_um"] is not None:
            same = (name, p["pixel_size_um"], p["camera_type"] or decl.CameraType.MONO)
            by_key.setdefault(same, []).append(p)
    # frames are counted only for groups with a pair still to ask: one camera alone, or a group
    # where every pair already had a no, is not a question whichever is the most used
    groups = [g for g in by_key.values() if _still_asks(g, distinct)]
    frames = _frames_of(conn, [p["id"] for g in groups for p in g]) if groups else {}
    for p in (p for g in groups for p in g):
        p["frames"] = frames[p["id"]]
    out: list[LookalikeOut] = []
    for group in groups:
        kept = max(group, key=lambda p: (p["frames"], -p["id"]))
        out += [
            LookalikeOut(
                id=p["id"],
                name=p["name"],
                frames=p["frames"],
                into_id=kept["id"],
                into_name=kept["name"],
                into_frames=kept["frames"],
            )
            for p in group
            if p is not kept and frozenset((p["name"], kept["name"])) not in distinct
        ]
    out.sort(key=lambda q: (-(q.frames + q.into_frames), q.name))
    return out


def answer_all(conn: sqlite3.Connection, edits: Iterable[LookalikeEdit], now: str) -> set[int]:
    """The pairs are recomputed only after a merge: it moves frames and may change who stays in the
    next pair."""
    requeued: set[int] = set()
    asked: dict[tuple[int, int], LookalikeOut] | None = None
    for edit in edits:
        if asked is None:
            asked = {(q.id, q.into_id): q for q in lookalikes(conn)}
        pair = asked.pop((edit.id, edit.into_id), None)
        if pair is None:  # a pair no longer asked is an old page, said before writing
            raise LookupError(f"coppia {edit.id} {edit.into_id}")
        if edit.same:
            requeued |= instrument_answer.merge(conn, edit.id, edit.into_id, now)
            asked = None
            continue
        decl.write_declaration(
            conn,
            decl.EntityType.INSTRUMENT,
            decl.instrument_key("camera", pair.name),
            decl.not_same_as(pair.into_name),
            pair.into_name,
            now,
        )
    return requeued


def _still_asks(group: list[dict[str, Any]], distinct: Collection[frozenset[str]]) -> bool:
    names = [p["name"] for p in group]
    return any(
        frozenset((a, b)) not in distinct for i, a in enumerate(names) for b in names[i + 1 :]
    )


def _answered_no(conn: sqlite3.Connection) -> set[frozenset[str]]:
    """As sets of two names: the direction does not count."""
    return {
        frozenset((r["entity_key"].split("|", 1)[1], r["value"]))
        for r in conn.execute(
            "SELECT entity_key, value FROM declarations WHERE entity_type = 'instrument'"
            " AND substr(field, 1, ?) = ?",
            (len(decl.NOT_SAME_AS), decl.NOT_SAME_AS),
        )
    }


def _bare_name(name: str) -> str:
    return re.sub(r"\([^)]*\)|[^a-z0-9]", "", normalize_header_value(name))
