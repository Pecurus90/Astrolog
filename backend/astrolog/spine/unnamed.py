"""Frames with no name and no sky, grouped by night, camera, telescope and pointing: the group, the
question, and the answer `identify` reads, which also holds for frames still to come."""

import json
import sqlite3
from dataclasses import dataclass
from typing import Literal

from ..catalog import NamedEntry
from ..clock import NIGHT_SQL, local_iso
from ..db.row import Row
from ..units import angular_separation_deg, field_deg, scale_arcsec_px
from ..vocab.header_value import normalize_header_value
from . import declarations as decl
from . import frame_folder as folder
from . import object_answer
from .object_answer import Answer, TargetKind
from .stages import WAITING_SQL, StageName, invalidate

_OF_FRAME = f"""
SELECT f.unnamed_key, {NIGHT_SQL} AS night, f.instrument_raw, f.telescope_raw, f.ra_hint_deg,
  f.dec_hint_deg, f.focal_mm_raw, f.pixel_size_um, f.naxis1, f.naxis2
FROM frames f WHERE f.id = ?
"""  # noqa: S608 - constant fragment of the spine

# `IS`, not `=`: "no date" is a group as well.
_GROUPS_OF_NIGHT = """
SELECT DISTINCT unnamed_key FROM frames
WHERE unnamed_key IS NOT NULL AND json_extract(unnamed_key, '$[0]') IS ?
"""

# A sky that says nothing counts as none. Frames waiting on their type stay out: answering with an
# object would turn a calibration into hours. `EXISTS`, or SQLite starts from every frame's stages.
_BY_GROUP = f"""
SELECT f.unnamed_key AS key, MIN(f.instrument_raw) AS instrument_raw,
  MIN(f.telescope_raw) AS telescope_raw, SUM(f.copy_of IS NULL) AS n,
  COALESCE(SUM(f.exposure_s) FILTER (WHERE f.copy_of IS NULL), 0) AS integration_s,
  SUM(f.copy_of IS NULL AND f.exposure_s IS NULL) AS untimed,
  MIN(f.date_obs) AS first_frame, MAX(f.date_obs) AS last_frame, MIN(f.local_tz) AS tz
FROM frames f {folder.JOIN}
WHERE f.unnamed_key IS NOT NULL AND NOT ({WAITING_SQL}) AND EXISTS (
  SELECT 1 FROM frame_stages so WHERE so.frame_id = f.id AND so.stage = 'solve'
    AND so.status <> 'pending') AND (
  f.empty_cone = 1 OR NOT EXISTS (SELECT 1 FROM frame_wcs w WHERE w.frame_id = f.id))
GROUP BY f.unnamed_key
"""  # noqa: S608 - constant fragments of the spine

# The frames a group's answer is about: a sky with candidates decides by itself, so those frames
# neither take the answer nor carry one that counts. Without a sky yet (NULL) they are asked.
_ASKED = "COALESCE(f.empty_cone, 1) = 1"

# Copies and frames with a sky included: `identify` makes the choice again.
_FRAMES_OF_GROUP = f"SELECT f.id FROM frames f {folder.JOIN} WHERE f.unnamed_key = ?"  # noqa: S608

# Two are enough to tell one answer from a disagreement. `CROSS JOIN` starts from the group's
# frames, or SQLite would walk every frame answer for each group.
_ANSWERS_OF_GROUP = f"""
SELECT DISTINCT d.value FROM frames f CROSS JOIN declarations d ON d.entity_type = ?
  AND d.entity_key = f.frame_hash AND d.field = ?
WHERE f.unnamed_key = ? AND {_ASKED} LIMIT 2
"""  # noqa: S608 - constant fragment of this file


@dataclass(frozen=True, slots=True)
class Group:
    """A group as the page asks it, with the opener's pointing. `first_frame` and `last_frame`
    tell two pointing-less targets of one night apart: only frames that say the time count."""

    key: str
    night: str | None
    camera: str | None
    telescope: str | None
    ra_deg: float | None
    dec_deg: float | None
    frames: int
    integration_s: float
    untimed: int
    answer: Answer | None
    first_frame: str | None
    last_frame: str | None


def _field(r: Row) -> float | None:
    """The short side of the field, in degrees."""
    sides = [p for p in (r["naxis1"], r["naxis2"]) if p]
    return (
        field_deg(min(sides), scale_arcsec_px(r["pixel_size_um"], r["focal_mm_raw"]))
        if sides
        else None
    )


