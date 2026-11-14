"""The Nights page, read from what `group` wrote: a night is a date plus a site and one row, its
objects and filters inside, or the hours would split and two rows look like duplicates."""

import json
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from ..clock import midnight_of, night_window
from ..db import idlist
from ..ephemeris import moon
from ..levels import MoonRule
from . import counts, filters_used, stages
from . import objects as obj
from .group import GroupReason


class AnswerAt(StrEnum):
    """Where a frame no night took is answered: one waiting for its site, or one with nothing to
    answer (no date), sent to the review page would find a list with nothing for it."""

    REVIEW = "review"
    SITE = "site"
    DATE = "date"
    NEVER = "never"


_ANSWER_AT = {
    GroupReason.SITE_UNCLEAR: AnswerAt.REVIEW,
    GroupReason.NO_OBJECT: AnswerAt.REVIEW,
    GroupReason.NO_ACTIVE_SITE: AnswerAt.SITE,
    GroupReason.SITE_NO_TIMEZONE: AnswerAt.SITE,
    # the user writes the date, per folder (`spine/undated.py`)
    GroupReason.NO_DATE: AnswerAt.DATE,
}


class SiteFrom(StrEnum):
    """Where a night's site comes from: the frames' coordinates, home for frames without them, or
    the user's answer in To confirm."""

    FRAMES = "frames"
    HOME = "home"
    ANSWER = "answer"


@dataclass(frozen=True)
class Observed:
    """What the weather's writer knows, passed in: the spine and `weather` do not import each other.
    `kind` of the observed rows; `arrives_on(night_date, zone)`, the day a young night's comes."""

    kind: str
    arrives_on: Callable[[str, str], str | None]


_PAGE = f"""
SELECT n.id, n.night_date, n.site_source, s.name AS site, s.timezone, s.latitude, s.longitude,
       EXISTS (SELECT 1 FROM frames f WHERE f.night_id = n.id AND f.site_lat IS NOT NULL)
         AS from_frames,
       w.summary_json AS weather,
       {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN weather_nights w
  ON w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
WHERE n.id IN {{listed}}
ORDER BY n.night_date DESC, n.id DESC
"""  # noqa: S608 - constant fragments of the spine, `listed` a placeholder

# Per night, for the months of a list: the hours of every night that passes, not of a page.
_MONTHS = f"""
SELECT substr(n.night_date, 1, 7) AS month, {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n WHERE n.id IN {{listed}}
"""  # noqa: S608 - constant fragments, `listed` a placeholder

# Objects with or without a night: `identify` names them before `group` places them.
_TOTALS = f"""SELECT{counts.counts_on(counts.Subject.ARCHIVE)},
       (SELECT COUNT(DISTINCT f.object_id) FROM frames f WHERE f.copy_of IS NULL) AS objects"""  # noqa: S608 - our columns

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


# Under this a bar would vanish and read as "no time"; the floor is for time, never for none. [T]
_SLIVER_PCT = 2


