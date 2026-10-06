"""The user's answer on an OBJECT: correction and learned rule. It never touches
`objects` or `object_names`: `identify` rewrites them, so the answer is one truth in one place."""

import logging
import sqlite3
from dataclasses import asdict, dataclass
from enum import StrEnum

from ..catalog import NamedEntry, lookup
from ..clock import now_iso
from ..vocab.object_label import clean_object_name
from . import objects
from .declarations import (
    FRAME_OBJECT,
    EntityType,
    MosaicAnswer,
    UnknownTargetError,
    declared,
    forget,
    learn,
    write_declaration,
)
from .stages import StageName, invalidate

log = logging.getLogger(__name__)

# One field carrying the kind in its value: the key is (type, key, field), and two fields would let
# two contradictory corrections stand on one object.
CORRECTION = "correction"

CATALOG, NAME = "catalog:", "name:"  # the target's kind, at the head of the value


class TargetKind(StrEnum):
    """An answer's kind. `NONE` is "not an object", and also the value written on a frame."""

    CATALOG = "catalog"
    NAME = "name"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class Answer:
    """An answer as a card shows it: `value` the slug or the written name, `name` how it reads;
    both empty for "not an object"."""

    kind: TargetKind
    value: str | None
    name: str | None


@dataclass(frozen=True, slots=True)
class OutOfArchive:
    """The frames put out under one found key; `name` is the catalog's, None for an unknown key."""

    key: str
    frames: int
    integration_s: float
    untimed: int
    name: str | None


# The frames the user put out of the archive, under what `identify` had found for them. Copies
# count nowhere; a frame still linked waits for `identify` and counts on its object.
_OUT = f"""
SELECT f.found_key AS key, COUNT(*) AS frames,
  COALESCE(SUM(f.exposure_s), 0) AS integration_s, SUM(f.exposure_s IS NULL) AS untimed
FROM frames f JOIN declarations d ON d.entity_type = '{EntityType.FRAME}'
  AND d.entity_key = f.frame_hash AND d.field = '{FRAME_OBJECT}' AND d.value = '{TargetKind.NONE}'
WHERE f.found_key IS NOT NULL AND f.object_id IS NULL AND f.copy_of IS NULL
GROUP BY f.found_key
"""  # noqa: S608 - constants of the spine

# Linked frames already answered "not an object", per object: between Apply and `identify`.
_LINKED_OUT = f"""
SELECT f.object_id, COUNT(*) FROM frames f
  JOIN declarations d ON d.entity_type = '{EntityType.FRAME}' AND d.entity_key = f.frame_hash
  AND d.field = '{FRAME_OBJECT}' AND d.value = '{TargetKind.NONE}'
WHERE f.object_id IS NOT NULL AND f.copy_of IS NULL GROUP BY f.object_id
"""  # noqa: S608 - constants of the spine


def said_not_an_object(conn: sqlite3.Connection, frame_hash: str) -> bool:
    """The user's word on this frame itself, from its group or from the card of what was found."""
    return declared(conn, EntityType.FRAME, frame_hash, FRAME_OBJECT) == TargetKind.NONE


def out_of_archive(conn: sqlite3.Connection) -> dict[str, OutOfArchive]:
    """Per found key, the frames put out: their card stays on the page so one can change one's
    mind."""
    out: dict[str, OutOfArchive] = {}
    for r in conn.execute(_OUT).fetchall():
        entry = lookup.by_slug(conn, r["key"])
        out[r["key"]] = OutOfArchive(**dict(r), name=entry.name if entry else None)
    return out


def linked_out(conn: sqlite3.Connection) -> dict[int, int]:
    return dict(conn.execute(_LINKED_OUT).fetchall())


def _card_frames(conn: sqlite3.Connection, key: str) -> list[sqlite3.Row]:
    """Every frame of the card, copies too: those on the object and those put out under its key."""
    return conn.execute(
        "SELECT id, frame_hash, object_raw, empty_cone FROM frames"
        " WHERE (found_key = ? AND object_id IS NULL) OR object_id = ?",
        (key, (objects.by_key(conn, key) or {}).get("id")),
    ).fetchall()


def declare_not_an_object(conn: sqlite3.Connection, key: str, now: str | None = None) -> list[int]:
    """On each frame's fingerprint, fixed now, read by `identify` before name and sky; `found_key`
    written now tells it from a group's answer, which a sky with candidates overrides."""
    rows = _card_frames(conn, key)
    if not rows:
        raise LookupError(f"oggetto {key}")
    for r in rows:
        write_declaration(
            conn, EntityType.FRAME, r["frame_hash"], FRAME_OBJECT, TargetKind.NONE, now
        )
        conn.execute("UPDATE frames SET found_key = ? WHERE id = ?", (key, r["id"]))
    frames = [r["id"] for r in rows]
    invalidate(conn, frames, StageName.IDENTIFY)
    return frames


def declare_found(
    conn: sqlite3.Connection,
    key: str,
    *,
    slug: str | None = None,
    name: str | None = None,
    now: str | None = None,
) -> list[int]:
    """The card of what was found, answered with a target: the frames put out come back, and the
    correction moves them all. Without the object's row only the correction is written."""
    rows = _card_frames(conn, key)
    if not rows:
        raise LookupError(f"oggetto {key}")
    if objects.by_key(conn, key) is not None:
        declare_object(conn, key, slug=slug, name=name, now=now)
    else:
        refuse_unknown_slug(conn, slug)
        slug, name = resolved(conn, slug, name)
        correct_object(conn, key, slug=slug, name=name, now=now)
    # Without name and sky only the frame's own word can bring it back: the target, not silence.
    target = target_value(*resolved(conn, slug, name))
    for r in rows:
        if not said_not_an_object(conn, r["frame_hash"]):
            continue
        if not clean_object_name(r["object_raw"]) and r["empty_cone"] in (None, 1):
            write_declaration(conn, EntityType.FRAME, r["frame_hash"], FRAME_OBJECT, target, now)
        else:
            forget(conn, EntityType.FRAME, r["frame_hash"], FRAME_OBJECT)
    frames = [r["id"] for r in rows]
    invalidate(conn, frames, StageName.IDENTIFY)
    return frames


