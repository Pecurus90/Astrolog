"""The Nights' calendar (`docs/domini/notti.md`): a month of nights, one sign per night with the
verdict of its sky, and the month's totals; from the first month with nights to tonight's."""

import datetime as dt
import sqlite3
from typing import Any

from ..levels import Verdict
from . import counts

_MONTH = f"""
SELECT n.id, n.night_date, s.name AS site,
       json_extract(w.summary_json, '$.verdict') AS verdict,
       {counts.counts_on(counts.Subject.NIGHT)}
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN weather_nights w
  ON w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
WHERE n.night_date >= ? AND n.night_date < ?
ORDER BY n.night_date, s.name COLLATE NOCASE, n.id
"""  # noqa: S608 - constant fragments of the spine

_FIRST = "SELECT substr(MIN(night_date), 1, 7) FROM nights"


def _next(month: dt.date) -> dt.date:
    return (month.replace(day=28) + dt.timedelta(days=4)).replace(day=1)


def month(
    conn: sqlite3.Connection, first_day: dt.date, kind: str, tonight: dt.date
) -> dict[str, Any]:
    """Days in order, each with its nights (two sites, two signs); `good` counts the go ones."""
    rows = conn.execute(
        _MONTH, (kind, first_day.isoformat(), _next(first_day).isoformat())
    ).fetchall()
    days: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        day = int(r["night_date"][8:10])
        days.setdefault(day, []).append({"id": r["id"], "site": r["site"], "verdict": r["verdict"]})
    return {
        "month": first_day.isoformat()[:7],
        "days": [{"day": d, "nights": ns} for d, ns in days.items()],
        "nights": len(rows),
        "good": sum(r["verdict"] == Verdict.GO for r in rows),
        "integration_s": float(sum(r["integration_s"] for r in rows)),
        "untimed": sum(r["untimed"] for r in rows),
        "first_month": conn.execute(_FIRST).fetchone()[0],
        "last_month": tonight.isoformat()[:7],
    }
