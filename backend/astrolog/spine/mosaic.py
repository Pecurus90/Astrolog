"""Written mosaics: `group` writes panels and mosaics once per frame, the answer whoever answers,
and nobody recomputes them. The product rule lives in `docs/domini/mosaico.md`."""

import json
import sqlite3
from collections.abc import Iterable
from typing import Any

from ..db.inserted import inserted_id
from . import declarations as decl
from . import mosaic_describe as descrizione
from . import mosaic_proposals as proposte
from . import mosaic_weight as peso
from . import object_answer as risposta
from .identify_geometry import frame_radius_deg, frame_shape
from .mosaic_geometry import Relation, overlap, same_pointing

_SKY = ("ra_deg", "dec_deg", "width_deg", "height_deg", "rotation_deg")

# In shooting order. Copies are not another frame.
_POSES = f"""
SELECT f.id, f.frame_hash, f.rig_id, f.panel_id, {", ".join("w." + c for c in _SKY)}
FROM frames f JOIN frame_wcs w ON w.frame_id = f.id
WHERE f.id IN (SELECT value FROM json_each(?)) AND f.copy_of IS NULL
ORDER BY f.date_obs IS NULL, f.date_obs, f.id
"""  # noqa: S608 - constant fragments

_BAND = f"""
SELECT id, mosaic_id, {", ".join(_SKY)} FROM panels
WHERE rig_id IS ? AND dec_deg BETWEEN ? AND ?
ORDER BY id
"""  # noqa: S608 - constant fragments

_NEW_PANEL = (
    f"INSERT INTO panels(rig_id, {', '.join(_SKY)}, radius_deg)"  # noqa: S608 - constant fragments
    " VALUES(?, ?, ?, ?, ?, ?, ?)"
)


def place(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> None:
    """A panel is measured on the frame that opened it: without a fixed anchor, a chain of steps
    under the threshold would walk across the sky."""
    widest: dict[int | None, float] = {}
    pannelli: set[int] = set()
    for pose in map(dict, conn.execute(_POSES, (json.dumps(list(frame_ids)),)).fetchall()):
        if pose["panel_id"] is not None:
            pannelli.add(pose["panel_id"])  # the one it leaves too: its mosaic is reweighed
            if _stays(conn, pose):
                continue
        if frame_shape(pose) is None or frame_radius_deg(pose) is None:
            continue  # without a sky, or the field's size, what it frames is unknown
        band = _band(conn, pose, widest)
        panel = next((p for p in band if same_pointing(p, pose)), None)
        panel_id = panel["id"] if panel else _open(conn, pose, band, widest)
        conn.execute("UPDATE frames SET panel_id = ? WHERE id = ?", (panel_id, pose["id"]))
        pannelli.add(panel_id)
    settle(conn, _mosaics_of(conn, pannelli))


def settle(conn: sqlite3.Connection, mosaic_ids: Iterable[int]) -> None:
    """Only the mosaics frames reached or left: reweighing them all would cost the whole archive
    on every run."""
    _sweep(conn)
    vivi = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM mosaics WHERE id IN (SELECT value FROM json_each(?))",
            (json.dumps(sorted(mosaic_ids)),),
        )
    ]
    peso.weigh(conn, vivi)
    for mosaic_id in vivi:
        descrizione.describe(conn, mosaic_id)
        _write_key(conn, mosaic_id)
    conn.execute(
        "UPDATE frames SET mosaic_key = NULL"  # noqa: S608 - constant fragments
        " WHERE mosaic_key IS NOT NULL AND mosaic_key NOT IN"
        f" (SELECT m.key FROM mosaics m JOIN ({proposte.LIVE}) r ON r.mosaic_id = m.id)"
    )


def _mosaics_of(conn: sqlite3.Connection, panel_ids: Iterable[int]) -> set[int]:
    """Asked before the empty panels are removed."""
    return {
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT mosaic_id FROM panels WHERE id IN (SELECT value FROM json_each(?))"
            " AND mosaic_id IS NOT NULL",
            (json.dumps(sorted(panel_ids)),),
        )
    }


