"""An Archive page: a row is a group of frames, a confirmed mosaic being one row. Rows and count
share one condition, and nothing from outside becomes SQL (`docs/domini/archivio.md`)."""

import sqlite3
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..db import idlist
from . import counts
from .declarations import MOSAIC_FIELD, EntityType
from .object_answer import CATALOG, NAME
from .objects import NAME_COLUMNS, subjects_of, subjects_sql, together

# Rows say only who they are; hours are counted after the filter, or the count would pay for them.
# The `NOT IN` uses the partial index; `object_id IS NOT NULL` since one NULL in it fails them all.
_OBJECTS = f"""
SELECT 'o:' || o.id AS row_key, o.id, NULL AS mosaic_key, o.catalog_slug, {NAME_COLUMNS},
       e.constellation, e.type_code, c.catalog, c.designation, NULL AS panels
FROM objects o
LEFT JOIN catalog_entries e ON e.slug = o.catalog_slug
LEFT JOIN catalog_names c ON c.slug = o.catalog_slug AND c.is_primary = 1
WHERE o.id NOT IN (SELECT f.object_id FROM frames f WHERE f.mosaic_key IS NOT NULL
                   AND f.copy_of IS NULL AND f.object_id IS NOT NULL)
   OR EXISTS (SELECT 1 FROM frames f WHERE f.object_id = o.id AND f.copy_of IS NULL
              AND {counts.ALONE})"""  # noqa: S608 - constant fragments of the spine

# The user's target, slug or written name; as in `read_target`, a blank target is not one.
_SLUG, _NAME = f"substr(d.value, {len(CATALOG) + 1})", f"substr(d.value, {len(NAME) + 1})"
_OF_SLUG = f"CASE WHEN d.value LIKE '{CATALOG}%' AND TRIM({_SLUG}) <> '' THEN {_SLUG} END"
_OF_NAME = f"CASE WHEN d.value LIKE '{NAME}%' AND TRIM({_NAME}) <> '' THEN {_NAME} END"

# Grouped first, so the answer is found by mosaic key on the `declarations` index. Constant
# fragments of the spine, hence the `noqa`.
_MOSAICS = f"""
SELECT 'm:' || g.mosaic_key AS row_key, NULL AS id, g.mosaic_key, t.slug AS catalog_slug,
       t.name AS primary_name, e.name AS catalog_name,
       e.constellation, e.type_code, c.catalog, c.designation, g.panels
FROM (SELECT f.mosaic_key, COUNT(DISTINCT f.panel_id) AS panels FROM frames f
      WHERE f.mosaic_key IS NOT NULL AND f.copy_of IS NULL GROUP BY f.mosaic_key) g
LEFT JOIN (SELECT d.entity_key, d.field, {_OF_SLUG} AS slug, {_OF_NAME} AS name
           FROM declarations d
           WHERE d.entity_type = '{EntityType.MOSAIC}' AND d.field = '{MOSAIC_FIELD}') t
       ON t.entity_key = g.mosaic_key
LEFT JOIN catalog_entries e ON e.slug = t.slug
LEFT JOIN catalog_names c ON c.slug = t.slug AND c.is_primary = 1"""  # noqa: S608

_ROWS = f"({_OBJECTS} UNION ALL {_MOSAICS}) r"


class Order(StrEnum):
    NAME = "name"
    HOURS = "hours"
    FRAMES = "frames"


# By name is catalog then number, or `M 13` would follow `M 103`; `NOCASE` or `vdB` follows `WR`.
# The row key always closes, or two consecutive pages could repeat or skip a row.
ORDERS = {
    Order.NAME: (
        "ORDER BY (r.catalog_slug IS NULL), r.catalog COLLATE NOCASE,"
        " CAST(r.designation AS INTEGER), r.designation COLLATE NOCASE,"
        " r.primary_name COLLATE NOCASE, r.row_key"
    ),
    Order.HOURS: f"{counts.ORDER_BY_TIME}, r.row_key",
    Order.FRAMES: "ORDER BY frames DESC, integration_s DESC, r.row_key",
}

