"""The group is checked BEFORE writing: an answer to a group that no longer asks anything is an
old page, and would stay forever unseen. Hence LookupError, which the route turns into 404."""

import sqlite3
from collections.abc import Mapping

from ..spine import declarations as decl
from ..spine import rig_optics, rigless, typeless, typeless_answer, unnamed
from .models_review import RigChoice
from .models_review_apply import (
    OpticslessEdit,
    RiglessGroupEdit,
    TypelessFolderEdit,
    UnnamedEdit,
)


def answer_rigless(
    conn: sqlite3.Connection, edit: RiglessGroupEdit, now: str, scelte: Mapping[int, RigChoice]
) -> list[int]:
    """The pieces come into being from the names on the next round
    (`normalize_rig.instrument_named`)."""
    riga = rigless.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"gruppo {edit.key}")
    optics, camera, focal = rig_parts(edit, scelte)
    rigless.declare(conn, edit.key, optics, camera, focal, now)
    return rigless.requeue(conn, riga)


def answer_opticsless(conn: sqlite3.Connection, edit: OpticslessEdit, now: str) -> list[int]:
    riga = rig_optics.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"camera e focale {edit.key}")
    rig_optics.declare(conn, edit.key, edit.optics.strip(), now)
    return rig_optics.requeue(conn, riga)


def answer_unnamed(conn: sqlite3.Connection, edit: UnnamedEdit, now: str) -> list[int]:
    riga = unnamed.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"gruppo {edit.key}")
    unnamed.declare(
        conn, edit.key, slug=edit.slug, name=edit.name, not_an_object=edit.not_an_object, now=now
    )
    return unnamed.requeue(conn, riga)


def rig_parts(
    edit: RiglessGroupEdit, scelte: Mapping[int, RigChoice]
) -> tuple[str | None, str | None, float | None]:
    """Always NAMES: a merge deletes the detected row, and the declaration must survive. A rig
    `scelte` does not offer (one without a camera, say) is a target that does not exist."""
    if edit.rig_id is None:
        return edit.optics, edit.camera, edit.focal_mm
    scelto = scelte.get(edit.rig_id)
    if scelto is None:
        raise decl.UnknownTargetError(f"corredo {edit.rig_id}")
    return scelto.optics, scelto.camera, scelto.focal_mm


def answer_typeless(conn: sqlite3.Connection, edit: TypelessFolderEdit, now: str) -> list[int]:
    """Only sky pictures go back in the queue: a calibration file has no sky to look for."""
    riga = typeless.row_of(conn, edit.key)
    if riga is None:
        raise LookupError(f"cartella {edit.key}")
    typeless.declare(conn, edit.key, edit.kind, now)
    return typeless_answer.apply_answer(conn, {**riga, "answer": edit.kind}, now)
