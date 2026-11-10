"""An Archive page: a row is a group of frames, a confirmed mosaic being one row. Rows and count
share one condition, and nothing from outside becomes SQL (`docs/domini/archivio.md`)."""

import sqlite3
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..db import idlist
from . import counts, filters_used
from .declarations import MOSAIC_FIELD, EntityType
from .object_answer import CATALOG, NAME
from .objects import NAME_COLUMNS, subjects_of, subjects_sql, together

# Rows say only who they are; hours are counted after the filter, or the count would pay for them.
# The `NOT IN` uses the partial index; `object_id IS NOT NULL` since one NULL in it fails them all.
_OBJECTS = f"""
SELECT 'o:' || o.id AS row_key, o.id, NULL AS mosaic_key, o.catalog_slug, {NAME_COLUMNS},
       e.constellation, e.type_code, e.common_name, c.catalog, c.designation, NULL AS panels
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
       e.constellation, e.type_code, e.common_name, c.catalog, c.designation, g.panels
FROM (SELECT f.mosaic_key, COUNT(DISTINCT f.panel_id) AS panels FROM frames f
      WHERE f.mosaic_key IS NOT NULL AND f.copy_of IS NULL GROUP BY f.mosaic_key) g
LEFT JOIN (SELECT d.entity_key, d.field, {_OF_SLUG} AS slug, {_OF_NAME} AS name
           FROM declarations d
           WHERE d.entity_type = '{EntityType.MOSAIC}' AND d.field = '{MOSAIC_FIELD}') t
       ON t.entity_key = g.mosaic_key
LEFT JOIN catalog_entries e ON e.slug = t.slug
LEFT JOIN catalog_names c ON c.slug = t.slug AND c.is_primary = 1"""  # noqa: S608

ROWS = f"({_OBJECTS} UNION ALL {_MOSAICS}) r"


class Order(StrEnum):
    NAME = "name"
    HOURS = "hours"
    RECENT = "recent"


# By name is catalog then number, or `M 13` would follow `M 103`; `NOCASE` or `vdB` follows `WR`.
# The row key always closes, or two consecutive pages could repeat or skip a row.
ORDERS = {
    Order.NAME: (
        "ORDER BY (r.catalog_slug IS NULL), r.catalog COLLATE NOCASE,"
        " CAST(r.designation AS INTEGER), r.designation COLLATE NOCASE,"
        " r.primary_name COLLATE NOCASE, r.row_key"
    ),
    Order.HOURS: f"{counts.ORDER_BY_TIME}, r.row_key",
    # a row with no night goes last: it was never shot, or its frames do not say when
    Order.RECENT: "ORDER BY last_night IS NULL, last_night DESC, r.row_key",
}


class Family(StrEnum):
    """What kind of thing, by family (archivio.md): the catalog's code is too fine to choose by."""

    GALAXY = "galaxy"
    NEBULA = "nebula"
    CLUSTER = "cluster"
    STAR = "star"
    OTHER = "other"
    UNKNOWN = "unknown"  # the catalog does not know the row


# The catalog's codes (schema.sql, catalog_entries.type_code); one missing here reads "other".
TYPE_FAMILY: dict[str, Family] = {
    **dict.fromkeys(("GALAXY", "GALAXY_PAIR", "GALAXY_GROUP", "GALAXY_CLUSTER"), Family.GALAXY),
    **dict.fromkeys(
        (
            "NEBULA",
            "DARK_NEBULA",
            "EMISSION_NEBULA",
            "REFLECTION_NEBULA",
            "PLANETARY_NEBULA",
            "HII_REGION",
            "SUPERNOVA_REMNANT",
        ),
        Family.NEBULA,
    ),  # fmt: skip
    **dict.fromkeys(("OPEN_CLUSTER", "GLOBULAR_CLUSTER", "STAR_CLUSTER"), Family.CLUSTER),
    **dict.fromkeys(("STAR", "DOUBLE_STAR", "NOVA_WR"), Family.STAR),
}


def family_sql(column: str) -> str:
    """The family of a `type_code` column, in SQL; constants only, so no placeholder."""
    cases = "".join(
        f" WHEN {column} IN ({', '.join(repr(c) for c, f in TYPE_FAMILY.items() if f == fam)})"
        f" THEN '{fam}'"
        for fam in dict.fromkeys(TYPE_FAMILY.values())
    )
    return f"(CASE WHEN {column} IS NULL THEN '{Family.UNKNOWN}'{cases} ELSE '{Family.OTHER}' END)"