# An object row's objects are itself, even without frames, or a catalog filter would lose it;
# panels are looked up only for a mosaic, elsewhere the search would find nothing new.
_ROW_FRAMES = f"f.copy_of IS NULL AND {counts.of(counts.Subject.ROW)}"
_IN_ROW_PANELS = (
    "r.mosaic_key IS NOT NULL AND o2.id IN (SELECT f.object_id FROM frames f"  # noqa: S608
    f" WHERE f.copy_of IS NULL AND {counts.of(counts.Subject.MOSAIC)})"
)
_ROW_OBJECTS = f"(o2.id = r.id OR ({_IN_ROW_PANELS}))"

# One frame is enough: the question is "what did I shoot in Ha", not "mostly in Ha". `{scope}`
# asks it of the frames the row counts: "Lum in 2025" is one frame, not one of each.
_WITH_FILTER = (
    "EXISTS (SELECT 1 FROM frames f JOIN filters x ON x.id = f.filter_id"  # noqa: S608
    f" WHERE {_ROW_FRAMES}{{scope}} AND x.name = ?)"
)
# Narrowed by period, site or gear, a row passes with a frame of its own in it; an object never
# shot has none, and goes.
_IN_SCOPE = f"EXISTS (SELECT 1 FROM frames f WHERE {_ROW_FRAMES}{{scope}})"  # noqa: S608
# For a mosaic, start from its frames (`CROSS JOIN` fixes the order), or SQLite would start from
# the chosen catalog's thousands of entries, for every mosaic.
_FROM_PANELS = (
    "r.mosaic_key IS NOT NULL AND EXISTS (SELECT 1 FROM frames f CROSS JOIN objects o2"  # noqa: S608
    " CROSS JOIN {table} WHERE f.copy_of IS NULL AND " + counts.of(counts.Subject.MOSAIC) +
    " AND o2.id = f.object_id AND {link} AND {column} = ?)"
)  # fmt: skip
_OF_CATALOG = (
    "(r.catalog = ? OR ("
    + _FROM_PANELS.format(  # noqa: S608 - constants
        table="catalog_names c2",
        link="c2.slug = o2.catalog_slug AND c2.is_primary = 1",
        column="c2.catalog",
    )
    + "))"
)
_IN_CONSTELLATION = (
    "(r.constellation = ? OR ("
    + _FROM_PANELS.format(  # noqa: S608
        table="catalog_entries e2", link="e2.slug = o2.catalog_slug", column="e2.constellation"
    )
    + "))"
)

# ASCII only, as SQLite's `LOWER()`: half of a rule that lives on both sides.
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

FOLDED = "REPLACE(LOWER({}), ' ', '') LIKE ? ESCAPE '\\'"
# Any name of object `{o}`, its own or its catalog's designations; the search bar asks it too.
NAMED = (
    "(EXISTS (SELECT 1 FROM object_names n WHERE n.object_id = {o}.id AND "  # noqa: S608
    + FOLDED.format("n.name") + ")"
    " OR EXISTS (SELECT 1 FROM catalog_names k WHERE k.slug = {o}.catalog_slug AND "
    + FOLDED.format("k.catalog || k.designation") + "))"
)  # fmt: skip
_SEARCHED = (
    "(EXISTS (SELECT 1 FROM objects o2 WHERE " + _ROW_OBJECTS +  # noqa: S608
    " AND " + NAMED.format(o="o2") + ")"
    " OR " + FOLDED.format("r.primary_name") +
    " OR EXISTS (SELECT 1 FROM catalog_names k WHERE k.slug = r.catalog_slug AND "
    + FOLDED.format("k.catalog || k.designation") + "))"
)  # fmt: skip
# A row's key, read as `key` and narrowed by `Criteria.key`: a mosaic's, else `objects.stable_key`.
_KEY = "COALESCE(r.mosaic_key, r.catalog_slug, r.primary_name, r.catalog_name)"


def folded(q: str | None) -> str | None:
    """The `LIKE` pattern for `FOLDED`; `None` for blanks, or `LIKE '%   %'` would find nothing.
    `%` and `_` are escaped: who types them is looking for those signs."""
    typed = (q or "").strip().translate(_ASCII_LOWER).replace(" ", "")
    if not typed:
        return None
    escaped = typed.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _searching(q: str | None) -> tuple[str, list[str]]:
    pattern = folded(q)
    if pattern is None:
        return "", []
    return _SEARCHED, [pattern] * _SEARCHED.count("LIKE ?")


