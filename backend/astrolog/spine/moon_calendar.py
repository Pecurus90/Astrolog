"""The Moon calendar of the home site, written by the background round: this month and the next,
each night with its Moon, its dark hours without it, and its step on the Moon rule."""

import calendar
import datetime as dt
import sqlite3

from ..clock import night_date, night_window
from ..db import config
from ..db.replace_table import replace_rows
from ..ephemeris import moon
from ..levels import moon_level
from ..site_of import Site

COLUMNS = (
    "site_id", "night_date", "latitude", "longitude", "phase_key", "illumination_pct",
    "dark_s", "moonless_dark_s", "event", "event_at", "moon_level",
)  # fmt: skip


def nights_of(today: dt.date) -> list[str]:
    """From the first of this month to the last of the next."""
    first = today.replace(day=1)
    year, month = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    last = dt.date(year, month, calendar.monthrange(year, month)[1])
    return [(first + dt.timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]


def step(conn: sqlite3.Connection, site: Site | None, today: dt.date) -> bool:
    """Rewrites only when a night is missing or the site moved; True when it did. Without a site or
    a zone there is no sky to compute."""
    if site is None or not site.timezone:
        return False
    wanted = nights_of(today)
    have = conn.execute(
        "SELECT COUNT(*) FROM moon_nights WHERE site_id = ? AND latitude = ? AND longitude = ?"
        " AND night_date BETWEEN ? AND ?",
        (site.id, site.latitude, site.longitude, wanted[0], wanted[-1]),
    ).fetchone()[0]
    if have == len(wanted):
        return False
    rebuild(conn, site, wanted)
    return True


def rebuild(conn: sqlite3.Connection, site: Site, wanted: list[str]) -> None:
    tz = site.timezone
    windows = [(d, *night_window(d, tz)) for d in wanted]
    rule = config.moon_rule(config.read(conn))
    nights = moon.calendar_nights(windows, site.latitude, site.longitude, rule.floor_deg)
    # true hours on from the start: added in UTC, else the clock-change night gains an hour
    start = windows[0][1]
    end = windows[-1][1].astimezone(dt.UTC) + dt.timedelta(hours=windows[-1][2])
    events = {}
    for e in moon.main_phases(start, end):
        when = e.at.astimezone(start.tzinfo)
        events[night_date(when.isoformat(), tz)] = (e.kind, when.isoformat())
    rows = [
        (
            site.id,
            n.night,
            site.latitude,
            site.longitude,
            n.phase_key.value,
            n.illumination_pct,
            n.dark_s,
            n.moonless_dark_s,
            *events.get(n.night, (None, None)),
            moon_level(n.illumination_pct, rule),
        )  # fmt: skip
        for n in nights
    ]
    replace_rows(conn, "moon_nights", COLUMNS, rows, where="site_id = ?", args=(site.id,))


def refresh(conn: sqlite3.Connection, site: Site | None) -> None:
    """The Moon rule changed: the same nights again, at once. Its floor moves the dark without the
    Moon, so the sky is recomputed, not only the steps."""
    if site is None or not site.timezone:
        return
    wanted = [
        r[0]
        for r in conn.execute(
            "SELECT night_date FROM moon_nights WHERE site_id = ? ORDER BY night_date", (site.id,)
        )
    ]
    if wanted:
        rebuild(conn, site, wanted)
