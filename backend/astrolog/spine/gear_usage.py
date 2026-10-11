"""How much each piece, rig and filter served, written at the end of every stage that moves frames.
Hours the app cannot know are NULL, not zero; a rig's field is measured on solved frames."""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass
from enum import StrEnum
from typing import Any

from ..db import idlist
from ..db.replace_table import replace_rows
from ..units import hundredths, median
from . import counts, rigs
from . import objects as obj


class UsageSubject(StrEnum):
    """The words of the `gear_usage.subject` CHECK."""

    INSTRUMENT = "instrument"
    RIG = "rig"
    FILTER = "filter"


# Optics and camera always have hours: they pass through the rig, which the spine derives from
# every frame. For the others it depends on the archive (`_with_hours`).
_ALWAYS = ("optics", "camera")

# Frames grouped once per list, not a correlated subselect per row, with `counts`'s link: the
# nights too, or one row would tell two numbers.
_COUNTS = f"{counts.AGGREGATE}, {counts.UNTIMED}, COUNT(DISTINCT f.night_id) AS nights"
_USED = """COALESCE(u.frames, 0) AS frames, COALESCE(u.integration_s, 0) AS integration_s,
       COALESCE(u.untimed, 0) AS untimed, COALESCE(u.nights, 0) AS nights"""

_INSTRUMENTS = f"""
SELECT i.id, i.kind, {_USED}
FROM instruments i LEFT JOIN (
  SELECT l.piece AS id, {_COUNTS}
  FROM ({counts.PIECE_FRAMES}) l JOIN frames f ON f.id = l.frame
  WHERE f.copy_of IS NULL GROUP BY l.piece
) u ON u.id = i.id
"""  # noqa: S608 - constant fragments of the spine, not user values

_RIGS = f"""
SELECT g.id, {_USED}
FROM rigs g LEFT JOIN (
  SELECT f.rig_id AS id, {_COUNTS} FROM frames f
  WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL GROUP BY f.rig_id
) u ON u.id = g.id
{counts.ORDER_BY_TIME}, g.id
"""  # noqa: S608 - constant fragments of the spine, not user values

_FILTERS = f"""
SELECT x.id, {_USED}
FROM filters x LEFT JOIN (
  SELECT f.filter_id AS id, {_COUNTS} FROM frames f
  WHERE f.copy_of IS NULL AND f.filter_id IS NOT NULL GROUP BY f.filter_id
) u ON u.id = x.id
WHERE x.is_none = 0
{counts.ORDER_BY_TIME}, x.name
"""  # noqa: S608 - constant fragments of the spine, not user values

# What each one shot, most shot first: one body, three keys.
_OBJECTS = f"""
SELECT {{owner}} AS owner, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id {{join}}
WHERE {{column}} IN {{{{listed}}}} AND f.copy_of IS NULL
GROUP BY owner, o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - constant fragments of the spine, not user values

_RIG_OBJECTS = _OBJECTS.format(owner="f.rig_id", join="", column="f.rig_id")
_FILTER_OBJECTS = _OBJECTS.format(owner="f.filter_id", join="", column="f.filter_id")
# `counts`'s link with the rigs in the `FROM`, not a subselect searched per (frame, piece). The
# `LEFT` matters: a frame naming a wheel may have no rig.
_PIECE_OBJECTS = _OBJECTS.format(
    owner="i.id",
    join=(
        "LEFT JOIN rigs g ON g.id = f.rig_id JOIN instruments i ON "
        + counts.of(counts.Subject.INSTRUMENT, rigs_joined=True)
    ),
    column="i.id",
)

_SKY = """
SELECT f.rig_id AS owner, w.scale_arcsec_px, w.width_deg, w.height_deg
FROM frames f JOIN frame_wcs w ON w.frame_id = f.id
WHERE f.rig_id IN {listed} AND f.copy_of IS NULL
"""

# What a rig's frames used besides optics and camera, in the card's order. Written copies do not
# count, as in the hours; "no filter" is not a filter you own.
_PIECE_PART = """
SELECT f.rig_id, '{kind}' AS kind, f.{kind}_id AS piece_id, NULL AS software, COUNT(*) AS frames
FROM frames f WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL AND f.{kind}_id IS NOT NULL
GROUP BY f.rig_id, f.{kind}_id
"""
# The words of the `rig_parts.kind` CHECK, in the card's order.
_PIECE_KINDS = ("mount", *counts.ON_THE_FRAME, *counts.CHOSEN_ONLY)
PART_KINDS = (*_PIECE_KINDS, "software", "filter")
_PARTS = (
    *(_PIECE_PART.format(kind=kind) for kind in _PIECE_KINDS),
    """
