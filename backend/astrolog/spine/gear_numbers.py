"""Writes the numbers of every rig and piece from the cards (`rig_numbers`), whole, after each write
of cards or parts: a read never computes them."""

import json
import sqlite3
from collections.abc import Mapping
from typing import Any

from ..db.replace_table import replace_rows
from ..vocab.instruments import InstrumentKind
from . import gear, rigs
from . import rig_numbers as rn

_GUIDES = tuple(rigs.GUIDES)
# The parts a number reads, besides optics, camera and the guide.
_ONE_OF_A_KIND = {
    "reducer": InstrumentKind.REDUCER,
    "guide_camera": InstrumentKind.GUIDE_CAMERA,
    "wheel": InstrumentKind.FILTER_WHEEL,
    "focuser": InstrumentKind.FOCUSER,
    "mount": InstrumentKind.MOUNT,
}

_PARTS = """
SELECT rig_id, kind, piece_id, frames, chosen FROM rig_parts
WHERE piece_id IS NOT NULL AND kind NOT IN ('software', 'filter', 'spacer')
ORDER BY rig_id, position
"""


def _cards(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    """Every piece's card, a camera's file-told fields under the user's word."""
    declared = gear.camera_specs(conn)
    return {
        r["id"]: {**dict(r), **declared.get(r["id"], {})}
        for r in conn.execute("SELECT * FROM instruments")
    }


def _used(conn: sqlite3.Connection) -> dict[int, dict[str, int]]:
    """Per rig and kind, the part a number reads: the one you chose, else the most used. The guide
    is one, scope or OAG: the chosen one, else the most used of the two."""
    best: dict[int, dict[str, tuple[tuple[int, int], int]]] = {}
    # rows come in the card's order, most used first: a later row wins only by being chosen
    for r in conn.execute(_PARTS):
        kind = "guide" if r["kind"] in _GUIDES else r["kind"]
        rank = (r["chosen"], r["frames"])
        mine = best.setdefault(r["rig_id"], {})
        if kind not in mine or rank > mine[kind][0]:
            mine[kind] = (rank, r["piece_id"])
    return {rig: {k: piece for k, (_, piece) in kinds.items()} for rig, kinds in best.items()}


def _rig_card(
    rig: sqlite3.Row,
    cards: Mapping[int, dict[str, Any]],
    used: Mapping[str, int],
    spacers: list[int],
) -> rn.RigCard:
    card = lambda piece_id: None if piece_id is None else cards.get(piece_id)  # noqa: E731
    return rn.RigCard(
        focal_mm=rig["focal_mm"],
        optics=card(rig["optics_id"]),
        camera=card(rig["camera_id"]),
        guide=card(used.get("guide")),
        spacers=tuple(c for c in map(card, spacers) if c is not None),
        **{field: card(used.get(kind)) for field, kind in _ONE_OF_A_KIND.items()},
    )


def write(conn: sqlite3.Connection) -> None:
    cards = _cards(conn)
    used = _used(conn)
    spacers = rigs.spacers(conn)
    rows: list[tuple[str, int, str]] = [
        ("instrument", piece_id, json.dumps(rn.piece_numbers(card)))
        for piece_id, card in cards.items()
    ]
    for rig in conn.execute("SELECT id, focal_mm, optics_id, camera_id FROM rigs"):
        rig_card = _rig_card(rig, cards, used.get(rig["id"], {}), spacers.get(rig["id"], []))
        rows.append(("rig", rig["id"], json.dumps(rn.numbers(rig_card))))
    replace_rows(conn, "gear_numbers", ("subject", "subject_id", "numbers_json"), rows)
