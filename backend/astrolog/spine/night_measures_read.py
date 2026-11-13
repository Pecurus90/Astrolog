"""A night's measures as `night_measures.py` wrote them, its objects the groups, and its frames
one by one through the bridge (ADR 0045); `object_measures_read.py` reads an object's."""

import json
import sqlite3
from collections.abc import Callable, Iterable
from typing import Any

from ..clock import local_iso
from ..measure_list import MEASURES, Entry
from ..night_measures import JOINS, VALUES
from ..vocab.filters import Passband
from . import filters_used
from . import objects as obj
from .night_criteria import NO_FILTER

_NIGHT = "SELECT s.timezone FROM nights n JOIN sites s ON s.id = n.site_id WHERE n.id = ?"

# The columns of a frame of the series, `f` through the bridge; the caller adds FROM and WHERE.
SERIES = f"""
SELECT f.id, f.object_id, f.night_id, f.filter_id, m.outcome, m.shape, m.tilt_level,
       m.sampling_class, k.angle_axis, k.gradient_side,
       (SELECT c.start_utc FROM pipeline_files pf JOIN pipeline_cards c ON c.file_id = pf.id
         WHERE pf.frame_id = b.pipeline_frame_id AND pf.state = 'present'
         ORDER BY pf.id LIMIT 1) AS start_utc,
       (SELECT c.pier_side FROM pipeline_cards c WHERE c.file_id = m.file_id) AS pier_side,
       {VALUES}"""  # noqa: S608 - our columns
# Never measured (a program not read, a compressed file): not in the series.
SERIES_WHERE = """f.copy_of IS NULL AND b.skip_reason IS NULL
  AND m.outcome IS NOT 'not_supported' AND m.outcome IS NOT 'fz_unsupported'"""
SERIES_ORDER = "ORDER BY start_utc IS NULL, start_utc, f.id"

_SERIES = f"""{SERIES}
FROM frames f{JOINS}
WHERE f.night_id = ? AND {SERIES_WHERE}
{SERIES_ORDER}
"""

_OBJECTS = f"""
SELECT g.frames, g.pending, o.id, o.catalog_slug, {obj.NAME_COLUMNS}
FROM night_measure_groups g JOIN objects o ON o.id = g.object_id
WHERE g.night_id = ? AND g.filter_id IS NULL AND g.unfiltered = 0
ORDER BY g.frames DESC, o.id
"""  # noqa: S608 - constant fragments of the spine

_FILTERS = f"""
SELECT g.frames, g.unfiltered, x.id, x.name, x.passband
FROM night_measure_groups g LEFT JOIN filters x ON x.id = g.filter_id
WHERE g.night_id = ? AND g.object_id IS NULL AND (g.filter_id IS NOT NULL OR g.unfiltered = 1)
ORDER BY g.unfiltered, {filters_used.order_by("x")}
"""  # noqa: S608 - constant fragments of the spine

_GROUPS = "SELECT * FROM night_measure_groups WHERE night_id = ?"
_MEASURES = "SELECT * FROM night_measures WHERE night_id = ?"
_STATES = {"measured", "too_few_stars"}


def night_measures(conn: sqlite3.Connection, night_id: int) -> dict[str, Any] | None:
    """None: no such night."""
    night = conn.execute(_NIGHT, (night_id,)).fetchone()
    if night is None:
        return None
    objects = {r["id"]: r for r in conn.execute(_OBJECTS, (night_id,))}
    keys = {i: obj.stable_key(r) for i, r in objects.items()}
    found = conn.execute(_FILTERS, (night_id,)).fetchall()
    names = {r["id"]: r["name"] for r in found if not r["unfiltered"]}
    zone = night["timezone"]
    series = [
        frame(r, keys.get(r["object_id"]), names, zone) for r in conn.execute(_SERIES, (night_id,))
    ]
    groups = conn.execute(_GROUPS, (night_id,)).fetchall()
    rows = conn.execute(_MEASURES, (night_id,)).fetchall()
    whole = next((g for g in groups if _whole(g)), None)
    return {
        "night_id": night_id,
        "timezone": zone,
        # not written yet (a scan still running): every frame is still to be measured
        "frames": whole["frames"] if whole else len(series),
        "pending": whole["pending"] if whole else len(series),
        "groups": [
            {
                "key": keys[i],
                "name": obj.display_name(r),
                "night_date": None,
                "frames": r["frames"],
                "pending": r["pending"],
            }
            for i, r in objects.items()
        ],  # fmt: skip
        "filters": filters(found),
        "sets": sets(groups, rows, "object_id", lambda g: keys.get(g["object_id"]), names),
        "series": series,
    }


