"""The gear question once per header signature (ADR 0014, S1): camera, optics and filter the files
leave out, answered for frames to come with that signature too, on any night."""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass, replace
from enum import StrEnum

from ..db.row import Row
from ..units import known_focal, same_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from . import declarations as decl
from .declarations import EntityType
from .stages import StageName, invalidate

log = logging.getLogger(__name__)


class FilterAnswer(StrEnum):
    """The filter words of an answer; "colour" is not one: it is written on the camera's card."""

    NO_FILTER = "no_filter"
    ONE_OF_YOURS = "filter"


_FILTER_WORDS = tuple(FilterAnswer)

# Copies included: whoever answers requeues them too. The sensor narrows by index-free equality.
_SAME_SENSOR = """
SELECT id, instrument_raw, telescope_raw, software_raw, focal_mm_raw, naxis1, naxis2, pixel_size_um
FROM frames WHERE naxis1 IS ? AND naxis2 IS ? AND pixel_size_um IS ?
"""


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
class Answer:
    """NAMES, never row ids: a merge deletes the row, and the answer must survive it."""

    camera: str | None = None
    optics: str | None = None
    focal_mm: float | None = None
    filter: FilterAnswer | None = None
    filter_name: str | None = None


@dataclass(frozen=True, slots=True)
class AnswerOnPage:
    """The filter by id, as the dropdown holds it; `None` once that filter is gone."""

    camera: str | None
    optics: str | None
    focal_mm: float | None
    filter: FilterAnswer | None
    filter_id: int | None


def parts_of(r: Row) -> Parts:
    """A `TELESCOP` the software calls the mount says nothing of the optics: two mount names of one
    ASIAIR user would otherwise ask the same camera twice."""
    on_mount = telescope_is_mount(normalize_software(r["software_raw"]))
    return Parts(
        normalize_header_value(r["instrument_raw"]) or None,
        None if on_mount else normalize_header_value(r["telescope_raw"]) or None,
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
        items = json.loads(key)
        return Parts(*items) if isinstance(items, list) else None
    except (ValueError, TypeError):
        return None


def _text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _read(value: object) -> Answer | None:
    """A malformed row counts as no answer, and is logged: it is a user's answer being lost."""
    try:
        data = json.loads(value) if isinstance(value, str) else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        log.warning("signature: risposta illeggibile, ignorata")
        return None
    word = data.get("filter")
    filter_word = FilterAnswer(word) if word in _FILTER_WORDS else None
    return Answer(
        camera=_text(data.get("camera")),
        optics=_text(data.get("optics")),
        focal_mm=known_focal(data.get("focal_mm")),
        filter=filter_word,
        filter_name=(
            _text(data.get("filter_name")) if filter_word == FilterAnswer.ONE_OF_YOURS else None
        ),
    )


type Answers = list[tuple[Parts, str, Answer]]


def answers(conn: sqlite3.Connection) -> Answers:
    """All of them, read once per round or page: an archive has a handful of signatures."""
    out: Answers = []
    stored = decl.values_of(conn, EntityType.SIGNATURE, decl.SIGNATURE_GEAR)
    for answer_key, raw in sorted(stored, key=lambda r: r[0]):
        sought, stored_answer = parts_of_key(answer_key), _read(raw)
        if sought is not None and stored_answer is not None:
            out.append((sought, answer_key, stored_answer))
    return out


def answer_for(given: Answers, parts: Parts) -> tuple[str, Answer] | None:
    """The first by key: two answers within one focal tolerance are not chosen between at random."""
    return next(((k, a) for p, k, a in given if p.same_as(parts)), None)


def answer(conn: sqlite3.Connection, key: str) -> Answer | None:
    raw = decl.declared(conn, EntityType.SIGNATURE, key, decl.SIGNATURE_GEAR)
    return None if raw is None else _read(raw)  # no answer yet is not a lost one


def declare(conn: sqlite3.Connection, key: str, given: Answer, now: str | None = None) -> None:
    value = json.dumps(asdict(given))
    decl.write_declaration(conn, EntityType.SIGNATURE, key, decl.SIGNATURE_GEAR, value, now)


def frames_of(conn: sqlite3.Connection, key: str) -> list[int]:
    """Copies and frames an earlier answer settled included: that is how one changes one's mind.
    The key on the left, as in `answer_for`: the focal tolerance is measured on the key."""
    sought = parts_of_key(key)
    if sought is None:
        return []
    rows = conn.execute(_SAME_SENSOR, (sought.width, sought.height, sought.pixel_um))
    return [r["id"] for r in rows if sought.same_as(parts_of(r))]


def requeue(conn: sqlite3.Connection, key: str) -> list[int]:
    frames = frames_of(conn, key)
    invalidate(conn, frames, StageName.NORMALIZE)
    return frames


def _every_answer(conn: sqlite3.Connection) -> list[tuple[str, Answer]]:
    """Also under a key no reader parses: a name followed is never left behind."""
    stored = decl.values_of(conn, EntityType.SIGNATURE, decl.SIGNATURE_GEAR)
    return [(k, a) for k, v in stored if (a := _read(v)) is not None]


def follow_piece(
    conn: sqlite3.Connection, kind: str, old_name: str, new_name: str, now: str | None = None
) -> None:
    """On the old name the piece would be reborn beside the new one at the next round."""
    for answer_key, stored_answer in _every_answer(conn):
        if getattr(stored_answer, kind) == old_name:
            declare(conn, answer_key, replace(stored_answer, **{kind: new_name}), now)


def follow_filter(conn: sqlite3.Connection, old_name: str, new_name: str) -> None:
    """Renamed or merged, the filter carries the answer along, or its frames lose it."""
    for answer_key, stored_answer in _every_answer(conn):
        if stored_answer.filter_name == old_name:
            declare(conn, answer_key, replace(stored_answer, filter_name=new_name))


def as_page(conn: sqlite3.Connection, given: Answer) -> AnswerOnPage:
    filter_row = conn.execute(
        "SELECT id FROM filters WHERE name = ?", (given.filter_name,)
    ).fetchone()
    return AnswerOnPage(
        given.camera,
        given.optics,
        given.focal_mm,
        given.filter,
        None if filter_row is None else filter_row["id"],
    )
