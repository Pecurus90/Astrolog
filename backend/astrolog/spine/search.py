"""The search in the bar, a few per kind with how many in all. It reads what others wrote: the
Archive's rows, the Nights' counts, `gear_usage` (`docs/domini/navigazione.md`)."""

import re
import sqlite3
from datetime import date
from typing import Any

from . import archive, counts, inventory, objects

# The active languages' month names, full: an abbreviation like "mar" or "set" is also a word.
_MONTHS = {
    name: number
    for names in (
        "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre"
        " dicembre",
        "january february march april may june july august september october november december",
    )
    for number, name in enumerate(names.split(), start=1)
}

_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
_NUMERIC = re.compile(r"(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2}|\d{4}))?")
_DAY_MONTH = re.compile(r"(\d{1,2}) ([a-z]+)(?: (\d{4}))?")
_MONTH_DAY = re.compile(r"([a-z]+) (\d{1,2}),?(?: (\d{4}))?")
_MONTH = re.compile(r"([a-z]+)(?: (\d{4}))?")

# A year that does not count, for a day asked without one: leap, so 29/2 exists.
_ANY_YEAR = 2000


def _year(written: str | None) -> int | None:
    if written is None:
        return None
    return 2000 + int(written) if len(written) == 2 else int(written)


def _day(year: int | None, month: int, day: int | None) -> str | None:
    """`LIKE` pattern on `nights.night_date`, `_` where not written; `None` if no such day."""
    try:
        date(year or _ANY_YEAR, month, day or 1)
    except ValueError:
        return None
    y = f"{year:04d}" if year else "____"
    d = f"{day:02d}" if day else "__"
    return f"{y}-{month:02d}-{d}"


def _readings(typed: str) -> list[tuple[int | None, int, int | None]]:
    """(year, month, day) the text can mean. `5/6` means both, day/month and month/day: the
    search does not know where the user learned to write dates."""
    if m := _ISO.fullmatch(typed):
        return [(int(m[1]), int(m[2]), int(m[3]))]
    if m := _NUMERIC.fullmatch(typed):
        a, b, year = int(m[1]), int(m[2]), _year(m[3])
        return list(dict.fromkeys([(year, b, a), (year, a, b)]))
    if (m := _DAY_MONTH.fullmatch(typed)) and m[2] in _MONTHS:
        return [(_year(m[3]), _MONTHS[m[2]], int(m[1]))]
    if (m := _MONTH_DAY.fullmatch(typed)) and m[1] in _MONTHS:
        return [(_year(m[3]), _MONTHS[m[1]], int(m[2]))]
    if (m := _MONTH.fullmatch(typed)) and m[1] in _MONTHS:
        return [(_year(m[2]), _MONTHS[m[1]], None)]
    return []


def night_dates(q: str) -> list[str]:
    """`LIKE` patterns of the dates `q` writes, in the common forms; none if it is not a date."""
    typed = " ".join(q.lower().split())
    found = (_day(y, m, d) for y, m, d in _readings(typed) if 1 <= m <= 12)
    return [p for p in found if p is not None]


def _objects(conn: sqlite3.Connection, q: str, limit: int) -> tuple[list[dict[str, Any]], int]:
    """The Archive's rows for `q`, most time first; the catalog's common name beside the name."""
    rows, total = archive.page(conn, limit=limit, offset=0, sort=archive.Order.HOURS, q=q)
    slugs = [r["catalog_slug"] for r in rows if r["catalog_slug"]]
    marks = ", ".join("?" * len(slugs))  # segnaposto-ok: at most `limit` (20) rows
    common = dict(
        conn.execute(
            f"SELECT slug, common_name FROM catalog_entries WHERE slug IN ({marks})",  # noqa: S608
            slugs,
        ).fetchall()
    )
    items = []
    for r in rows:
        name = objects.display_name(r)
        other = common.get(r["catalog_slug"])
        items.append(
            {
                "key": r["key"],
                "name": name,
                "common_name": other if other != name else None,
                "frames": r["frames"],
                "integration_s": r["integration_s"],
                "untimed": r["untimed"],
                "panels": r["panels"],
            }
        )
    return items, total