class Form(StrEnum):
    """How many productions a row has, or whether it is a mosaic (sheet, "Produzioni")."""

    ONE = "one"
    SEVERAL = "several"
    MOSAIC = "mosaic"


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
    f" WHERE {_ROW_FRAMES}{{scope}} AND x.name IN ({{marks}}))"
)
# Narrowed by period, site or gear, a row passes with a frame of its own in it; an object never
# shot has none, and goes.
_IN_SCOPE = f"EXISTS (SELECT 1 FROM frames f WHERE {_ROW_FRAMES}{{scope}})"  # noqa: S608
# For a mosaic, start from its frames (`CROSS JOIN` fixes the order), or SQLite would start from
# the chosen catalog's thousands of entries, for every mosaic.
_FROM_PANELS = (
    "r.mosaic_key IS NOT NULL AND EXISTS (SELECT 1 FROM frames f CROSS JOIN objects o2"  # noqa: S608
    " CROSS JOIN {table} WHERE f.copy_of IS NULL AND " + counts.of(counts.Subject.MOSAIC) +
    " AND o2.id = f.object_id AND {link} AND {column} IN ({marks}))"
)  # fmt: skip
_NAMES, _ENTRIES = "catalog_names c2", "catalog_entries e2"
_NAME_LINK, _ENTRY_LINK = (
    "c2.slug = o2.catalog_slug AND c2.is_primary = 1",
    "e2.slug = o2.catalog_slug",
)
# (row column, panel table, panel link, panel column): the row's own value, or a panel's.
_ROW_OR_PANEL = {
    "catalogs": ("r.catalog", _NAMES, _NAME_LINK, "c2.catalog"),
    "constellations": ("r.constellation", _ENTRIES, _ENTRY_LINK, "e2.constellation"),
    "types": (family_sql("r.type_code"), _ENTRIES, _ENTRY_LINK, family_sql("e2.type_code")),
}
# How many optics and camera pairs the row's frames have, as `productions.py` groups them.
PAIR = "COALESCE(pg.optics_id, 0) || ':' || COALESCE(pg.camera_id, 0)"
PRODUCTIONS = (
    f"(SELECT COUNT(DISTINCT {PAIR})"  # noqa: S608
    f" FROM frames f LEFT JOIN rigs pg ON pg.id = f.rig_id WHERE {_ROW_FRAMES}{{scope}})"
)
_FORMS = {
    Form.MOSAIC: "r.mosaic_key IS NOT NULL",
    Form.ONE: f"(r.mosaic_key IS NULL AND {PRODUCTIONS} = 1)",
    Form.SEVERAL: f"(r.mosaic_key IS NULL AND {PRODUCTIONS} > 1)",
}


# The latest night of the frames the row counts: the order "Piu' recenti".
_LAST_NIGHT = (
    "(SELECT MAX(n.night_date) FROM frames f JOIN nights n ON n.id = f.night_id"  # noqa: S608
    f" WHERE {_ROW_FRAMES}{{scope}}) AS last_night"
)


def _row_or_panel(field_name: str, chosen: tuple[str, ...]) -> tuple[str, list[Any]]:
    column, table, link, panel_column = _ROW_OR_PANEL[field_name]
    marks = counts.marks(chosen)
    panels = _FROM_PANELS.format(table=table, link=link, column=panel_column, marks=marks)
    return f"({column} IN ({marks}) OR ({panels}))", [*chosen, *chosen]


def _forms(chosen: tuple[Form, ...], narrowed: str, values: list[Any]) -> tuple[str, list[Any]]:
    """Either form: each with its own sub-select, each with the scope's values."""
    parts, out = [], []
    for form in chosen:
        sql = _FORMS[Form(form)]
        parts.append(sql.format(scope=narrowed))
        out += values * sql.count("{scope}")
    return "(" + " OR ".join(parts) + ")", out


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


def plain(q: str | None) -> str:
    """The typed text as `FOLDED` folds a column: ASCII lower case, no spaces."""
    return (q or "").strip().translate(_ASCII_LOWER).replace(" ", "")


def folded(q: str | None) -> str | None:
    """The `LIKE` pattern for `FOLDED`; `None` for blanks, or `LIKE '%   %'` would find nothing.
    `%` and `_` are escaped: who types them is looking for those signs."""
    typed = plain(q)
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
    """What the bar asks: q, key, catalogs, constellations, types, forms ask the row; filters and
    `scope` its frames. Values of one field are either, fields hold together."""

    q: str | None = None
    key: str | None = None
    catalogs: tuple[str, ...] = ()
    constellations: tuple[str, ...] = ()
    types: tuple[Family, ...] = ()
    forms: tuple[Form, ...] = ()
    filters: tuple[str, ...] = ()
    scope: counts.Scope = field(default_factory=counts.Scope)


