"""The search in the bar, a few per kind with how many in all. It reads what others wrote: the
Archive's rows, the Nights' counts, `gear_usage` (`docs/domini/navigazione.md`)."""

import re
import sqlite3
from datetime import date
from typing import Any

from . import archive, counts, inventory, objects

# One group of the answer: `items`, `total`, and for the nights `why`.
type Found = dict[str, Any]

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
_MONTH_YEAR = re.compile(r"(\d{1,2})[/.-](\d{4})")
_NUMERIC = re.compile(r"(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2}|\d{4}))?")
_DAY_MONTH = re.compile(r"(\d{1,2}) ([a-z]+)(?: (\d{4}))?")
_MONTH_DAY = re.compile(r"([a-z]+) (\d{1,2}),?(?: (\d{4}))?")
_MONTH = re.compile(r"([a-z]+)(?: (\d{4}))?")

# A year that does not count, for a day asked without one.
_ANY_YEAR = 2000  # [T] leap year, so 29 Feb exists


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
    if m := _MONTH_YEAR.fullmatch(typed):
        return [(int(m[2]), int(m[1]), None)]
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


def date_readings(q: str) -> list[tuple[int | None, int, int | None]]:
    """(year, month, day) of the real dates `q` writes, in the common forms; none if not a date."""
    typed = " ".join(q.lower().split())
    return [(y, m, d) for y, m, d in _readings(typed) if 1 <= m <= 12 and _day(y, m, d)]


def night_dates(q: str) -> list[str]:
    """`LIKE` patterns of the dates `q` writes; none if it is not a date."""
    return [p for y, m, d in date_readings(q) if (p := _day(y, m, d)) is not None]


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


# A name holding the typed text; ending in a figure, not followed by one: "M 3" is not M 31, and
# "NGC" still finds NGC 7000. Each `?` is the typed text folded, without `%`.
_WHOLE = (
    "(instr({f}, ?) > 0 AND (? NOT GLOB '*[0-9]'"
    " OR substr({f}, instr({f}, ?) + length(?), 1) NOT GLOB '[0-9]'))"
)
_WHOLE_ARGS = 4  # [T] the `?` in `_WHOLE`


def _whole(column: str) -> str:
    return _WHOLE.format(f=f"REPLACE(LOWER({column}), ' ', '')")


# A frame of an object so named: the two names', each `_WHOLE`.
_BY_OBJECT = (
    "n.id IN (SELECT f.night_id FROM frames f JOIN objects o ON o.id = f.object_id"  # noqa: S608
    " WHERE f.copy_of IS NULL AND f.night_id IS NOT NULL AND"
    " (EXISTS (SELECT 1 FROM object_names m WHERE m.object_id = o.id AND " + _whole("m.name") + ")"
    " OR EXISTS (SELECT 1 FROM catalog_names k WHERE k.slug = o.catalog_slug AND "
    + _whole("k.catalog || k.designation") + ")))"
)  # fmt: skip
_NIGHTS = f"""
SELECT n.id, n.night_date, s.name AS site, {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n JOIN sites s ON s.id = n.site_id
WHERE {{where}}
ORDER BY n.night_date DESC, n.id DESC
LIMIT ?
"""  # noqa: S608 - constant fragments; `where` holds placeholders


def _nights(conn: sqlite3.Connection, q: str, limit: int, objects: Found) -> Found:
    """By date when `q` reads as one, else by the objects shot; `why` says which (Cerca v77)."""
    readings = date_readings(q)
    dates = night_dates(q)
    if dates:
        where = "(" + " OR ".join("n.night_date LIKE ?" for _ in dates) + ")"
        values: list[str] = dates
    else:
        where, values = _BY_OBJECT, [archive.plain(q)] * (2 * _WHOLE_ARGS)
    rows = conn.execute(_NIGHTS.format(where=where), (*values, limit)).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) FROM nights n WHERE {where}",  # noqa: S608 - placeholders
        values,
    ).fetchone()[0]
    keep = ("id", "night_date", "site", "frames", "integration_s", "untimed")
    found: Found = {"items": [{k: r[k] for k in keep} for r in rows], "total": total, "why": None}
    if total:
        found["why"] = _why(readings, objects)
    return found


def _why(readings: list[tuple[int | None, int, int | None]], objects: Found) -> dict[str, Any]:
    if readings:
        dates = [{"year": y, "month": m, "day": d} for y, m, d in readings]
        return {"by": "dates", "dates": dates, "object": None}
    if objects["total"] == 1:
        return {"by": "object", "dates": [], "object": objects["items"][0]["name"]}
    return {"by": "objects", "dates": [], "object": None}


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


def _examples(conn: sqlite3.Connection) -> dict[str, str | None]:
    """The empty field's hints from your own archive: the most used piece, the default site."""
    gear, _ = _gear(conn, "%", 1)
    site = conn.execute("SELECT name FROM sites ORDER BY is_default DESC, id LIMIT 1").fetchone()
    return {"gear": gear[0]["name"] if gear else None, "site": site[0] if site else None}


def _none() -> dict[str, Found]:
    nothing: dict[str, Found] = {k: {"items": [], "total": 0} for k in ("objects", "gear", "sites")}
    return {**nothing, "nights": {"items": [], "total": 0, "why": None}}


def find(conn: sqlite3.Connection, q: str, limit: int) -> dict[str, Any]:
    """`{kind: {items, total}}`, at most `limit` per kind, plus `archive_empty` and `examples`.
    Blank `q`, or no frames, finds nothing of the archive (Cerca v77)."""
    empty = conn.execute("SELECT NOT EXISTS (SELECT 1 FROM frames)").fetchone()[0] == 1
    head = {"archive_empty": empty, "examples": _examples(conn)}
    pattern = archive.folded(q)
    if pattern is None or empty:
        return {**_none(), **head}
    found: dict[str, Found] = {
        kind: {"items": items, "total": total}
        for kind, (items, total) in (
            ("objects", _objects(conn, q, limit)),
            ("gear", _gear(conn, pattern, limit)),
            ("sites", _sites(conn, pattern, limit)),
        )
    }
    found["nights"] = _nights(conn, q, limit, found["objects"])
    return {**found, **head}