def _whole(g: sqlite3.Row) -> bool:
    return g["object_id"] is None and g["filter_id"] is None and g["unfiltered"] == 0


def filters(found: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    """In the app's one filter order; the frames naming none last, as in the Nights."""
    return [
        {"name": NO_FILTER, "passband": Passband.UNKNOWN, "frames": r["frames"]}
        if r["unfiltered"]
        else {"name": r["name"], "passband": r["passband"], "frames": r["frames"]}
        for r in found
    ]


def sets(
    groups: list[sqlite3.Row],
    rows: list[sqlite3.Row],
    column: str,
    group_of: Callable[[sqlite3.Row], str | None],
    names: dict[int, str],
) -> list[dict[str, Any]]:
    """Every written group with its measures. `column` is the group's own (object or night): with
    the filter it tells a group's rows among the ones the caller read."""

    def at_of(r: sqlite3.Row) -> tuple[Any, ...]:
        return r[column], r["filter_id"], r["unfiltered"]

    by_at = {(*at_of(r), r["key"]): r for r in rows}
    out = []
    for g in groups:
        at = at_of(g)
        measuring = g["pending"] == g["frames"]
        flt = g["filter_id"]
        out.append({
            "group": group_of(g),
            "filter": NO_FILTER if g["unfiltered"] else names.get(flt) if flt is not None else None,
            "frames": g["frames"],
            "pending": g["pending"],
            "differs": json.loads(g["differs"]),
            "differs_values": json.loads(g["differs_values"]),
            "pier_side": {"east": g["pier_east"], "west": g["pier_west"]},
            "measures": [_stat(e, by_at.get((*at, e.key)), measuring) for e in MEASURES],
        })  # fmt: skip
    return out


def _stat(entry: Entry, row: sqlite3.Row | None, measuring: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"key": entry.key, "unit": entry.unit, "group": entry.group}
    if row is None or row["median"] is None:
        silent = "measuring" if measuring else "no_value"
        measured = 0 if row is None else row["measured"]
        return out | {"measured": measured, "median": None, "q1": None, "q3": None, "low": None,
                      "high": None, "trend": None, "verdict": None, "silent": silent,
                      "per_filter": False}  # fmt: skip
    trend = json.loads(row["trend"]) if row["trend"] else None
    return out | {"measured": row["measured"], "median": row["median"], "q1": row["q1"],
                  "q3": row["q3"], "low": row["low"], "high": row["high"], "trend": trend,
                  "verdict": row["verdict"], "silent": None,
                  "per_filter": bool(row["per_filter"])}  # fmt: skip


def frame(
    r: sqlite3.Row, group: str | None, names: dict[int, str], zone: str | None
) -> dict[str, Any]:
    """One frame of the series, in its group, its start in the site's zone."""
    if r["outcome"] == "measured" and r["shape"] == "estimated":
        state = "estimated"
    else:  # a file unreadable now, or not measured yet, waits alike
        state = r["outcome"] if r["outcome"] in _STATES else "pending"
    return {
        "frame_id": r["id"],
        "start": local_iso(r["start_utc"], zone),
        "group": group,
        "filter": names.get(r["filter_id"], NO_FILTER) if r["filter_id"] is not None else NO_FILTER,
        "state": state,
        "tilt_level": r["tilt_level"],
        "sampling": r["sampling_class"],
        "angle_axis": r["angle_axis"],
        "gradient_side": r["gradient_side"],
        "pier_side": r["pier_side"],
        "values": {e.key: float(r[e.key]) for e in MEASURES if r[e.key] is not None},
    }