def assign(conn: sqlite3.Connection, frame_id: int) -> str:
    """Chosen on arrival and written on the frame. Compared with the opener's pointing, kept in the
    key: a fixed grid would split a dithered target, comparing every member would chain."""
    r = conn.execute(_OF_FRAME, (frame_id,)).fetchone()
    if r["unnamed_key"]:
        return r["unnamed_key"]
    camera = normalize_header_value(r["instrument_raw"]) or None
    telescope = normalize_header_value(r["telescope_raw"]) or None
    ra, dec, fov = r["ra_hint_deg"], r["dec_hint_deg"], _field(r)
    # without pointing, focal or pixel the field is unknown: the night's pointing-less group
    pointing = None if ra is None or dec is None or fov is None else (ra, dec, fov)
    key = json.dumps([r["night"], camera, telescope, *(pointing or (None, None))[:2]])
    near = []
    for (other,) in conn.execute(_GROUPS_OF_NIGHT, (r["night"],)):
        _, c, t, a_ra, a_dec = json.loads(other)
        if (c, t) != (camera, telescope) or (a_ra is None) != (pointing is None):
            continue
        if pointing is None:
            near.append((0.0, other))
        elif (distance := angular_separation_deg(*pointing[:2], a_ra, a_dec)) < pointing[2]:
            near.append((distance, other))
    if near:
        key = min(near)[1]
    conn.execute("UPDATE frames SET unnamed_key = ? WHERE id = ?", (key, frame_id))
    return key


def key_of_frame(conn: sqlite3.Connection, frame_id: int) -> str | None:
    return conn.execute("SELECT unnamed_key FROM frames WHERE id = ?", (frame_id,)).fetchone()[0]


def _written(value: str | None) -> str | None:
    """A raw header value as the page shows it."""
    return (value or "").strip() or None


def by_group(conn: sqlite3.Connection) -> list[Group]:
    """Largest first. A group of only copies asks nothing."""
    out = []
    for r in conn.execute(_BY_GROUP):
        if not r["n"]:
            continue
        night, _, _, ra, dec = json.loads(r["key"])
        out.append(Group(
            key=r["key"], night=night, camera=_written(r["instrument_raw"]),
            telescope=_written(r["telescope_raw"]), ra_deg=ra, dec_deg=dec,
            frames=r["n"], integration_s=r["integration_s"], untimed=r["untimed"],
            answer=answer(conn, r["key"]),
            # without a zone it stays UTC
            first_frame=local_iso(r["first_frame"], r["tz"]),
            last_frame=local_iso(r["last_frame"], r["tz"]),
        ))  # fmt: skip
    return sorted(out, key=lambda g: (-g.frames, g.key))


def declare(  # noqa: PLR0913
    conn: sqlite3.Connection,
    key: str,
    *,
    slug: str | None = None,
    name: str | None = None,
    not_an_object: bool = False,
    now: str | None = None,
) -> None:
    """On every frame's fingerprint, so a frame that changes group carries it. Rewritable; an
    unknown slug is refused before writing."""
    object_answer.refuse_unknown_slug(conn, slug)
    slug, name = object_answer.resolved(conn, slug, name)
    value = TargetKind.NONE if not_an_object else object_answer.target_value(slug, name)
    # every frame `answer` reads, missing ones too: a stale one would leave two answers
    rows = conn.execute(
        f"SELECT f.frame_hash FROM frames f WHERE f.unnamed_key = ? AND {_ASKED}",  # noqa: S608
        (key,),
    ).fetchall()
    for r in rows:
        decl.write_declaration(
            conn, decl.EntityType.FRAME, r["frame_hash"], decl.FRAME_OBJECT, value, now
        )


def _said(conn: sqlite3.Connection, key: str | None) -> str | None:
    """The one answer its frames carry, which newcomers take. Two answers are none."""
    said = conn.execute(
        _ANSWERS_OF_GROUP, (decl.EntityType.FRAME, decl.FRAME_OBJECT, key)
    ).fetchall()
    return said[0][0] if len(said) == 1 else None


def answer(conn: sqlite3.Connection, key: str | None) -> Answer | None:
    """A gone catalog entry is no answer: its frames stay a question."""
    value = _said(conn, key)
    if value is None:
        return None
    if value == TargetKind.NONE:
        return Answer(TargetKind.NONE, None, None)
    return object_answer.shown_target(conn, value)


def requeue(conn: sqlite3.Connection, key: str) -> list[int]:
    """All of them, copies and frames with a sky included: `identify` redoes the choice, and where
    the sky has candidates it makes the same one."""
    frames = [r["id"] for r in conn.execute(_FRAMES_OF_GROUP, (key,))]
    invalidate(conn, frames, StageName.IDENTIFY)
    return frames


def named_by_group(
    conn: sqlite3.Connection, key: str | None
) -> tuple[str, NamedEntry | None] | Literal[TargetKind.NONE] | None:
    """`(name, catalog entry)`, `NONE` for "not an object", `None` for no answer or a vanished slug:
    the user's word moves frames, it never makes them disappear."""
    value = _said(conn, key)
    if value == TargetKind.NONE:
        return TargetKind.NONE
    read = object_answer.read_target(value)
    if read is None:
        return None
    kind, target = read
    if kind == TargetKind.NAME:
        return target, None
    return object_answer.catalog_target(conn, target)
