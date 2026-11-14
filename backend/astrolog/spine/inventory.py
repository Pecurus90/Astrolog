"""The gear, read: nothing is computed here. Hours the app cannot know arrive `None`, not zero
(`gear_usage` decides); a piece born mid-round has `counted` false: not yet is not unknowable."""

import json
import sqlite3
from typing import Any

from . import filters_used, gear
from . import rigs as gear_rigs

_USAGE = """u.frames, u.integration_s, u.untimed, u.nights, u.scale_arcsec_px, u.width_deg,
       u.height_deg, u.objects_json, u.bar_pct"""

_INSTRUMENTS = f"""
SELECT i.*, {_USAGE}
FROM instruments i
LEFT JOIN gear_usage u ON u.subject = 'instrument' AND u.subject_id = i.id
ORDER BY i.kind, i.name COLLATE NOCASE, i.id
"""  # noqa: S608 - constant fragment of this file

# The order the counter wrote (`position`, most used first); a row not yet counted goes last.
_RIGS = f"""
SELECT g.id, g.focal_mm, g.optics_id, g.camera_id, o.name AS optics, c.name AS camera,
       o.brand AS optics_brand,
       o.model AS optics_model, c.brand AS camera_brand, c.model AS camera_model, {_USAGE}
FROM rigs g LEFT JOIN instruments o ON o.id = g.optics_id
            LEFT JOIN instruments c ON c.id = g.camera_id
LEFT JOIN gear_usage u ON u.subject = 'rig' AND u.subject_id = g.id
ORDER BY u.position IS NULL, u.position, g.id
"""  # noqa: S608 - constant fragment of this file

# "No filter" is the row marking a frame with no glass in front, not a filter you own.
_FILTERS = f"""
SELECT x.*, {_USAGE}
FROM filters x
LEFT JOIN gear_usage u ON u.subject = 'filter' AND u.subject_id = x.id
WHERE x.is_none = 0
ORDER BY {filters_used.order_by("x")}
"""  # noqa: S608 - constant fragment of this file

_BANDS = "SELECT filter_id, band, width_nm FROM filter_bands ORDER BY filter_id, band"

# The name is the piece's now, not the one it had when counted: a rename reads at once.
_PARTS = """
SELECT p.rig_id, p.kind, p.piece_id AS id, p.frames, p.chosen, p.ring_from, p.ring_to,
       COALESCE(p.software, x.name, i.name) AS name, x.passband
FROM rig_parts p
LEFT JOIN filters x ON p.kind = 'filter' AND x.id = p.piece_id
LEFT JOIN instruments i ON p.kind NOT IN ('filter', 'software') AND i.id = p.piece_id
ORDER BY p.rig_id, p.position
"""


_NUMBERS = "SELECT subject_id, numbers_json FROM gear_numbers WHERE subject = ?"

# The rigs holding a piece: as a part (`rig_parts`), or as their optics or camera, with the rig's
# frames. Whoever deletes reads it before the gesture.
_IN_RIGS = """
SELECT 'instrument' AS subject, piece_id AS id, rig_id, frames, chosen FROM rig_parts
WHERE kind NOT IN ('filter', 'software')
UNION ALL
SELECT 'filter', piece_id, rig_id, frames, chosen FROM rig_parts WHERE kind = 'filter'
UNION ALL
SELECT 'instrument', p.id, g.id, COALESCE(u.frames, 0), 0
FROM rigs g JOIN instruments p ON p.id IN (g.optics_id, g.camera_id)
LEFT JOIN gear_usage u ON u.subject = 'rig' AND u.subject_id = g.id
ORDER BY 1, 2, 3
"""


_MAKERS = "SELECT id, optics_id, camera_id FROM rigs ORDER BY id"