# Dates, or a frame of an object so named: `{dates}` are `OR`ed patterns, then `NAMED`'s two.
_NIGHTS_WHERE = (
    "({dates} n.id IN (SELECT f.night_id FROM frames f JOIN objects o ON o.id = f.object_id"  # noqa: S608
    " WHERE f.copy_of IS NULL AND f.night_id IS NOT NULL AND " + archive.NAMED.format(o="o") + "))"
)
_NIGHTS = f"""
SELECT n.id, n.night_date, s.name AS site, {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n JOIN sites s ON s.id = n.site_id
WHERE {{where}}
ORDER BY n.night_date DESC, n.id DESC
LIMIT ?
"""  # noqa: S608 - constant fragments; `where` holds placeholders


def _nights(
    conn: sqlite3.Connection, q: str, pattern: str, limit: int
) -> tuple[list[dict[str, Any]], int]:
    dates = night_dates(q)
    where = _NIGHTS_WHERE.format(dates="".join("n.night_date LIKE ? OR " for _ in dates))
    values = [*dates, pattern, pattern]
    rows = conn.execute(_NIGHTS.format(where=where), (*values, limit)).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) FROM nights n WHERE {where}",  # noqa: S608 - placeholders
        values,
    ).fetchone()[0]
    keep = ("id", "night_date", "site", "frames", "integration_s", "untimed")
    return [{k: r[k] for k in keep} for r in rows], total


# Pieces and filters you own, with what the counter wrote; "no filter" is not one.
_GEAR = """
SELECT * FROM (
  SELECT i.id, i.kind, i.name, u.frames, u.integration_s, u.untimed, u.objects_json
  FROM instruments i
  LEFT JOIN gear_usage u ON u.subject = 'instrument' AND u.subject_id = i.id
  UNION ALL
  SELECT x.id, 'filter', x.name, u.frames, u.integration_s, u.untimed, u.objects_json
  FROM filters x
  LEFT JOIN gear_usage u ON u.subject = 'filter' AND u.subject_id = x.id
  WHERE x.is_none = 0
) p WHERE """ + archive.FOLDED.format("p.name")  # noqa: S608 - constant fragments


def _gear(conn: sqlite3.Connection, pattern: str, limit: int) -> tuple[list[dict[str, Any]], int]:
    """Most time first, then by name; a piece not yet counted goes last."""
    rows = conn.execute(
        _GEAR + " ORDER BY p.integration_s IS NULL, p.integration_s DESC, p.name COLLATE NOCASE,"
        " p.kind, p.id",
        (pattern,),
    ).fetchall()
    items = [
        {
            "id": r["id"],
            "kind": r["kind"],
            "name": r["name"],
            "counted": r["objects_json"] is not None,
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
            "no_hours": inventory.no_hours(r),
        }
        for r in rows
    ]
    return items[:limit], len(items)


_SITES = (
    "SELECT s.id, s.name, (SELECT COUNT(*) FROM nights n WHERE n.site_id = s.id) AS nights"  # noqa: S608
    " FROM sites s WHERE " + archive.FOLDED.format("s.name") +
    " ORDER BY s.is_default DESC, s.name COLLATE NOCASE, s.id"
)  # fmt: skip


def _sites(conn: sqlite3.Connection, pattern: str, limit: int) -> tuple[list[dict[str, Any]], int]:
    rows = [dict(r) for r in conn.execute(_SITES, (pattern,))]
    return rows[:limit], len(rows)


def find(conn: sqlite3.Connection, q: str, limit: int) -> dict[str, dict[str, Any]]:
    """`{kind: {items, total}}`, at most `limit` items per kind. A blank `q` finds nothing:
    the Archive reads it as no search, the bar as no question."""
    pattern = archive.folded(q)
    if pattern is None:
        return {kind: {"items": [], "total": 0} for kind in ("objects", "nights", "gear", "sites")}
    found = {
        "objects": _objects(conn, q, limit),
        "nights": _nights(conn, q, pattern, limit),
        "gear": _gear(conn, pattern, limit),
        "sites": _sites(conn, pattern, limit),
    }
    return {kind: {"items": items, "total": total} for kind, (items, total) in found.items()}
