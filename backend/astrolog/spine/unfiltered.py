"""Frames that do not say their filter, asked per camera: without `BAYERPAT` mono and colour look
alike, and the answer is a fact about the camera that holds for frames still to come."""

import sqlite3
from collections.abc import Mapping
from typing import Any

from ..vocab.filters import NO_FILTER, normalize_filter, passband_of
from . import declarations as decl
from . import objects as obj
from .stages import WAITING_SQL, invalidate

# "Colour" IS the card's colour word; the other two share one field on the camera
# (`declarations.UNFILTERED`), and "one of yours" names the filter in `UNFILTERED_FILTER`.
COLOR, NO_FILTER_ANSWER, FILTER_ANSWER = decl.CAMERA_COLOR, "no_filter", "filter"
ANSWERS = (COLOR, NO_FILTER_ANSWER, FILTER_ANSWER)

# Frames with a matrix are OSC whatever the answer; frames waiting on their type may be darks.
_BY_CAMERA = f"""
SELECT i.name, {obj.SUBJECT} AS subject, COUNT(*) AS n
FROM frames f JOIN rigs r ON r.id = f.rig_id JOIN instruments i ON i.id = r.camera_id
{obj.SUBJECT_JOIN}
WHERE f.copy_of IS NULL AND f.bayer_pattern IS NULL AND f.asks_filter = 1 AND NOT ({WAITING_SQL})
GROUP BY i.id, subject
"""  # noqa: S608 - constant fragments of the spine, not user values

_COLOUR = "SELECT camera_type FROM instruments WHERE kind = 'camera' AND name = ?"

_OF_CAMERA = """
SELECT f.id FROM frames f JOIN rigs r ON r.id = f.rig_id
WHERE r.camera_id = ? AND f.bayer_pattern IS NULL
"""


def _voted_colour(conn: sqlite3.Connection, camera_name: str) -> bool:
    """What the FILES voted (`camera_specs`), not what the user wrote on the card."""
    row = conn.execute(_COLOUR, (camera_name,)).fetchone()
    return row is not None and row["camera_type"] == COLOR


def is_colour(
    conn: sqlite3.Connection,
    camera_name: str | None,
    voted: Mapping[str, str | None] | None = None,
) -> bool:
    """The card first, then the files' vote, as the page shows the card (`gear.camera_specs`).
    `voted` is the vote normalization takes before its round (`camera_specs.ahead`)."""
    if not camera_name:
        return False
    written = written_colour(conn, camera_name)
    if written is not None:
        return written == COLOR
    if voted is not None:
        return voted.get(camera_name) == COLOR
    return _voted_colour(conn, camera_name)


def written_colour(conn: sqlite3.Connection, camera_name: str) -> str | None:
    key = decl.instrument_key("camera", camera_name)
    return decl.declared(conn, "instrument", key, "camera_type")


def declare(
    conn: sqlite3.Connection,
    camera_name: str,
    answer: str,
    filter_name: str | None = None,
    now: str | None = None,
) -> None:
    """The non-colour answers also write mono on the card, unless the files say colour: there the
    answer speaks of the filter, and the sensor is theirs to tell."""
    if answer == COLOR:
        decl.declare_instrument_spec(conn, "camera", camera_name, "camera_type", COLOR, now)
        return
    if not _voted_colour(conn, camera_name):
        spec = decl.CAMERA_MONO
        decl.declare_instrument_spec(conn, "camera", camera_name, "camera_type", spec, now)
    key = decl.instrument_key("camera", camera_name)
    decl.write_declaration(conn, "instrument", key, decl.UNFILTERED, answer, now)
    if answer == FILTER_ANSWER:
        decl.write_declaration(conn, "instrument", key, decl.UNFILTERED_FILTER, filter_name, now)


def said(conn: sqlite3.Connection, camera_name: str | None) -> tuple[str | None, str | None]:
    """(answer, filter), the filter only with "one of yours". "Colour" is written on the card."""
    if not camera_name:
        return None, None
    key = decl.instrument_key("camera", camera_name)
    risposta = decl.declared(conn, "instrument", key, decl.UNFILTERED)
    if risposta != FILTER_ANSWER:
        return risposta, None
    return risposta, decl.declared(conn, "instrument", key, decl.UNFILTERED_FILTER)


def follow_filter(conn: sqlite3.Connection, old_name: str, new_name: str) -> None:
    """Renamed or merged, the filter carries the answer along, or the camera's frames lose it."""
    conn.execute(
        "UPDATE declarations SET value = ? WHERE entity_type = 'instrument' AND field = ?"
        " AND value = ?",
        (new_name, decl.UNFILTERED_FILTER, old_name),
    )


def says_no_filter(filter_raw: str | None) -> bool:
    """Missing, garbage, or "none"."""
    canonical = normalize_filter(filter_raw, bayer=False)
    return canonical is None or passband_of(canonical) == NO_FILTER


def by_camera(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Non-colour cameras, largest first; `filter_id` is `None` once that filter is gone."""
    colore: dict[str, bool] = {}
    gruppi: dict[str, dict[str, Any]] = {}
    for r in conn.execute(_BY_CAMERA):
        if r["name"] not in colore:
            colore[r["name"]] = is_colour(conn, r["name"])
        if not colore[r["name"]]:
            gruppo = gruppi.setdefault(r["name"], {"key": r["name"], "frames": 0})
            gruppo["frames"] += r["n"]
            obj.count_subject(gruppo, r["subject"], r["n"])
    out = []
    for g in obj.subjects(conn, gruppi.values()):
        risposta, filtro = said(conn, g["key"])
        riga = conn.execute("SELECT id FROM filters WHERE name = ?", (filtro,)).fetchone()
        out.append({**g, "answer": risposta, "filter_id": riga and riga["id"]})
    return sorted(out, key=lambda g: (-g["frames"], g["key"]))


def requeue(conn: sqlite3.Connection, camera_id: int) -> list[int]:
    """Copies and frames already answered included, or changing one's mind would move nothing.
    Frames with a matrix stay out: OSC whatever the answer, reworking them would be dead work."""
    frames = [r[0] for r in conn.execute(_OF_CAMERA, (camera_id,))]
    invalidate(conn, frames, "normalize")
    return frames
