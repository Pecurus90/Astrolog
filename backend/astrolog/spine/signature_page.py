"""The gear cards of "To confirm", one per signature, each saying which of camera, optics and
filter its frames leave out. A part the night or the camera's colour settles is not asked."""

import sqlite3
from collections.abc import Callable
from dataclasses import asdict, replace
from functools import cache
from typing import Any

from ..clock import NIGHT_SQL
from ..db.row import Row
from ..units import focal_buckets, known_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from . import declarations as decl
from . import frame_folder as folder
from . import objects as obj
from .night_rig import NightRig, night_rigs
from .signature import Answer, Parts, answer_for, answers, as_page, key_of, parts_of
from .stages import WAITING_SQL
from .unfiltered import is_colour

# Grouped in SQL, never a row per frame; the rig's camera says what normalize settled.
_COLUMNS = """
f.instrument_raw, f.telescope_raw, f.focal_mm_raw, f.naxis1, f.naxis2, f.pixel_size_um,
f.software_raw, f.asks_camera, f.names_optics
"""
_BY_FRAME = f"""
SELECT {_COLUMNS}, {NIGHT_SQL} AS night, c.name AS rig_camera,
       (f.asks_filter = 1 AND f.bayer_pattern IS NULL AND NOT ({WAITING_SQL})) AS silent_filter,
       {obj.SUBJECT} AS subject, SUM(f.copy_of IS NULL) AS n
FROM frames f {folder.JOIN}
LEFT JOIN rigs g ON g.id = f.rig_id LEFT JOIN instruments c ON c.id = g.camera_id
{obj.SUBJECT_JOIN}
WHERE f.asks_camera = 1 OR f.names_optics = 0 OR (f.asks_filter = 1 AND f.bayer_pattern IS NULL)
GROUP BY {_COLUMNS}, night, rig_camera, silent_filter, subject
"""  # noqa: S608 - constant fragments of the spine, not user values

_NATIVE_FOCAL = "SELECT focal_mm FROM instruments WHERE kind = 'optics' AND name = ?"


def _bucketed(rows: list[sqlite3.Row]) -> list[tuple[sqlite3.Row, Parts]]:
    """Focals within the rigs' tolerance are one signature, whatever the files' order."""
    parts = [(r, parts_of(r)) for r in rows]
    by_sensor: dict[Parts, list[float | None]] = {}
    for _, p in parts:
        by_sensor.setdefault(replace(p, focal_mm=None), []).append(p.focal_mm)
    buckets = {k: focal_buckets(v) for k, v in by_sensor.items()}
    out = []
    for r, p in parts:
        focal = buckets[replace(p, focal_mm=None)].get(p.focal_mm, p.focal_mm)  # type: ignore[arg-type]
        out.append((r, replace(p, focal_mm=focal)))
    return out


def _camera_of(
    conn: sqlite3.Connection, r: Row, night: NightRig | None, given: Answer | None
) -> str | None:
    """What normalize settled, else what the header, the answer or the night would give."""
    return (
        r["rig_camera"]
        or decl.instrument_name(conn, "camera", r["instrument_raw"])
        or (given.camera if given else None)
        or (night.camera if night is not None else None)
    )


def _asks(
    conn: sqlite3.Connection,
    r: Row,
    night: NightRig | None,
    given: Answer | None,
    colour: Callable[[str | None], bool],
) -> tuple[bool, bool, bool]:
    """(camera, optics, filter): what this row needs, answered or not. The night settles a frame
    with no camera, and its optics too when it names one."""
    camera = bool(r["asks_camera"]) and night is None
    optics = not r["names_optics"] and not (night is not None and night.optics)
    filter_asked = bool(r["silent_filter"]) and not colour(_camera_of(conn, r, night, given))
    return camera, optics, filter_asked


def _native_focal(conn: sqlite3.Connection, optics_name: str | None) -> float | None:
    """Proposed when the frames are silent: without a focal the answer's rig would stay a twin of
    the detected one forever (`rigs.rig_for`)."""
    if not optics_name:
        return None
    row = conn.execute(_NATIVE_FOCAL, (optics_name,)).fetchone()
    return None if row is None else row["focal_mm"]


