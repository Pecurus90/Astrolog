"""A camera's colour for frames silent on the filter: without `BAYERPAT` mono and colour look alike.
The card first, then the files' vote; what sat in front is the gear answer (`signature.py`)."""

import sqlite3
from collections.abc import Mapping

from ..vocab.filters import Passband, normalize_filter, passband_of
from . import declarations as decl
from .stages import invalidate

COLOR = decl.CAMERA_COLOR

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


def declare_sensor(
    conn: sqlite3.Connection, camera_name: str, colour: bool, now: str | None = None
) -> None:
    """A filter answer also writes mono, over an earlier "colour" too, unless the files say colour:
    there the answer speaks of the filter, and the sensor is theirs to tell."""
    if colour:
        decl.declare_instrument_spec(conn, "camera", camera_name, "camera_type", COLOR, now)
    elif not _voted_colour(conn, camera_name):
        spec = decl.CAMERA_MONO
        decl.declare_instrument_spec(conn, "camera", camera_name, "camera_type", spec, now)


def says_no_filter(filter_raw: str | None) -> bool:
    """Missing, garbage, or "none"."""
    canonical = normalize_filter(filter_raw, bayer=False)
    return canonical is None or passband_of(canonical) == Passband.NO_FILTER


def requeue(conn: sqlite3.Connection, camera_id: int) -> list[int]:
    """Copies and frames already answered included, or changing one's mind would move nothing.
    Frames with a matrix stay out: OSC whatever the answer, reworking them would be dead work."""
    frames = [r[0] for r in conn.execute(_OF_CAMERA, (camera_id,))]
    invalidate(conn, frames, "normalize")
    return frames
