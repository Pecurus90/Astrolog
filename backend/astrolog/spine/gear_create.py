"""The birth of a piece or a filter, found in the files or written by the user: the same row, since
a piece is its name within its kind. Only the caller knows who made a piece: it passes `detected`.
"""

import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from ..db.inserted import inserted_id
from ..vocab.filters import Passband, normalize_filter
from ..vocab.header_value import normalize_header_value
from ..vocab.instruments import InstrumentKind
from . import declarations, gear


def instrument(
    conn: sqlite3.Connection, kind: InstrumentKind, name: str, now: str, *, detected: bool
) -> int:
    """Name only: `camera_specs` writes a camera's pixel and colour at the end of the pass, the
    rest is filled by whoever declares."""
    return inserted_id(
        conn.execute(
            "INSERT INTO instruments(kind, name, detected, created_at) VALUES(?, ?, ?, ?)",
            (kind, name, int(detected), now),
        )
    )


def filter_id_by_name(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute("SELECT id FROM filters WHERE name = ?", (name,)).fetchone()
    return None if row is None else row["id"]


def create_filter(
    conn: sqlite3.Connection, name: str, passband: str, now: str, is_none: bool = False
) -> int:
    """`is_none` for the "no filter" row, one in the archive."""
    return inserted_id(
        conn.execute(
            "INSERT INTO filters(name, passband, is_none, created_at) VALUES(?, ?, ?, ?)",
            (name, passband, int(is_none), now),
        )
    )


class SpellingTakenError(ValueError):
    """That name is already a spelling of another filter of yours: the scan takes it there."""


def filter_declared(
    conn: sqlite3.Connection,
    name: str,
    bands: Sequence[Mapping[str, Any]],
    now: str,
    card: Mapping[str, Any] | None = None,
) -> int:
    """A vocabulary rename (`L` -> `Lum`) is learnt after the colour, so colour frames stay OSC; a
    taken name is refused. `card` is brand, model and sheet (`gear.FILTER_FIELDS`)."""
    mono = normalize_filter(name, bayer=False)
    for spelling in {name, mono} - {None}:
        taken = declarations.alias_target(conn, "filter", normalize_header_value(spelling))
        if taken is not None and taken != name:
            raise SpellingTakenError(f"{spelling} e' una grafia di {taken}")
    if mono and mono != name and filter_id_by_name(conn, mono) is not None:
        raise SpellingTakenError(f"{name} e' il tuo {mono}")
    filter_id = create_filter(conn, name, Passband.UNKNOWN, now)
    written = {k: v for k, v in (card or {}).items() if v is not None and v != ""}
    gear.declare_filter(conn, filter_id, written, bands=bands, now=now)
    if mono and mono != name:
        declarations.learn(conn, "filter", mono, name, now)
    return filter_id
