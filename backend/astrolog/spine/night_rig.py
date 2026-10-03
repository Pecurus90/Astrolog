"""What a night's frames say about the gear, for the frame that does not say it. Read from the raw
columns: the night's frames may not be normalized yet when it is asked."""

import json
import sqlite3
from collections.abc import Iterable
from typing import Any

from ..clock import NIGHT_SQL
from ..db.row import Row
from ..units import known_focal, same_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from . import declarations as decl


def rigs_by_night(listed: bool) -> str:
    """One row per night and raw values, never per frame. `listed` keeps the nights of a JSON list,
    which are looked up through the index."""
    dove = f"{NIGHT_SQL} IN (SELECT value FROM json_each(?))" if listed else "1"  # noqa: S608
    return f"""
SELECT {NIGHT_SQL} AS night, f.instrument_raw, f.telescope_raw, f.software_raw, f.focal_mm_raw
FROM frames f WHERE {NIGHT_SQL} IS NOT NULL AND f.instrument_raw IS NOT NULL AND {dove}
GROUP BY night, f.instrument_raw, f.telescope_raw, f.software_raw, f.focal_mm_raw
"""  # noqa: S608 - constant fragments


# In SQL, not `clock.night_date`: it must be the grouping key, and with the zone written in the
# date the two languages disagree.
NIGHT_OF = f"SELECT {NIGHT_SQL} AS night FROM frames f WHERE f.id = ?"  # noqa: S608

_RAW_OF = "SELECT id, instrument_raw FROM frames WHERE id IN (SELECT value FROM json_each(?))"

_IN_NIGHTS_OF = f"""
SELECT f.id, f.instrument_raw FROM frames f
WHERE {NIGHT_SQL} IN (
  SELECT {NIGHT_SQL} FROM frames f WHERE f.id IN (SELECT value FROM json_each(?))
)
"""  # noqa: S608 - constant fragment

type _Seen = tuple[str, str | None, float | None]


def asks_camera(instrument_raw: str | None) -> bool:
    """Normalized as a learned rule is looked up: blanks or a bare ASCOM instance index are not a
    name."""
    return not normalize_header_value(instrument_raw)


def night_rigs(
    conn: sqlite3.Connection, nights: Iterable[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Nights whose headers name one camera. Optics and focal only if the night says one: the
    ASIAIR's "no optics" is an answer too. `nights` spares reading the whole archive."""
    per_notte: dict[str, list[_Seen]] = {}
    nomi: dict[tuple[str, str | None], str | None] = {}
    if nights is None:
        righe = conn.execute(rigs_by_night(False))
    else:
        righe = conn.execute(rigs_by_night(True), (json.dumps(sorted(nights)),))

    def nome(kind: str, grafia: str | None) -> str | None:  # one lookup per spelling, not per night
        if (kind, grafia) not in nomi:
            nomi[kind, grafia] = decl.instrument_name(conn, kind, grafia) if grafia else None
        return nomi[kind, grafia]

    for r in righe:
        if (camera := nome("camera", r["instrument_raw"])) is None:
            continue
        mount = telescope_is_mount(normalize_software(r["software_raw"]))
        ottica = None if mount else nome("optics", r["telescope_raw"])
        visto = (camera, ottica, known_focal(r["focal_mm_raw"]))
        per_notte.setdefault(r["night"], []).append(visto)
    corredi = {notte: _rig_of(viste) for notte, viste in per_notte.items()}
    return {notte: corredo for notte, corredo in corredi.items() if corredo is not None}


def _rig_of(viste: list[_Seen]) -> dict[str, Any] | None:
    camere, ottiche = {v[0] for v in viste}, {v[1] for v in viste}
    if len(camere) != 1:
        return None
    focali = [v[2] for v in viste]
    intero = len(ottiche) == 1 and all(same_focal(focali[0], f) for f in focali)
    return {
        "camera": camere.pop(),
        "optics": ottiche.pop() if intero else None,
        "focal_mm": focali[0] if intero else None,
    }


def rig_of_night(
    conn: sqlite3.Connection, frame: Row, rigs: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    return rigs.get(conn.execute(NIGHT_OF, (frame["id"],)).fetchone()["night"])


def in_nights_of(conn: sqlite3.Connection, frame_ids: Iterable[int]) -> list[int]:
    """Camera-less frames in the nights of these camera-naming frames: their night's rig may have
    changed, so the caller requeues them."""
    dicono = [r["id"] for r in conn.execute(_RAW_OF, (json.dumps(list(frame_ids)),))
              if not asks_camera(r["instrument_raw"])]  # fmt: skip
    if not dicono:
        return []
    rows = conn.execute(_IN_NIGHTS_OF, (json.dumps(dicono),))
    return [r["id"] for r in rows if asks_camera(r["instrument_raw"])]
