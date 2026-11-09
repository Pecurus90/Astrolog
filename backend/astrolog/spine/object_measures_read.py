"""An Archive row's measures, read: the sets `night_measures.py` wrote for it, its nights as the
groups, and its frames one by one. Nothing computed here."""

import sqlite3
from typing import Any

from ..night_measures import JOINS
from . import counts, filters_used
from .night_measures_read import SERIES, SERIES_ORDER, SERIES_WHERE, filters, frame, sets
from .object_detail import frames_of


def object_measures(
    conn: sqlite3.Connection, row: dict[str, Any], scope: counts.Scope
) -> dict[str, Any]:
    """`row` is `archive.page`'s; `scope` one of its productions or of its panels, or all."""
    production = scope.production
    on_g, values = _where(row, scope)
    groups = conn.execute(f"SELECT * FROM object_measure_groups g WHERE {on_g}", values).fetchall()  # noqa: S608 - ours
    rows = conn.execute(f"SELECT * FROM object_measures g WHERE {on_g}", values).fetchall()  # noqa: S608 - ours
    nights = conn.execute(
        "SELECT g.night_id, g.frames, g.pending, n.night_date FROM object_measure_groups g"  # noqa: S608 - ours
        f" JOIN nights n ON n.id = g.night_id WHERE {on_g}"
        " AND g.filter_id IS NULL AND g.unfiltered = 0 ORDER BY n.night_date, g.night_id",
        values,
    ).fetchall()
    found = conn.execute(
        "SELECT g.frames, g.unfiltered, x.id, x.name, x.passband FROM object_measure_groups g"  # noqa: S608 - ours
        f" LEFT JOIN filters x ON x.id = g.filter_id WHERE {on_g}"
        " AND g.night_id IS NULL AND (g.filter_id IS NOT NULL OR g.unfiltered = 1)"
        f" ORDER BY g.unfiltered, {filters_used.order_by('x')}",
        values,
    ).fetchall()
    names = {r["id"]: r["name"] for r in found if not r["unfiltered"]}
    series = _series(conn, row, scope, names)
    whole = next(
        (g for g in groups if g["night_id"] is None and g["filter_id"] is None
         and not g["unfiltered"]),
        None,
    )  # fmt: skip
    return {
        "key": row["key"],
        # not written yet (a scan still running): every frame is still to be measured
        "frames": whole["frames"] if whole else len(series),
        "pending": whole["pending"] if whole else len(series),
        "one_production": production is not None or _productions(conn, row) <= 1,
        "groups": [
            {
                "key": str(n["night_id"]),
                "name": None,
                "night_date": n["night_date"],
                "frames": n["frames"],
                "pending": n["pending"],
            }
            for n in nights
        ],  # fmt: skip
        "filters": filters(found),
        "sets": sets(groups, rows, "night_id", _night_key, names),
        "series": series,
    }


def _night_key(g: sqlite3.Row) -> str | None:
    return None if g["night_id"] is None else str(g["night_id"])


def _owner(row: dict[str, Any]) -> tuple[int | None, str | None]:
    return (None, row["mosaic_key"]) if row["mosaic_key"] else (row["id"], None)


def _where(row: dict[str, Any], scope: counts.Scope) -> tuple[str, list[Any]]:
    """On `object_measures` or its groups, as `g`."""
    production = scope.production
    where = "g.object_id IS ? AND g.mosaic_key IS ? AND g.panel_id IS ? AND g.every_production = ?"
    values: list[Any] = [*_owner(row), scope.panel, int(production is None)]
    if production is not None:
        where += " AND g.optics_id IS ? AND g.camera_id IS ?"
        values += list(production)
    return where, values


def _productions(conn: sqlite3.Connection, row: dict[str, Any]) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM object_measure_groups WHERE object_id IS ? AND mosaic_key IS ?"
        " AND panel_id IS NULL AND every_production = 0 AND night_id IS NULL AND filter_id IS NULL"
        " AND unfiltered = 0",
        _owner(row),
    ).fetchone()[0]


def _series(
    conn: sqlite3.Connection,
    row: dict[str, Any],
    scope: counts.Scope,
    names: dict[int, str],
) -> list[dict[str, Any]]:
    narrowed, values = frames_of(row, scope)
    found = conn.execute(
        f"{SERIES}, s.timezone FROM frames f{JOINS}"
        " JOIN nights n ON n.id = f.night_id JOIN sites s ON s.id = n.site_id"
        f" WHERE {SERIES_WHERE}{narrowed} {SERIES_ORDER}",
        values,
    )
    return [frame(r, str(r["night_id"]), names, r["timezone"]) for r in found]
