"""The group is checked BEFORE writing: an answer to a group that no longer asks anything is an
old page, and would stay forever unseen. Hence LookupError, which the route turns into 404."""

import sqlite3
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from ..spine import declarations as decl
from ..spine import gear, signature, typeless, typeless_answer, unfiltered, unnamed
from ..spine import signature_page as cards
from .models_review import FilterCandidate, RigChoice
from .models_review_apply import GearEdit, TypelessFolderEdit, UnnamedEdit


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
    riga = cards.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"firma {edit.key}")
    _only_what_is_asked(riga, edit)
    corredi, filtri = choices
    data = signature.answer(conn, edit.key) or signature.Answer()
    if edit.rig_id is not None or edit.camera is not None:
        optics, camera, focal = rig_parts(edit, corredi)
        optics = data.optics if optics is None else optics  # a part not sent keeps the earlier one
        data = replace(data, camera=camera, optics=optics, focal_mm=focal)
    elif edit.optics is not None:
        data = replace(data, optics=edit.optics.strip())
    rimesse: list[int] = []
    if edit.filter is not None:
        if edit.filter_id is not None and edit.filter_id not in filtri:
            raise LookupError(f"filtro {edit.filter_id}")  # an old page, said before writing
        camera = (  # the night's camera too: the card asks the filter because of it
            decl.instrument_name(conn, "camera", riga["camera"])
            or data.camera
            or riga["settled_camera"]
        )
        rimesse = _sensor(conn, camera, edit.filter == unfiltered.COLOR, now)
        if edit.filter != unfiltered.COLOR:
            nome = filtri[edit.filter_id].name if edit.filter_id is not None else None
            data = replace(data, filter=edit.filter, filter_name=nome)
    signature.declare(conn, edit.key, data, now)
    return rimesse + signature.requeue(conn, edit.key)


def _only_what_is_asked(card: Mapping[str, Any], edit: GearEdit) -> None:
    fuori = []
    if (edit.rig_id is not None or edit.camera is not None) and not card["asks_camera"]:
        fuori.append("camera")
    if edit.optics is not None and not (card["asks_optics"] or card["asks_camera"]):
        fuori.append("optics")
    if edit.filter is not None and not card["asks_filter"]:
        fuori.append("filter")
    if fuori:
        raise NotAskedError(", ".join(fuori))


def _sensor(conn: sqlite3.Connection, camera: str | None, colour: bool, now: str) -> list[int]:
    """Colour is written on the camera's card; the other two write mono there unless the files
    say colour. The camera's frames move with it."""
    if camera is None:
        if colour:
            raise NotAskedError("color")  # no camera to write it on: answer the camera first
        return []
    unfiltered.declare_sensor(conn, camera, colour, now)
    camera_id = gear.instrument_id(conn, "camera", camera)
    return [] if camera_id is None else unfiltered.requeue(conn, camera_id)


def rig_parts(
    edit: GearEdit, choices: Mapping[int, RigChoice]
) -> tuple[str | None, str | None, float | None]:
    """Always NAMES: a merge deletes the detected row, and the declaration must survive. A rig
    `choices` does not offer (one without a camera, say) is a target that does not exist."""
    if edit.rig_id is None:
        return edit.optics, edit.camera, edit.focal_mm
    scelto = choices.get(edit.rig_id)
    if scelto is None:
        raise decl.UnknownTargetError(f"corredo {edit.rig_id}")
    return scelto.optics, scelto.camera, scelto.focal_mm


def answer_unnamed(conn: sqlite3.Connection, edit: UnnamedEdit, now: str) -> list[int]:
    riga = unnamed.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"gruppo {edit.key}")
    unnamed.declare(
        conn, edit.key, slug=edit.slug, name=edit.name, not_an_object=edit.not_an_object, now=now
    )
    return unnamed.requeue(conn, riga)


def answer_typeless(conn: sqlite3.Connection, edit: TypelessFolderEdit, now: str) -> list[int]:
    """Only sky pictures go back in the queue: a calibration file has no sky to look for."""
    riga = typeless.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"cartella {edit.key}")
    typeless.declare(conn, edit.key, edit.kind, now)
    return typeless_answer.apply_answer(conn, {**riga, "answer": edit.kind}, now)
