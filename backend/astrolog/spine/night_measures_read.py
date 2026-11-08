"""A night's measures, read: the sets `night_measures.py` wrote and the frames one by one as the
pipeline wrote them, by SQL through the bridge (ADR 0045). Nothing computed here."""

import json
import sqlite3
from typing import Any

from ..clock import local_iso
from ..measure_list import MEASURES, Entry
from ..night_measures import JOINS, VALUES
from . import filters_used
from . import objects as obj

_NIGHT = "SELECT s.timezone FROM nights n JOIN sites s ON s.id = n.site_id WHERE n.id = ?"

_SERIES = f"""
SELECT f.id, f.object_id, f.filter_id, m.outcome, m.shape, m.tilt_level, m.sampling_class,
       (SELECT c.start_utc FROM pipeline_files pf JOIN pipeline_cards c ON c.file_id = pf.id
         WHERE pf.frame_id = b.pipeline_frame_id AND pf.state = 'present'
         ORDER BY pf.id LIMIT 1) AS start_utc, {VALUES}
FROM frames f{JOINS}
WHERE f.night_id = ? AND f.copy_of IS NULL AND b.skip_reason IS NULL
  AND m.outcome IS NOT 'not_supported' AND m.outcome IS NOT 'fz_unsupported'
ORDER BY start_utc IS NULL, start_utc, f.id
"""  # noqa: S608 - our columns

_OBJECTS = f"""
SELECT g.frames, g.pending, o.id, o.catalog_slug, {obj.NAME_COLUMNS}
FROM night_measure_groups g JOIN objects o ON o.id = g.object_id
WHERE g.night_id = ? AND g.filter_id IS NULL
ORDER BY g.frames DESC, o.id
"""  # noqa: S608 - constant fragments of the spine

_FILTERS = f"""
SELECT g.frames, x.id, x.name, x.passband
FROM night_measure_groups g JOIN filters x ON x.id = g.filter_id
WHERE g.night_id = ? AND g.object_id IS NULL
ORDER BY {filters_used.order_by("x")}
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
    filters = {r["id"]: r for r in conn.execute(_FILTERS, (night_id,))}
    keys = {i: obj.stable_key(r) for i, r in objects.items()}
    names = {i: r["name"] for i, r in filters.items()}
    zone = night["timezone"]
    series = [_frame(r, keys, names, zone) for r in conn.execute(_SERIES, (night_id,))]
    groups = conn.execute(_GROUPS, (night_id,)).fetchall()
    whole = next((g for g in groups if g["object_id"] is None and g["filter_id"] is None), None)
    return {
        "night_id": night_id,
        "timezone": night["timezone"],
        # not written yet (a scan still running): every frame is still to be measured
        "frames": whole["frames"] if whole else len(series),
        "pending": whole["pending"] if whole else len(series),
        "objects": [
            {
                "key": keys[i],
                "name": obj.display_name(r),
                "frames": r["frames"],
                "pending": r["pending"],
            }
            for i, r in objects.items()
        ],  # fmt: skip
        "filters": [
            {"name": r["name"], "passband": r["passband"], "frames": r["frames"]}
            for r in filters.values()
        ],
        "sets": _sets(conn, night_id, groups, keys, names),
        "series": series,
    }


def _sets(
    conn: sqlite3.Connection,
    night_id: int,
    groups: list[sqlite3.Row],
    keys: dict[int, str],
    names: dict[int, str],
) -> list[dict[str, Any]]:
    rows = {
        (r["object_id"], r["filter_id"], r["key"]): r for r in conn.execute(_MEASURES, (night_id,))
    }
    out = []
    for g in groups:
        at = (g["object_id"], g["filter_id"])
        measuring = g["pending"] == g["frames"]
        out.append({
            "object_key": keys.get(at[0]) if at[0] is not None else None,
            "filter": names.get(at[1]) if at[1] is not None else None,
            "frames": g["frames"],
            "pending": g["pending"],
            "differs": json.loads(g["differs"]),
            "measures": [_stat(e, rows.get((*at, e.key)), measuring) for e in MEASURES],
        })  # fmt: skip
    return out


def _stat(entry: Entry, row: sqlite3.Row | None, measuring: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"key": entry.key, "unit": entry.unit, "group": entry.group}
    if row is None or row["median"] is None:
        silent = "measuring" if measuring else "no_value"
        measured = 0 if row is None else row["measured"]
        return out | {"measured": measured, "median": None, "q1": None, "q3": None,
                      "trend": None, "silent": silent}  # fmt: skip
    trend = json.loads(row["trend"]) if row["trend"] else None
    return out | {"measured": row["measured"], "median": row["median"], "q1": row["q1"],
                  "q3": row["q3"], "trend": trend, "silent": None}  # fmt: skip


def _frame(
    r: sqlite3.Row, keys: dict[int, str], names: dict[int, str], zone: str | None
) -> dict[str, Any]:
    if r["outcome"] == "measured" and r["shape"] == "estimated":
        state = "estimated"
    else:  # a file unreadable now, or not measured yet, waits alike
        state = r["outcome"] if r["outcome"] in _STATES else "pending"
    return {
        "frame_id": r["id"],
        "start": local_iso(r["start_utc"], zone),
        "object_key": keys.get(r["object_id"]),
        "filter": names.get(r["filter_id"]),
        "state": state,
        "tilt_level": r["tilt_level"],
        "sampling": r["sampling_class"],
        "values": {e.key: float(r[e.key]) for e in MEASURES if r[e.key] is not None},
    }
