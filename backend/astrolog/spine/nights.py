"""The Nights page, read from what `group` wrote: a night is a date plus a site and one row, its
objects and filters inside, or the hours would split and two rows look like duplicates."""

import json
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
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


@dataclass(frozen=True)
class Observed:
    """What the weather's writer knows, passed in: the spine and `weather` do not import each other.
    `kind` of the observed rows; `arrives_on(night_date, zone)`, the day a young night's comes."""

    kind: str
    arrives_on: Callable[[str, str], str | None]


_PAGE = f"""
SELECT n.id, n.night_date, n.site_source, s.name AS site, s.timezone, s.latitude,
       w.summary_json AS weather,
       {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN weather_nights w
  ON w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
WHERE (? IS NULL OR n.id = ?)
ORDER BY n.night_date DESC, n.id DESC
LIMIT ? OFFSET ?
"""  # noqa: S608 - constant fragments of the spine, not user values

_HOW_MANY = "SELECT COUNT(*) FROM nights n WHERE (? IS NULL OR n.id = ?)"

_TOTALS = f"SELECT{counts.counts_on(counts.Subject.ARCHIVE)}"

# Asked for the whole page at once, never per row.
_OBJECTS = f"""
SELECT f.night_id, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}, {counts.UNTIMED}
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
    latitude = {r["id"]: r["latitude"] for r in rows}
    return {
        i: {**asdict(p), "lit_side": moon.lit_side(p.phase_key, latitude[i])}
        for i, p in zip(known, moon.phases(list(known.values())), strict=True)
    }


# Under this a bar would vanish and read as "no time"; the floor is for time, never for none.
_SLIVER_PCT = 2


def _with_bars(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each object's hours as a share of the night's longest, the first by `ORDER_BY_TIME`."""
    longest = objects[0]["integration_s"] if objects else 0
    for o in objects:
        share = round(o["integration_s"] * 100 / longest) if longest else 0
        o["bar_pct"] = max(share, _SLIVER_PCT) if o["integration_s"] > 0 else 0
    return objects


def page(
    conn: sqlite3.Connection,
    *,
    limit: int,
    offset: int,
    weather: Observed,
    night: int | None = None,
) -> list[dict[str, Any]]:
    """Most recent first; `night` asks one night by id, wherever it falls (the search opens it)."""
    rows = conn.execute(_PAGE, (weather.kind, night, night, limit, offset)).fetchall()
    ids = [r["id"] for r in rows]
    moons = _moons(rows)
    night_objects = idlist.grouped(
        conn, _OBJECTS, ids, "night_id", lambda r: {**obj.counted(r), "untimed": r["untimed"]}
    )
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
            "objects": _with_bars(night_objects.get(r["id"], [])),
            "filters": filters.get(r["id"], []),
            "moon": moons.get(r["id"]),
            "weather": _weather(r, weather.arrives_on if r["id"] in moons else None),
        }
        for r in rows
    ]


def _weather(
    row: sqlite3.Row, arrives_on: Callable[[str, str], str | None] | None
) -> dict[str, Any]:
    """`unknown` without the site's zone (no `arrives_on`, as no Moon); `waiting` when the night
    is too young for the reanalysis, with the day it comes, or the history has not reached it."""
    if row["weather"] is not None:
        return {"state": "ok", **json.loads(row["weather"]), "arrives_on": None}
    if arrives_on is None:
        return {"state": "unknown", **_NO_SKY, "arrives_on": None}
    when = arrives_on(row["night_date"], row["timezone"])
    return {"state": "waiting", **_NO_SKY, "arrives_on": when}


# Every field, empty, as the response shape wants them.
_NO_SKY = dict.fromkeys(("verdict", "cloud_total_pct", "usable_hours", "window", "window_hours"))


def how_many(conn: sqlite3.Connection, night: int | None = None) -> int:
    return conn.execute(_HOW_MANY, (night, night)).fetchone()[0]


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


_PLACED = "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'done'"


def reading_done_pct(conn: sqlite3.Connection, left: int) -> int | None:
    """Of the frames `group` has to place, how many it placed, rounded down: 100 only when none is
    left, and then there is no reading to tell."""
    if not left:
        return None
    placed = conn.execute(_PLACED, (stages.StageName.GROUP,)).fetchone()[0]
    return placed * 100 // (placed + left)


def still_reading(conn: sqlite3.Connection) -> int:
    """`group`'s residue, not the sum of stages: a frame stuck at `solve` would count three times,
    and `measure`, which nobody runs yet, would never reach zero."""
    return stages.count_pending(conn, stages.StageName.GROUP)