def where(c: Criteria) -> tuple[str, list[Any]]:
    """The one rule a row passes by: the page, its count and every option's count ask it."""
    parts, values = ["1 = 1"], []
    searched, its_values = _searching(c.q)
    if searched:
        parts.append(searched)
        values += its_values
    if c.key:
        parts.append(f"{_KEY} = ?")
        values.append(c.key)
    for name in ("catalogs", "constellations", "types"):
        chosen = getattr(c, name)
        if chosen:
            part, its_values = _row_or_panel(name, tuple(chosen))
            parts.append(part)
            values += its_values
    narrowed, scope_values = c.scope.sql
    if c.forms:
        part, its_values = _forms(c.forms, narrowed, scope_values)
        parts.append(part)
        values += its_values
    if narrowed:
        parts.append(_IN_SCOPE.format(scope=narrowed))
        values += scope_values
    if c.filters:
        parts.append(_WITH_FILTER.format(scope=narrowed, marks=counts.marks(c.filters)))
        values += [*scope_values, *c.filters]
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
    cond, values = where(criteria)
    narrowed, scope_values = criteria.scope.sql
    hours = counts.counts_on(counts.Subject.ROW, narrowed)
    last = _LAST_NIGHT.format(scope=narrowed)
    rows = conn.execute(
        f"SELECT r.*, {_KEY} AS key, {hours}, {last} FROM {ROWS}"  # noqa: S608
        f" WHERE {cond} {order} LIMIT ? OFFSET ?",
        (*scope_values * 4, *values, limit, offset),
    )
    total = conn.execute(
        f"SELECT COUNT(*) FROM {ROWS} WHERE {cond}",  # noqa: S608 - `where` are placeholders
        values,
    ).fetchone()[0]
    return [dict(r) for r in rows], total


def found(conn: sqlite3.Connection, **conditions: Any) -> dict[str, int]:
    """Objects and mosaics apart: the on-screen count does not call a mosaic an object."""
    cond, values = where(Criteria(**conditions))
    # `where` are placeholders, hence the `noqa`
    sql = (
        "SELECT COALESCE(SUM(r.mosaic_key IS NULL), 0), COALESCE(SUM(r.mosaic_key IS NOT NULL), 0)"  # noqa: S608
        f" FROM {ROWS} WHERE {cond}"
    )
    n_objects, n_mosaics = conn.execute(sql, values).fetchone()
    return {"objects": n_objects, "mosaics": n_mosaics}


# Frames that belong to a row: an object's alone, or a mosaic's even on a panel without one.
SHOT = (
    "f.copy_of IS NULL AND (f.mosaic_key IS NOT NULL"
    " OR (f.object_id IS NOT NULL AND " + counts.ALONE + "))"
)
# The row a frame belongs to, as `ROWS` keys it.
ROW_OF_FRAME = (
    "CASE WHEN f.mosaic_key IS NOT NULL THEN 'm:' || f.mosaic_key ELSE 'o:' || f.object_id END"
)
_TOTALS = (
    f"SELECT {counts.AGGREGATE}, {counts.UNTIMED}, COUNT(DISTINCT f.night_id) AS nights"  # noqa: S608
    f" FROM frames f WHERE {SHOT}"
)
# Light frames that no object and no mosaic took: unsolved, or solved on a sky with nothing named.
_UNRESOLVED = (
    "f.copy_of IS NULL AND f.image_type = 'light' AND f.object_id IS NULL AND f.mosaic_key IS NULL"
)


def totals(conn: sqlite3.Connection) -> dict[str, Any]:
    """The whole archive, whatever the bar asks: rows, mosaics among them, frames, nights."""
    rows = found(conn)
    frames = dict(conn.execute(_TOTALS).fetchone())
    return {
        "rows": rows["objects"] + rows["mosaics"],
        "mosaics": rows["mosaics"],
        "frames": frames["frames"],
        "integration_s": frames["integration_s"],
        "untimed": frames["untimed"] or 0,
        "nights": frames["nights"],
    }


def unresolved(conn: sqlite3.Connection) -> dict[str, Any] | None:
    """The frames without an object, counted like a row, with filters; None if none."""
    head = dict(
        conn.execute(
            f"SELECT {counts.AGGREGATE}, {counts.UNTIMED} FROM frames f WHERE {_UNRESOLVED}"  # noqa: S608
        ).fetchone()
    )
    if not head["frames"]:
        return None
    by_filter = conn.execute(
        f"SELECT x.name, x.passband, {counts.AGGREGATE} FROM frames f"  # noqa: S608
        f" JOIN filters x ON x.id = f.filter_id WHERE {_UNRESOLVED}"
        f" GROUP BY x.id ORDER BY {filters_used.order_by('x')}"
    )
    return {**head, "filters": [dict(r) for r in by_filter]}


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
            "id": r["panel_id"],
            "object": together(names.get(r["panel_id"], [])) or None,
            "ra_deg": r["ra_deg"],
            "dec_deg": r["dec_deg"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
        },
    )
