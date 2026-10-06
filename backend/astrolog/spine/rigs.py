"""The rig as the declarer sees it: its fingerprint, its key, what the user writes on it. A merge
can delete the row, so name and mount live among the declarations, on a key that outlives it."""

import json
import sqlite3
from enum import StrEnum

from ..clock import now_iso
from ..db.inserted import inserted_id
from ..units import same_focal
from . import gear_usage, signature
from .declarations import (
    EntityType,
    forget,
    instrument_id,
    rig_key,
    rig_key_parts,
    values_of,
    write_declaration,
)
from .gear_usage import UsageSubject
from .stages import StageName, invalidate


class RigField(StrEnum):
    """The fields of a rig's declarations."""

    NAME = "name"
    # the kind as field: the value is the mount's name
    MOUNT = "mount"
    DECLARED = "declared"


class NotAMountError(ValueError):
    """The piece asked to mount on a rig is not a mount."""


class WrongKindError(ValueError):
    """A rig is made of an optics and a camera you own: another piece does not fit."""


class RigExistsError(ValueError):
    """You already have that rig: same optics, same camera, focal within `units.FOCAL_TOLERANCE`."""


def rig_for(  # noqa: PLR0913
    conn: sqlite3.Connection,
    optics_id: int | None,
    camera_id: int | None,
    focal_mm: float | None,
    now: str,
    *,
    detected: bool = True,
) -> tuple[int, bool]:
    """(id, created?). `rigs.focal_mm` is fixed at creation: nearby focals join without moving it,
    which would rewrite a value the user has already seen."""
    found = find_rig(conn, optics_id, camera_id, focal_mm)
    if found is not None:
        return found, False
    rig_id = inserted_id(
        conn.execute(
            "INSERT INTO rigs(optics_id, camera_id, focal_mm, detected, created_at)"
            " VALUES(?, ?, ?, ?, ?)",
            (optics_id, camera_id, focal_mm, int(detected), now),
        )
    )
    return rig_id, True


def find_rig(
    conn: sqlite3.Connection, optics_id: int | None, camera_id: int | None, focal_mm: float | None
) -> int | None:
    """The unique index is on exact equality: the focal grouping (`units.same_focal`) lives here."""
    for row in conn.execute(
        "SELECT id, focal_mm FROM rigs WHERE optics_id IS ? AND camera_id IS ?",
        (optics_id, camera_id),
    ).fetchall():
        if same_focal(row["focal_mm"], focal_mm):
            return row["id"]
    return None


# What a rig carries to its frames' new key.
CARRIED_FIELDS = (RigField.NAME, RigField.MOUNT)


def optics_less_key(
    conn: sqlite3.Connection, camera: str | None, focal_mm: float | None
) -> str | None:
    """The key the user named or mounted the optics-less rig on, focal by the rigs' rule: the rig
    may be gone, its declarations are not."""
    keys = conn.execute(
        "SELECT DISTINCT entity_key FROM declarations WHERE entity_type = 'rig'"
        " AND field IN (SELECT value FROM json_each(?)) ORDER BY entity_key",
        (json.dumps(CARRIED_FIELDS),),
    )
    for (key,) in keys:
        parts = rig_key_parts(key)
        if parts and parts[0] is None and parts[1] == camera and same_focal(parts[2], focal_mm):
            return key
    return None


def carry_declarations(conn: sqlite3.Connection, old_key: str, rig_id: int, now: str) -> None:
    """Copied, not moved: on a change of mind the new rig finds them there."""
    for field in CARRIED_FIELDS:
        conn.execute(
            "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
            " SELECT entity_type, ?, field, value, ? FROM declarations"
            " WHERE entity_type = 'rig' AND entity_key = ? AND field = ?"
            " ON CONFLICT(entity_type, entity_key, field) DO NOTHING",
            (decl_key(_rig(conn, rig_id)), now, old_key, field),
        )


