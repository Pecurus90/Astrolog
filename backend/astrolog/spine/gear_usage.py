"""How much each piece, rig and filter served, written at the end of every stage that moves frames.
Hours the app cannot know are NULL, not zero; a rig's field is measured on solved frames."""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from ..db import idlist
from ..db.replace_table import replace_rows
from ..units import hundredths, median
from . import counts
from . import objects as obj

# Optics and camera always have hours: they pass through the rig, which the spine derives from
# every frame. For the others it depends on the archive (`_con_le_ore`).
_SEMPRE = ("optics", "camera")

# Frames grouped once per list, not a correlated subselect per row, with `counts`'s link: the
# nights too, or one row would tell two numbers.
_CONTI = f"{counts.AGGREGATE}, {counts.UNTIMED}, COUNT(DISTINCT f.night_id) AS nights"
_USATI = """COALESCE(u.frames, 0) AS frames, COALESCE(u.integration_s, 0) AS integration_s,
       COALESCE(u.untimed, 0) AS untimed, COALESCE(u.nights, 0) AS nights"""

_STRUMENTI = f"""
SELECT i.id, i.kind, {_USATI}
FROM instruments i LEFT JOIN (
  SELECT l.piece AS id, {_CONTI}
  FROM ({counts.PIECE_FRAMES}) l JOIN frames f ON f.id = l.frame
  WHERE f.copy_of IS NULL GROUP BY l.piece
) u ON u.id = i.id
"""  # noqa: S608 - constant fragments of the spine, not user values

_CORREDI = f"""
SELECT g.id, {_USATI}
FROM rigs g LEFT JOIN (
  SELECT f.rig_id AS id, {_CONTI} FROM frames f
  WHERE f.copy_of IS NULL AND f.rig_id IS NOT NULL GROUP BY f.rig_id
) u ON u.id = g.id
{counts.ORDER_BY_TIME}, g.id
"""  # noqa: S608 - constant fragments of the spine, not user values

_FILTRI = f"""
SELECT x.id, {_USATI}
FROM filters x LEFT JOIN (
  SELECT f.filter_id AS id, {_CONTI} FROM frames f
  WHERE f.copy_of IS NULL AND f.filter_id IS NOT NULL GROUP BY f.filter_id
) u ON u.id = x.id
WHERE x.is_none = 0
{counts.ORDER_BY_TIME}, x.name
"""  # noqa: S608 - constant fragments of the spine, not user values

