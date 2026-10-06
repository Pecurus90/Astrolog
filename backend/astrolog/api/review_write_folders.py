"""Each answer checks its group BEFORE writing: one written on a group no longer asked would stay
forever unseen. The `LookupError` is the 404 of `POST /review/apply`."""

import sqlite3
from collections.abc import Collection, Mapping
from dataclasses import replace
from typing import Any

from ..spine import declarations as decl
from ..spine import signature, typeless, typeless_answer, unfiltered, unnamed
from ..spine import signature_page as cards
from .models_review import FilterCandidate, RigChoice
from .models_review_apply import GearEdit, ObjectEdit, TypelessFolderEdit


class NotAskedError(ValueError):
    """A part the card does not ask: written, it would say "done" and move nothing."""


def answer_gear(
    conn: sqlite3.Connection,
    edit: GearEdit,
    now: str,
    choices: tuple[Mapping[int, RigChoice], Mapping[int, FilterCandidate]],
) -> list[int]:
    """The parts sent replace the earlier ones, the others stay. The pieces come into being from
    the names on the next round (`normalize_rig.instrument_named`)."""
    row = cards.row_of(conn, edit.key)
    if row is None:
        raise LookupError(f"firma {edit.key}")
    _only_what_is_asked(row, edit)
    rig_choices, filter_choices = choices
    data = signature.answer(conn, edit.key) or signature.Answer()
    if edit.rig_id is not None or edit.camera is not None:
        optics, camera, focal = rig_parts(edit, rig_choices)
        optics = data.optics if optics is None else optics  # a part not sent keeps the earlier one
        data = replace(data, camera=camera, optics=optics, focal_mm=focal)
    elif edit.optics is not None:
        data = replace(data, optics=edit.optics.strip())
    requeued: list[int] = []
    if edit.filter is not None:
        if edit.filter_id is not None and edit.filter_id not in filter_choices:
            raise LookupError(f"filtro {edit.filter_id}")  # an old page, said before writing
        camera = (  # the night's camera too: the card asks the filter because of it
            decl.instrument_name(conn, "camera", row["camera"])
            or data.camera
            or row["settled_camera"]
        )
        requeued = _sensor(conn, camera, edit.filter == decl.CameraType.COLOR, now)
        if edit.filter != decl.CameraType.COLOR:
            filter_name = (
                filter_choices[edit.filter_id].name if edit.filter_id is not None else None
            )
            data = replace(
                data, filter=signature.FilterAnswer(edit.filter), filter_name=filter_name
            )
    signature.declare(conn, edit.key, data, now)
    return requeued + signature.requeue(conn, edit.key)


def _only_what_is_asked(card: Mapping[str, Any], edit: GearEdit) -> None:
    stray = []
    if (edit.rig_id is not None or edit.camera is not None) and not card["asks_camera"]:
        stray.append("camera")
    if edit.optics is not None and not (card["asks_optics"] or card["asks_camera"]):
        stray.append("optics")
    if edit.filter is not None and not card["asks_filter"]:
        stray.append("filter")
    if stray:
        raise NotAskedError(", ".join(stray))


def _sensor(conn: sqlite3.Connection, camera: str | None, colour: bool, now: str) -> list[int]:
    """Colour is written on the camera's card; the other two write mono there unless the files
    say colour. The camera's frames move with it."""
    if camera is None:
        if colour:
            raise NotAskedError("color")  # no camera to write it on: answer the camera first
        return []
    unfiltered.declare_sensor(conn, camera, colour, now)
    camera_id = decl.instrument_id(conn, "camera", camera)
    return [] if camera_id is None else unfiltered.requeue(conn, camera_id)


def rig_parts(
    edit: GearEdit, choices: Mapping[int, RigChoice]
) -> tuple[str | None, str | None, float | None]:
    """Always NAMES: a merge deletes the detected row, and the declaration must survive. A rig
    `choices` does not offer (one without a camera, say) is a target that does not exist."""
    if edit.rig_id is None:
        return edit.optics, edit.camera, edit.focal_mm
    chosen = choices.get(edit.rig_id)
    if chosen is None:
        raise decl.UnknownTargetError(f"corredo {edit.rig_id}")
    return chosen.optics, chosen.camera, chosen.focal_mm


def answer_unnamed(
    conn: sqlite3.Connection, key: str, edit: ObjectEdit, now: str, groups: Collection[str]
) -> list[int]:
    """`groups` are the unnamed groups that ask, read once for the whole Apply."""
    if key not in groups:
        raise LookupError(f"gruppo {key}")
    unnamed.declare(
        conn, key, slug=edit.slug, name=edit.name, not_an_object=edit.not_an_object, now=now
    )
    return unnamed.requeue(conn, key)


def answer_typeless(conn: sqlite3.Connection, edit: TypelessFolderEdit, now: str) -> list[int]:
    """Only sky pictures go back in the queue: a calibration file has no sky to look for."""
    row = typeless.row_of(conn, edit.key)
    if row is None:
        raise LookupError(f"cartella {edit.key}")
    typeless.declare(conn, edit.key, edit.kind, now)
    return typeless_answer.apply_answer(conn, {**row, "answer": edit.kind}, now, rewrite=False)