@dataclass(frozen=True)
class Criteria:
    """What the bar asks. `q`, `key` (one row), catalog and constellation ask the row; the filter
    and `scope` its frames, and `scope` also narrows what the row counts."""

    q: str | None = None
    key: str | None = None
    catalog: str | None = None
    constellation: str | None = None
    filter_name: str | None = None
    mosaic: bool = False
    scope: counts.Scope = field(default_factory=counts.Scope)


def _where(c: Criteria) -> tuple[str, list[Any]]:
    parts, values = ["1 = 1"], []
    if c.mosaic:
        parts.append("r.mosaic_key IS NOT NULL")
    searched, its_values = _searching(c.q)
    if searched:
        parts.append(searched)
        values += its_values
    if c.key:
        parts.append(f"{_KEY} = ?")
        values.append(c.key)
    for part, value in ((_OF_CATALOG, c.catalog), (_IN_CONSTELLATION, c.constellation)):
        if value:
            parts.append(part)
            values += [value, value]
    narrowed, scope_values = c.scope.sql
    if narrowed:
        parts.append(_IN_SCOPE.format(scope=narrowed))
        values += scope_values
    if c.filter_name:
        parts.append(_WITH_FILTER.format(scope=narrowed))
        values += [*scope_values, c.filter_name]
    return " AND ".join(parts), values


def page(
    conn: sqlite3.Connection,
    *,
    limit: int,
    offset: int,
    sort: Order = Order.NAME,
    **conditions: Any,
) -> tuple[list[dict[str, Any]], int]:
    """The rows and how many pass `Criteria(**conditions)`: the page decides on it whether another
    follows. Hours, and the order by hours, are the scope's."""
    order = ORDERS[sort]  # from a closed list: nothing from outside becomes `ORDER BY`
    criteria = Criteria(**conditions)
    where, values = _where(criteria)
    narrowed, scope_values = criteria.scope.sql
    hours = counts.counts_on(counts.Subject.ROW, narrowed)
    rows = conn.execute(
        f"SELECT r.*, {_KEY} AS key, {hours} FROM {_ROWS} WHERE {where} {order} LIMIT ? OFFSET ?",  # noqa: S608
        (*scope_values * 3, *values, limit, offset),
    )
    total = conn.execute(
        f"SELECT COUNT(*) FROM {_ROWS} WHERE {where}",  # noqa: S608 - `where` are placeholders
        values,
    ).fetchone()[0]
    return [dict(r) for r in rows], total


def found(conn: sqlite3.Connection, **conditions: Any) -> dict[str, int]:
    """Objects and mosaics apart: the on-screen count does not call a mosaic an object."""
    where, values = _where(Criteria(**conditions))
    # `where` are placeholders, hence the `noqa`
    sql = (
        "SELECT COALESCE(SUM(r.mosaic_key IS NULL), 0), COALESCE(SUM(r.mosaic_key IS NOT NULL), 0)"  # noqa: S608
        f" FROM {_ROWS} WHERE {where}"
    )
    n_objects, n_mosaics = conn.execute(sql, values).fetchone()
    return {"objects": n_objects, "mosaics": n_mosaics}


# The first good frame per filter is enough, and the `frames.filter_id` index keeps the search
# short; a `JOIN` with `DISTINCT` would read them all.
FILTERS_USED = (
    "SELECT x.name FROM filters x WHERE EXISTS (SELECT 1 FROM frames f WHERE f.filter_id = x.id"
    " AND f.object_id IS NOT NULL AND f.copy_of IS NULL) ORDER BY x.name COLLATE NOCASE"
)


