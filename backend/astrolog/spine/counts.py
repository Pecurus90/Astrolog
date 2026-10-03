"""Frames, hours and untimed frames, counted in one place so no two pages tell different numbers.
Rewritten copies never count, and a subject is a key from a closed list, never SQL from outside."""

import re

# Kinds the frame names itself, each with its `<kind>_raw`; a copy of this list elsewhere would let
# a new kind be created but never renamed, so it is reborn as a duplicate.
ON_THE_FRAME = ("filter_wheel", "focuser", "guide_camera")
# Kinds the frame carries in a column of its own; forgetting one where hours are tied or a piece is
# detached makes a merge crash.
CARRIED = (*ON_THE_FRAME, "mount")


def _pezzo(dai_corredi: str) -> str:
    """A frame reaches a piece through its rig, which depends on the caller's `FROM`, or through
    the columns it carries, which never change."""
    return (  # noqa: S608 - kinds from our list, never user values
        "(" + dai_corredi + "".join(f" OR f.{k}_id = i.id" for k in CARRIED) + ")"
    )


# For callers with `rigs g` already joined: the same link, without a correlated sub-select per pair.
_WITH_RIGS = _pezzo("i.id IN (g.optics_id, g.camera_id)")

# (piece, frame) pairs, so all pieces are counted at once by grouping instead of one correlated
# sub-select per piece; `UNION` drops a frame reaching the same piece twice.
_DAI_CORREDI = ("optics", "camera")
PIECE_FRAMES = " UNION ".join(
    [
        f"SELECT g.{k}_id AS piece, f.id AS frame FROM frames f"  # noqa: S608 - our kinds
        f" JOIN rigs g ON g.id = f.rig_id WHERE g.{k}_id IS NOT NULL"
        for k in _DAI_CORREDI
    ]
    + [
        f"SELECT f.{k}_id AS piece, f.id AS frame FROM frames f WHERE f.{k}_id IS NOT NULL"  # noqa: S608
        for k in CARRIED
    ]
)

# Frames no confirmed mosaic took: the Archive counts by groups, and a mosaic's frames are counted
# in its own row only.
ALONE = "f.mosaic_key IS NULL"
_DEL_MOSAICO = "f.mosaic_key = r.mosaic_key"

# Each subject needs its table already in the caller's `FROM`, except `archive`.
_SOGGETTI = {
    "object": "f.object_id = o.id",
    "night": "f.night_id = n.id",
    "archive": "f.night_id IS NOT NULL",
    "rig": "f.rig_id = g.id",
    "filter": "f.filter_id = x.id",
    "mosaic": _DEL_MOSAICO,
    # what Da confermare proposes, answered or not
    "proposal": "f.panel_id IN (SELECT p.id FROM panels p WHERE p.mosaic_id = m.id"
    " AND p.counts_in_mosaic = 1)",
    # an Archive row: a mosaic, or an object with only its frames outside mosaics
    "row": f"({_DEL_MOSAICO} OR (r.mosaic_key IS NULL AND f.object_id = r.id AND {ALONE}))",
    # optics and camera through the rig, the carried kinds through the frame's own columns
    "instrument": _pezzo(
        "f.rig_id IN (SELECT id FROM rigs WHERE optics_id = i.id OR camera_id = i.id)"
    ),
}

# The same count when grouping, and the order: most time first.
AGGREGATE = "COUNT(*) AS frames, COALESCE(SUM(f.exposure_s), 0) AS integration_s"
UNTIMED = "SUM(f.exposure_s IS NULL) AS untimed"
ORDER_BY_TIME = "ORDER BY integration_s DESC, frames DESC"

# The column is derived from the link, so it can never be written differently from its `WHERE`.
_UNA_COLONNA = re.compile(r"f\.(\w+) = \w+\.\w+$")


def column_of(soggetto: str) -> str:
    """Raises for links that are not one column (the whole archive, a piece reached two ways):
    grouping them on a column would count other frames."""
    dove = _SOGGETTI[soggetto]  # closed list: an unknown key is a KeyError
    trovata = _UNA_COLONNA.fullmatch(dove)
    if trovata is None:
        raise KeyError(f"il legame di {soggetto} non e' una colonna sola: {dove}")
    return trovata.group(1)


def of(soggetto: str, *, rigs_joined: bool = False) -> str:
    """Asked, never rewritten, so that whoever counts something else on the same frames ties them
    the same way. `rigs_joined` is for callers with `rigs g` in their `FROM`."""
    dove = _SOGGETTI[soggetto]
    if not rigs_joined:
        return dove
    if soggetto != "instrument":
        raise KeyError(f"la forma coi corredi esiste solo per il pezzo, non per {soggetto}")
    return _WITH_RIGS


def counts_on(soggetto: str) -> str:
    """The three sub-selects `frames`, `integration_s`, `untimed` for that subject."""
    dove = of(soggetto)
    tre = f"""
       (SELECT COUNT(*) FROM frames f
         WHERE {dove} AND f.copy_of IS NULL) AS frames,
       (SELECT COALESCE(SUM(f.exposure_s), 0) FROM frames f
         WHERE {dove} AND f.copy_of IS NULL) AS integration_s,
       (SELECT COUNT(*) FROM frames f
         WHERE {dove} AND f.copy_of IS NULL AND f.exposure_s IS NULL) AS untimed"""  # noqa: S608
    return tre