def correct_object(
    conn: sqlite3.Connection,
    found_key: str,
    *,
    slug: str | None = None,
    name: str | None = None,
    now: str | None = None,
) -> str:
    """A correction, not a lock: the user lock guards the object, not the frame, so `identify` would
    take the frames back; a declaration is read every time and survives a reset."""
    target = _one_target(found_key, slug, name)
    write_declaration(conn, EntityType.OBJECT, found_key, CORRECTION, target_value(slug, name), now)
    return target


def _one_target(found_key: str, slug: str | None, name: str | None) -> str:
    """The slug or the name, never both: two would let the correction pick for the user."""
    if found_key and slug and not name:
        return slug
    if found_key and name and not slug:
        return name
    raise ValueError("la correzione vuole un bersaglio solo, slug o nome")


def target_value(slug: str | None, name: str | None) -> str:
    """The kind in the value, so a slug and a name spelled alike stay two things."""
    return f"{CATALOG}{slug}" if slug else f"{NAME}{name}"


def catalog_target(conn: sqlite3.Connection, slug: str) -> tuple[str, NamedEntry] | None:
    """`is_primary` because a rule points at the ENTRY, not one spelling: the decider says
    `exact_name` instead of `historic_name`."""
    entry = lookup.by_slug(conn, slug)
    return None if entry is None else (entry.name, NamedEntry(**asdict(entry), is_primary=1))


def resolved(
    conn: sqlite3.Connection, slug: str | None, name: str | None
) -> tuple[str | None, str | None]:
    """A written name the catalog knows as a designation goes to its entry, or the hours split over
    two. Only without a slug: with both, "one target" refuses it later."""
    hit = lookup.by_designation(conn, name) if name and not slug else None
    return (hit.slug, None) if hit else (slug, name)


def refuse_unknown_slug(conn: sqlite3.Connection, slug: str | None) -> None:
    """Before writing: otherwise the answer points at nothing, and only the stage notices, much
    later, in a log nobody reads."""
    if slug and lookup.by_slug(conn, slug) is None:
        raise UnknownTargetError(slug)


def read_target(value: object) -> tuple[TargetKind, str] | None:
    """The prefix is checked, not assumed: cutting a value written elsewhere would mangle a name. A
    blank target is not a target."""
    if not isinstance(value, str):
        return None
    for prefix, kind in ((CATALOG, TargetKind.CATALOG), (NAME, TargetKind.NAME)):
        if value.startswith(prefix) and value[len(prefix) :].strip():
            return kind, value[len(prefix) :]
    log.warning("declarations: bersaglio senza tipo, ignorato", extra={"value": value})
    return None


def mosaic_word(value: str | None) -> str | None:
    """A value that is neither word was written elsewhere: taking it would switch a question off."""
    if value is None or value == MosaicAnswer.NO:
        return value
    return None if read_target(value) is None else MosaicAnswer.YES


def shown_target(conn: sqlite3.Connection, value: str) -> Answer | None:
    """A catalog entry that is gone counts as no target: its slug would show a name nobody wrote."""
    read = read_target(value)
    if read is None:
        return None
    kind, target = read
    if kind == TargetKind.NAME:
        return Answer(kind, target, target)
    entry = lookup.by_slug(conn, target)
    return None if entry is None else Answer(kind, target, entry.name)


def correction_of(conn: sqlite3.Connection, found_key: str) -> tuple[TargetKind, str] | None:
    value = declared(conn, EntityType.OBJECT, found_key, CORRECTION)
    return None if value is None else read_target(value)


def declare_object(
    conn: sqlite3.Connection,
    key: str,
    *,
    slug: str | None = None,
    name: str | None = None,
    now: str | None = None,
) -> list[int]:
    """`key` is the STABLE key, never the row id. The correction moves the frames; the rule is
    learned only on spellings that point to this object alone, or a placeholder drags others."""
    now = now or now_iso()
    row = objects.by_key(conn, key)
    if row is None:
        raise LookupError(f"oggetto {key}")
    refuse_unknown_slug(conn, slug)
    slug, name = resolved(conn, slug, name)
    object_id = row["id"]

    target = correct_object(conn, key, slug=slug, name=name, now=now)
    for spelling in _unambiguous_spellings(conn, object_id):
        learn(conn, "object", spelling, target, now=now)

    frames = objects.frames_of(conn, object_id)
    invalidate(conn, frames, StageName.IDENTIFY)
    return frames


def _unambiguous_spellings(conn: sqlite3.Connection, object_id: int) -> list[str]:
    """Compared cleaned of palette words, the form `identify` looks rules up in: `Snapshot LRGB` and
    `Snapshot` are one spelling, or the rule would never hook."""
    touches: dict[str | None, set[int]] = {}
    for raw, other_id in objects.raw_names_with_objects(conn):
        touches.setdefault(clean_object_name(raw), set()).add(other_id)
    mine = {clean_object_name(g) for g in objects.raw_names_of(conn, object_id)}
    return [g for g in mine if g and len(touches.get(g, ())) == 1]