def _only[T](values: set[T | None]) -> T | None:
    """With two values in one card nothing is chosen for the user, and a blank means "unknown"."""
    said = {v for v in values if v is not None}
    return said.pop() if len(said) == 1 else None


def _card(key: str, r: Row) -> dict[str, Any]:
    return {
        "key": key,
        "camera": (r["instrument_raw"] or "").strip() or None,
        "telescope": (r["telescope_raw"] or "").strip() or None,
        "width_px": r["naxis1"],
        "height_px": r["naxis2"],
        "pixel_um": r["pixel_size_um"],
        "frames": 0,
        "asks_camera": False,
        "asks_optics": False,
        "asks_filter": False,
        "optics": set(),
        "focal": set(),
        "spellings": set(),
        "cameras": set(),
    }


def by_signature(conn: sqlite3.Connection, only: str | None = None) -> list[dict[str, Any]]:
    """Largest first. A row that needs nothing is shown only under an answer, which wins over the
    night. `only` keeps one card: the whole page for each answer of an Apply costs the square."""
    frame_rows = conn.execute(_BY_FRAME).fetchall()
    stored = answers(conn)
    asking_nights = {r["night"] for r in frame_rows if r["night"] and r["asks_camera"]}
    nights = night_rigs(conn, asking_nights) if asking_nights else {}
    colour = cache(lambda name: is_colour(conn, name))
    cards: dict[str, dict[str, Any]] = {}
    answer_by_card: dict[str, Answer | None] = {}
    for r, parts in _bucketed(frame_rows):
        found = answer_for(stored, parts)
        card_key, data = found if found else (key_of(parts), None)
        if only is not None and card_key != only:
            continue
        its_night = nights.get(r["night"]) if r["asks_camera"] else None
        asked = _asks(conn, r, its_night, data, colour)
        if not any(asked) and data is None:
            continue
        this_card = cards.setdefault(card_key, _card(card_key, r))
        _add(conn, this_card, r, asked)
        this_card["cameras"].add(_camera_of(conn, r, its_night, data))
        answer_by_card[card_key] = data
    # with the ASIAIR `TELESCOP` is the mount, on every card with that spelling
    mount_spellings = {
        normalize_header_value(r["telescope_raw"])
        for r in frame_rows
        if telescope_is_mount(normalize_software(r["software_raw"]))
    }
    with_subjects = obj.subjects(conn, cards.values())
    out = [_shown(conn, s, answer_by_card[s["key"]], mount_spellings) for s in with_subjects]
    return sorted(out, key=lambda s: (-s["frames"], s["key"]))


def _add(
    conn: sqlite3.Connection,
    card: dict[str, Any],
    r: Row,
    asks: tuple[bool, bool, bool],
) -> None:
    card["frames"] += r["n"] or 0
    if r["n"]:  # an object with only copies in the card is not another frame
        obj.count_subject(card, r["subject"], r["n"])
    for field, asked in zip(("asks_camera", "asks_optics", "asks_filter"), asks, strict=True):
        card[field] = card[field] or asked
    card["spellings"].add(normalize_header_value(r["telescope_raw"]))
    card["optics"].add(decl.instrument_name(conn, "optics", r["telescope_raw"]))
    card["focal"].add(known_focal(r["focal_mm_raw"]))


def _shown(
    conn: sqlite3.Connection, card: dict[str, Any], data: Answer | None, mounts: set[str]
) -> dict[str, Any]:
    """Complete when every part asked has its answer; the native focal only where frames are
    silent. A spelling some file calls the mount is never offered as the optics."""
    optics, focal = _only(card.pop("optics")), _only(card.pop("focal"))
    optics = None if card.pop("spellings") & mounts else optics
    camera = _only(card.pop("cameras"))  # where the sensor answer goes; not on the page
    missing = [
        card["asks_camera"] and not (data and data.camera),
        card["asks_optics"] and not (data and data.optics),
        card["asks_filter"] and not (data and data.filter),
    ]
    return {
        **card,
        "settled_camera": camera,
        "optics": optics,
        "focal_mm": focal,
        "focal_suggested": None if focal is not None else _native_focal(conn, optics),
        "answer": asdict(as_page(conn, data)) if data else None,
        "complete": not any(missing),
    }


def row_of(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return next(iter(by_signature(conn, only=key)), None)
