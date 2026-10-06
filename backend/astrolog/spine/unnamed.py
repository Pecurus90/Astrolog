"""Frames with no name and no sky, grouped by night, camera, telescope and pointing: the group, the
question, and the answer `identify` reads, which also holds for frames still to come."""

import json
import sqlite3
from typing import Any, Literal

from ..clock import NIGHT_SQL, local_iso
from ..db.row import Row
from ..units import angular_separation_deg, field_deg, scale_arcsec_px
from ..vocab.header_value import normalize_header_value
from . import declarations as decl
from . import frame_folder as folder
from . import object_answer as risposta
from .object_answer import NONE
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
_POSES_OF_GROUP = f"SELECT f.id FROM frames f {folder.JOIN} WHERE f.unnamed_key = ?"  # noqa: S608

# Two are enough to tell one answer from a disagreement.
_ANSWERS_OF_GROUP = f"""
SELECT DISTINCT d.value FROM frames f JOIN declarations d ON d.entity_type = ?
  AND d.entity_key = f.frame_hash AND d.field = ?
WHERE f.unnamed_key = ? AND {_ASKED} LIMIT 2
"""  # noqa: S608 - constant fragment of this file


def _field(r: Row) -> float | None:
    """The short side of the field, in degrees."""
    lati = [p for p in (r["naxis1"], r["naxis2"]) if p]
    return (
        field_deg(min(lati), scale_arcsec_px(r["pixel_size_um"], r["focal_mm_raw"]))
        if lati
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
    ra, dec, campo = r["ra_hint_deg"], r["dec_hint_deg"], _field(r)
    # without pointing, focal or pixel the field is unknown: the night's pointing-less group
    pointing = None if ra is None or dec is None or campo is None else (ra, dec, campo)
    chiave = json.dumps([r["night"], camera, telescope, *(pointing or (None, None))[:2]])
    vicini = []
    for (altra,) in conn.execute(_GROUPS_OF_NIGHT, (r["night"],)):
        _, c, t, a_ra, a_dec = json.loads(altra)
        if (c, t) != (camera, telescope) or (a_ra is None) != (pointing is None):
            continue
        if pointing is None:
            vicini.append((0.0, altra))
        elif (distanza := angular_separation_deg(*pointing[:2], a_ra, a_dec)) < pointing[2]:
            vicini.append((distanza, altra))
    if vicini:
        chiave = min(vicini)[1]
    conn.execute("UPDATE frames SET unnamed_key = ? WHERE id = ?", (chiave, frame_id))
    return chiave


def key_of_frame(conn: sqlite3.Connection, frame_id: int) -> str | None:
    return conn.execute("SELECT unnamed_key FROM frames WHERE id = ?", (frame_id,)).fetchone()[0]


def _written(value: str | None) -> str | None:
    """A raw header value as the page shows it."""
    return (value or "").strip() or None


def by_group(conn: sqlite3.Connection, only: str | None = None) -> list[dict[str, Any]]:
    """Largest first, with the opener's pointing; `only` keeps one group. A group of only copies
    asks nothing."""
    out = []
    for r in conn.execute(_BY_GROUP):
        if not r["n"] or (only is not None and r["key"] != only):
            continue
        notte, _, _, ra, dec = json.loads(r["key"])
        out.append({
            "key": r["key"], "night": notte, "camera": _written(r["instrument_raw"]),
            "telescope": _written(r["telescope_raw"]), "ra_deg": ra, "dec_deg": dec,
            "frames": r["n"], "integration_s": r["integration_s"], "untimed": r["untimed"],
            "answer": answer(conn, r["key"]),
            # two pointing-less targets in one night are one question: the hours tell a series
            # from two. Only frames that say the time count; without a zone it stays UTC
            "first_frame": local_iso(r["first_frame"], r["tz"]),
            "last_frame": local_iso(r["last_frame"], r["tz"]),
        })  # fmt: skip
    return sorted(out, key=lambda g: (-g["frames"], g["key"]))


def row_of(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return next(iter(by_group(conn, only=key)), None)


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
    risposta.refuse_unknown_slug(conn, slug)
    slug, name = risposta.resolved(conn, slug, name)
    value = NONE if not_an_object else risposta.target_value(slug, name)
    # every frame `answer` reads, missing ones too: a stale one would leave two answers
    rows = conn.execute(
        f"SELECT f.frame_hash FROM frames f WHERE f.unnamed_key = ? AND {_ASKED}",  # noqa: S608
        (key,),
    ).fetchall()
    for r in rows:
        decl.write_declaration(conn, decl.FRAME, r["frame_hash"], decl.FRAME_OBJECT, value, now)


def answer(conn: sqlite3.Connection, key: str | None) -> dict[str, Any] | None:
    """`{"kind", "value", "name"}`: the one answer its frames carry, which newcomers take. Two
    answers are none, and so is a gone catalog entry: its frames stay a question."""
    dette = conn.execute(_ANSWERS_OF_GROUP, (decl.FRAME, decl.FRAME_OBJECT, key)).fetchall()
    if len(dette) != 1:
        return None
    value = dette[0][0]
    if value == NONE:
        return {"kind": NONE, "value": None, "name": None}
    detto = risposta.shown_target(conn, value)
    if detto is None:
        return None
    kind, valore, nome = detto
    return {"kind": kind, "value": valore, "name": nome}


def requeue(conn: sqlite3.Connection, row: Row) -> list[int]:
    """All of them, copies and frames with a sky included: `identify` redoes the choice, and where
    the sky has candidates it makes the same one."""
    frames = [r["id"] for r in conn.execute(_POSES_OF_GROUP, (row["key"],))]
    invalidate(conn, frames, StageName.IDENTIFY)
    return frames


def named_by_group(
    conn: sqlite3.Connection, key: str | None
) -> tuple[str, dict[str, Any] | None] | Literal["none"] | None:
    """`(name, catalog entry)`, `NONE` for "not an object", `None` for no answer or a vanished slug:
    the user's word moves frames, it never makes them disappear."""
    detto = answer(conn, key)
    if detto is None:
        return None
    if detto["kind"] == NONE:
        return NONE
    if detto["kind"] == "name":
        return detto["value"], None
    return risposta.catalog_target(conn, detto["value"])
