"""The Archive's nine criteria (archivio.md): each option counted by `archive.where`, the other
choices on; offered from two options up, or while one is chosen."""

import sqlite3
from dataclasses import replace
from enum import StrEnum
from typing import Any

from . import archive, counts, filters_used
from .archive import Criteria, Family, Form


class Key(StrEnum):
    """In the sheet's order (Archivio.dc.html 140)."""

    YEAR = "year"
    TYPE = "type"
    CONSTELLATION = "constellation"
    FILTER = "filter"
    FORM = "form"
    SITE = "site"
    OPTICS = "optics"
    CAMERA = "camera"
    CATALOG = "catalog"


# Asked of a frame of the row: one pass over the frames, by option and row (`_frame_counts`).
_ON_FRAMES = {Key.YEAR, Key.SITE, Key.OPTICS, Key.CAMERA, Key.FILTER}
_IN_SCOPE = {Key.YEAR: "years", Key.SITE: "sites", Key.OPTICS: "optics", Key.CAMERA: "cameras"}
_IN_CRITERIA = {
    Key.TYPE: "types",
    Key.CONSTELLATION: "constellations",
    Key.FILTER: "filters",
    Key.FORM: "forms",
    Key.CATALOG: "catalogs",
}

# (value, label, order, owner, link) of what the frames carry: the small table that holds the
# value, and how a frame `f` reaches it.
_FRAME_FACTS = {
    Key.YEAR: (
        "substr(n.night_date, 1, 4)", "NULL", "1 DESC", "nights n", "f.night_id = n.id",
    ),
    Key.SITE: (
        "CAST(s.id AS TEXT)", "s.name", "s.name COLLATE NOCASE, s.id",
        "sites s JOIN nights n ON n.site_id = s.id", "f.night_id = n.id",
    ),
    Key.OPTICS: (
        "CAST(i.id AS TEXT)", "i.name", "i.name COLLATE NOCASE, i.id",
        "instruments i JOIN rigs g ON g.optics_id = i.id", "f.rig_id = g.id",
    ),
    Key.CAMERA: (
        "CAST(i.id AS TEXT)", "i.name", "i.name COLLATE NOCASE, i.id",
        "instruments i JOIN rigs g ON g.camera_id = i.id", "f.rig_id = g.id",
    ),
    Key.FILTER: (
        "x.name", "NULL", filters_used.order_by("x"), "filters x", "f.filter_id = x.id",
    ),
}  # fmt: skip

# The frames of the rows, one line per row, night, rig and filter: everything a frame-level
# option asks, read once for the nine criteria instead of once per criterion.
_SHOT_GROUPS = (
    f"shot AS MATERIALIZED (SELECT {archive.ROW_OF_FRAME} AS row_key,"  # noqa: S608 - constants
    f" f.night_id, f.rig_id, f.filter_id FROM frames f WHERE {archive.SHOT} GROUP BY 1, 2, 3, 4)"
)

# A row's own value, and its panels' for a mosaic, as `archive._row_or_panel` asks them. `CROSS
# JOIN` starts from the mosaics' frames, or SQLite walks every object's frames.
_PANEL_FRAMES = (
    "FROM frames f CROSS JOIN objects o2 ON o2.id = f.object_id {join}"
    " WHERE f.mosaic_key IS NOT NULL AND f.copy_of IS NULL"
)
_ROW_FACTS = {
    Key.CATALOG: (
        "r.catalog", "c2.catalog",
        "JOIN catalog_names c2 ON c2.slug = o2.catalog_slug AND c2.is_primary = 1",
    ),
    Key.CONSTELLATION: (
        "r.constellation", "e2.constellation",
        "JOIN catalog_entries e2 ON e2.slug = o2.catalog_slug",
    ),
    Key.TYPE: (
        archive.family_sql("r.type_code"), archive.family_sql("e2.type_code"),
        "JOIN catalog_entries e2 ON e2.slug = o2.catalog_slug",
    ),
}  # fmt: skip
_ROWS = archive.ROWS