# What each one shot, most shot first: one body, three keys.
_OGGETTI = f"""
SELECT {{chiave}} AS chiave, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id {{giunzione}}
WHERE {{campo}} IN {{{{listed}}}} AND f.copy_of IS NULL
GROUP BY chiave, o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - constant fragments of the spine, not user values

_OGGETTI_DEL_CORREDO = _OGGETTI.format(chiave="f.rig_id", giunzione="", campo="f.rig_id")
_OGGETTI_DEL_FILTRO = _OGGETTI.format(chiave="f.filter_id", giunzione="", campo="f.filter_id")
# `counts`'s link with the rigs in the `FROM`, not a subselect searched per (frame, piece). The
# `LEFT` matters: a frame naming a wheel may have no rig.
_OGGETTI_DEL_PEZZO = _OGGETTI.format(
    chiave="i.id",
    giunzione=(
        "LEFT JOIN rigs g ON g.id = f.rig_id JOIN instruments i ON "
        + counts.of(counts.Subject.INSTRUMENT, rigs_joined=True)
    ),
    campo="i.id",
)

_CIELO = """
SELECT f.rig_id AS chiave, w.scale_arcsec_px, w.width_deg, w.height_deg
FROM frames f JOIN frame_wcs w ON w.frame_id = f.id
WHERE f.rig_id IN {listed} AND f.copy_of IS NULL
"""

USAGE = ("frames", "integration_s", "untimed", "nights")
_COLONNE = (
    "subject", "subject_id", *USAGE, "scale_arcsec_px", "width_deg", "height_deg",
    "objects_json", "position",
)  # fmt: skip


def write(conn: sqlite3.Connection) -> None:
    """Redone whole, all or nothing: a frame changing rig moves four rows, and following them one
    by one would get one wrong. The page order is `counts.ORDER_BY_TIME`, written as position."""
    righe = [
        (r["subject"], r["id"], *(r[c] for c in _COLONNE[2:-1]), n)
        for elenco in (_strumenti(conn), _corredi(conn), _filtri(conn))
        for n, r in enumerate(elenco)
    ]
    replace_rows(conn, "gear_usage", _COLONNE, righe)


def add_piece(conn: sqlite3.Connection, instrument_id: int, kind: str) -> None:
    """Only its own row: recounting the whole archive inside the request that creates it would
    cost seconds."""
    _nuova(conn, "instrument", instrument_id, conta=kind in _con_le_ore(conn))


def add_new(conn: sqlite3.Connection, subject: str, row_id: int) -> None:
    """A filter's or rig's hours are always known: the frame names its filter and its rig."""
    _nuova(conn, subject, row_id, conta=True)


def _nuova(conn: sqlite3.Connection, subject: str, row_id: int, *, conta: bool) -> None:
    """At the bottom of its list, which runs from the most used: at the top, with zero hours, it
    would lie."""
    conn.execute(
        "INSERT OR REPLACE INTO gear_usage(subject, subject_id, frames, integration_s, untimed,"
        " nights, objects_json, position) VALUES(?, ?, ?, ?, ?, ?, '[]',"
        " (SELECT COALESCE(MAX(position) + 1, 0) FROM gear_usage WHERE subject = ?))",
        (subject, row_id, *((0, 0.0, 0, 0) if conta else (None,) * 4), subject),
    )


def _con_le_ore(conn: sqlite3.Connection) -> set[str]:
    """A kind the frame names itself counts only if some frame names it: a wheel no file ever wrote
    has not done zero hours, it has hours the app cannot know."""
    generi: set[str] = set(_SEMPRE)
    for kind in counts.CARRIED:
        detto = conn.execute(
            f"SELECT 1 FROM frames WHERE {kind}_id IS NOT NULL LIMIT 1"  # noqa: S608 - our kinds
        ).fetchone()
        if detto is not None:
            generi.add(kind)
    return generi


def _riga(
    subject: str,
    r: sqlite3.Row,
    oggetti: Mapping[Any, Sequence[Any]],
    *,
    conta: bool = True,
    cielo: Mapping[str, float | None] | None = None,
) -> dict[str, Any]:
    uso: dict[str, Any] = {c: r[c] for c in USAGE} if conta else dict.fromkeys(USAGE)
    cielo = cielo or {}
    return {
        "subject": subject,
        "id": r["id"],
        **uso,
        "scale_arcsec_px": cielo.get("scale_arcsec_px"),
        "width_deg": cielo.get("width_deg"),
        "height_deg": cielo.get("height_deg"),
        "objects_json": json.dumps(oggetti.get(r["id"], []) if conta else []),
    }


def _strumenti(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    righe = conn.execute(_STRUMENTI).fetchall()
    con_le_ore = _con_le_ore(conn)
    ids = [r["id"] for r in righe if r["kind"] in con_le_ore]
    oggetti = idlist.grouped(conn, _OGGETTI_DEL_PEZZO, ids, "chiave", obj.counted)
    return [_riga("instrument", r, oggetti, conta=r["kind"] in con_le_ore) for r in righe]


def _corredi(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    righe = conn.execute(_CORREDI).fetchall()
    ids = [r["id"] for r in righe]
    oggetti = idlist.grouped(conn, _OGGETTI_DEL_CORREDO, ids, "chiave", obj.counted)
    visto = idlist.grouped(conn, _CIELO, ids, "chiave", dict)
    return [
        _riga(
            "rig",
            r,
            oggetti,
            cielo={
                campo: hundredths(median([v[campo] for v in visto.get(r["id"], [])]))
                for campo in ("scale_arcsec_px", "width_deg", "height_deg")
            },
        )
        for r in righe
    ]


def _filtri(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    righe = conn.execute(_FILTRI).fetchall()
    oggetti = idlist.grouped(
        conn, _OGGETTI_DEL_FILTRO, [r["id"] for r in righe], "chiave", obj.counted
    )
    return [_riga("filter", r, oggetti) for r in righe]
