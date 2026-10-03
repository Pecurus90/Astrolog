"""The user's answer on an OBJECT: correction, learned rule, confirmation. It never touches
`objects` or `object_names`: `identify` rewrites them, so the answer is one truth in one place."""

import logging
import sqlite3
from typing import Any

from ..catalog import lookup
from ..clock import now_iso
from ..vocab.object_label import clean_object_name
from . import objects
from .declarations import (
    MOSAIC_NO,
    MOSAIC_YES,
    UnknownTargetError,
    confirm,
    declared,
    learn,
    write_declaration,
)
from .stages import invalidate

log = logging.getLogger(__name__)

# One field carrying the kind in its value: the key is (type, key, field), and two fields would let
# two contradictory corrections stand on one object.
CORRECTION = "correction"

CATALOG, NAME = "catalog:", "name:"  # the target's kind, at the head of the value


def correct_object(
    conn: sqlite3.Connection,
    found_key: str,
    *,
    slug: str | None = None,
    name: str | None = None,
    now: str | None = None,
) -> None:
    """A correction, not a lock: the user lock guards the object, not the frame, so `identify` would
    take the frames back; a declaration is read every time and survives a reset."""
    if not found_key or bool(slug) == bool(name):
        raise ValueError("la correzione vuole un bersaglio solo, slug o nome")
    write_declaration(conn, "object", found_key, CORRECTION, target_value(slug, name), now)


def target_value(slug: str | None, name: str | None) -> str:
    """The kind in the value, so a slug and a name spelled alike stay two things."""
    return f"{CATALOG}{slug}" if slug else f"{NAME}{name}"


def catalog_target(conn: sqlite3.Connection, slug: str) -> tuple[str, dict[str, Any]] | None:
    """`is_primary` because a rule points at the ENTRY, not one spelling: the decider says
    `exact_name` instead of `historic_name`."""
    entry = lookup.by_slug(conn, slug)
    return None if entry is None else (entry["name"], {**entry, "is_primary": 1})


def resolved(
    conn: sqlite3.Connection, slug: str | None, name: str | None
) -> tuple[str | None, str | None]:
    """A written name the catalog knows as a designation goes to its entry, or the hours split over
    two. Only without a slug: with both, "one target" refuses it later."""
    hit = lookup.by_designation(conn, name) if name and not slug else None
    return (hit["slug"], None) if hit else (slug, name)


def refuse_unknown_slug(conn: sqlite3.Connection, slug: str | None) -> None:
    """Before writing: otherwise the answer points at nothing, and only the stage notices, much
    later, in a log nobody reads."""
    if slug and lookup.by_slug(conn, slug) is None:
        raise UnknownTargetError(slug)


def read_target(value: object) -> tuple[str, str] | None:
    """The prefix is checked, not assumed: cutting a value written elsewhere would mangle a name. A
    blank target is not a target."""
    if not isinstance(value, str):
        return None
    for prefisso, kind in ((CATALOG, "catalog"), (NAME, "name")):
        if value.startswith(prefisso) and value[len(prefisso) :].strip():
            return kind, value[len(prefisso) :]
    log.warning("declarations: bersaglio senza tipo, ignorato", extra={"value": value})
    return None


def mosaic_word(value: str | None) -> str | None:
    """A value that is neither word was written elsewhere: taking it would switch a question off."""
    if value is None or value == MOSAIC_NO:
        return value
    return None if read_target(value) is None else MOSAIC_YES


def shown_target(conn: sqlite3.Connection, value: str) -> tuple[str, str, str] | None:
    """A catalog entry that is gone counts as no target: its slug would show a name nobody wrote."""
    letto = read_target(value)
    if letto is None:
        return None
    kind, valore = letto
    if kind == "name":
        return kind, valore, valore
    entry = lookup.by_slug(conn, valore)
    return None if entry is None else (kind, valore, entry["name"])


def correction_of(conn: sqlite3.Connection, found_key: str) -> tuple[str, str] | None:
    value = declared(conn, "object", found_key, CORRECTION)
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

    correct_object(conn, key, slug=slug, name=name, now=now)
    target = slug or name
    for grafia in _unambiguous_spellings(conn, object_id):
        learn(conn, "object", grafia, target, now=now)
    confirm(conn, "object", target, now)

    frames = objects.frames_of(conn, object_id)
    invalidate(conn, frames, "identify")
    return frames


def _unambiguous_spellings(conn: sqlite3.Connection, object_id: int) -> list[str]:
    """Compared cleaned of palette words, the form `identify` looks rules up in: `Snapshot LRGB` and
    `Snapshot` are one spelling, or the rule would never hook."""
    tocca: dict[str | None, set[int]] = {}
    for grezzo, altro_id in objects.raw_names_with_objects(conn):
        tocca.setdefault(clean_object_name(grezzo), set()).add(altro_id)
    mie = {clean_object_name(g) for g in objects.raw_names_of(conn, object_id)}
    return [g for g in mie if g and len(tocca.get(g, ())) == 1]
