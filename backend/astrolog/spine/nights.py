"""The Nights page, read from what `group` wrote: a night is a date plus a site and one row, its
objects and filters inside, or the hours would split and two rows look like duplicates."""

import json
import sqlite3
from collections.abc import Sequence
from typing import Any

from ..clock import midnight_of
from ..db import idlist
from ..ephemeris import moon
from . import counts, filters_used, stages
from . import objects as obj
from .group import (
    NO_ACTIVE_SITE,
    NO_DATE,
    NO_OBJECT,
    SITE_NO_TIMEZONE,
    SITE_UNCLEAR,
)

# Where a frame no night took is answered: one waiting for its site, or one with nothing to answer
# (no date), sent to the review page would find a list with nothing for it.
REVIEW, SITE, NEVER = "review", "site", "never"
_DOVE = {
    SITE_UNCLEAR: REVIEW,
    NO_OBJECT: REVIEW,
    NO_ACTIVE_SITE: SITE,
    SITE_NO_TIMEZONE: SITE,
    NO_DATE: NEVER,
}

# The caller passes the observed weather's kind.
_PAGINA = f"""
SELECT n.id, n.night_date, n.site_source, s.name AS site, s.timezone, w.summary_json AS meteo,
       {counts.counts_on("night")}
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN weather_nights w
  ON w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
ORDER BY n.night_date DESC, n.id DESC
LIMIT ? OFFSET ?
"""  # noqa: S608 - constant fragments of the spine, not user values

_QUANTE = "SELECT COUNT(*) FROM nights"

_TOTALI = f"SELECT{counts.counts_on('archive')}"

# Asked for the whole page at once, never per row.
_OGGETTI = f"""
SELECT f.night_id, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id
WHERE f.night_id IN {{listed}} AND f.copy_of IS NULL
GROUP BY f.night_id, o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - `listed` is a placeholder, not a value

# `group` is the last stage to look at them: a frame another stage skipped stops here with its code.
_FERME = """
SELECT s.reason, COUNT(*) AS frames
FROM frame_stages s JOIN frames f ON f.id = s.frame_id
WHERE s.stage = 'group' AND s.status = 'skipped' AND f.copy_of IS NULL
GROUP BY s.reason ORDER BY frames DESC, s.reason
"""


def _lune(righe: Sequence[sqlite3.Row]) -> dict[int, dict[str, Any]]:
    """One call to the sky, at midnight in the site's zone; a night without a known zone is left
    out. Not stored: a derivable number frozen in a column would outlive a corrected formula."""
    quando = {r["id"]: midnight_of(r["night_date"], r["timezone"]) for r in righe}
    certe = {i: q for i, q in quando.items() if q is not None}
    return dict(zip(certe, moon.phases(list(certe.values())), strict=True))


def page(
    conn: sqlite3.Connection, *, limit: int, offset: int, observed: str
) -> list[dict[str, Any]]:
    """Most recent first; `observed` is the kind of the weather rows, known to their writer."""
    righe = conn.execute(_PAGINA, (observed, limit, offset)).fetchall()
    ids = [r["id"] for r in righe]
    lune = _lune(righe)
    oggetti = idlist.grouped(conn, _OGGETTI, ids, "night_id", obj.counted)
    filtri = filters_used.of(conn, "night", ids)
    return [
        {
            "id": r["id"],
            "night_date": r["night_date"],
            "site": r["site"],
            "site_source": r["site_source"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
            "objects": oggetti.get(r["id"], []),
            "filters": filtri.get(r["id"], []),
            "moon": lune.get(r["id"]),
            "weather": _meteo(r, fuso_riconosciuto=r["id"] in lune),
        }
        for r in righe
    ]


def _meteo(riga: sqlite3.Row, *, fuso_riconosciuto: bool) -> dict[str, Any]:
    """`unknown` when the site's zone is not recognised, so its nights cannot be split; `waiting`
    when the night is too young for the reanalysis or the history has not reached it."""
    if riga["meteo"] is not None:
        return {"state": "ok", **json.loads(riga["meteo"])}
    # whether `_lune` found the zone: one test for Moon and weather
    return {"state": "waiting" if fuso_riconosciuto else "unknown", **_SENZA_CIELO}


# Every field, empty, as the response shape wants them.
_SENZA_CIELO = dict.fromkeys(
    ("verdict", "cloud_total_pct", "usable_hours", "window", "window_hours")
)


def how_many(conn: sqlite3.Connection) -> int:
    return conn.execute(_QUANTE).fetchone()[0]


def archive_totals(conn: sqlite3.Connection) -> dict[str, Any]:
    """Only what lies inside a night, or the top number would not add up with the rows."""
    r = conn.execute(_TOTALI).fetchone()
    return {
        "nights": how_many(conn),
        "frames": r["frames"],
        "integration_s": r["integration_s"],
        "untimed": r["untimed"],
    }


def waiting(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """By where the answer is given, largest first. An unmapped reason is `never`: better nowhere
    than the wrong place."""
    somme: dict[str, int] = {}
    for r in conn.execute(_FERME):
        dove = _DOVE.get(r["reason"], NEVER)
        somme[dove] = somme.get(dove, 0) + r["frames"]
    ordinati = sorted(somme.items(), key=lambda voce: (-voce[1], voce[0]))
    return [{"answer_at": dove, "frames": quanti} for dove, quanti in ordinati]


def still_reading(conn: sqlite3.Connection) -> int:
    """`group`'s residue, not the sum of stages: a frame stuck at `solve` would count three times,
    and `measure`, which nobody runs yet, would never reach zero."""
    return stages.count_pending(conn, "group")
