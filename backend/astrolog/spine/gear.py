"""The gear cards: what the user declares to own. Renaming or merging a piece learns the rule on the
old spelling, or the next scan would recreate it; what changes a frame's meaning requeues it."""

import sqlite3
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from ..db import idlist
from ..db.row import Row
from ..vocab.filters import Passband, model_by_id, passband_from_bands
from . import counts, signature
from . import rigs as corredi
from .declarations import (
    ALIAS_KINDS,
    CAMERA_SPECS,
    declare_instrument_spec,
    follow_not_same_as,
    instrument_key,
    rename,
)
from .stages import StageName, invalidate

# Closed like the preference keys: a field that is not here does not get in.
INSTRUMENT_FIELDS = (
    "name", "brand", "model", "camera_type", "pixel_size_um", "aperture_mm", "focal_mm",
    "reducer_factor", "weight_kg", "payload_kg", "slots", "backfocus_mm", "notes",
)  # fmt: skip
FILTER_FIELDS = ("name", "brand", "model", "catalog_id")


def _set_fields(
    conn: sqlite3.Connection,
    table: str,
    row_id: int,
    fields: Mapping[str, Any],
    allowed: Collection[str],
) -> bool:
    chosen = {k: v for k, v in fields.items() if k in allowed}
    if not chosen:
        return False
    columns = ", ".join(f'"{k}" = ?' for k in chosen)
    conn.execute(
        f"UPDATE {table} SET {columns} WHERE id = ?",  # noqa: S608 - columns from a closed list
        [*chosen.values(), row_id],
    )
    return True


def instrument_id(conn: sqlite3.Connection, kind: str, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM instruments WHERE kind = ? AND name = ?", (kind, name)
    ).fetchone()
    return None if row is None else row["id"]


def instrument_ids(conn: sqlite3.Connection, names: Mapping[str, str]) -> dict[str, int]:
    """`instrument_id` of one name per kind, in one query; a kind with no piece is left out."""
    if not names:
        return {}
    pairs = ", ".join("(?, ?)" for _ in names)  # segnaposto-ok: one pair per kind, not per frame
    # S608: only placeholders
    sql = f"SELECT kind, id FROM instruments WHERE (kind, name) IN (VALUES {pairs})"  # noqa: S608
    args = [v for pair in names.items() for v in pair]
    return {r["kind"]: r["id"] for r in conn.execute(sql, args)}


