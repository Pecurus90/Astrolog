"""User declarations and learned rules, read here too: several stages read them, and a stage may
not import another. A declaration hangs on a key that survives a reset, never a row id."""

import sqlite3
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from ..clock import now_iso
from ..vocab.header_value import normalize_header_value
from ..vocab.object_label import clean_object_name
from . import counts

# The kinds the spine creates from a header: without a rule, a renamed piece comes back doubled on
# the next night. `filter` and `object` stay out: they map a spelling, never merge two.
ALIAS_KINDS = ("optics", "camera", "mount", *counts.ON_THE_FRAME)


class UnknownTargetError(ValueError):
    """The answer points at a catalog entry that does not exist."""


class EntityType(StrEnum):
    """The words of the `declarations.entity_type` CHECK."""

    OBJECT = "object"
    RIG = "rig"
    INSTRUMENT = "instrument"
    NIGHT = "night"
    SESSION = "session"
    COORDINATES = "coordinates"
    # answers on a folder, keyed by its path
    FOLDER = "folder"
    # the target on frames with no name and no sky, keyed by the frame's fingerprint: the group's
    # key carries the night, which moves with home's zone
    FRAME = "frame"
    MOSAIC = "mosaic"
    # the gear the files leave out, keyed by the header signature (`spine/signature.py`)
    SIGNATURE = "signature"


def declared(
    conn: sqlite3.Connection, entity_type: EntityType, entity_key: str | None, field: str
) -> Any:
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
    entity_type: EntityType,
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


def forget(conn: sqlite3.Connection, entity_type: EntityType, entity_key: str, field: str) -> int:
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
    """Learned rule, else the name as written. `normalize` and the gear question both read it: two
    readings would propose a renamed piece's old name and give birth to a second one."""
    key = normalize_header_value(raw)
    return _named(raw, alias_target(conn, kind, key)) if key else None


def _named(raw: str | None, rule: str | None) -> str:
    return rule or (raw or "").strip()


def instrument_names(
    conn: sqlite3.Connection, raws: Mapping[str, str | None]
) -> dict[str, str | None]:
    """`instrument_name` of one raw value per kind, the rules read in one query."""
    keys = {kind: key for kind, raw in raws.items() if (key := normalize_header_value(raw))}
    rules: dict[str, str] = {}
    if keys:
        pairs = ", ".join("(?, ?)" for _ in keys)  # segnaposto-ok: one pair per kind, not per frame
        # S608: only placeholders
        sql = (
            "SELECT kind, target_key FROM header_aliases"  # noqa: S608
            f" WHERE (kind, header_value) IN (VALUES {pairs})"
        )
        args = [v for pair in keys.items() for v in pair]
        rules = {r["kind"]: r["target_key"] for r in conn.execute(sql, args)}
    return {
        kind: _named(raw, rules.get(kind)) if kind in keys else None for kind, raw in raws.items()
    }


def instrument_id(conn: sqlite3.Connection, kind: str, name: str | None) -> int | None:
    """Here, not in `gear`: `rigs` needs it too, and `gear` imports `rigs`."""
    row = conn.execute(
        "SELECT id FROM instruments WHERE kind = ? AND name = ?", (kind, name)
    ).fetchone()
    return None if row is None else row["id"]


def instrument_ids(conn: sqlite3.Connection, names: Mapping[str, str]) -> dict[str, int]:
    """`instrument_id` of one name per kind, in one query; a kind with no piece is left out."""
    if not names:
        return {}
    pairs = ", ".join("(?, ?)" for _ in names)  # segnaposto-ok: one pair per kind, not per frame
    # S608: only placeholders
    sql = f"SELECT kind, id FROM instruments WHERE (kind, name) IN (VALUES {pairs})"  # noqa: S608
    args = [v for pair in names.items() for v in pair]
    return {r["kind"]: r["id"] for r in conn.execute(sql, args)}


def instrument_key(kind: str, name: str) -> str:
    return f"{kind}|{name}"


# Camera fields the files can also tell: the user's word lives here, since the column is detected
# and the spine recomputes it.
CAMERA_SPECS = ("camera_type", "pixel_size_um")


class CameraType(StrEnum):
    """The words of the `instruments.camera_type` CHECK: the sensor. What sat in front when the file
    is silent is the signature's answer (`spine/signature.py`)."""

    MONO = "mono"
    COLOR = "color"


# The field of each entity type's answer.
SIGNATURE_GEAR = "gear"
FRAME_OBJECT = "object"
MOSAIC_FIELD = "answer"
# Whether frames that do not say what file they are are a light or a calibration.
FOLDER_TYPE = "image_type"


class TypeAnswer(StrEnum):
    LIGHT = "light"
    CALIBRATION = "calibration"


class MosaicAnswer(StrEnum):
    """A no is an answer, or accepting would silence a wrong proposal; a yes is written as the
    target (`object_answer.target_value`). Not in `mosaic`: proposals must not import geometry."""

    YES = "yes"
    NO = "no"


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
    write_declaration(conn, EntityType.INSTRUMENT, instrument_key(kind, name), field, value, now)


def rig_key(optics_name: str | None, camera_name: str | None, focal_mm: float | None) -> str:
    return f"{optics_name or ''}|{camera_name or ''}|{'' if focal_mm is None else focal_mm}"


def rig_key_parts(key: str) -> tuple[str | None, str | None, float | None] | None:
    """`None` when unreadable: a name with a bar in it makes more than three parts, and where to
    cut is not guessed."""
    parts = key.split("|")
    if len(parts) != 3:
        return None
    optics, camera, focal = parts
    return optics or None, camera or None, float(focal) if focal else None


def values_of(
    conn: sqlite3.Connection, entity_type: EntityType, field: str
) -> list[tuple[str, Any]]:
    """`(key, value)` pairs."""
    return [
        (r["entity_key"], r["value"])
        for r in conn.execute(
            "SELECT entity_key, value FROM declarations WHERE entity_type = ? AND field = ?",
            (entity_type, field),
        )
    ]


# A fact about the place, not a night, so it holds for nights to come: keyed by rounded coordinates
# (`place.coordinates_key`).
COORDINATES_SITE = "site"


def declare_coordinates(
    conn: sqlite3.Connection, coordinates_key: str, site_name: str, now: str | None = None
) -> None:
    """The site's name, not its id: a renamed site no longer matches and the app asks again, the
    safe way."""
    write_declaration(
        conn, EntityType.COORDINATES, coordinates_key, COORDINATES_SITE, site_name, now
    )


def site_for_coordinates(conn: sqlite3.Connection, coordinates_key: str | None) -> str | None:
    value = declared(conn, EntityType.COORDINATES, coordinates_key, COORDINATES_SITE)
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
