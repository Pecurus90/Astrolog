"""The archive's objects, read: what they are called and what hangs on them. Here and not in a
stage's store because many read them, and a stage may not import another."""

import sqlite3
from collections.abc import Iterable
from typing import Any, cast

from ..db.row import Row
from . import counts

# A name is two steps, not a column: the primary in `object_names`, else the catalog's name for the
# slug. A catalog object whose catalog names were all taken has no primary.
NAME_COLUMNS = """
       (SELECT n.name FROM object_names n
         WHERE n.object_id = o.id AND n.is_primary = 1) AS primary_name,
       (SELECT e.name FROM catalog_entries e WHERE e.slug = o.catalog_slug) AS catalog_name"""

_LIST = f"""
SELECT o.*, {NAME_COLUMNS},{counts.counts_on("object")}
FROM objects o
"""  # noqa: S608 - constant fragments of the spine

# The STATE before the object: a requeued, failed or skipped frame keeps its old `object_id`, which
# the sky did not say. LEFT, so a frame never drops out of its group's count.
NOT_YET, NOT_FOUND = "not_yet", "not_found"
SUBJECT_JOIN = "LEFT JOIN frame_stages si ON si.frame_id = f.id AND si.stage = 'identify'"
SUBJECT = (
    f"CASE WHEN si.status IN ('pending', 'failed') THEN '{NOT_YET}'"
    f" WHEN si.status = 'skipped' OR f.object_id IS NULL THEN '{NOT_FOUND}' ELSE f.object_id END"
)
_NAMES = f"""
SELECT o.id, o.catalog_slug, o.identity_confidence, {NAME_COLUMNS} FROM objects o
"""  # noqa: S608 - constant fragments of the spine


def display_name(row: Row) -> str | None:
    """`None` only for an object with neither catalog nor names, which nothing should create."""
    return row["primary_name"] or row["catalog_name"]


def counted(row: Row) -> dict[str, Any]:
    """An object inside a night or a rig, with its weight there: one way to compose its name."""
    return {
        "key": stable_key(row),
        "name": display_name(row),
        "frames": row["frames"],
        "integration_s": row["integration_s"],
    }


def stable_key(row: Row) -> str:
    """Never the row id: `identify` deletes frameless objects and rebuilds them with new ids, and an
    answer hooked to an id would point at nothing, silently."""
    # never None: see display_name
    return cast("str", row["catalog_slug"] or display_name(row))


def label(row: Row) -> str:
    """On screen an empty row cannot be read: the stable key stands in for a missing name."""
    return display_name(row) or stable_key(row)


def subjects_sql(per: str, sorgente: str = "frames f", where: str = "") -> str:
    """One row per (group, object); `where` is an `AND ...`. Duplicates go before the name lookup
    and the join drops object-less frames: asking inside makes SQLite leave the narrowing index."""
    return f"""
SELECT s.gruppo, o.id, o.catalog_slug, {NAME_COLUMNS}
FROM (SELECT DISTINCT {per} AS gruppo, f.object_id FROM {sorgente}
      WHERE f.copy_of IS NULL {where}) s
JOIN objects o ON o.id = s.object_id
"""  # noqa: S608 - constant fragments from the caller


def subjects_of(righe: Iterable[Row]) -> dict[Any, list[str]]:
    nomi: dict[Any, set[str]] = {}
    for r in righe:
        nomi.setdefault(r["gruppo"], set()).add(label(r))
    return {g: sorted(n) for g, n in nomi.items()}


def together(nomi: Iterable[str]) -> str:
    return ", ".join(nomi)


def count_subject(gruppo: dict[str, Any], subject: int | str, n: int) -> None:
    """`subject` is a row's `SUBJECT`: an object id or one of the two blanks."""
    conti = gruppo.setdefault("subjects", {})
    conti[subject] = conti.get(subject, 0) + n


def subjects[G: Iterable[dict[str, Any]]](conn: sqlite3.Connection, gruppi: G) -> G:
    """Names are read once for every group: an archive has a handful of objects, and the groups can
    be hundreds."""
    nomi = {r["id"]: label(r) for r in conn.execute(_NAMES)}
    for g in gruppi:
        conti = g.get("subjects", {})
        vuoti = (NOT_YET, NOT_FOUND)
        trovati = [{"name": nomi[s], "frames": n} for s, n in conti.items() if s not in vuoti]
        g["subjects"] = {
            "found": sorted(trovati, key=lambda t: (-t["frames"], t["name"])),
            "not_found": conti.get(NOT_FOUND, 0),
            "not_yet": conti.get(NOT_YET, 0),
        }
    return gruppi


def by_key(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    row = conn.execute(
        f"{_LIST} WHERE o.catalog_slug = ?"  # noqa: S608 - constant query of this file
        " OR (o.catalog_slug IS NULL AND o.id IN"
        "     (SELECT object_id FROM object_names WHERE name = ? AND is_primary = 1))",
        (key, key),
    ).fetchone()
    return dict(row) if row else None


def listing(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read whole, since objects are far fewer than frames: what is paged is the answer."""
    return [dict(r) for r in conn.execute(_LIST)]


def identities(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Without counting frames, for whoever does not show the numbers."""
    return [dict(r) for r in conn.execute(_NAMES)]


def a_frame_of(conn: sqlite3.Connection, object_id: int) -> dict[str, Any] | None:
    """One frame with a measured sky: an object's frames look at the same patch, and asking the cone
    for each would pay N times for one answer."""
    row = conn.execute(
        "SELECT w.ra_deg, w.dec_deg, w.scale_arcsec_px, w.rotation_deg, w.width_deg, w.height_deg"
        " FROM frame_wcs w JOIN frames f ON f.id = w.frame_id"
        " WHERE f.object_id = ? ORDER BY f.id LIMIT 1",
        (object_id,),
    ).fetchone()
    return dict(row) if row else None


def frames_of(conn: sqlite3.Connection, object_id: int) -> list[int]:
    return [r[0] for r in conn.execute("SELECT id FROM frames WHERE object_id = ?", (object_id,))]


def raw_names_of(conn: sqlite3.Connection, object_id: int) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT object_raw FROM frames WHERE object_id = ? AND object_raw IS NOT NULL",
            (object_id,),
        )
    ]


def raw_names_with_objects(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Each (header spelling, object) once. Cleaning the spellings is the caller's job: here a
    palette word means nothing."""
    return [
        (r["object_raw"], r["object_id"])
        for r in conn.execute(
            "SELECT DISTINCT object_raw, object_id FROM frames"
            " WHERE object_raw IS NOT NULL AND object_id IS NOT NULL"
        )
    ]