def _with_bars(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each object's hours as a share of the night's longest, the first by `ORDER_BY_TIME`."""
    longest = objects[0]["integration_s"] if objects else 0
    for o in objects:
        share = round(o["integration_s"] * 100 / longest) if longest else 0
        o["bar_pct"] = max(share, _SLIVER_PCT) if o["integration_s"] > 0 else 0
    return objects


def _shooting(
    rows: Sequence[sqlite3.Row], moons: dict[int, dict[str, Any]], rule: MoonRule
) -> dict[int, dict[str, Any]]:
    """Broadband dark the Moon left: all under the rule's good bound, else the dark with the Moon
    under its floor. Computed like the Moon, one call per site; none without Moon or dark."""
    by_site: dict[tuple[float, float], list[sqlite3.Row]] = {}
    for r in rows:
        if r["id"] in moons:
            by_site.setdefault((r["latitude"], r["longitude"]), []).append(r)
    out = {}
    for (lat, lon), mine in by_site.items():
        windows = [(r["night_date"], *night_window(r["night_date"], r["timezone"])) for r in mine]
        darks = moon.dark_seconds(windows, lat, lon, rule.floor_deg)
        for r, (dark_s, moonless_s) in zip(mine, darks, strict=True):
            if not dark_s:
                continue
            lit = moons[r["id"]]["illumination_pct"]
            free = dark_s if lit < rule.good_pct else moonless_s
            kind = "broadband" if free >= dark_s else "narrowband" if not free else "mixed"
            out[r["id"]] = {
                "kind": kind,
                "broadband_hours": round(free / 3600, 1),
                "dark_hours": round(dark_s / 3600, 1),
            }
    return out


def _site_from(r: sqlite3.Row) -> SiteFrom:
    if r["site_source"] == "declared":
        return SiteFrom.ANSWER
    return SiteFrom.FRAMES if r["from_frames"] else SiteFrom.HOME


def objects_of(conn: sqlite3.Connection, ids: Sequence[int]) -> dict[int, list[dict[str, Any]]]:
    """`{night id: [object]}`, the most shot first: Nights and Moon calendar ask it alike."""
    return idlist.grouped(
        conn, _OBJECTS, ids, "night_id", lambda r: {**obj.counted(r), "untimed": r["untimed"]}
    )


def page(
    conn: sqlite3.Connection, *, ids: Sequence[int], weather: Observed, rule: MoonRule
) -> list[dict[str, Any]]:
    """The listed nights, most recent first; the criteria chose them (`night_criteria`)."""
    with idlist.holding(conn, ids) as held:
        rows = conn.execute(_PAGE.format(listed=held), (weather.kind,)).fetchall()
    moons = _moons(rows)
    shooting = _shooting(rows, moons, rule)
    night_objects = objects_of(conn, ids)
    filters = filters_used.of(conn, counts.Subject.NIGHT, ids)
    return [
        {
            "id": r["id"],
            "night_date": r["night_date"],
            "site": r["site"],
            "site_source": r["site_source"],
            "site_from": _site_from(r),
            "shooting": shooting.get(r["id"]),
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


def months(conn: sqlite3.Connection, ids: Sequence[int]) -> list[dict[str, Any]]:
    """Newest first: nights and hours of every listed night per month, not of a loaded page."""
    out: dict[str, dict[str, Any]] = {}
    with idlist.holding(conn, ids) as held:
        for r in conn.execute(_MONTHS.format(listed=held)):
            m = out.setdefault(
                r["month"], {"month": r["month"], "nights": 0, "integration_s": 0.0, "untimed": 0}
            )
            m["nights"] += 1
            m["integration_s"] += r["integration_s"]
            m["untimed"] += r["untimed"]
    return [out[k] for k in sorted(out, reverse=True)]


def archive_totals(conn: sqlite3.Connection) -> dict[str, Any]:
    """Only what lies inside a night, or the top number would not add up with the rows."""
    r = conn.execute(_TOTALS).fetchone()
    return {
        "nights": conn.execute("SELECT COUNT(*) FROM nights").fetchone()[0],
        "frames": r["frames"],
        "integration_s": r["integration_s"],
        "untimed": r["untimed"],
        "objects": r["objects"],
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


class Empty(StrEnum):
    """Why there are no nights: five reasons, five answers (`docs/domini/notti.md`)."""

    NO_FOLDERS = "no_folders"
    NO_FRAMES = "no_frames"
    NO_SITE = "no_site"
    READING = "reading"
    WAITING = "waiting"


_FOLDERS = "SELECT EXISTS (SELECT 1 FROM folders WHERE retired_at IS NULL)"


def empty(conn: sqlite3.Connection, waiting: list[dict[str, Any]], left: int) -> Empty | None:
    """What the user fixes first: the site before the answers, the answers before the wait."""
    if conn.execute("SELECT EXISTS (SELECT 1 FROM nights)").fetchone()[0]:
        return None
    places = {w["answer_at"] for w in waiting}
    if AnswerAt.SITE in places:
        return Empty.NO_SITE
    if places:
        return Empty.WAITING
    if left:
        return Empty.READING
    return Empty.NO_FRAMES if conn.execute(_FOLDERS).fetchone()[0] else Empty.NO_FOLDERS
