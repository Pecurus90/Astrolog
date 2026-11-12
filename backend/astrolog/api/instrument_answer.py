"""The kind decides a card's fields, here and not in the page: the browser is not the only caller,
and the schema alone would let a mount be born with a telescope's aperture."""

import sqlite3
from collections.abc import Collection
from typing import Any, Final

from fastapi import HTTPException

from ..db import idlist
from ..spine import gear
from ..spine import unfiltered as unfiltered_reader
from ..spine.stages import StageName, invalidate
from ..vocab.instruments import InstrumentKind
from .models_gear import InstrumentCorrection

# The maker's sheet, kind by kind and in reading order (ADR 0021). The camera's file-told fields
# are `declarations.CAMERA_SPECS`, kept among the declarations; the guide camera's are not.
_COMMON = ("brand", "model")
_ON_EVERY_PIECE = ("weight_kg", "notes")
_SENSOR = ("sensor", "camera_type", "pixel_size_um", "width_px", "height_px", "adc_bits")
_BACK_END = ("image_circle_mm", "required_backfocus_mm", "backfocus_tolerance_mm")
CARD: Final[dict[InstrumentKind, tuple[str, ...]]] = {
    kind: (*_COMMON, *own, *_ON_EVERY_PIECE)
    for kind, own in {
        InstrumentKind.OPTICS: ("optical_design", "aperture_mm", "focal_mm", *_BACK_END),
        InstrumentKind.CAMERA: (*_SENSOR, "cooled", "cooling_c", "thickness_mm"),
        InstrumentKind.MOUNT: ("payload_kg", "payload_no_cw_kg"),
        InstrumentKind.REDUCER: ("reducer_factor", *_BACK_END),
        InstrumentKind.FILTER_WHEEL: ("slots", "filter_size", "thickness_mm"),
        InstrumentKind.GUIDE_SCOPE: ("aperture_mm", "focal_mm"),
        InstrumentKind.GUIDE_CAMERA: (*_SENSOR, "thickness_mm"),
        InstrumentKind.FOCUSER: ("step_um", "total_steps"),
        InstrumentKind.OAG: ("thickness_mm", "prism_mm"),
        InstrumentKind.SPACER: ("thickness_mm",),
    }.items()
}


class FieldNotOfKindError(ValueError):
    """A field that kind's card does not ask for; the route that exposes it makes it a 422."""

    def __init__(self, kind: InstrumentKind, fields: list[str]) -> None:
        super().__init__(f"{kind} non ha {', '.join(fields)}")
        self.fields = fields


def of_the_kind(kind: InstrumentKind, fields: dict[str, Any]) -> dict[str, Any]:
    """Refused, not dropped: a field the kind lacks is the caller's mistake, and swallowing it would
    accept an answer that did not do what it said."""
    # they say which piece and its name, for every kind: not card fields
    stray = sorted(set(fields) - {"kind", "name", "merge_into", *CARD[kind]})
    if stray:
        raise FieldNotOfKindError(kind, stray)
    return fields


def refused(err: FieldNotOfKindError) -> HTTPException:
    """A code, not a sentence. Here because more than one route translates it, and separate
    translations of one exception drift at the first field added."""
    return HTTPException(
        status_code=422, detail={"code": "field_not_of_kind", "fields": err.fields}
    )


def answer(
    conn: sqlite3.Connection, instrument_id: int, edit: InstrumentCorrection, now: str
) -> set[int]:
    """The corrected card, or the merge with another piece. Returns the frames to requeue."""
    if edit.merge_into is not None:
        return merge(conn, instrument_id, edit.merge_into, now)
    colour_before = _colour(conn, instrument_id)
    pixel_before = _pixel(conn, instrument_id)
    kind = _kind(conn, instrument_id)  # None: `declare_instrument` raises the LookupError
    card = edit.model_dump(exclude_none=True)
    if kind is not None:
        of_the_kind(kind, card)
    if not gear.declare_instrument(conn, instrument_id, card, now):
        return set()
    requeued: set[int] = set()
    # The colour also answers for the frames that do not name their filter, requeued only if it
    # changes: "mono" on a camera already treated as mono moves nothing.
    if edit.camera_type is not None and _colour(conn, instrument_id) != colour_before:
        requeued.update(unfiltered_reader.requeue(conn, instrument_id))
    if _pixel(conn, instrument_id) != pixel_before:
        requeued.update(solve_again(conn, instrument_id, now))
    return requeued


def solve_again(conn: sqlite3.Connection, camera_id: int, now: str) -> list[int]:
    """The frames without `XPIXSZ` measure their focal with the card's pixel (Issue #62)."""
    frames = [
        r[0]
        for r in conn.execute(
            "SELECT f.id FROM frames f JOIN rigs r ON r.id = f.rig_id"
            " WHERE r.camera_id = ? AND f.pixel_size_um IS NULL",
            (camera_id,),
        )
    ]
    invalidate(conn, frames, StageName.SOLVE, now=now)
    return frames


def _pixel(conn: sqlite3.Connection, instrument_id: int) -> float | None:
    """A camera's pixel as the page and the solve read it, your word over the files'."""
    return gear.camera_specs(conn).get(instrument_id, {}).get("pixel_size_um")


def merge(conn: sqlite3.Connection, instrument_id: int, into_id: int, now: str) -> set[int]:
    """The merge of two spellings. Returns the frames to requeue."""
    colour_before = _colour(conn, into_id)
    pixel_before = _pixel(conn, into_id)
    requeued = set(gear.merge_instrument(conn, instrument_id, into_id, now))
    # the absorbed camera's answer passes to the kept one: its frames feel it if it changes
    if _colour(conn, into_id) != colour_before:
        requeued.update(unfiltered_reader.requeue(conn, into_id))
    if _pixel(conn, into_id) != pixel_before:
        requeued.update(solve_again(conn, into_id, now))
    return requeued


def first_stage(conn: sqlite3.Connection, frames: Collection[int]) -> StageName:
    """Where the work restarts: the solve if some requeued frame waits for it."""
    with idlist.holding(conn, frames) as listed:
        waiting = conn.execute(
            f"SELECT 1 FROM frame_stages WHERE frame_id IN {listed}"  # noqa: S608
            " AND stage = 'solve' AND status = 'pending' LIMIT 1"
        ).fetchone()
    return StageName.SOLVE if waiting else StageName.NORMALIZE


def _kind(conn: sqlite3.Connection, instrument_id: int) -> InstrumentKind | None:
    row = conn.execute("SELECT kind FROM instruments WHERE id = ?", (instrument_id,)).fetchone()
    return None if row is None else row["kind"]


def _colour(conn: sqlite3.Connection, instrument_id: int) -> bool:
    """The same fact `normalize` reads (`unfiltered.is_colour`), read by id: the answer may also
    rename the camera."""
    row = conn.execute(
        "SELECT kind, name FROM instruments WHERE id = ?", (instrument_id,)
    ).fetchone()
    return (
        row is not None
        and row["kind"] == InstrumentKind.CAMERA
        and unfiltered_reader.is_colour(conn, row["name"])
    )