def _form(is_mosaic: str, made: str) -> str:
    """The form, as `archive._FORMS` says it; `made` (the productions) asked once."""
    return (
        f"CASE WHEN {is_mosaic} THEN '{Form.MOSAIC}' ELSE CASE MIN({made}, 2)"
        f" WHEN 1 THEN '{Form.ONE}' WHEN 2 THEN '{Form.SEVERAL}' END END"
    )


def choosing(criteria: Criteria, key: Key, values: tuple[str, ...]) -> Criteria:
    """`criteria` with `values` in place of what `key` chose: ids read as numbers."""
    if key in _IN_SCOPE:
        typed = values if key == Key.YEAR else tuple(int(v) for v in values)
        return replace(criteria, scope=replace(criteria.scope, **{_IN_SCOPE[key]: typed}))
    return replace(criteria, **{_IN_CRITERIA[key]: values})


def chosen_of(criteria: Criteria, key: Key) -> tuple[str, ...]:
    if key in _IN_SCOPE:
        return tuple(str(v) for v in getattr(criteria.scope, _IN_SCOPE[key]))
    return tuple(str(v) for v in getattr(criteria, _IN_CRITERIA[key]))


def _frame_universe(conn: sqlite3.Connection, key: Key) -> list[dict[str, Any]]:
    """From the small table: a value is held as soon as one frame of a row reaches it."""
    value, label, order, owner, link = _FRAME_FACTS[key]
    sql = (
        f"SELECT {value} AS value, {label} AS label FROM {owner}"  # noqa: S608 - constants
        f" WHERE {value} IS NOT NULL AND EXISTS (SELECT 1 FROM frames f WHERE {link}"
        f" AND {archive.SHOT}) GROUP BY 1 ORDER BY {order}"
    )
    return [dict(r) for r in conn.execute(sql)]


_A_MOSAIC = "substr(f.row_key, 1, 2) = 'm:'"  # the key `archive.ROW_OF_FRAME` gives a mosaic


def _frame_branch(key: Key, criteria: Criteria) -> tuple[str, list[Any]]:
    """Every option of a frame-level key, over `shot`: an option's frames of a row are the scope
    `where` would narrow to, so filter and form are asked of them, as `where` asks them."""
    value, _, _, owner, link = _FRAME_FACTS[key]
    others = choosing(criteria, key, ())
    narrowed, scope_values = others.scope.sql
    asked = others.filters if key != Key.FILTER else ()
    forms = others.forms if key != Key.FILTER else ()
    # a filter does not move the scope: the rest of `where` holds as it is
    rest = others if key == Key.FILTER else replace(others, filters=(), forms=())
    cond, values = archive.where(rest)
    with_filter = (
        f"f.filter_id IN (SELECT x.id FROM filters x WHERE x.name IN ({counts.marks(asked)}))"  # noqa: S608
        if asked
        else "1"
    )
    in_form = (
        f"{_form(_A_MOSAIC, f'COUNT(DISTINCT {archive.PAIR})')} IN ({counts.marks(forms)})"
        if forms
        else "1"
    )
    sql = (
        f"SELECT '{key}' AS key, value, COUNT(*) AS rows FROM (SELECT {value} AS value,"  # noqa: S608
        f" f.row_key, {in_form} AS in_form, MAX({with_filter}) AS with_filter"
        f" FROM {owner}, shot f LEFT JOIN rigs pg ON pg.id = f.rig_id"
        f" WHERE {link} AND {value} IS NOT NULL{narrowed}"
        f" AND f.row_key IN (SELECT r.row_key FROM {_ROWS} WHERE {cond})"
        f" GROUP BY 1, 2) WHERE with_filter AND in_form GROUP BY value"
    )
    return sql, [*forms, *asked, *scope_values, *values]