def declare_instrument(
    conn: sqlite3.Connection,
    instrument_id: int,
    fields: Mapping[str, Any],
    now: str | None = None,
) -> bool:
    """A camera's pixel and colour go among the declarations: the column belongs to the files, and
    the spine rewrites it."""
    row = conn.execute(
        "SELECT kind, name FROM instruments WHERE id = ?", (instrument_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"strumento {instrument_id}")
    new_name: str = fields.get("name") or ""
    renamed = bool(new_name) and new_name != row["name"]
    if renamed and row["kind"] in ALIAS_KINDS:
        rename(conn, row["kind"], row["name"], new_name, now)
    specs = {k: v for k, v in fields.items() if k in CAMERA_SPECS and row["kind"] == "camera"}
    columns = [f for f in INSTRUMENT_FIELDS if f not in specs]
    changed = _set_fields(conn, "instruments", instrument_id, fields, columns) or bool(specs)
    for field, value in specs.items():
        declare_instrument_spec(conn, row["kind"], row["name"], field, value, now)
    if renamed:  # the rig's key carries the piece's name too
        _move_instrument_declarations(conn, row["kind"], row["name"], new_name, merging=False)
        corredi.follow_piece(conn, row["kind"], row["name"], new_name, now)
    if changed:
        # from now on the user said it, not the spine
        conn.execute("UPDATE instruments SET detected = 0 WHERE id = ?", (instrument_id,))
    return changed


def _move_instrument_declarations(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, *, merging: bool
) -> None:
    """On a rename what moves wins: the new name holds only leftovers. On a merge the kept piece's
    card wins, and the absorbed one fills only what it left empty."""
    old, new = instrument_key(kind, old_name), instrument_key(kind, new_name)
    if not merging:
        conn.execute(
            "DELETE FROM declarations WHERE entity_type = 'instrument' AND entity_key = ?", (new,)
        )
    conn.execute(
        "UPDATE OR IGNORE declarations SET entity_key = ?"
        " WHERE entity_type = 'instrument' AND entity_key = ?",
        (new, old),
    )
    conn.execute(
        "DELETE FROM declarations WHERE entity_type = 'instrument' AND entity_key = ?", (old,)
    )
    if kind == "camera":
        follow_not_same_as(conn, old_name, new_name)


def camera_specs(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    """`{id: {field: value}}` of every camera: field by field, the user's word beats the files."""
    written: dict[str, dict[str, Any]] = {}
    for r in conn.execute(
        "SELECT entity_key, field, value FROM declarations"
        " WHERE entity_type = 'instrument' AND field IN (?, ?)",
        CAMERA_SPECS,
    ):
        written.setdefault(r["entity_key"], {})[r["field"]] = r["value"]
    return {
        r["id"]: {
            f: written.get(instrument_key(r["kind"], r["name"]), {}).get(f, r[f])
            for f in CAMERA_SPECS
        }
        for r in conn.execute(
            "SELECT id, kind, name, camera_type, pixel_size_um FROM instruments"
            " WHERE kind = 'camera'"
        )
    }


def declare_filter(  # noqa: PLR0913
    conn: sqlite3.Connection,
    filter_id: int,
    fields: Mapping[str, Any],
    bands: Sequence[Mapping[str, Any]] | None = None,
    is_none: bool | None = None,
    now: str | None = None,
) -> list[int]:
    """The canonical band derives from the bands it passes. Returns the frames to requeue: the
    band changes the answers downstream."""
    row = conn.execute(
        "SELECT name, passband, is_none FROM filters WHERE id = ?", (filter_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"filtro {filter_id}")
    if fields.get("catalog_id") and model_by_id(fields["catalog_id"]) is None:
        raise LookupError(f"modello {fields['catalog_id']}")  # before writing
    new_name = fields.get("name")
    if new_name and new_name != row["name"] and not row["is_none"]:
        # The "no filter" row's name comes from the vocabulary: a rule on "none" would decide for
        # every camera in place of its answer.
        rename(conn, "filter", row["name"], new_name, now)
        signature.follow_filter(conn, row["name"], new_name)  # the answer keeps the NAME
    _set_fields(conn, "filters", filter_id, fields, FILTER_FIELDS)
    if is_none is not None:
        # "no filter" IS a band of the closed domain: the switch alone would leave the old band,
        # two homes for one fact
        conn.execute(
            "UPDATE filters SET is_none = ?, passband = CASE WHEN ? THEN ? ELSE passband END"
            " WHERE id = ?",
            (int(is_none), int(is_none), Passband.NO_FILTER, filter_id),
        )
    if bands is not None:
        conn.execute("DELETE FROM filter_bands WHERE filter_id = ?", (filter_id,))
        for b in bands:
            conn.execute(
                "INSERT INTO filter_bands(filter_id, band, width_nm) VALUES(?, ?, ?)",
                (filter_id, b["band"], b.get("width_nm")),
            )
        conn.execute(
            "UPDATE filters SET passband = ? WHERE id = ?",
            (passband_from_bands([b["band"] for b in bands]), filter_id),
        )
    catalog_id = fields.get("catalog_id")
    modello = model_by_id(catalog_id) if bands is None and catalog_id is not None else None
    if modello:
        # the model carries its band: choosing it is a whole answer, not a brand
        conn.execute("UPDATE filters SET passband = ? WHERE id = ?", (modello.passband, filter_id))
    after = conn.execute("SELECT passband FROM filters WHERE id = ?", (filter_id,)).fetchone()
    if after["passband"] == row["passband"]:
        # brand, model or a note do not change what a frame means: nothing is redone
        return []
    frames = [r[0] for r in conn.execute("SELECT id FROM frames WHERE filter_id = ?", (filter_id,))]
    invalidate(conn, frames, StageName.NORMALIZE, now=now)
    return frames


def _rigs_using(conn: sqlite3.Connection, instrument_id: int) -> list[int]:
    """The rigs whose key carries that piece's name."""
    return [
        r[0]
        for r in conn.execute(
            "SELECT id FROM rigs WHERE optics_id = ? OR camera_id = ?",
            (instrument_id, instrument_id),
        )
    ]


class MergeRefusedError(ValueError):
    """A merge the spine refuses, with its reason: the route maps it to 422. Any other
    `ValueError` is a fault and stays one."""


def mergeable(src: Row, dst: Row) -> bool:
    """Only kinds with spellings to merge: without the rule the next scan would recreate the old
    one. The page offers these merges and `merge_instrument` refuses the others."""
    return src["id"] != dst["id"] and src["kind"] == dst["kind"] and src["kind"] in ALIAS_KINDS


def merge_instrument(
    conn: sqlite3.Connection, from_id: int, into_id: int, now: str | None = None
) -> list[int]:
    """The rule is learnt, the absorbed row and the rigs using it go, and the frames are requeued:
    `normalize` hooks them to the right piece."""
    src = conn.execute("SELECT id, kind, name FROM instruments WHERE id = ?", (from_id,)).fetchone()
    dst = conn.execute("SELECT id, kind, name FROM instruments WHERE id = ?", (into_id,)).fetchone()
    if src is None or dst is None:
        raise LookupError(f"pezzo {from_id if src is None else into_id}")
    if not mergeable(src, dst):
        raise MergeRefusedError(f"{from_id} non si unisce in {into_id}: non e' `mergeable`")
    rename(conn, src["kind"], src["name"], dst["name"], now)
    corredi.follow_piece(conn, src["kind"], src["name"], dst["name"], now)
    _move_instrument_declarations(conn, src["kind"], src["name"], dst["name"], merging=True)
    rigs = _rigs_using(conn, from_id)
    frames = set(_detach_rigs(conn, rigs)) | _detach_from_frames(conn, from_id)
    conn.execute("DELETE FROM instruments WHERE id = ?", (from_id,))
    corredi.restore_declared(conn, now)
    invalidate(conn, frames, StageName.NORMALIZE, now=now)
    return sorted(frames)


def _detach_from_frames(conn: sqlite3.Connection, instrument_id: int) -> set[int]:
    """Without it the foreign key keeps the row from being deleted, and the whole Apply fails,
    taking the good answers with it."""
    staccate: set[int] = set()
    for kind in counts.CARRIED:
        pose = [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE {kind}_id = ?",  # noqa: S608 - our own kinds
                (instrument_id,),
            )
        ]
        if pose:
            conn.execute(
                f"UPDATE frames SET {kind}_id = NULL WHERE {kind}_id = ?",  # noqa: S608
                (instrument_id,),
            )
            staccate.update(pose)
    return staccate


def band_unknown(row: Row) -> bool:
    """The "which filter is it?" question of the review page."""
    return row["passband"] == Passband.UNKNOWN


def filter_target(row: Row) -> bool:
    """Whether a filter can receive a merge or be chosen as "one of yours": one home for the
    dropdowns and for whoever merges."""
    return not row["is_none"] and not band_unknown(row)


def filter_mergeable(src: Row, dst: Row) -> bool:
    """Never from "no filter": its spelling would become a rule on "none", answering for every
    camera. The page offers these merges and `merge_filter` refuses the others."""
    return src["id"] != dst["id"] and not src["is_none"] and filter_target(dst)


def merge_filter(
    conn: sqlite3.Connection, from_id: int, into_id: int, now: str | None = None
) -> list[int]:
    riga = "SELECT id, name, is_none, passband FROM filters WHERE id = ?"
    src = conn.execute(riga, (from_id,)).fetchone()
    dst = conn.execute(riga, (into_id,)).fetchone()
    if src is None or dst is None:
        raise LookupError(f"filtro {from_id if src is None else into_id}")
    if not filter_mergeable(src, dst):
        raise MergeRefusedError("si unisce un filtro vero in un altro, con la banda nota")
    rename(conn, "filter", src["name"], dst["name"], now)
    signature.follow_filter(conn, src["name"], dst["name"])  # "the same filter" there too
    frames = [r[0] for r in conn.execute("SELECT id FROM frames WHERE filter_id = ?", (from_id,))]
    conn.execute("UPDATE frames SET filter_id = NULL WHERE filter_id = ?", (from_id,))
    conn.execute("DELETE FROM filters WHERE id = ?", (from_id,))
    invalidate(conn, frames, StageName.NORMALIZE, now=now)
    return frames


def _detach_rigs(conn: sqlite3.Connection, rig_ids: Collection[int]) -> list[int]:
    """Rigs are detected: `normalize` remakes them, identical or better, on the next pass."""
    if not rig_ids:
        return []
    with idlist.holding(conn, rig_ids) as listed:
        frames = [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE rig_id IN {listed}"  # noqa: S608 - our constant
            )
        ]
        conn.execute(f"UPDATE frames SET rig_id = NULL WHERE rig_id IN {listed}")  # noqa: S608
        conn.execute(f"DELETE FROM rigs WHERE id IN {listed}")  # noqa: S608 - our constant
    return frames
