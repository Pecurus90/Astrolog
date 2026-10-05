"""The order in which the answers apply; the rules live in the spine. The objects confirmed are
those the page READ listed (`seen`): a scan may have slipped in before the click."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException

from ..db.transaction import transaction
from ..spine import coordinates as places
from ..spine import declarations as decl
from ..spine import gear, gear_create, mosaic
from ..spine import object_answer as risposta
from ..spine import objects as obj
from ..spine import rigs as corredi
from ..spine import unfiltered as unfiltered_reader
from ..spine.group import SITE_UNCLEAR
from ..spine.stages import invalidate
from . import instrument_answer as strumento
from . import lookalike
from . import review_page as page
from . import review_write_folders as folders
from .models_review import ReviewSeen
from .models_review_apply import (
    CoordinatesEdit,
    FilterCorrection,
    MosaicEdit,
    ReviewApply,
    UnfilteredEdit,
)

_CONSTRAINT_CODES = {
    "filters.name": "name_taken",
    "instruments.kind": "name_taken",
    "filters.is_none": "none_filter_exists",
}


# SQLite's largest row id: the limit of whoever sends no `seen`, "confirm what is there now"
_TUTTO = 2**63 - 1
_SENZA_LIMITI = ReviewSeen(objects=_TUTTO)


def confirm_seen(conn: sqlite3.Connection, seen: ReviewSeen | None, now: str) -> int:
    """By row number, not time: two rows born in the same instant cannot be ordered. An object
    still open (`object_still_open`) is not confirmed by seeing it; gear is not confirmed here."""
    fino_a = seen or _SENZA_LIMITI
    count = 0
    for row in obj.identities(conn):
        chiave = obj.stable_key(row)
        if chiave and row["id"] <= fino_a.objects and not page.object_still_open(conn, row):
            decl.confirm(conn, "object", chiave, now)
            count += 1
    return count


def apply_answers(conn: sqlite3.Connection, body: ReviewApply, now: str) -> tuple[int, set[int]]:
    """Group answers first, then merges (which delete rows), then filters and objects: a merge in
    the same Apply carries the answer along instead of leaving it looking for a vanished name."""
    changed = 0
    requeued: set[int] = set()
    for edit in body.unfiltered:
        requeued.update(_answer_unfiltered(conn, edit, now))
        changed += 1
    # the rigs to choose from do not change inside Apply: read once
    scelte = {c.id: c for c in page.rig_choices(conn)} if body.rigless else {}
    for edit in body.rigless:
        requeued.update(folders.answer_rigless(conn, edit, now, scelte))
        changed += 1
    for edit in body.opticsless:
        requeued.update(folders.answer_opticsless(conn, edit, now))
        changed += 1
    for edit in body.unnamed:
        requeued.update(folders.answer_unnamed(conn, edit, now))
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
        rimesse, scritta = answer_filter(conn, edit.id, edit, now)
        requeued.update(rimesse)
        changed += int(scritta)
    for edit in body.objects:
        requeued.update(
            risposta.declare_object(conn, edit.key, slug=edit.slug, name=edit.name, now=now)
        )
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
def scrivendo(conn: sqlite3.Connection) -> Iterator[None]:
    """All or nothing, and the refusals of the database or the rules become words a page can show,
    not failures. One home for Apply and for the Gear gestures."""
    try:
        with transaction(conn):
            yield
    except Exception as err:
        rifiuto = _rifiuto(err)
        if rifiuto is None:
            raise
        raise rifiuto from err


def _rifiuto(err: Exception) -> HTTPException | None:
    """`None` if the error is a failure of ours."""
    if isinstance(err, strumento.FieldNotOfKindError):
        return strumento.refused(err)
    if isinstance(err, gear.MergeRefusedError):
        return HTTPException(status_code=422, detail={"code": "merge_refused"})
    if isinstance(err, decl.UnknownTargetError):
        return HTTPException(status_code=422, detail={"code": "unknown_target"})
    if isinstance(err, corredi.NotAMountError):
        return HTTPException(status_code=422, detail={"code": "not_a_mount"})
    if isinstance(err, corredi.WrongKindError):
        return HTTPException(status_code=422, detail={"code": "wrong_kind"})
    if isinstance(err, gear_create.SpellingTakenError):
        return HTTPException(status_code=409, detail={"code": "spelling_taken"})
    if isinstance(err, corredi.RigExistsError):
        return HTTPException(status_code=409, detail={"code": "rig_exists"})
    # a `KeyError` is a `LookupError` but a failure of ours: a 404 would tell the user their
    # piece is not there
    if isinstance(err, LookupError) and not isinstance(err, KeyError):
        return HTTPException(status_code=404, detail={"code": "not_found"})
    if isinstance(err, sqlite3.IntegrityError):
        return HTTPException(status_code=409, detail={"code": constraint_code(err)})
    return None


def _answer_unfiltered(conn: sqlite3.Connection, edit: UnfilteredEdit, now: str) -> list[int]:
    """A camera or a filter no longer there is an old page, said before writing. The filter's
    NAME is written, not its id: a merge deletes the row, and the answer must survive."""
    camera_id = gear.instrument_id(conn, "camera", edit.key)
    if camera_id is None:
        raise LookupError(f"camera {edit.key}")
    nome = None
    if edit.filter_id is not None:
        scelte = {f.id: f.name for f in page.filter_choices(conn)}
        if edit.filter_id not in scelte:
            raise LookupError(f"filtro {edit.filter_id}")
        nome = scelte[edit.filter_id]
    unfiltered_reader.declare(conn, edit.key, edit.answer, nome, now)
    return unfiltered_reader.requeue(conn, camera_id)


def _answer_mosaic(conn: sqlite3.Connection, edit: MosaicEdit, now: str) -> None:
    """No frame is requeued: the answer itself writes the mosaic on the frames. A name the catalog
    knows as a designation goes to its entry: whoever writes `IC 405` means IC 405."""
    value = decl.MOSAIC_NO
    if edit.answer == decl.MOSAIC_YES:
        slug, name = risposta.resolved(conn, None, (edit.name or "").strip())
        value = risposta.target_value(slug, name)
    mosaic.write_answer(conn, edit.key, value, now)


def _answer_where(conn: sqlite3.Connection, edit: CoordinatesEdit, now: str) -> list[int]:
    """Coordinates with no frame and a deleted site are checked before writing, or the declaration
    would point at nothing. The site's NAME is written, since ids are reused."""
    frames = places.frames_at(conn, edit.key, SITE_UNCLEAR)
    if not frames:
        raise LookupError(f"coordinate {edit.key}")
    sito = conn.execute("SELECT name FROM sites WHERE id = ?", (edit.site_id,)).fetchone()
    if sito is None:
        raise LookupError(f"sito {edit.site_id}")
    decl.declare_coordinates(conn, edit.key, sito["name"], now)
    # frames a previous answer had settled come back too: that is how one changes one's mind
    invalidate(conn, frames, "group")
    return frames


def constraint_code(err: sqlite3.IntegrityError) -> str:
    for needle, code in _CONSTRAINT_CODES.items():
        if needle in str(err):
            return code
    return "constraint_violated"
