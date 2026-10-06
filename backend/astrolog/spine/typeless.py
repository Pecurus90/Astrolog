"""Frames whose header does not say what file they are, asked per folder only where the sky cannot
tell (solved is a photo, starless is a calibration). Until answered they wait before the object."""

import sqlite3
from typing import Any

from ..db.row import Row
from ..fits.frame_type import FrameType
from . import declarations as decl
from . import frame_folder as folder

# The words live in `declarations`, because `stages` reads them too to know who is ready.
LIGHT, CALIBRATION = decl.TYPE_LIGHT, decl.TYPE_CALIBRATION
ANSWERS = (LIGHT, CALIBRATION)


_WRITTEN = f"""
SELECT t.key, t.root, t.sub, t.frames, dc.value AS answer FROM typeless_folders t
LEFT JOIN declarations dc ON dc.entity_type = '{decl.FOLDER}' AND dc.field = '{decl.FOLDER_TYPE}'
  AND dc.entity_key = t.key
"""  # noqa: S608 - `declarations` constants, not a user value


def by_folder(conn: sqlite3.Connection, only: str | None = None) -> list[dict[str, Any]]:
    """Largest first, as `typeless_folders.write` left them. An answered folder stays, or changing
    one's mind would be impossible; `only` keeps one folder."""
    where, args = (" WHERE t.key = ?", (only,)) if only is not None else ("", ())
    rows = conn.execute(_WRITTEN + where + " ORDER BY t.position", args)
    return [
        {"key": r["key"], "root": r["root"], "sub": r["sub"], "frames": r["frames"],
         "answer": r["answer"] if r["answer"] in ANSWERS else None}
        for r in rows
    ]  # fmt: skip


def row_of(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return next(iter(by_folder(conn, only=key)), None)


def declare(conn: sqlite3.Connection, key: str, kind: str, now: str | None = None) -> None:
    """The word, not a row id, keyed on the folder: the answer must survive a reset of what was
    detected."""
    if kind not in ANSWERS:  # a word outside the vocabulary is not half an answer: it is a bug
        raise ValueError(f"risposta che non esiste: {kind!r}")
    decl.write_declaration(conn, decl.FOLDER, key, decl.FOLDER_TYPE, kind, now)


def answer(conn: sqlite3.Connection, key: str | None) -> str | None:
    """A malformed row counts as no answer: the frames wait instead of becoming hours on a guess."""
    value = decl.declared(conn, decl.FOLDER, key, decl.FOLDER_TYPE) if key else None
    return value if value in ANSWERS else None


def answer_at(conn: sqlite3.Connection, root_path: str, rel_path: str) -> str | None:
    """The scan asks before writing the frame, so the key comes from the path, not the database."""
    return answer(conn, folder.key_of_path(root_path, rel_path))


def frames_of(conn: sqlite3.Connection, row: Row) -> list[int]:
    """Copies included: a copy has its own sky, even though on screen it is not counted."""
    return [r["id"] for r in folder.frames_in(conn, row) if r["image_type"] == FrameType.UNKNOWN]
