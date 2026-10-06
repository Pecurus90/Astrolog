"""The Nights page, read from what `group` wrote: a night is a date plus a site and one row, its
objects and filters inside, or the hours would split and two rows look like duplicates."""

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import asdict
from enum import StrEnum
from typing import Any

from ..clock import midnight_of
from ..db import idlist
from ..ephemeris import moon
from . import counts, filters_used, stages
from . import objects as obj
from .group import GroupReason


class AnswerAt(StrEnum):
    """Where a frame no night took is answered: one waiting for its site, or one with nothing to
    answer (no date), sent to the review page would find a list with nothing for it."""

    REVIEW = "review"
    SITE = "site"
    NEVER = "never"


_ANSWER_AT = {
    GroupReason.SITE_UNCLEAR: AnswerAt.REVIEW,
    GroupReason.NO_OBJECT: AnswerAt.REVIEW,
    GroupReason.NO_ACTIVE_SITE: AnswerAt.SITE,
    GroupReason.SITE_NO_TIMEZONE: AnswerAt.SITE,
    GroupReason.NO_DATE: AnswerAt.NEVER,
}

# The caller passes the observed weather's kind.
_PAGE = f"""
SELECT n.id, n.night_date, n.site_source, s.name AS site, s.timezone, w.summary_json AS weather,
       {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN weather_nights w
  ON w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
ORDER BY n.night_date DESC, n.id DESC
LIMIT ? OFFSET ?
"""  # noqa: S608 - constant fragments of the spine, not user values

_HOW_MANY = "SELECT COUNT(*) FROM nights"

_TOTALS = f"SELECT{counts.counts_on(counts.Subject.ARCHIVE)}"

# Asked for the whole page at once, never per row.
_OBJECTS = f"""
SELECT f.night_id, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id
WHERE f.night_id IN {{listed}} AND f.copy_of IS NULL
GROUP BY f.night_id, o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - `listed` is a placeholder, not a value

# `group` is the last stage to look at them: a frame another stage skipped stops here with its code.
_STOPPED = """
SELECT s.reason, COUNT(*) AS frames
FROM frame_stages s JOIN frames f ON f.id = s.frame_id
WHERE s.stage = 'group' AND s.status = 'skipped' AND f.copy_of IS NULL
GROUP BY s.reason ORDER BY frames DESC, s.reason
"""


def _moons(rows: Sequence[sqlite3.Row]) -> dict[int, dict[str, Any]]:
    """One call to the sky, at midnight in the site's zone; a night without a known zone is left
    out. Not stored: a derivable number frozen in a column would outlive a corrected formula."""
    when = {r["id"]: midnight_of(r["night_date"], r["timezone"]) for r in rows}
    known = {i: q for i, q in when.items() if q is not None}
    return dict(zip(known, map(asdict, moon.phases(list(known.values()))), strict=True))


def page(
    conn: sqlite3.Connection, *, limit: int, offset: int, observed: str
) -> list[dict[str, Any]]:
    """Most recent first; `observed` is the kind of the weather rows, known to their writer."""
    rows = conn.execute(_PAGE, (observed, limit, offset)).fetchall()
    ids = [r["id"] for r in rows]
    moons = _moons(rows)
    night_objects = idlist.grouped(conn, _OBJECTS, ids, "night_id", obj.counted)
    filters = filters_used.of(conn, counts.Subject.NIGHT, ids)
    return [
        {
            "id": r["id"],
            "night_date": r["night_date"],
            "site": r["site"],
            "site_source": r["site_source"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
            "objects": night_objects.get(r["id"], []),
            "filters": filters.get(r["id"], []),
            "moon": moons.get(r["id"]),
            "weather": _weather(r, zone_known=r["id"] in moons),
        }
        for r in rows
    ]


def _weather(row: sqlite3.Row, *, zone_known: bool) -> dict[str, Any]:
    """`unknown` when the site's zone is not recognised, so its nights cannot be split; `waiting`
    when the night is too young for the reanalysis or the history has not reached it."""
    if row["weather"] is not None:
        return {"state": "ok", **json.loads(row["weather"])}
    # whether `_moons` found the zone: one test for Moon and weather
    return {"state": "waiting" if zone_known else "unknown", **_NO_SKY}


# Every field, empty, as the response shape wants them.
_NO_SKY = dict.fromkeys(("verdict", "cloud_total_pct", "usable_hours", "window", "window_hours"))


def how_many(conn: sqlite3.Connection) -> int:
    return conn.execute(_HOW_MANY).fetchone()[0]


def archive_totals(conn: sqlite3.Connection) -> dict[str, Any]:
    """Only what lies inside a night, or the top number would not add up with the rows."""
    r = conn.execute(_TOTALS).fetchone()
    return {
        "nights": how_many(conn),
        "frames": r["frames"],
        "integration_s": r["integration_s"],
        "untimed": r["untimed"],
    }


def waiting(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """By where the answer is given, largest first. An unmapped reason is `never`: better nowhere
    than the wrong place."""
    sums: dict[AnswerAt, int] = {}
    for r in conn.execute(_STOPPED):
        place = _ANSWER_AT.get(r["reason"], AnswerAt.NEVER)
        sums[place] = sums.get(place, 0) + r["frames"]
    ordered = sorted(sums.items(), key=lambda item: (-item[1], item[0]))
    return [{"answer_at": place, "frames": count} for place, count in ordered]


def still_reading(conn: sqlite3.Connection) -> int:
    """`group`'s residue, not the sum of stages: a frame stuck at `solve` would count three times,
    and `measure`, which nobody runs yet, would never reach zero."""
    return stages.count_pending(conn, stages.StageName.GROUP)
