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
from ..units import MOON_DIAMETER_DEG, hundredths, median
from ..vocab.instruments import InstrumentKind
from . import counts, gear_numbers, rig_card, rigs
from . import objects as obj


class UsageSubject(StrEnum):
    """The words of the `gear_usage.subject` CHECK."""

    INSTRUMENT = "instrument"
    RIG = "rig"
    FILTER = "filter"


# Optics, camera and spacers always have hours: they pass through the rig, which the spine derives
# from every frame. For the others it depends on the archive (`_with_hours`).
_ALWAYS = (InstrumentKind.OPTICS, InstrumentKind.CAMERA, InstrumentKind.SPACER)

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
_PIECE_KINDS = (InstrumentKind.MOUNT, *counts.ON_THE_FRAME, *counts.CHOSEN_ONLY)
PART_KINDS = (*_PIECE_KINDS, InstrumentKind.SPACER, "software", "filter")
_PARTS = (
    *(_PIECE_PART.format(kind=kind) for kind in _PIECE_KINDS),
    # a spacer is on all of its rig's frames: it is the rig's, not the file's
    """
SELECT s.rig_id, 'spacer' AS kind, s.piece_id, NULL AS software, COUNT(f.id) AS frames
FROM rig_spacers s LEFT JOIN frames f ON f.rig_id = s.rig_id AND f.copy_of IS NULL
GROUP BY s.rig_id, s.piece_id
""",
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
_PART_COLUMNS = (
    "rig_id", "kind", "piece_id", "software", "frames", "chosen", "position",
    "ring_from", "ring_to",
)  # fmt: skip

USAGE = ("frames", "integration_s", "untimed", "nights")

# A bar is never thinner than this, or a short one would vanish. [T] board Attrezzatura, v82
BAR_FLOOR_PCT = 3.0
# Rigs and filters each one group, pieces by kind: the board's bars, on the most used of the group.
_BARS = """
WITH g AS (
  SELECT u.subject, u.subject_id, u.integration_s,
         CASE WHEN u.subject = 'instrument' THEN i.kind ELSE u.subject END AS grp
  FROM gear_usage u LEFT JOIN instruments i ON u.subject = 'instrument' AND i.id = u.subject_id
), top AS (SELECT grp, MAX(integration_s) AS most FROM g GROUP BY grp)
UPDATE gear_usage SET bar_pct = (
  SELECT CASE WHEN g.integration_s IS NULL THEN NULL
              WHEN top.most > 0 THEN MAX(:floor, ROUND(100.0 * g.integration_s / top.most, 1))
              ELSE :floor END
  FROM g JOIN top ON top.grp = g.grp
  WHERE g.subject = gear_usage.subject AND g.subject_id = gear_usage.subject_id
)
"""


def write_bars(conn: sqlite3.Connection) -> None:
    """After every write of the usage: one row moving changes the bars of its whole group."""
    conn.execute(_BARS, {"floor": BAR_FLOOR_PCT})


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
    """Redone whole: a frame changing rig moves four rows, one by one would get one wrong. Only
    rigs keep a position (`counts.ORDER_BY_TIME`); the page orders the rest on its own."""
    rigs.write_spacers(conn)
    rows = [(*astuple(r), None) for r in (*_instruments(conn), *_filters(conn))]
    rows += [(*astuple(r), n) for n, r in enumerate(_rigs(conn))]
    replace_rows(conn, "gear_usage", _COLUMNS, rows)
    write_bars(conn)
    write_fields(conn)
    write_parts(conn)


_FIELDS = """SELECT subject_id, width_deg, height_deg FROM gear_usage
WHERE subject = 'rig' AND width_deg IS NOT NULL AND height_deg IS NOT NULL"""


def write_fields(conn: sqlite3.Connection) -> None:
    """The rigs' fields on the comparison frame: one rig measured anew moves every box."""
    fields = {r[0]: (r[1], r[2]) for r in conn.execute(_FIELDS)}
    boxes, moon = rig_card.field_boxes(fields, MOON_DIAMETER_DEG)
    conn.execute("UPDATE gear_usage SET field_w_pct = NULL, field_h_pct = NULL, moon_pct = NULL")
    conn.executemany(
        "UPDATE gear_usage SET field_w_pct = ?, field_h_pct = ?, moon_pct = ?"
        " WHERE subject = 'rig' AND subject_id = ?",
        [(round(w, 2), round(h, 2), round(moon or 0, 2), k) for k, (w, h) in boxes.items()],
    )


def write_parts(conn: sqlite3.Connection) -> None:
    """Alone after a choice on a rig, so the page reads it before the frames are reworked. The
    rig's numbers come after: they read the parts."""
    rigs.write_spacers(conn)
    replace_rows(conn, "rig_parts", _PART_COLUMNS, _parts(conn))
    gear_numbers.write(conn)


_SPACER_USAGE = f"""
SELECT i.id, i.kind, {_USED}
FROM instruments i LEFT JOIN (
  SELECT s.piece_id AS id, {_COUNTS}
  FROM rig_spacers s JOIN frames f ON f.rig_id = s.rig_id
  WHERE f.copy_of IS NULL GROUP BY s.piece_id
) u ON u.id = i.id
WHERE i.kind = 'spacer'
"""  # noqa: S608 - constant fragments of the spine, not user values


def write_spacer_usage(conn: sqlite3.Connection) -> None:
    """After a rig's spacers change: theirs are the rig's hours, so only they are recounted, not
    the archive inside the request."""
    write_parts(conn)
    rows = conn.execute(_SPACER_USAGE).fetchall()
    shot = idlist.grouped(conn, _PIECE_OBJECTS, [r["id"] for r in rows], "owner", obj.counted)
    conn.executemany(
        f"INSERT OR REPLACE INTO gear_usage({', '.join(_COLUMNS)})"
        f" VALUES({', '.join('?' * len(_COLUMNS))})",  # segnaposto-ok: the columns, not the rows
        [(*astuple(_row(UsageSubject.INSTRUMENT, r, shot)), None) for r in rows],
    )
    write_bars(conn)


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
            ring = _ring([f for _, _, f in listed]) if kind == "filter" else None
            for n, (piece, software, frames) in enumerate(listed):
                # asked by kind first: the software has no id, and no id is not a choice
                chosen = kind == InstrumentKind.SPACER or (kind in mine and mine[kind] == piece)
                cut = ring[n] if ring else (None, None)
                rows.append((rig["id"], kind, piece, software, frames, int(chosen), position, *cut))
                position += 1
    return rows


def _ring(frames: Sequence[int]) -> list[tuple[float, float]] | None:
    """Each filter's slice of the rig's ring, in percent of its filtered frames; none without."""
    total = sum(frames)
    if not total:
        return None
    cuts, start = [], 0.0
    for n in frames:
        end = start + n / total * 100
        cuts.append((round(start, 2), round(end, 2)))
        start = end
    return cuts


def add_piece(conn: sqlite3.Connection, instrument_id: int, kind: InstrumentKind) -> None:
    """Only its own row: recounting the whole archive inside the request that creates it would
    cost seconds."""
    _add_row(conn, UsageSubject.INSTRUMENT, instrument_id, known=kind in _with_hours(conn))


def add_new(conn: sqlite3.Connection, subject: UsageSubject, row_id: int) -> None:
    """A filter's or rig's hours are always known: the frame names its filter and its rig."""
    _add_row(conn, subject, row_id, known=True)


def _add_row(conn: sqlite3.Connection, subject: UsageSubject, row_id: int, *, known: bool) -> None:
    """A rig goes at the bottom of its list, which runs from the most used: at the top, with zero
    hours, it would lie."""
    conn.execute(
        "INSERT OR REPLACE INTO gear_usage(subject, subject_id, frames, integration_s, untimed,"
        " nights, objects_json, position) VALUES(?, ?, ?, ?, ?, ?, '[]',"
        " CASE WHEN ? = 'rig' THEN"
        " (SELECT COALESCE(MAX(position) + 1, 0) FROM gear_usage WHERE subject = 'rig') END)",
        (subject, row_id, *((0, 0.0, 0, 0) if known else (None,) * 4), subject),
    )
    write_bars(conn)


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