def drop_empty(conn: sqlite3.Connection) -> None:
    """Detected rigs left without frames would look real with zero hours; a hand-written one
    stays."""
    conn.execute(
        "DELETE FROM rigs WHERE detected = 1"
        " AND NOT EXISTS (SELECT 1 FROM frames f WHERE f.rig_id = rigs.id)"
    )


def create_declared(
    conn: sqlite3.Connection,
    optics_id: int,
    camera_id: int,
    focal_mm: float,
    now: str | None = None,
) -> int:
    """Also written among the declarations: merging its optics or camera deletes the rigs, and
    `normalize` remakes them only from frames."""
    names: dict[str, str] = {}
    for kind, piece_id in (("optics", optics_id), ("camera", camera_id)):
        row = conn.execute(
            "SELECT name FROM instruments WHERE id = ? AND kind = ?", (piece_id, kind)
        ).fetchone()
        if row is None:
            raise WrongKindError(f"{piece_id} non e' un pezzo di genere {kind}")
        names[kind] = row["name"]
    if find_rig(conn, optics_id, camera_id, focal_mm) is not None:
        raise RigExistsError(f"{names['optics']} + {names['camera']} a {focal_mm} mm")
    rig_id, _ = rig_for(conn, optics_id, camera_id, focal_mm, now or now_iso(), detected=False)
    key = rig_key(names["optics"], names["camera"], focal_mm)
    write_declaration(conn, EntityType.RIG, key, RigField.DECLARED, 1, now)
    return rig_id


def restore_declared(conn: sqlite3.Connection, now: str | None = None) -> None:
    """Remakes your rigs a merge deleted: the key already followed the kept piece
    (`follow_rename`), here the row and its usage row come back."""
    for key, _ in values_of(conn, EntityType.RIG, RigField.DECLARED):
        parts = rig_key_parts(key)
        if parts is None:
            continue  # a name with the bar inside: as in `follow_rename`, left alone
        optics, camera, focal = parts
        optics_id = instrument_id(conn, "optics", optics)
        camera_id = instrument_id(conn, "camera", camera)
        if optics_id is None or camera_id is None:
            continue
        if find_rig(conn, optics_id, camera_id, focal) is None:
            when = now or now_iso()
            rebuilt, _ = rig_for(conn, optics_id, camera_id, focal, when, detected=False)
            gear_usage.add_new(conn, UsageSubject.RIG, rebuilt)


RIG_ROWS = """
SELECT g.id, g.focal_mm, o.name AS optics, c.name AS camera
FROM rigs g LEFT JOIN instruments o ON o.id = g.optics_id
            LEFT JOIN instruments c ON c.id = g.camera_id
"""


def rigs_with_keys(conn: sqlite3.Connection) -> list[tuple[str, sqlite3.Row]]:
    """The key read and the key written both come from here, or a rig's name would land on
    another."""
    return [(decl_key(r), r) for r in conn.execute(RIG_ROWS).fetchall()]


def decl_key(row: sqlite3.Row) -> str:
    return rig_key(row["optics"], row["camera"], row["focal_mm"])


def _rig_or_none(conn: sqlite3.Connection, rig_id: int) -> sqlite3.Row | None:
    return conn.execute(RIG_ROWS + " WHERE g.id = ?", (rig_id,)).fetchone()


def _rig(conn: sqlite3.Connection, rig_id: int) -> sqlite3.Row:
    row = _rig_or_none(conn, rig_id)
    if row is None:
        raise LookupError(f"corredo {rig_id}")
    return row


