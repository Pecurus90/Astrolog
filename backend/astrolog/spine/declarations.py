"""User declarations and learned rules, read here too: several stages read them, and a stage may
not import another. A declaration hangs on a key that survives a reset, never a row id."""

import sqlite3
from typing import Any

from ..clock import now_iso
from ..vocab.header_value import normalize_header_value
from ..vocab.object_label import clean_object_name
from . import counts

CONFIRMED = "confirmed"

# The kinds the spine creates from a header: without a rule, a renamed piece comes back doubled on
# the next night. `filter` and `object` stay out: they map a spelling, never merge two.
ALIAS_KINDS = ("optics", "camera", "mount", *counts.ON_THE_FRAME)


class UnknownTargetError(ValueError):
    """The answer points at a catalog entry that does not exist."""


def declared(conn: sqlite3.Connection, entity_type: str, entity_key: str | None, field: str) -> Any:
    """The row's presence wins over what was detected."""
    if entity_key is None:
        return None
    row = conn.execute(
        "SELECT value FROM declarations WHERE entity_type = ? AND entity_key = ? AND field = ?",
        (entity_type, entity_key, field),
    ).fetchone()
    return None if row is None else row["value"]


def write_declaration(  # noqa: PLR0913
    conn: sqlite3.Connection,
    entity_type: str,
    entity_key: str,
    field: str,
    value: Any,
    now: str | None = None,
) -> None:
    """The one home for writes that replace the value; rewriting updates it."""
    conn.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES(?, ?, ?, ?, ?)"
        " ON CONFLICT(entity_type, entity_key, field) DO UPDATE SET value = excluded.value",
        (entity_type, entity_key, field, value, now or now_iso()),
    )


def forget(conn: sqlite3.Connection, entity_type: str, entity_key: str, field: str) -> int:
    """How many went: the question opens again."""
    return conn.execute(
        "DELETE FROM declarations WHERE entity_type = ? AND entity_key = ? AND field = ?",
        (entity_type, entity_key, field),
    ).rowcount


def alias_target(conn: sqlite3.Connection, kind: str, header_value: str) -> str | None:
    row = conn.execute(
        "SELECT target_key FROM header_aliases WHERE kind = ? AND header_value = ?",
        (kind, header_value),
    ).fetchone()
    return None if row is None else row["target_key"]


def instrument_name(conn: sqlite3.Connection, kind: str, raw: str | None) -> str | None:
    """Learned rule, else the name as written. `normalize` and `rigless` both read it: two readings
    would propose a renamed piece's old name and give birth to a second one."""
    key = normalize_header_value(raw)
    if not key:
        return None
    return alias_target(conn, kind, key) or (raw or "").strip()


def instrument_key(kind: str, name: str) -> str:
    return f"{kind}|{name}"


# Camera fields the files can also tell: the user's word lives here, since the column is detected
# and the spine recomputes it.
CAMERA_SPECS = ("camera_type", "pixel_size_um")
# The words of the `instruments.camera_type` CHECK: the sensor. What sat in front when the file is
# silent is another field, `UNFILTERED`.
CAMERA_MONO, CAMERA_COLOR = "mono", "color"
UNFILTERED = "unfiltered"
# With "one of yours", which: its name in a field of its own, so a filter named like an answer does
# not become that answer.
UNFILTERED_FILTER = "unfiltered_filter"

# Answers on a group of frames: the rig on frames that do not say the camera, keyed by the night
# with the header values; the target on frames with no name and no sky. Their keys differ.
FRAME_GROUP, GROUP_RIG = "frame_group", "rig"
GROUP_OBJECT = "object"
# Answers on a folder, keyed by its path.
FOLDER = "folder"
# Whether frames that do not say what file they are are a light or a calibration. Here and not in
# `typeless` because `stages` reads them too, and the imports would go round.
FOLDER_TYPE = "image_type"
TYPE_LIGHT, TYPE_CALIBRATION = "light", "calibration"

# The answer on a mosaic, keyed by the mosaic's key.
MOSAIC, MOSAIC_FIELD = "mosaic", "answer"
# A no is an answer, or accepting would silence a wrong proposal. A yes is written as the target
# (`object_answer.target_value`). Not in `mosaic`: the proposals page must not import geometry.
MOSAIC_YES, MOSAIC_NO = "yes", "no"
MOSAIC_ANSWERS = (MOSAIC_YES, MOSAIC_NO)