def leave(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> set[int]:
    """The mosaics they leave, to reweigh with `settle`: after the detach nothing says so any
    more."""
    lista = json.dumps(list(frame_ids))
    lasciati = _mosaics_of(
        conn,
        [r[0] for r in conn.execute(
            "SELECT panel_id FROM frames WHERE id IN (SELECT value FROM json_each(?))"
            " AND panel_id IS NOT NULL", (lista,),
        )],
    )  # fmt: skip
    conn.execute(
        "UPDATE frames SET panel_id = NULL, mosaic_key = NULL"
        " WHERE id IN (SELECT value FROM json_each(?))",
        (lista,),
    )
    return lasciati


def _stays(conn: sqlite3.Connection, pose: dict[str, Any]) -> bool:
    """A frame that changed rig stays if its mosaic has an answer, the panel taking the new rig
    once all its frames have it; otherwise it re-places and joins that rig's mosaic there."""
    row = conn.execute(
        "SELECT p.rig_id, m.key FROM panels p LEFT JOIN mosaics m ON m.id = p.mosaic_id"
        " WHERE p.id = ?",
        (pose["panel_id"],),
    ).fetchone()
    if row["rig_id"] == pose["rig_id"]:
        return True
    if row["key"] is not None and answer_of(conn, row["key"]) is not None:
        conn.execute(
            "UPDATE panels SET rig_id = ? WHERE id = ? AND NOT EXISTS"
            " (SELECT 1 FROM frames f WHERE f.panel_id = ? AND f.rig_id IS NOT ?)",
            (pose["rig_id"], pose["panel_id"], pose["panel_id"], pose["rig_id"]),
        )
        return True
    leave(conn, [pose["id"]])
    return False


def _sweep(conn: sqlite3.Connection) -> None:
    """An empty panel would still bind its neighbours."""
    conn.execute(
        "DELETE FROM panels WHERE NOT EXISTS (SELECT 1 FROM frames f WHERE f.panel_id = panels.id)"
    )
    conn.execute(
        "DELETE FROM mosaics WHERE NOT EXISTS"
        " (SELECT 1 FROM panels p WHERE p.mosaic_id = mosaics.id)"
    )


def write_answer(conn: sqlite3.Connection, key: str, value: str, now: str | None = None) -> None:
    """`decl.MosaicAnswer.NO` or the target. A mosaic that is gone or down to one panel is a stale
    page, and raises: an answer to nothing would sit there unseen."""
    row = conn.execute(
        f"SELECT m.id FROM mosaics m JOIN ({proposte.LIVE}) r ON r.mosaic_id = m.id"  # noqa: S608
        " WHERE m.key = ?",
        (key,),
    ).fetchone()
    if row is None:
        raise LookupError(f"mosaico {key}")
    decl.write_declaration(conn, decl.EntityType.MOSAIC, key, decl.MOSAIC_FIELD, value, now)
    _write_key(conn, row["id"])


def answer_of(conn: sqlite3.Connection, key: str) -> str | None:
    return decl.declared(conn, decl.EntityType.MOSAIC, key, decl.MOSAIC_FIELD)


def _band(
    conn: sqlite3.Connection, pose: dict[str, Any], widest: dict[int | None, float]
) -> list[dict[str, Any]]:
    """The rig's panels within reach in declination, never the archive; right ascension is left to
    the geometry. The rig's widest radius is asked once per run."""
    rig = pose["rig_id"]
    if rig not in widest:
        (widest[rig],) = conn.execute(
            "SELECT COALESCE(MAX(radius_deg), 0) FROM panels WHERE rig_id IS ?", (rig,)
        ).fetchone()
    reach = widest[rig] + (frame_radius_deg(pose) or 0.0)
    righe = conn.execute(_BAND, (pose["rig_id"], pose["dec_deg"] - reach, pose["dec_deg"] + reach))
    return [dict(r) for r in righe]


def _open(
    conn: sqlite3.Connection,
    pose: dict[str, Any],
    band: list[dict[str, Any]],
    widest: dict[int | None, float],
) -> int:
    radius = frame_radius_deg(pose) or 0.0
    widest[pose["rig_id"]] = max(widest.get(pose["rig_id"], 0.0), radius)
    panel_id = inserted_id(
        conn.execute(_NEW_PANEL, (pose["rig_id"], *(pose[c] for c in _SKY), radius))
    )
    touching = [p for p in band if overlap(p, pose) == Relation.PARTIAL]
    if touching:
        _join(conn, panel_id, pose["frame_hash"], touching)
    return panel_id


def _join(
    conn: sqlite3.Connection, panel_id: int, frame_hash: str, touching: list[dict[str, Any]]
) -> None:
    """Into the oldest answered mosaic, or the oldest; it takes only the unanswered others: two
    user answers never merge silently."""
    ids = sorted({p["mosaic_id"] for p in touching if p["mosaic_id"] is not None})
    keys = dict(
        conn.execute(
            "SELECT id, key FROM mosaics WHERE id IN (SELECT value FROM json_each(?))",
            (json.dumps(ids),),
        ).fetchall()
    )
    answered = [i for i in ids if answer_of(conn, keys[i]) is not None]
    if ids:
        target = answered[0] if answered else ids[0]
        merged = [i for i in ids if i != target and i not in answered]
    else:
        # the same frames remaking the same mosaic get the same key back, and its answer
        target = conn.execute(
            "INSERT INTO mosaics(key, ra_deg, dec_deg, proposed) VALUES(?, 0, 0, '')"
            " ON CONFLICT(key) DO UPDATE SET key = excluded.key RETURNING id",
            (_new_key(conn, touching, frame_hash),),
        ).fetchone()[0]
        merged = []
    for i in merged:
        conn.execute("UPDATE panels SET mosaic_id = ? WHERE mosaic_id = ?", (target, i))
        conn.execute("DELETE FROM mosaics WHERE id = ?", (i,))
    free = [p["id"] for p in touching if p["mosaic_id"] is None] + [panel_id]
    conn.executemany("UPDATE panels SET mosaic_id = ? WHERE id = ?", [(target, i) for i in free])


def _new_key(conn: sqlite3.Connection, panels: list[dict[str, Any]], frame_hash: str) -> str:
    """The oldest frame's hash, fixed at birth, never a live mosaic's key: a frame that changed rig
    carries its old mosaic's key, and reusing it would join the two across rigs."""
    for (candidate,) in conn.execute(
        "SELECT frame_hash FROM frames WHERE panel_id IN (SELECT value FROM json_each(?))"
        " ORDER BY date_obs IS NULL, date_obs, id",
        (json.dumps([p["id"] for p in panels]),),
    ):
        if not _alive(conn, candidate):
            return candidate
    return frame_hash


def _alive(conn: sqlite3.Connection, key: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM mosaics m JOIN panels p ON p.mosaic_id = m.id WHERE m.key = ? LIMIT 1",
            (key,),
        ).fetchone()
        is not None
    )


def _write_key(conn: sqlite3.Connection, mosaic_id: int) -> None:
    """Only a yes writes the key, and not on panels that do not count: those frames keep their
    object."""
    (key,) = conn.execute("SELECT key FROM mosaics WHERE id = ?", (mosaic_id,)).fetchone()
    confirmed = key if risposta.mosaic_word(answer_of(conn, key)) == decl.MosaicAnswer.YES else None
    conn.execute(
        "UPDATE frames SET mosaic_key = CASE WHEN p.counts_in_mosaic = 1 THEN ? END"
        " FROM panels p WHERE frames.panel_id = p.id AND p.mosaic_id = ?",
        (confirmed, mosaic_id),
    )