# A camera's offsets through the bridge (ADR 0045): the bias belongs to the camera as the files
# write it, so a camera of the page reaches it through its frames' files.
_OFFSETS = """
SELECT g.camera_id, c.camera, c.offset, COUNT(DISTINCT f.id) AS frames
FROM frames f JOIN rigs g ON g.id = f.rig_id
JOIN night_measure_frames b ON b.frame_id = f.id
JOIN pipeline_files pf ON pf.frame_id = b.pipeline_frame_id
JOIN pipeline_cards c ON c.file_id = pf.id
WHERE g.camera_id IS NOT NULL AND f.copy_of IS NULL AND c.camera IS NOT NULL
  AND c.frame_type = 'light'
GROUP BY g.camera_id, c.camera, c.offset
ORDER BY g.camera_id, c.camera, c.offset
"""

_DECLARED_BIAS = "SELECT camera, offset, bias_adu FROM pipeline_camera_bias"


def camera_spellings(conn: sqlite3.Connection, camera_id: int) -> list[tuple[str, int | None]]:
    """The camera and offset pairs its files write: where a bias declared on the page goes."""
    return [
        (r["camera"], r["offset"])
        for r in conn.execute(_OFFSETS).fetchall()
        if r["camera_id"] == camera_id
    ]


def _biases(conn: sqlite3.Connection) -> dict[int, list[dict[str, Any]]]:
    declared = {(r[0], r[1]): r[2] for r in conn.execute(_DECLARED_BIAS)}
    by_camera: dict[int, dict[int | None, dict[str, Any]]] = {}
    for r in conn.execute(_OFFSETS):
        row = by_camera.setdefault(r["camera_id"], {}).setdefault(
            r["offset"], {"offset": r["offset"], "bias_adu": None, "frames": 0}
        )
        row["frames"] += r["frames"]
        bias = declared.get((r["camera"], r["offset"]))
        row["bias_adu"] = row["bias_adu"] if bias is None else bias
    return {
        cam: sorted(rows.values(), key=lambda b: (b["offset"] is not None, b["offset"] or 0))
        for cam, rows in by_camera.items()
    }


# "ZWO" and "Zwo" are one maker: the first written spelling stands for both
_BRANDS = """
SELECT MIN(brand) FROM (
  SELECT brand FROM instruments WHERE brand IS NOT NULL
  UNION ALL SELECT brand FROM filters WHERE brand IS NOT NULL AND is_none = 0
) GROUP BY brand COLLATE NOCASE ORDER BY 1 COLLATE NOCASE
"""


def brands(conn: sqlite3.Connection) -> list[str]:
    """The makers already written, for "altra" in the card's Marca."""
    return [r[0] for r in conn.execute(_BRANDS)]


def camera_biases(conn: sqlite3.Connection, camera_id: int) -> list[dict[str, Any]]:
    return _biases(conn).get(camera_id, [])


def _refused(row: dict[str, Any], held: list[dict[str, Any]], makes: list[int]) -> Any:
    """The DELETE's refusal, from the counted frames: `gear_delete` refuses the same way."""
    if row["frames"]:
        rigs = sorted({h["rig_id"] for h in held if h["frames"]})
        return {"code": "in_use", "frames": row["frames"], "rigs": rigs}
    if makes:
        return {"code": "in_rig", "frames": 0, "rigs": makes}
    return None


def _in_rigs(conn: sqlite3.Connection, subject: str) -> dict[int, list[dict[str, Any]]]:
    held: dict[int, list[dict[str, Any]]] = {}
    for r in conn.execute(_IN_RIGS):
        if r["subject"] == subject:
            row = {"rig_id": r["rig_id"], "frames": r["frames"], "chosen": bool(r["chosen"])}
            held.setdefault(r["id"], []).append(row)
    return held


def _numbers(conn: sqlite3.Connection, subject: str) -> dict[int, Any]:
    """What `gear_numbers` wrote: a row not yet written reads as none, never recomputed here."""
    return {r[0]: json.loads(r[1]) for r in conn.execute(_NUMBERS, (subject,))}