# The "not the same piece" answer on a camera: one field per other camera, its name in field and
# value, so it follows a rename or merge (`follow_not_same_as`).
NOT_SAME_AS = "not_same_as:"


def not_same_as(other_name: str) -> str:
    return NOT_SAME_AS + other_name


def follow_not_same_as(conn: sqlite3.Connection, old_name: str, new_name: str) -> None:
    """Without it the pair would ask again under the new name. A no already pointing at the new
    name is kept, and the old one goes."""
    conn.execute(
        "UPDATE OR IGNORE declarations SET field = ?, value = ?"
        " WHERE entity_type = 'instrument' AND field = ?",
        (not_same_as(new_name), new_name, not_same_as(old_name)),
    )
    conn.execute(
        "DELETE FROM declarations WHERE entity_type = 'instrument' AND field = ?",
        (not_same_as(old_name),),
    )


def declare_instrument_spec(  # noqa: PLR0913
    conn: sqlite3.Connection,
    kind: str,
    name: str,
    field: str,
    value: Any,
    now: str | None = None,
) -> None:
    write_declaration(conn, "instrument", instrument_key(kind, name), field, value, now)


def rig_key(optics_name: str | None, camera_name: str | None, focal_mm: float | None) -> str:
    return f"{optics_name or ''}|{camera_name or ''}|{'' if focal_mm is None else focal_mm}"


def rig_key_parts(key: str) -> tuple[str | None, str | None, float | None] | None:
    """`None` when unreadable: a name with a bar in it makes more than three parts, and where to
    cut is not guessed."""
    parti = key.split("|")
    if len(parti) != 3:
        return None
    ottica, camera, focale = parti
    return ottica or None, camera or None, float(focale) if focale else None


def values_of(conn: sqlite3.Connection, entity_type: str, field: str) -> list[Any]:
    """`(key, value)` pairs."""
    return conn.execute(
        "SELECT entity_key, value FROM declarations WHERE entity_type = ? AND field = ?",
        (entity_type, field),
    ).fetchall()


def confirmed_keys(conn: sqlite3.Connection, entity_type: str) -> set[str]:
    """What is not in here is new."""
    return {chiave for chiave, _ in values_of(conn, entity_type, CONFIRMED)}


def confirm(
    conn: sqlite3.Connection, entity_type: str, key: str | None, now: str | None = None
) -> None:
    conn.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES(?, ?, ?, 1, ?) ON CONFLICT(entity_type, entity_key, field) DO NOTHING",
        (entity_type, key, CONFIRMED, now or now_iso()),
    )


# A fact about the place, not a night, so it holds for nights to come: keyed by rounded coordinates
# (`place.coordinates_key`).
COORDINATES_SITE = "site"


def declare_coordinates(
    conn: sqlite3.Connection, coordinates_key: str, site_name: str, now: str | None = None
) -> None:
    """The name, not the id: ids are reused and the answer would land on another site silently; a
    renamed site no longer matches and the app asks again, the safe way."""
    write_declaration(conn, "coordinates", coordinates_key, COORDINATES_SITE, site_name, now)


def site_for_coordinates(conn: sqlite3.Connection, coordinates_key: str | None) -> str | None:
    value = declared(conn, "coordinates", coordinates_key, COORDINATES_SITE)
    return value if isinstance(value, str) and value else None


def learn(
    conn: sqlite3.Connection,
    kind: str,
    header_value: str | None,
    target_key: str | None,
    now: str | None = None,
) -> None:
    """Normalised once here, as the schema declares and the readers expect: a raw spelling would
    never match."""
    if kind == "object":
        # cleaned of palette words as `identify` looks it up, here so write and read cannot diverge
        header_value = clean_object_name(header_value)
    key = normalize_header_value(header_value)
    if kind not in (*ALIAS_KINDS, "filter", "object") or not key:
        return
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES(?, ?, ?, ?) ON CONFLICT(kind, header_value)"
        " DO UPDATE SET target_key = excluded.target_key",
        (kind, key, target_key, now or now_iso()),
    )


def rename(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, now: str | None = None
) -> None:
    """Unlike `learn`, the rules leading to the old name follow: a rule points at a name, and one
    left behind points at nobody. Rename and merge are the same gesture here."""
    learn(conn, kind, old_name, new_name, now)
    conn.execute(
        "UPDATE header_aliases SET target_key = ? WHERE kind = ? AND target_key = ?",
        (new_name, kind, old_name),
    )