def declare_mount(
    conn: sqlite3.Connection, rig_id: int, mount_id: int | None, now: str | None = None
) -> list[int]:
    """`None` drops the user's word and goes back to the files'. Returns the frames requeued to
    `normalize`, which writes the mount on each: none if nothing changed."""
    key = decl_key(_rig(conn, rig_id))
    if mount_id is None:
        dropped = forget(conn, EntityType.RIG, key, RigField.MOUNT)
        if not dropped:
            return []
    else:
        mount_row = conn.execute(
            "SELECT name FROM instruments WHERE id = ? AND kind = ?", (mount_id, RigField.MOUNT)
        ).fetchone()
        if mount_row is None:
            raise NotAMountError(f"{mount_id} non e' una montatura")
        if declared_mount(conn, rig_id) == mount_id:
            return []
        write_declaration(conn, EntityType.RIG, key, RigField.MOUNT, mount_row["name"], now)
    frames = [r[0] for r in conn.execute("SELECT id FROM frames WHERE rig_id = ?", (rig_id,))]
    invalidate(conn, frames, StageName.NORMALIZE, now=now)
    return frames


_MOUNTS = """
SELECT d.entity_key, i.id FROM declarations d
JOIN instruments i ON i.kind = 'mount' AND i.name = d.value
WHERE d.entity_type = 'rig' AND d.field = 'mount'
"""


def rig_mounts(conn: sqlite3.Connection) -> dict[str, int]:
    return {r["entity_key"]: r["id"] for r in conn.execute(_MOUNTS)}


def declared_mount(conn: sqlite3.Connection, rig_id: int) -> int | None:
    """`normalize` asks it for every frame: a lookup by key, not all the declarations."""
    row = _rig_or_none(conn, rig_id)
    if row is None:
        return None
    found_mount = conn.execute(_MOUNTS + " AND d.entity_key = ?", (decl_key(row),)).fetchone()
    return None if found_mount is None else found_mount["id"]


def rig_names(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(values_of(conn, EntityType.RIG, RigField.NAME))


def declare_rig(conn: sqlite3.Connection, rig_id: int, name: str, now: str | None = None) -> bool:
    """Among the declarations, not in the row a merge can delete: the name comes back by itself
    when `normalize` rebuilds the same rig."""
    row = _rig(conn, rig_id)
    if not name:
        return False
    write_declaration(conn, EntityType.RIG, decl_key(row), RigField.NAME, name, now)
    return True


# Only these kinds are in a rig's key (`optics|camera|focal`). `follow_rename` looks at names, not
# kinds, and real guide cameras carry camera-family names: called for one, it would move others'.
KEY_KINDS = ("optics", "camera")


# The pieces a rig declaration carries in its value, with the kind as field: the mount you give it.
VALUE_KINDS = (RigField.MOUNT,)


def follow_piece(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, now: str | None = None
) -> None:
    """Optics and camera move the rig key and the gear answers, a mount the value naming it; no
    other kind is touched."""
    if kind in KEY_KINDS:
        follow_rename(conn, old_name, new_name, now)
        signature.follow_piece(conn, kind, old_name, new_name, now)  # and the gear answers
    if kind in VALUE_KINDS:
        conn.execute(
            "UPDATE declarations SET value = ?"
            " WHERE entity_type = 'rig' AND field = ? AND value = ?",
            (new_name, kind, old_name),
        )


def follow_rename(
    conn: sqlite3.Connection, old_name: str, new_name: str, now: str | None = None
) -> None:
    """The key carries the piece's name: without following it the rig's name would be orphaned and
    the rebuilt rig would come back nameless."""
    for r in conn.execute(
        "SELECT entity_key, field, value FROM declarations WHERE entity_type = 'rig'"
    ).fetchall():
        parts = rig_key_parts(r["entity_key"])
        if parts is None or old_name not in parts[:2]:
            continue
        optics, camera = (new_name if p == old_name else p for p in parts[:2])
        new_key = rig_key(optics, camera, parts[2])
        forget(conn, EntityType.RIG, r["entity_key"], r["field"])
        conn.execute(
            "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
            " VALUES(?, ?, ?, ?, ?) ON CONFLICT(entity_type, entity_key, field)"
            " DO NOTHING",  # if the target rig already has an answer, its own wins
            (EntityType.RIG, new_key, r["field"], r["value"], now or now_iso()),
        )
