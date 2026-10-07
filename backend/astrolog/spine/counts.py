"""Frames, hours and untimed frames, counted in one place so no two pages tell different numbers.
Rewritten copies never count, and a subject is a key from a closed list, never SQL from outside."""

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

# Kinds the frame names itself, each with its `<kind>_raw`; a copy of this list elsewhere would let
# a new kind be created but never renamed, so it is reborn as a duplicate.
ON_THE_FRAME = ("filter_wheel", "focuser", "guide_camera")
# Kinds the frame carries in a column of its own; forgetting one where hours are tied or a piece is
# detached makes a merge crash.
CARRIED = (*ON_THE_FRAME, "mount")


def _piece(through_rigs: str) -> str:
    """A frame reaches a piece through its rig, which depends on the caller's `FROM`, or through
    the columns it carries, which never change."""
    return (  # noqa: S608 - kinds from our list, never user values
        "(" + through_rigs + "".join(f" OR f.{k}_id = i.id" for k in CARRIED) + ")"
    )


# For callers with `rigs g` already joined: the same link, without a correlated sub-select per pair.
_WITH_RIGS = _piece("i.id IN (g.optics_id, g.camera_id)")

# (piece, frame) pairs, so all pieces are counted at once by grouping instead of one correlated
# sub-select per piece; `UNION` drops a frame reaching the same piece twice.
_THROUGH_RIGS = ("optics", "camera")
PIECE_FRAMES = " UNION ".join(
    [
        f"SELECT g.{k}_id AS piece, f.id AS frame FROM frames f"  # noqa: S608 - our kinds
        f" JOIN rigs g ON g.id = f.rig_id WHERE g.{k}_id IS NOT NULL"
        for k in _THROUGH_RIGS
    ]
    + [
        f"SELECT f.{k}_id AS piece, f.id AS frame FROM frames f"  # noqa: S608 - our kinds
        f" WHERE f.{k}_id IS NOT NULL"
        for k in CARRIED
    ]
)

# Frames no confirmed mosaic took: the Archive counts by groups, and a mosaic's frames are counted
# in its own row only.
ALONE = "f.mosaic_key IS NULL"
_OF_MOSAIC = "f.mosaic_key = r.mosaic_key"


class Subject(StrEnum):
    OBJECT = "object"
    NIGHT = "night"
    ARCHIVE = "archive"
    RIG = "rig"
    FILTER = "filter"
    MOSAIC = "mosaic"
    PROPOSAL = "proposal"
    ROW = "row"
    INSTRUMENT = "instrument"


# Each subject needs its table already in the caller's `FROM`, except `archive`.
_SUBJECTS = {
    Subject.OBJECT: "f.object_id = o.id",
    Subject.NIGHT: "f.night_id = n.id",
    Subject.ARCHIVE: "f.night_id IS NOT NULL",
    Subject.RIG: "f.rig_id = g.id",
    Subject.FILTER: "f.filter_id = x.id",
    Subject.MOSAIC: _OF_MOSAIC,
    # what Da confermare proposes, answered or not
    Subject.PROPOSAL: "f.panel_id IN (SELECT p.id FROM panels p WHERE p.mosaic_id = m.id"
    " AND p.counts_in_mosaic = 1)",
    # an Archive row: a mosaic, or an object with only its frames outside mosaics
    Subject.ROW: f"({_OF_MOSAIC} OR (r.mosaic_key IS NULL AND f.object_id = r.id AND {ALONE}))",
    # optics and camera through the rig, the carried kinds through the frame's own columns
    Subject.INSTRUMENT: _piece(
        "f.rig_id IN (SELECT id FROM rigs WHERE optics_id = i.id OR camera_id = i.id)"
    ),
}

# The same count when grouping, and the order: most time first.
AGGREGATE = "COUNT(*) AS frames, COALESCE(SUM(f.exposure_s), 0) AS integration_s"
UNTIMED = "SUM(f.exposure_s IS NULL) AS untimed"
ORDER_BY_TIME = "ORDER BY integration_s DESC, frames DESC"

# The column is derived from the link, so it can never be written differently from its `WHERE`.
_ONE_COLUMN = re.compile(r"f\.(\w+) = \w+\.\w+$")


def column_of(subject: Subject) -> str:
    """Raises for links that are not one column (the whole archive, a piece reached two ways):
    grouping them on a column would count other frames."""
    where = _SUBJECTS[subject]  # closed list: an unknown key is a KeyError
    match = _ONE_COLUMN.fullmatch(where)
    if match is None:
        raise KeyError(f"il legame di {subject} non e' una colonna sola: {where}")
    return match.group(1)


def of(subject: Subject, *, rigs_joined: bool = False) -> str:
    """Asked, never rewritten, so that whoever counts something else on the same frames ties them
    the same way."""
    where = _SUBJECTS[subject]
    if not rigs_joined:
        return where
    if subject != Subject.INSTRUMENT:
        raise KeyError(f"la forma coi corredi esiste solo per il pezzo, non per {subject}")
    return _WITH_RIGS


@dataclass(frozen=True)
class Scope:
    """Which frames count, when the user narrows by period, site or gear: a row then tells what
    was asked, not its whole life. `since`/`until` are night dates, in the site's time zone."""

    since: str | None = None
    until: str | None = None
    site: int | None = None
    optics: int | None = None
    camera: int | None = None

    @property
    def sql(self) -> tuple[str, list[Any]]:
        """`(" AND ...", values)` on frames `f`, or `("", [])` when nothing narrows."""
        nights = [
            (c, v)
            for c, v in (
                ("n.night_date >= ?", self.since),
                ("n.night_date <= ?", self.until),
                ("n.site_id = ?", self.site),
            )
            if v is not None
        ]
        rigs = [
            (c, v)
            for c, v in (("g.optics_id = ?", self.optics), ("g.camera_id = ?", self.camera))
            if v is not None
        ]
        parts = []
        if nights:
            parts.append(
                "f.night_id IN (SELECT n.id FROM nights n WHERE "  # noqa: S608 - our columns
                + " AND ".join(c for c, _ in nights)
                + ")"
            )
        if rigs:
            parts.append(
                "f.rig_id IN (SELECT g.id FROM rigs g WHERE "  # noqa: S608 - our columns
                + " AND ".join(c for c, _ in rigs)
                + ")"
            )
        return "".join(f" AND {p}" for p in parts), [v for _, v in nights + rigs]


def counts_on(subject: Subject, narrowed: str = "") -> str:
    """The three sub-selects `frames`, `integration_s`, `untimed` for that subject. `narrowed` is
    a `Scope`'s SQL: its values go three times, once per sub-select."""
    where = of(subject) + narrowed
    three = f"""
       (SELECT COUNT(*) FROM frames f
         WHERE {where} AND f.copy_of IS NULL) AS frames,
       (SELECT COALESCE(SUM(f.exposure_s), 0) FROM frames f
         WHERE {where} AND f.copy_of IS NULL) AS integration_s,
       (SELECT COUNT(*) FROM frames f
         WHERE {where} AND f.copy_of IS NULL AND f.exposure_s IS NULL) AS untimed"""  # noqa: S608
    return three
