"""Frames that do not say their camera: the question per group (night plus the header values that
name a camera and an optics), its answer, and what it requeues. The night's rig comes first."""

import json
import logging
import sqlite3
from typing import Any

from ..clock import NIGHT_SQL
from ..db.row import Row
from ..units import known_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import telescope_is_mount
from . import declarations as decl
from . import frame_folder as folder
from . import objects as obj
from .night_rig import NIGHT_OF as _NIGHT_OF
from .night_rig import asks_camera as _asks
from .night_rig import night_rigs
from .stages import invalidate

log = logging.getLogger(__name__)

# The key's header values, after the night, in key order.
_HEADER = "f.telescope_raw, f.naxis1, f.naxis2, f.pixel_size_um"

# Grouped in SQL, never a row per frame. Focal and object ride along for the page, outside the key.
_BY_GROUP = f"""
SELECT {NIGHT_SQL} AS night, {_HEADER}, f.focal_mm_raw, f.software,
       {obj.SUBJECT} AS subject, SUM(f.copy_of IS NULL) AS n
FROM frames f {folder.JOIN}
{obj.SUBJECT_JOIN}
WHERE f.asks_camera = 1
GROUP BY night, {_HEADER}, f.focal_mm_raw, f.software, subject
"""  # noqa: S608 - a constant fragment of this file, not a user value

# Copies included: whoever answers requeues them too. `IS`, not `=`: "no date" is a group as well.
_POSES_OF_NIGHT = f"""
SELECT f.id, {NIGHT_SQL} AS night, f.instrument_raw, {_HEADER} FROM frames f {folder.JOIN}
WHERE {NIGHT_SQL} IS ?
"""  # noqa: S608 - the same constant fragment

_NATIVE_FOCAL = "SELECT focal_mm FROM instruments WHERE kind = 'optics' AND name = ?"


def group_key(
    night: str | None,
    telescope_raw: str | None,
    naxis1: int | None,
    naxis2: int | None,
    pixel_size_um: float | None,
) -> str:
    """From the raw values, without the focal (it drifts between files): a rename leaves it alone,
    and a later file with the same values finds it again."""
    telescope = normalize_header_value(telescope_raw) or None
    return json.dumps([night, telescope, naxis1, naxis2, pixel_size_um])


def key_of_row(r: Row, night: str | None) -> str:
    """The night comes apart because whoever moves it (`home_nights`) composes the old and new."""
    return group_key(night, r["telescope_raw"], r["naxis1"], r["naxis2"], r["pixel_size_um"])


def key_of_frame(conn: sqlite3.Connection, frame: Row) -> str:
    """Composed also for a frame outside every live folder: the answer reaches it all the same."""
    return key_of_row(frame, conn.execute(_NIGHT_OF, (frame["id"],)).fetchone()["night"])


def _only[T](valori: set[T | None]) -> T | None:
    """With two focals in one group nothing is chosen for the user, and a blank means "unknown"."""
    detti = {v for v in valori if v is not None}
    return detti.pop() if len(detti) == 1 else None


def _native_focal(conn: sqlite3.Connection, optics_name: str | None) -> float | None:
    """Proposed when the frames are silent: without a focal the answer's rig would stay a twin of
    the detected one forever (`rigs.rig_for`)."""
    if not optics_name:
        return None
    row = conn.execute(_NATIVE_FOCAL, (optics_name,)).fetchone()
    return None if row is None else row["focal_mm"]


def by_group(conn: sqlite3.Connection, only: str | None = None) -> list[dict[str, Any]]:
    """Largest first; a group the night resolves is not asked unless already answered. `only` keeps
    one group: the whole page for each answer of an Apply costs the square of the groups."""
    righe = [(r, key_of_row(r, r["night"])) for r in conn.execute(_BY_GROUP)]
    righe = [(r, k) for r, k in righe if only is None or k == only]
    notti = night_rigs(conn, {r["night"] for r, _ in righe if r["night"]}) if righe else {}
    risposte = {k: answer(conn, k) for k in {k for _, k in righe}}
    gruppi: dict[str, dict[str, Any]] = {}
    for r, chiave in righe:
        if risposte[chiave] is None and r["night"] in notti:
            continue
        scritto = (r["telescope_raw"] or "").strip() or None
        gruppo = gruppi.setdefault(chiave, {
            "key": chiave, "night": r["night"], "telescope": scritto,
            "width_px": r["naxis1"], "height_px": r["naxis2"], "pixel_um": r["pixel_size_um"],
            "frames": 0, "optics": set(), "focal": set(),
        })  # fmt: skip
        gruppo["frames"] += r["n"] or 0
        if r["n"]:  # an object with only copies in the group is not another frame
            obj.count_subject(gruppo, r["subject"], r["n"])
        # with the ASIAIR `TELESCOP` is the mount, for the whole group: same spelling
        if telescope_is_mount(r["software"]):
            gruppo["mount_named"] = True
        gruppo["optics"].add(decl.instrument_name(conn, "optics", r["telescope_raw"]))
        gruppo["focal"].add(known_focal(r["focal_mm_raw"]))
    out = [_shown(conn, g, risposte[g["key"]]) for g in obj.subjects(conn, gruppi.values())]
    return sorted(out, key=lambda g: (-g["frames"], g["key"]))