def instruments(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    # A camera's colour and pixel the user writes among the declarations, not in the column, which
    # belongs to the files: the column alone would show what the files say over the user.
    declared = gear.camera_specs(conn)
    numbers = _numbers(conn, "instrument")
    held = _in_rigs(conn, "instrument")
    told = gear.files_told(conn)
    biases = _biases(conn)
    makes: dict[int, list[int]] = {}
    for g in conn.execute(_MAKERS):
        for piece in {g["optics_id"], g["camera_id"]} - {None}:
            makes.setdefault(piece, []).append(g["id"])
    rows = []
    for r in conn.execute(_INSTRUMENTS).fetchall():
        row = _row(r)
        rows.append(
            {
                **row,
                **declared.get(r["id"], {}),
                "no_hours": no_hours(r),
                "numbers": numbers.get(r["id"], {}),
                "in_rigs": held.get(r["id"], []),
                "from_files": told.get(r["id"], []),
                "delete_refused": _refused(row, held.get(r["id"], []), makes.get(r["id"], [])),
                "rig_for_mount": None,
                "biases": biases.get(r["id"], []),
            }
        )
    return rows


def no_hours(r: sqlite3.Row) -> str | None:
    """A mount, reducer or guide scope without frames is not "the files are silent": no rig
    carries it yet, even where others of its kind have hours."""
    if r["objects_json"] is None:
        return None  # not counted yet: `counted` says so
    if r["kind"] in gear_rigs.NEEDS_A_RIG and not r["frames"]:
        return "no_rig"
    return "files_silent" if r["frames"] is None else None


def rigs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    names = gear_rigs.rig_names(conn)
    numbers = _numbers(conn, "rig")
    parts: dict[int, list[dict[str, Any]]] = {}
    for p in conn.execute(_PARTS):
        # a piece merged away since the count has no name until the next one: left out, not blank
        if p["name"] is not None:
            part = {
                k: p[k]
                for k in ("kind", "id", "name", "frames", "passband", "ring_from", "ring_to")
            }
            parts.setdefault(p["rig_id"], []).append({**part, "chosen": bool(p["chosen"])})
    rows = []
    for r in conn.execute(_RIGS).fetchall():
        written = numbers.get(r["id"])
        # the pieces the numbers read are written with them; on the page they are not a number
        pieces = written.pop("pieces") if written else None
        rows.append(
            {
                **_row(r),
                "name": names.get(gear_rigs.decl_key(r)),
                "parts": parts.get(r["id"], []),
                "numbers": written,
                "pieces": pieces,
            }
        )
    return rows


# Widest first: on the frame the narrow boxes sit over the wide ones.
_FIELDS = """
SELECT subject_id AS rig_id, field_w_pct AS width_pct, field_h_pct AS height_pct, moon_pct
FROM gear_usage WHERE subject = 'rig' AND field_w_pct IS NOT NULL
ORDER BY field_w_pct DESC, subject_id
"""


def fields(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], float | None]:
    """The rigs' boxes on the comparison frame and the Moon on it, as `write_fields` wrote them."""
    rows = conn.execute(_FIELDS).fetchall()
    boxes = [{k: r[k] for k in ("rig_id", "width_pct", "height_pct")} for r in rows]
    return boxes, rows[0]["moon_pct"] if rows else None


def filters(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    bands: dict[int, list[dict[str, Any]]] = {}
    for r in conn.execute(_BANDS):
        bands.setdefault(r["filter_id"], []).append({"band": r["band"], "width_nm": r["width_nm"]})
    held = _in_rigs(conn, "filter")
    rows = []
    for r in conn.execute(_FILTERS).fetchall():
        row = {**_row(r), "bands": bands.get(r["id"], []), "in_rigs": held.get(r["id"], [])}
        row["delete_refused"] = _refused(row, row["in_rigs"], [])
        rows.append(row)
    return rows


def _row(r: sqlite3.Row) -> dict[str, Any]:
    row = {k: r[k] for k in r.keys() if k != "objects_json"}  # noqa: SIM118 - Row iterates values
    row["counted"] = r["objects_json"] is not None
    row["objects"] = json.loads(r["objects_json"] or "[]")
    return row
