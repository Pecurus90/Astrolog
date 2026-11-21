"""A camera's colour for frames silent on the filter: without `BAYERPAT` mono and colour look alike.
The card first, then the files' vote; what sat in front is the gear answer (`signature.py`)."""

import sqlite3
from collections.abc import Callable, Mapping

from ..db.declared import declared_by_key
from ..vocab.filters import Passband, normalize_filter, passband_of
from ..vocab.instruments import InstrumentKind
from . import declarations as decl
from .declarations import CameraType
from .stages import StageName, invalidate

_COLOUR = "SELECT camera_type FROM instruments WHERE kind = 'camera' AND name = ?"
_COLOURS = "SELECT name, camera_type FROM instruments WHERE kind = 'camera'"

_OF_CAMERA = """
SELECT f.id FROM frames f JOIN rigs r ON r.id = f.rig_id
WHERE r.camera_id = ? AND f.bayer_pattern IS NULL
"""


def _voted_colour(conn: sqlite3.Connection, camera_name: str) -> bool:
    """What the FILES voted (`camera_specs`), not what the user wrote on the card."""
    row = conn.execute(_COLOUR, (camera_name,)).fetchone()
    return row is not None and row["camera_type"] == CameraType.COLOR


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
        return written == CameraType.COLOR
    if voted is not None:
        return voted.get(camera_name) == CameraType.COLOR
    return _voted_colour(conn, camera_name)


def colour_reader(conn: sqlite3.Connection) -> Callable[[str | None], bool]:
    """`is_colour` for many cameras, same rule: the cards and the files' votes read once each."""
    written = declared_by_key(conn, decl.EntityType.INSTRUMENT, "camera_type")
    voted = {r["name"]: r["camera_type"] for r in conn.execute(_COLOURS)}

    def colour(camera_name: str | None) -> bool:
        if not camera_name:
            return False
        said = written.get(decl.instrument_key(InstrumentKind.CAMERA, camera_name))
        return (said if said is not None else voted.get(camera_name)) == CameraType.COLOR

    return colour


def written_colour(conn: sqlite3.Connection, camera_name: str) -> str | None:
    key = decl.instrument_key(InstrumentKind.CAMERA, camera_name)
    return decl.declared(conn, decl.EntityType.INSTRUMENT, key, "camera_type")


def declare_sensor(
    conn: sqlite3.Connection, camera_name: str, colour: bool, now: str | None = None
) -> None:
    """A filter answer also writes mono, over an earlier "colour" too, unless the files say colour:
    there the answer speaks of the filter, and the sensor is theirs to tell."""
    if colour:
        spec = CameraType.COLOR
    elif not _voted_colour(conn, camera_name):
        spec = CameraType.MONO
    else:
        return
    decl.declare_instrument_spec(conn, InstrumentKind.CAMERA, camera_name, "camera_type", spec, now)


def says_no_filter(filter_raw: str | None) -> bool:
    """Missing, garbage, or "none"."""
    canonical = normalize_filter(filter_raw, bayer=False)
    return canonical is None or passband_of(canonical) == Passband.NO_FILTER


def requeue(conn: sqlite3.Connection, camera_id: int) -> list[int]:
    """Copies and frames already answered included, or changing one's mind would move nothing.
    Frames with a matrix stay out: OSC whatever the answer, reworking them would be dead work."""
    frames = [r[0] for r in conn.execute(_OF_CAMERA, (camera_id,))]
    invalidate(conn, frames, StageName.NORMALIZE)
    return frames
