"""What the FILES say of a camera's card, physical pixel and colour, voted by its frames. The most
frequent value wins and a tie gives none; who wins on reading: `gear.camera_specs`."""

import sqlite3
from collections import Counter
from collections.abc import Collection, Iterable, Mapping

from ..units import most_frequent, physical_pixel_um
from . import declarations as decl
from . import normalize_store as store
from . import unfiltered


def ahead(
    conn: sqlite3.Connection, frame_ids: Collection[int], pending: Iterable[tuple[str, bool]]
) -> dict[str, str | None]:
    """`{camera name: colour}` as the run's end will vote it, queued frames with the camera this
    pass gives them. Unqueued matrix-less frames of a camera changing colour are requeued."""
    votes: dict[str, Counter[bool]] = {}
    for r in store.camera_votes(conn, leaving_out=frame_ids):
        votes.setdefault(r["camera"], Counter())[bool(r["color"])] += r["n"]
    for camera, bayer in pending:
        votes.setdefault(camera, Counter())[bayer] += 1
    colours = {camera: _colour(v) for camera, v in votes.items()}
    for camera_id, (name, voted) in store.camera_colours(conn).items():
        if colours[name] != voted and unfiltered.written_colour(conn, name) is None:
            unfiltered.requeue(conn, camera_id)
    return colours


def from_files(conn: sqlite3.Connection, used: Mapping[str, str | None] | None = None) -> None:
    """Redone after every pass that worked a frame, so the first file does not decide for good. A
    colour other than the one the frames chose with requeues the camera's matrix-less frames."""
    before = store.camera_colours(conn)
    for camera_id, (colour, pixel) in _voted(store.camera_votes(conn)).items():
        store.set_camera_specs(conn, camera_id, colour, pixel)
        name, voted = before[camera_id]
        chosen = (used or {}).get(name, voted)  # the colour the frames chose with
        if chosen != colour and unfiltered.written_colour(conn, name) is None:
            unfiltered.requeue(conn, camera_id)


def _colour(votes: Counter[bool]) -> str | None:
    """A tie gives none: between two values of the same weight none is picked at random."""
    return decl.CameraType.COLOR if most_frequent(+votes) else None


def _voted(rows: Iterable[sqlite3.Row]) -> dict[int, tuple[str | None, float | None]]:
    """`{camera id: (colour, physical pixel)}` from `normalize_store.camera_votes`."""
    votes: dict[int, tuple[Counter[float | None], Counter[bool]]] = {}
    for r in rows:
        pixels, colours = votes.setdefault(r["camera_id"], (Counter(), Counter()))
        pixels[physical_pixel_um(r["pixel_size_um"], r["binning"])] += r["n"]
        colours[bool(r["color"])] += r["n"]
    out: dict[int, tuple[str | None, float | None]] = {}
    for camera_id, (pixels, colours) in votes.items():
        pixels.pop(None, None)  # no physical pixel, no vote
        out[camera_id] = (_colour(colours), most_frequent(pixels))
    return out
