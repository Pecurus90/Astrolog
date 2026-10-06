"""The gear cards of "To confirm", one per signature, each saying which of camera, optics and
filter its frames leave out. A part the night or the camera's colour settles is not asked."""

import sqlite3
from collections.abc import Callable
from dataclasses import replace
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
from .night_rig import night_rigs
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
    parti = [(r, parts_of(r)) for r in rows]
    per_sensore: dict[Parts, list[float | None]] = {}
    for _, p in parti:
        per_sensore.setdefault(replace(p, focal_mm=None), []).append(p.focal_mm)
    secchi = {k: focal_buckets(v) for k, v in per_sensore.items()}
    out = []
    for r, p in parti:
        focale = secchi[replace(p, focal_mm=None)].get(p.focal_mm, p.focal_mm)  # type: ignore[arg-type]
        out.append((r, replace(p, focal_mm=focale)))
    return out


def _camera_of(
    conn: sqlite3.Connection, r: Row, night: dict[str, Any] | None, given: Answer | None
) -> str | None:
    """What normalize settled, else what the header, the answer or the night would give."""
    return (
        r["rig_camera"]
        or decl.instrument_name(conn, "camera", r["instrument_raw"])
        or (given.camera if given else None)
        or (night or {}).get("camera")
    )


def _asks(
    conn: sqlite3.Connection,
    r: Row,
    night: dict[str, Any] | None,
    given: Answer | None,
    colour: Callable[[str | None], bool],
) -> tuple[bool, bool, bool]:
    """(camera, optics, filter): what this row needs, answered or not. The night settles a frame
    with no camera, and its optics too when it names one."""
    camera = bool(r["asks_camera"]) and night is None
    optics = not r["names_optics"] and not (night or {}).get("optics")
    filtro = bool(r["silent_filter"]) and not colour(_camera_of(conn, r, night, given))
    return camera, optics, filtro


def _native_focal(conn: sqlite3.Connection, optics_name: str | None) -> float | None:
    """Proposed when the frames are silent: without a focal the answer's rig would stay a twin of
    the detected one forever (`rigs.rig_for`)."""
    if not optics_name:
        return None
    row = conn.execute(_NATIVE_FOCAL, (optics_name,)).fetchone()
    return None if row is None else row["focal_mm"]


def _only[T](values: set[T | None]) -> T | None:
    """With two values in one card nothing is chosen for the user, and a blank means "unknown"."""
    detti = {v for v in values if v is not None}
    return detti.pop() if len(detti) == 1 else None


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
    righe = conn.execute(_BY_FRAME).fetchall()
    date = answers(conn)
    chiedono = {r["night"] for r in righe if r["night"] and r["asks_camera"]}
    notti = night_rigs(conn, chiedono) if chiedono else {}
    colour = cache(lambda name: is_colour(conn, name))
    schede: dict[str, dict[str, Any]] = {}
    date_per_scheda: dict[str, Answer | None] = {}
    for r, parti in _bucketed(righe):
        trovata = answer_for(date, parti)
        chiave, data = trovata if trovata else (key_of(parti), None)
        if only is not None and chiave != only:
            continue
        notte = notti.get(r["night"]) if r["asks_camera"] else None
        chiede = _asks(conn, r, notte, data, colour)
        if not any(chiede) and data is None:
            continue
        scheda = schede.setdefault(chiave, _card(chiave, r))
        _add(conn, scheda, r, chiede)
        scheda["cameras"].add(_camera_of(conn, r, notte, data))
        date_per_scheda[chiave] = data
    # with the ASIAIR `TELESCOP` is the mount, on every card with that spelling
    montature = {
        normalize_header_value(r["telescope_raw"])
        for r in righe
        if telescope_is_mount(normalize_software(r["software_raw"]))
    }
    gruppi = obj.subjects(conn, schede.values())
    out = [_shown(conn, s, date_per_scheda[s["key"]], montature) for s in gruppi]
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
    for campo, chiede in zip(("asks_camera", "asks_optics", "asks_filter"), asks, strict=True):
        card[campo] = card[campo] or chiede
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
    manca = [
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
        "answer": as_page(conn, data) if data else None,
        "complete": not any(manca),
    }


def row_of(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return next(iter(by_signature(conn, only=key)), None)
