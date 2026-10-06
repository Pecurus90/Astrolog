"""The gear question once per header signature (ADR 0014, S1): camera, optics and filter the files
leave out, answered for frames to come with that signature too, on any night."""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass, replace
from typing import Any

from ..db.row import Row
from ..units import known_focal, same_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from . import declarations as decl
from .stages import StageName, invalidate

log = logging.getLogger(__name__)

# The filter words of an answer; "colour" is not one: it is written on the camera's card.
NO_FILTER, ONE_OF_YOURS = "no_filter", "filter"
FILTER_ANSWERS = (NO_FILTER, ONE_OF_YOURS)

# Copies included: whoever answers requeues them too. The sensor narrows by index-free equality.
_SAME_SENSOR = """
SELECT id, instrument_raw, telescope_raw, software_raw, focal_mm_raw, naxis1, naxis2, pixel_size_um
FROM frames WHERE naxis1 IS ? AND naxis2 IS ? AND pixel_size_um IS ?
"""


@dataclass(frozen=True)
class Parts:
    """What the header says, spellings normalized as an alias is: a rename leaves the key alone."""

    camera: str | None
    telescope: str | None
    focal_mm: float | None
    width: int | None
    height: int | None
    pixel_um: float | None

    def same_as(self, other: "Parts") -> bool:
        """The focal by the rigs' rule: 800 mm and 803 are one signature, as they are one rig."""
        return replace(self, focal_mm=None) == replace(other, focal_mm=None) and same_focal(
            self.focal_mm, other.focal_mm
        )


@dataclass(frozen=True)
class Answer:
    """NAMES, never row ids: a merge deletes the row, and the answer must survive it."""

    camera: str | None = None
    optics: str | None = None
    focal_mm: float | None = None
    filter: str | None = None
    filter_name: str | None = None


def parts_of(r: Row) -> Parts:
    """A `TELESCOP` the software calls the mount says nothing of the optics: two mount names of one
    ASIAIR user would otherwise ask the same camera twice."""
    montatura = telescope_is_mount(normalize_software(r["software_raw"]))
    return Parts(
        normalize_header_value(r["instrument_raw"]) or None,
        None if montatura else normalize_header_value(r["telescope_raw"]) or None,
        known_focal(r["focal_mm_raw"]),
        r["naxis1"],
        r["naxis2"],
        r["pixel_size_um"],
    )


def key_of(parts: Parts) -> str:
    return json.dumps(list(asdict(parts).values()))


def parts_of_key(key: str) -> Parts | None:
    """`None` for a key no reader wrote: a malformed answer is no answer."""
    try:
        valori = json.loads(key)
        return Parts(*valori) if isinstance(valori, list) else None
    except (ValueError, TypeError):
        return None


def _text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _read(value: object) -> Answer | None:
    """A malformed row counts as no answer, and is logged: it is a user's answer being lost."""
    try:
        dato = json.loads(value) if isinstance(value, str) else None
    except ValueError:
        dato = None
    if not isinstance(dato, dict):
        log.warning("signature: risposta illeggibile, ignorata")
        return None
    filtro = dato.get("filter") if dato.get("filter") in FILTER_ANSWERS else None
    return Answer(
        camera=_text(dato.get("camera")),
        optics=_text(dato.get("optics")),
        focal_mm=known_focal(dato.get("focal_mm")),
        filter=filtro,
        filter_name=_text(dato.get("filter_name")) if filtro == ONE_OF_YOURS else None,
    )


type Answers = list[tuple[Parts, str, Answer]]


def answers(conn: sqlite3.Connection) -> Answers:
    """All of them, read once per round or page: an archive has a handful of signatures."""
    out: Answers = []
    for chiave, valore in sorted(
        decl.values_of(conn, decl.SIGNATURE, decl.SIGNATURE_GEAR), key=lambda r: r[0]
    ):
        parti, risposta = parts_of_key(chiave), _read(valore)
        if parti is not None and risposta is not None:
            out.append((parti, chiave, risposta))
    return out


def answer_for(given: Answers, parts: Parts) -> tuple[str, Answer] | None:
    """The first by key: two answers within one focal tolerance are not chosen between at random."""
    return next(((k, a) for p, k, a in given if p.same_as(parts)), None)


def answer(conn: sqlite3.Connection, key: str) -> Answer | None:
    valore = decl.declared(conn, decl.SIGNATURE, key, decl.SIGNATURE_GEAR)
    return None if valore is None else _read(valore)  # no answer yet is not a lost one


def declare(conn: sqlite3.Connection, key: str, given: Answer, now: str | None = None) -> None:
    value = json.dumps(asdict(given))
    decl.write_declaration(conn, decl.SIGNATURE, key, decl.SIGNATURE_GEAR, value, now)


def frames_of(conn: sqlite3.Connection, key: str) -> list[int]:
    """Copies and frames an earlier answer settled included: that is how one changes one's mind."""
    parti = parts_of_key(key)
    if parti is None:
        return []
    righe = conn.execute(_SAME_SENSOR, (parti.width, parti.height, parti.pixel_um))
    return [r["id"] for r in righe if parts_of(r).same_as(parti)]


def requeue(conn: sqlite3.Connection, key: str) -> list[int]:
    frames = frames_of(conn, key)
    invalidate(conn, frames, StageName.NORMALIZE)
    return frames


def _every_answer(conn: sqlite3.Connection) -> list[tuple[str, Answer]]:
    """Also under a key no reader parses: a name followed is never left behind."""
    lette = decl.values_of(conn, decl.SIGNATURE, decl.SIGNATURE_GEAR)
    return [(k, a) for k, v in lette if (a := _read(v)) is not None]


def follow_piece(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, now: str | None = None
) -> None:
    """On the old name the piece would be reborn beside the new one at the next round."""
    for chiave, risposta in _every_answer(conn):
        if getattr(risposta, kind) == old_name:
            declare(conn, chiave, replace(risposta, **{kind: new_name}), now)


def follow_filter(conn: sqlite3.Connection, old_name: str, new_name: str) -> None:
    """Renamed or merged, the filter carries the answer along, or its frames lose it."""
    for chiave, risposta in _every_answer(conn):
        if risposta.filter_name == old_name:
            declare(conn, chiave, replace(risposta, filter_name=new_name))


def as_page(conn: sqlite3.Connection, given: Answer) -> dict[str, Any]:
    """The filter by id, as the dropdown holds it; `None` once that filter is gone."""
    riga = conn.execute("SELECT id FROM filters WHERE name = ?", (given.filter_name,)).fetchone()
    return {
        "camera": given.camera,
        "optics": given.optics,
        "focal_mm": given.focal_mm,
        "filter": given.filter,
        "filter_id": riga and riga["id"],
    }
