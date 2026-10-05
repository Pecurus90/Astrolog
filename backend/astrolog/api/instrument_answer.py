"""The kind decides a card's fields, here and not in the page: the browser is not the only caller,
and the schema alone would let a mount be born with a telescope's aperture."""

import sqlite3
from typing import Any, Final

from fastapi import HTTPException

from ..spine import declarations as decl
from ..spine import gear
from ..spine import unfiltered as unfiltered_reader
from .models_gear import InstrumentCorrection

# Only what the app computes with (`docs/domini/spina.md`, *Le schede*); the camera's two fields
# are `decl.CAMERA_SPECS` and not a copy, being the ones the card writes among the declarations.
_COMMON = ("brand", "model")
_ON_EVERY_PIECE = ("weight_kg", "notes")
CARD: Final[dict[str, tuple[str, ...]]] = {
    kind: (*_COMMON, *own, *_ON_EVERY_PIECE)
    for kind, own in {
        "optics": ("aperture_mm", "focal_mm"),
        "camera": decl.CAMERA_SPECS,
        "mount": ("payload_kg",),
        "reducer": ("reducer_factor",),
        "filter_wheel": ("slots",),
        "guide_scope": (),
        "guide_camera": (),
        "focuser": (),
    }.items()
}


class FieldNotOfKindError(ValueError):
    """A field that kind's card does not ask for; the route that exposes it makes it a 422."""

    def __init__(self, kind: str, fields: list[str]) -> None:
        super().__init__(f"{kind} non ha {', '.join(fields)}")
        self.fields = fields


def of_the_kind(kind: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Refused, not dropped: a field the kind lacks is the caller's mistake, and swallowing it would
    accept an answer that did not do what it said."""
    # they say which piece and its name, for every kind: not card fields
    fuori = sorted(set(fields) - {"kind", "name", "merge_into", *CARD[kind]})
    if fuori:
        raise FieldNotOfKindError(kind, fuori)
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
    kind = _kind(conn, instrument_id)  # None: `declare_instrument` raises the LookupError
    scheda = edit.model_dump(exclude_none=True)
    if kind is not None:
        of_the_kind(kind, scheda)
    if not gear.declare_instrument(conn, instrument_id, scheda, now):
        return set()
    # The colour also answers for the frames that do not name their filter, requeued only if it
    # changes: "mono" on a camera already treated as mono moves nothing.
    if edit.camera_type is not None and _colour(conn, instrument_id) != colour_before:
        return set(unfiltered_reader.requeue(conn, instrument_id))
    return set()


def merge(conn: sqlite3.Connection, instrument_id: int, into_id: int, now: str) -> set[int]:
    """The merge of two spellings. Returns the frames to requeue."""
    requeued = set(gear.merge_instrument(conn, instrument_id, into_id, now))
    # the absorbed camera's answer passes to the kept one: its frames must feel it
    requeued.update(unfiltered_reader.requeue(conn, into_id))
    return requeued


def _kind(conn: sqlite3.Connection, instrument_id: int) -> str | None:
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
        and row["kind"] == "camera"
        and unfiltered_reader.is_colour(conn, row["name"])
    )