# Frames that belong to a row: an object's, or a mosaic's even on a panel without one.
_SHOT = "(f.object_id IS NOT NULL OR f.mosaic_key IS NOT NULL) AND f.copy_of IS NULL"
_YEARS = (
    "SELECT DISTINCT substr(n.night_date, 1, 4) FROM nights n"  # noqa: S608 - constants
    f" WHERE EXISTS (SELECT 1 FROM frames f WHERE f.night_id = n.id AND {_SHOT}) ORDER BY 1 DESC"
)
_SITES = (
    "SELECT s.id, s.name FROM sites s WHERE EXISTS (SELECT 1 FROM nights n"  # noqa: S608
    f" JOIN frames f ON f.night_id = n.id WHERE n.site_id = s.id AND {_SHOT})"
    " ORDER BY s.name COLLATE NOCASE"
)
# Through the rig, as `Scope` narrows; `{column}` is `optics_id` or `camera_id`.
_PIECES = (
    "SELECT i.id, i.name FROM instruments i WHERE EXISTS (SELECT 1 FROM rigs g"  # noqa: S608
    f" JOIN frames f ON f.rig_id = g.id WHERE g.{{column}} = i.id AND {_SHOT})"
    " ORDER BY i.name COLLATE NOCASE"
)


def _picks(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    """`{id, name}`, or none if only one: choosing the only site narrows nothing."""
    picks = [{"id": r[0], "name": r[1]} for r in conn.execute(sql)]
    return picks if len(picks) > 1 else []


def choices(conn: sqlite3.Connection) -> dict[str, Any]:
    """What the archive holds, not what the catalog knows; `NOCASE` like the rows, and the user's
    filter names mix case for sure."""
    return {
        "catalogs": _column(
            conn,
            "SELECT DISTINCT c.catalog FROM objects o"
            " JOIN catalog_names c ON c.slug = o.catalog_slug AND c.is_primary = 1"
            " ORDER BY c.catalog COLLATE NOCASE",
        ),
        "constellations": _column(
            conn,
            "SELECT DISTINCT e.constellation FROM objects o"
            " JOIN catalog_entries e ON e.slug = o.catalog_slug"
            " ORDER BY e.constellation COLLATE NOCASE",
        ),
        # filters that shot an object: one owned and never used narrows nothing
        "filters": _column(conn, FILTERS_USED),
        # the user's nights, latest first: the period offers years and dates of your choosing
        "years": _column(conn, _YEARS),
        "sites": _picks(conn, _SITES),
        "optics": _picks(conn, _PIECES.format(column="optics_id")),
        "cameras": _picks(conn, _PIECES.format(column="camera_id")),
        # offered to whoever has a confirmed mosaic: the partial index says so at once
        "mosaics": conn.execute(
            "SELECT EXISTS (SELECT 1 FROM frames WHERE mosaic_key IS NOT NULL)"
        ).fetchone()[0]
        == 1,
    }


# By framing, with the centre `group` wrote, counted like every row, longest first.
_PANELS = f"""
SELECT f.mosaic_key, f.panel_id, p.ra_deg, p.dec_deg, {counts.AGGREGATE}, {counts.UNTIMED}
FROM frames f JOIN panels p ON p.id = f.panel_id
WHERE f.mosaic_key IN {{listed}} AND f.copy_of IS NULL{{scope}}
GROUP BY f.mosaic_key, f.panel_id
{counts.ORDER_BY_TIME}, f.panel_id"""  # noqa: S608 - constant fragments, `listed` a placeholder
_PANEL_OBJECTS = subjects_sql("f.panel_id", where="AND f.mosaic_key IN {listed}")


def panels(
    conn: sqlite3.Connection, keys: list[str], scope: counts.Scope | None = None
) -> dict[Any, list[Any]]:
    """`{mosaic key: [panel]}`, two queries per page; no object, null `object`, no invented name.
    A `scope` keeps the panels shot in it, counted like their row."""
    if not keys:
        return {}  # the page of whoever has no mosaics, nearly all: no query
    with idlist.holding(conn, keys) as held:
        names = subjects_of(conn.execute(_PANEL_OBJECTS.format(listed=held)))
    narrowed, values = (scope or counts.Scope()).sql
    return idlist.grouped(
        conn,
        (_PANELS.format(listed="{listed}", scope=narrowed), values),
        keys,
        "mosaic_key",
        lambda r: {
            "object": together(names.get(r["panel_id"], [])) or None,
            "ra_deg": r["ra_deg"],
            "dec_deg": r["dec_deg"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
        },
    )


def _column(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [r[0] for r in conn.execute(sql)]
