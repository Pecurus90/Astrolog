"""The gear, read: nothing is computed here. Hours the app cannot know arrive `None`, not zero
(`gear_usage` decides); a piece born mid-round has `counted` false: not yet is not unknowable."""

import json
import sqlite3
from typing import Any

from . import gear
from . import rigs as corredi

_USO = """u.frames, u.integration_s, u.untimed, u.nights, u.scale_arcsec_px, u.width_deg,
       u.height_deg, u.objects_json"""

_STRUMENTI = f"""
SELECT i.*, {_USO}
FROM instruments i
LEFT JOIN gear_usage u ON u.subject = 'instrument' AND u.subject_id = i.id
ORDER BY i.kind, i.name
"""  # noqa: S608 - constant fragment of this file

# The order the counter wrote (`position`, most used first); a row not yet counted goes last.
_CORREDI = f"""
SELECT g.id, g.focal_mm, o.name AS optics, c.name AS camera, {_USO}
FROM rigs g LEFT JOIN instruments o ON o.id = g.optics_id
            LEFT JOIN instruments c ON c.id = g.camera_id
LEFT JOIN gear_usage u ON u.subject = 'rig' AND u.subject_id = g.id
ORDER BY u.position IS NULL, u.position, g.id
"""  # noqa: S608 - constant fragment of this file

# "No filter" is the row marking a frame with no glass in front, not a filter you own.
_FILTRI = f"""
SELECT x.*, {_USO}
FROM filters x
LEFT JOIN gear_usage u ON u.subject = 'filter' AND u.subject_id = x.id
WHERE x.is_none = 0
ORDER BY u.position IS NULL, u.position, x.name
"""  # noqa: S608 - constant fragment of this file

_BANDE = "SELECT filter_id, band, width_nm FROM filter_bands ORDER BY filter_id, band"


def instruments(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    # A camera's colour and pixel the user writes among the declarations, not in the column, which
    # belongs to the files: the column alone would show what the files say over the user.
    dichiarato = gear.camera_specs(conn)
    return [
        {**_riga(r), **dichiarato.get(r["id"], {}), "no_hours": _senza_ore(r)}
        for r in conn.execute(_STRUMENTI).fetchall()
    ]


def _senza_ore(r: sqlite3.Row) -> str | None:
    """A mount without frames is not "the files are silent": no rig carries it yet, even where
    other mounts have hours."""
    if r["objects_json"] is None:
        return None  # not counted yet: `counted` says so
    if r["kind"] == "mount" and not r["frames"]:
        return "no_rig"
    return "files_silent" if r["frames"] is None else None


def rigs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    nomi, montature = corredi.rig_names(conn), corredi.rig_mounts(conn)
    return [
        {
            **_riga(r),
            "name": nomi.get(corredi.decl_key(r)),
            "mount_id": montature.get(corredi.decl_key(r)),
        }
        for r in conn.execute(_CORREDI).fetchall()
    ]


def filters(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    bande: dict[int, list[dict[str, Any]]] = {}
    for r in conn.execute(_BANDE):
        bande.setdefault(r["filter_id"], []).append({"band": r["band"], "width_nm": r["width_nm"]})
    return [{**_riga(r), "bands": bande.get(r["id"], [])} for r in conn.execute(_FILTRI).fetchall()]


def _riga(r: sqlite3.Row) -> dict[str, Any]:
    riga = {k: r[k] for k in r.keys() if k != "objects_json"}  # noqa: SIM118 - Row iterates values
    riga["counted"] = r["objects_json"] is not None
    riga["objects"] = json.loads(r["objects_json"] or "[]")
    return riga
