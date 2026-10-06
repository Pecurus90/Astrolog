"""The order in which the answers apply; the rules live in the spine."""

import sqlite3
from collections.abc import Collection, Iterator
from contextlib import contextmanager

from fastapi import HTTPException

from ..db.transaction import transaction
from ..spine import coordinates as places
from ..spine import declarations as decl
from ..spine import gear, gear_create, mosaic, object_answer, rigs, unnamed
from ..spine.group import GroupReason
from ..spine.stages import StageName, invalidate
from . import instrument_answer, lookalike
from . import review_page as page
from . import review_write_folders as folders
from .models_review_apply import (
    CoordinatesEdit,
    FilterCorrection,
    MosaicEdit,
    ObjectEdit,
    ReviewApply,
)

_CONSTRAINT_CODES = {
    "filters.name": "name_taken",
    "instruments.kind": "name_taken",
    "filters.is_none": "none_filter_exists",
}


def apply_answers(conn: sqlite3.Connection, body: ReviewApply, now: str) -> tuple[int, set[int]]:
    """Group answers first, then merges (which delete rows), then filters and objects: a merge in
    the same Apply carries the answer along instead of leaving it looking for a vanished name."""
    changed = 0
    requeued: set[int] = set()
    # the rigs and filters to choose from do not change inside Apply: read once
    choices = (
        ({c.id: c for c in page.rig_choices(conn)}, {f.id: f for f in page.filter_choices(conn)})
        if body.gear
        else ({}, {})
    )
    for edit in body.gear:
        requeued.update(folders.answer_gear(conn, edit, now, choices))
        changed += 1
    for edit in body.typeless:
        requeued.update(folders.answer_typeless(conn, edit, now))
        changed += 1
    for edit in body.mosaics:
        _answer_mosaic(conn, edit, now)
        changed += 1
    requeued.update(lookalike.answer_all(conn, body.lookalikes, now))
    changed += len(body.lookalikes)
    for edit in body.filters:
        filter_requeued, written = answer_filter(conn, edit.id, edit, now)
        requeued.update(filter_requeued)
        changed += int(written)
    # objects' answers move no unnamed group in or out: read them once, not once per answer
    groups = (
        {g.key for g in unnamed.by_group(conn)}
        if any(e.key.startswith(page.FRAMES_KEY) for e in body.objects)
        else set()
    )
    for edit in body.objects:
        requeued.update(_answer_object(conn, edit, now, groups))
        changed += 1
    for edit in body.unclear:
        requeued.update(_answer_where(conn, edit, now))
        changed += 1
    return changed, requeued


def answer_filter(
    conn: sqlite3.Connection, filter_id: int, edit: FilterCorrection, now: str
) -> tuple[list[int], bool]:
    """From both doors, the merge or the card with the bands. The flag says whether anything was
    written: an empty card is not."""
    if edit.merge_into is not None:
        return gear.merge_filter(conn, filter_id, edit.merge_into, now), True
    fields = edit.model_dump(exclude_none=True, exclude={"id", "bands", "is_none", "merge_into"})
    bands = [b.model_dump() for b in edit.bands] if edit.bands is not None else None
    is_none = getattr(edit, "is_none", None)
    requeued = gear.declare_filter(conn, filter_id, fields, bands, is_none, now)
    return requeued, bool(fields) or bands is not None or is_none is not None


@contextmanager
def writing(conn: sqlite3.Connection) -> Iterator[None]:
    """All or nothing, and the refusals of the database or the rules become words a page can show,
    not failures. One home for Apply and for the Gear gestures."""
    try:
        with transaction(conn):
            yield
    except Exception as err:
        refusal = _refusal(err)
        if refusal is None:
            raise
        raise refusal from err


# The refusals of the rules, as (status, code): words a page can show.
_REFUSALS: tuple[tuple[type[Exception], int, str], ...] = (
    (gear.MergeRefusedError, 422, "merge_refused"),
    (folders.NotAskedError, 422, "not_asked"),
    (decl.UnknownTargetError, 422, "unknown_target"),
    (rigs.NotAMountError, 422, "not_a_mount"),
    (rigs.WrongKindError, 422, "wrong_kind"),
    (gear_create.SpellingTakenError, 409, "spelling_taken"),
    (rigs.RigExistsError, 409, "rig_exists"),
)


def _refusal(err: Exception) -> HTTPException | None:
    """`None` if the error is a failure of ours."""
    if isinstance(err, instrument_answer.FieldNotOfKindError):
        return instrument_answer.refused(err)
    for error_type, status, code in _REFUSALS:
        if isinstance(err, error_type):
            return HTTPException(status_code=status, detail={"code": code})
    # a `KeyError` is a `LookupError` but a failure of ours: a 404 would tell the user their
    # piece is not there
    if isinstance(err, LookupError) and not isinstance(err, KeyError):
        return HTTPException(status_code=404, detail={"code": "not_found"})
    if isinstance(err, sqlite3.IntegrityError):
        return HTTPException(status_code=409, detail={"code": constraint_code(err)})
    return None


def _answer_mosaic(conn: sqlite3.Connection, edit: MosaicEdit, now: str) -> None:
    """No frame is requeued: the answer itself writes the mosaic on the frames. A name the catalog
    knows as a designation goes to its entry: whoever writes `IC 405` means IC 405."""
    value = decl.MosaicAnswer.NO
    if edit.answer == decl.MosaicAnswer.YES:
        slug, name = object_answer.resolved(conn, None, (edit.name or "").strip())
        value = object_answer.target_value(slug, name)
    mosaic.write_answer(conn, edit.key, value, now)


def _answer_object(
    conn: sqlite3.Connection, edit: ObjectEdit, now: str, groups: Collection[str]
) -> list[int]:
    """The card's key says who writes: the found object's, or the group's of frames with no name
    and no sky. A key with neither head is a card that is not there."""
    if edit.key.startswith(page.FRAMES_KEY):
        key = edit.key.removeprefix(page.FRAMES_KEY)
        return folders.answer_unnamed(conn, key, edit, now, groups)
    if not edit.key.startswith(page.OBJECT_KEY):
        raise LookupError(f"scheda {edit.key}")
    object_key = edit.key.removeprefix(page.OBJECT_KEY)
    if edit.not_an_object:
        return object_answer.declare_not_an_object(conn, object_key, now)
    return object_answer.declare_found(conn, object_key, slug=edit.slug, name=edit.name, now=now)


def _answer_where(conn: sqlite3.Connection, edit: CoordinatesEdit, now: str) -> list[int]:
    """Coordinates with no frame and a deleted site are checked before writing, or the declaration
    would point at nothing. The site's NAME is written, since ids are reused."""
    frames = places.frames_at(conn, edit.key, GroupReason.SITE_UNCLEAR)
    if not frames:
        raise LookupError(f"coordinate {edit.key}")
    site = conn.execute("SELECT name FROM sites WHERE id = ?", (edit.site_id,)).fetchone()
    if site is None:
        raise LookupError(f"sito {edit.site_id}")
    decl.declare_coordinates(conn, edit.key, site["name"], now)
    invalidate(conn, frames, StageName.GROUP)
    return frames


def constraint_code(err: sqlite3.IntegrityError) -> str:
    for needle, code in _CONSTRAINT_CODES.items():
        if needle in str(err):
            return code
    return "constraint_violated"
