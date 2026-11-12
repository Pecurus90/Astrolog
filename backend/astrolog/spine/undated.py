"""Frames that do not say when, asked per folder: the file's date on disk is the copy's, shown and
never used. The answer is the evening on the site, also for files that arrive later there."""

import json
import sqlite3
from typing import Any

from . import declarations as decl
from . import frame_folder as folder
from .stages import StageName, invalidate

# The night's date the user said, on the folder: the `group` stage reads it.
FOLDER_NIGHT = "night"

# `julianday` fails where `clock.night_date` fails on canonical dates; only the calendar's first and
# last days differ. A frame grouped by the answer keeps a NULL date: the question stays.
_UNDATED = f"""
SELECT {folder.COLUMNS}, f.id, f.copy_of, f.exposure_s, f.local_night, f.rig_id, f.site_lat,
       f.site_lon
FROM frames f {folder.JOIN}
WHERE f.image_type = 'light' AND julianday(f.date_obs) IS NULL
ORDER BY f.id
"""  # noqa: S608 - constants of frame_folder

_KEY_OF = f"SELECT ({folder.KEY_OF_FRAME}) FROM frames f WHERE f.id = ?"  # noqa: S608

# The nights a rig already has: "a night with the same setup" is one of these.
_RIG_NIGHTS = """
SELECT DISTINCT s.rig_id, n.night_date FROM sessions s JOIN nights n ON n.id = s.night_id
WHERE s.rig_id IN (SELECT value FROM json_each(?))
"""


def by_folder(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Largest first. `frame_ids` holds copies too: a copy is grouped like its original."""
    groups: dict[str, dict[str, Any]] = {}
    for r in conn.execute(_UNDATED):
        # the first frame's coordinates say the site, as for the frames of one night
        g = folder.group_of(groups, r, frames=0, integration_s=0.0, untimed=0,
                            file_nights=set(), rig_ids=set(), frame_ids=[],
                            site_lat=r["site_lat"], site_lon=r["site_lon"])  # fmt: skip
        g["frame_ids"].append(r["id"])
        if r["copy_of"] is not None:
            continue
        g["frames"] += 1
        g["integration_s"] += r["exposure_s"] or 0.0
        g["untimed"] += r["exposure_s"] is None
        if r["local_night"]:
            g["file_nights"].add(r["local_night"])
        if r["rig_id"] is not None:
            g["rig_ids"].add(r["rig_id"])
    out = sorted(
        (g for g in groups.values() if g["frames"]), key=lambda g: (-g["frames"], g["key"])
    )
    for g in out:
        g["file_nights"] = sorted(g["file_nights"])
        g["answer"] = answer(conn, g["key"])
    return out


def rig_nights(conn: sqlite3.Connection, rig_ids: set[int]) -> list[str]:
    """Most recent first: the shot without a date is usually a recent one being sorted out."""
    rows = conn.execute(_RIG_NIGHTS, (json.dumps(sorted(rig_ids)),))
    return sorted({r["night_date"] for r in rows}, reverse=True)


def answer(conn: sqlite3.Connection, key: str) -> str | None:
    value = decl.declared(conn, decl.EntityType.FOLDER, key, FOLDER_NIGHT)
    return value if isinstance(value, str) else None


def answer_of_frame(conn: sqlite3.Connection, frame_id: int) -> str | None:
    """For `group`: the night said on the frame's folder, if any."""
    row = conn.execute(_KEY_OF, (frame_id,)).fetchone()
    return answer(conn, row[0]) if row and row[0] else None


def declare(conn: sqlite3.Connection, key: str, night: str, now: str) -> list[int]:
    """Written on the folder, then its frames are grouped again."""
    row = next((g for g in by_folder(conn) if g["key"] == key), None)
    if row is None:
        raise LookupError(f"cartella {key}")
    decl.write_declaration(conn, decl.EntityType.FOLDER, key, FOLDER_NIGHT, night, now)
    invalidate(conn, row["frame_ids"], StageName.GROUP, now=now)
    return row["frame_ids"]