SELECT f.rig_id, 'software' AS kind, NULL AS piece_id, f.software, COUNT(*) AS frames
FROM frames f WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL AND f.software IS NOT NULL
GROUP BY f.rig_id, f.software
""",
    """
SELECT f.rig_id, 'filter' AS kind, f.filter_id AS piece_id, NULL AS software, COUNT(*) AS frames
FROM frames f JOIN filters x ON x.id = f.filter_id AND x.is_none = 0
WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL
GROUP BY f.rig_id, f.filter_id
""",
)
_PART_COLUMNS = ("rig_id", "kind", "piece_id", "software", "frames", "chosen", "position")

USAGE = ("frames", "integration_s", "untimed", "nights")
_SKY_FIELDS = ("scale_arcsec_px", "width_deg", "height_deg")
_COLUMNS = ("subject", "subject_id", *USAGE, *_SKY_FIELDS, "objects_json", "position")


@dataclass(frozen=True, slots=True)
class UsageRow:
    """A `gear_usage` row but its position, in the table's column order."""

    subject: UsageSubject
    subject_id: int
    frames: int | None
    integration_s: float | None
    untimed: int | None
    nights: int | None
    scale_arcsec_px: float | None
    width_deg: float | None
    height_deg: float | None
    objects_json: str


def write(conn: sqlite3.Connection) -> None:
    """Redone whole, all or nothing: a frame changing rig moves four rows, and following them one
    by one would get one wrong. The page order is `counts.ORDER_BY_TIME`, written as position."""
    rows = [
        (*astuple(r), n)
        for listing in (_instruments(conn), _rigs(conn), _filters(conn))
        for n, r in enumerate(listing)
    ]
    replace_rows(conn, "gear_usage", _COLUMNS, rows)
    write_parts(conn)


def write_parts(conn: sqlite3.Connection) -> None:
    """Alone after a choice on a rig, so the page reads it before the frames are reworked."""
    replace_rows(conn, "rig_parts", _PART_COLUMNS, _parts(conn))


def restore_rigs(conn: sqlite3.Connection, now: str | None = None) -> None:
    """Your rigs a merge deleted come back with their usage row, or the page would not list them."""
    for rig_id in rigs.restore_declared(conn, now):
        add_new(conn, UsageSubject.RIG, rig_id)


def _parts(conn: sqlite3.Connection) -> list[tuple[Any, ...]]:
    """Kind by kind in the card's order, each from the most used; the position runs per rig. A
    part the user chose says so, and is listed even before a frame carries it."""
    counted: dict[tuple[int, str], list[tuple[int | None, str | None, int]]] = {}
    for kind, query in zip(PART_KINDS, _PARTS, strict=True):
        ordered = f"{query} ORDER BY frames DESC, piece_id, software"
        for r in conn.execute(ordered).fetchall():
            part = (r["piece_id"], r["software"], r["frames"])
            counted.setdefault((r["rig_id"], kind), []).append(part)
    choices = rigs.chosen_parts(conn)
    rows: list[tuple[Any, ...]] = []
    for key, rig in rigs.rigs_with_keys(conn):
        mine = choices.get(key, {})
        position = 0
        for kind in PART_KINDS:
            listed = list(counted.get((rig["id"], kind), []))
            if kind in mine and mine[kind] not in [piece for piece, _, _ in listed]:
                listed.append((mine[kind], None, 0))
            for piece, software, frames in listed:
                # asked by kind first: the software has no id, and no id is not a choice
                chosen = kind in mine and mine[kind] == piece
                rows.append((rig["id"], kind, piece, software, frames, int(chosen), position))
                position += 1
    return rows