def _frame_counts(conn: sqlite3.Connection, criteria: Criteria) -> dict[Key, dict[str, int]]:
    """The five frame-level keys in one statement, over the frames read once."""
    branches = [_frame_branch(key, criteria) for key in Key if key in _ON_FRAMES]
    sql = f"WITH {_SHOT_GROUPS} " + " UNION ALL ".join(s for s, _ in branches)
    out: dict[Key, dict[str, int]] = {key: {} for key in Key if key in _ON_FRAMES}
    for key, value, rows in conn.execute(sql, [v for _, values in branches for v in values]):
        out[Key(key)][value] = rows
    return out


def _row_values(key: Key, criteria: Criteria) -> tuple[str, list[Any]]:
    """`(row_key, value)` of every row, for a row-level key; the form reads the scope."""
    if key == Key.FORM:
        narrowed, values = criteria.scope.sql
        form = _form("r.mosaic_key IS NOT NULL", archive.PRODUCTIONS.format(scope=narrowed))
        return f"SELECT r.row_key, {form} AS value FROM {_ROWS}", values  # noqa: S608
    own, panel, join = _ROW_FACTS[key]
    sql = (
        f"SELECT r.row_key, {own} AS value FROM {_ROWS} UNION"  # noqa: S608 - constants
        f" SELECT 'm:' || f.mosaic_key, {panel} " + _PANEL_FRAMES.format(join=join)
    )
    return sql, []


def _row_counts(conn: sqlite3.Connection, key: Key, criteria: Criteria) -> dict[str, int]:
    """Every option of a row-level key in one query: rows passing the others, by their values."""
    others = choosing(criteria, key, ())
    cond, where_values = archive.where(others)
    facts, fact_values = _row_values(key, criteria)
    sql = (
        f"SELECT v.value, COUNT(DISTINCT r.row_key) FROM {_ROWS} JOIN ({facts}) v"  # noqa: S608
        f" ON v.row_key = r.row_key WHERE v.value IS NOT NULL AND {cond} GROUP BY v.value"
    )
    return dict(conn.execute(sql, [*fact_values, *where_values]).fetchall())


def _options(
    conn: sqlite3.Connection, key: Key, criteria: Criteria, on_frames: dict[Key, dict[str, int]]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """The options the archive holds, in order, and each one's rows under `criteria`."""
    if key in _ON_FRAMES:
        return _frame_universe(conn, key), on_frames[key]
    held_rows = _row_counts(conn, key, Criteria())
    order: list[str] = list(Family) if key == Key.TYPE else list(Form) if key == Key.FORM else []
    values = sorted(held_rows, key=lambda v: (order.index(v) if v in order else 0, v.casefold()))
    # nothing else chosen: the counts are what the archive holds, already asked
    alone = choosing(criteria, key, ()) == Criteria()
    rows = held_rows if alone else _row_counts(conn, key, criteria)
    return [{"value": v, "label": None} for v in values], rows


def offered(conn: sqlite3.Connection, criteria: Criteria) -> list[dict[str, Any]]:
    """`[{key, options: [{value, label, passband, rows, chosen}]}]`: a chosen option nobody holds
    stays listed, chosen, at zero, or it could not be taken off."""
    passbands = {r[0]: r[1] for r in conn.execute("SELECT name, passband FROM filters")}
    on_frames = _frame_counts(conn, criteria)
    out = []
    for key in Key:
        held, rows = _options(conn, key, criteria, on_frames)
        chosen = chosen_of(criteria, key)
        held_values = {o["value"] for o in held}
        listed = held + [{"value": v, "label": None} for v in chosen if v not in held_values]
        if len(listed) < 2 and not chosen:
            continue
        out.append(
            {
                "key": key,
                "options": [
                    {
                        **o,
                        "passband": passbands.get(o["value"]) if key == Key.FILTER else None,
                        "rows": rows.get(o["value"], 0),
                        "chosen": o["value"] in chosen,
                    }
                    for o in listed
                ],
            }
        )
    return out