def _shown(
    conn: sqlite3.Connection, gruppo: dict[str, Any], risposta: dict[str, Any] | None
) -> dict[str, Any]:
    """The native focal is proposed only where the frames carry none."""
    optics, focal = _only(gruppo.pop("optics")), _only(gruppo.pop("focal"))
    optics = None if gruppo.pop("mount_named", False) else optics
    return {
        **gruppo,
        "optics": optics,
        "focal_mm": focal,
        "focal_suggested": None if focal is not None else _native_focal(conn, optics),
        "answer": risposta,
    }


def row_of(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return next(iter(by_group(conn, only=key)), None)


def declare(  # noqa: PLR0913
    conn: sqlite3.Connection,
    key: str,
    optics: str | None,
    camera: str | None,
    focal_mm: float | None,
    now: str | None = None,
) -> None:
    """Names, never row ids: a merge deletes the piece's row, and an answer on its id would not
    survive a reset of what was detected."""
    dato = {"optics": optics, "camera": camera, "focal_mm": focal_mm}
    decl.write_declaration(conn, decl.FRAME_GROUP, key, decl.GROUP_RIG, json.dumps(dato), now)


def follow_piece(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, now: str | None = None
) -> None:
    """On the old name the piece would be reborn beside the new one at the next round."""
    for chiave, valore in decl.values_of(conn, decl.FRAME_GROUP, decl.GROUP_RIG):
        dato = _read(valore)
        if dato is not None and dato[kind] == old_name:
            dato[kind] = new_name
            declare(conn, chiave, dato["optics"], dato["camera"], dato["focal_mm"], now)


def _read(value: object) -> dict[str, Any] | None:
    """A malformed row counts as no answer, and is logged: it is a user's answer being lost. The
    camera is the question, so without it there is nothing to read."""
    if value is None:
        return None  # no answer is not a malformed answer: nothing to log
    try:
        dato = json.loads(value) if isinstance(value, str) else None
    except ValueError:
        dato = None
    if not isinstance(dato, dict) or not isinstance(dato.get("camera"), str) or not dato["camera"]:
        log.warning("rigless: risposta sul gruppo illeggibile, ignorata")
        return None
    optics = dato.get("optics")
    return {
        "optics": optics if isinstance(optics, str) and optics else None,
        "camera": dato["camera"],
        "focal_mm": known_focal(dato.get("focal_mm")),
    }


def answer(conn: sqlite3.Connection, key: str | None) -> dict[str, Any] | None:
    return _read(decl.declared(conn, decl.FRAME_GROUP, key, decl.GROUP_RIG) if key else None)


def rig_of_frame(conn: sqlite3.Connection, frame: Row) -> dict[str, Any] | None:
    """Read again at every round, so it also holds for frames arriving with the same values."""
    return answer(conn, key_of_frame(conn, frame))


def frames_of(conn: sqlite3.Connection, row: Row) -> list[int]:
    """Copies included: they have a rig too, and their session looks at it."""
    return [
        r["id"] for r in conn.execute(_POSES_OF_NIGHT, (row["night"],))
        if _asks(r["instrument_raw"]) and key_of_row(r, r["night"]) == row["key"]
    ]  # fmt: skip


def requeue(conn: sqlite3.Connection, row: Row) -> list[int]:
    """Frames an earlier answer already settled are included: that is how one changes one's mind."""
    frames = frames_of(conn, row)
    invalidate(conn, frames, "normalize")
    return frames