def add_piece(conn: sqlite3.Connection, instrument_id: int, kind: str) -> None:
    """Only its own row: recounting the whole archive inside the request that creates it would
    cost seconds."""
    _add_row(conn, UsageSubject.INSTRUMENT, instrument_id, known=kind in _with_hours(conn))


def add_new(conn: sqlite3.Connection, subject: UsageSubject, row_id: int) -> None:
    """A filter's or rig's hours are always known: the frame names its filter and its rig."""
    _add_row(conn, subject, row_id, known=True)


def _add_row(conn: sqlite3.Connection, subject: UsageSubject, row_id: int, *, known: bool) -> None:
    """At the bottom of its list, which runs from the most used: at the top, with zero hours, it
    would lie."""
    conn.execute(
        "INSERT OR REPLACE INTO gear_usage(subject, subject_id, frames, integration_s, untimed,"
        " nights, objects_json, position) VALUES(?, ?, ?, ?, ?, ?, '[]',"
        " (SELECT COALESCE(MAX(position) + 1, 0) FROM gear_usage WHERE subject = ?))",
        (subject, row_id, *((0, 0.0, 0, 0) if known else (None,) * 4), subject),
    )


def _with_hours(conn: sqlite3.Connection) -> set[str]:
    """A kind the frame names itself counts only if some frame names it: a wheel no file ever wrote
    has not done zero hours, it has hours the app cannot know."""
    kinds: set[str] = set(_ALWAYS)
    for kind in counts.CARRIED:
        said = conn.execute(
            f"SELECT 1 FROM frames WHERE {kind}_id IS NOT NULL LIMIT 1"  # noqa: S608 - our kinds
        ).fetchone()
        if said is not None:
            kinds.add(kind)
    return kinds


def _row(
    subject: UsageSubject,
    r: sqlite3.Row,
    shot: Mapping[Any, Sequence[Any]],
    *,
    known: bool = True,
    sky: Mapping[str, float | None] | None = None,
) -> UsageRow:
    usage: dict[str, Any] = {c: r[c] for c in USAGE} if known else dict.fromkeys(USAGE)
    sky = sky or {}
    return UsageRow(
        subject,
        r["id"],
        usage["frames"],
        usage["integration_s"],
        usage["untimed"],
        usage["nights"],
        sky.get("scale_arcsec_px"),
        sky.get("width_deg"),
        sky.get("height_deg"),
        json.dumps(shot.get(r["id"], []) if known else []),
    )


def _instruments(conn: sqlite3.Connection) -> list[UsageRow]:
    rows = conn.execute(_INSTRUMENTS).fetchall()
    with_hours = _with_hours(conn)
    ids = [r["id"] for r in rows if r["kind"] in with_hours]
    shot = idlist.grouped(conn, _PIECE_OBJECTS, ids, "owner", obj.counted)
    return [_row(UsageSubject.INSTRUMENT, r, shot, known=r["kind"] in with_hours) for r in rows]


def _rigs(conn: sqlite3.Connection) -> list[UsageRow]:
    rows = conn.execute(_RIGS).fetchall()
    ids = [r["id"] for r in rows]
    shot = idlist.grouped(conn, _RIG_OBJECTS, ids, "owner", obj.counted)
    seen = idlist.grouped(conn, _SKY, ids, "owner", dict)
    return [
        _row(
            UsageSubject.RIG,
            r,
            shot,
            sky={
                field: hundredths(median([v[field] for v in seen.get(r["id"], [])]))
                for field in _SKY_FIELDS
            },
        )
        for r in rows
    ]


def _filters(conn: sqlite3.Connection) -> list[UsageRow]:
    rows = conn.execute(_FILTERS).fetchall()
    shot = idlist.grouped(conn, _FILTER_OBJECTS, [r["id"] for r in rows], "owner", obj.counted)
    return [_row(UsageSubject.FILTER, r, shot) for r in rows]
