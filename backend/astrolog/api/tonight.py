"""Tonight and the Moon calendar, as written: the sky is computed by `tonight_sky` and by the Moon
calendar's round, never here (#96)."""

import sqlite3

from fastapi import APIRouter, Depends

from ..clock import night_date, now_iso
from ..db import config
from ..ephemeris import moon
from ..site_of import Site, home_site
from ..spine import night_calendar
from ..units import bortle_of
from . import weather
from .deps import get_db
from .models_tonight import (
    MoonCalendarNightOut,
    MoonCalendarOut,
    MoonCalendarShotOut,
    SiteSkyOut,
    TonightOut,
)

router = APIRouter(prefix="/api/v1", tags=["tonight"])


def _site_sky(row: Site) -> SiteSkyOut:
    return SiteSkyOut(name=row.name, sky_sqm=row.sky_sqm, bortle=bortle_of(row.sky_sqm))


# Only the rows written for where the site is now: a moved site has none until the round rewrites.
_HERE = "site_id = ? AND latitude = ? AND longitude = ?"


def _here(site: Site) -> tuple[int, float, float]:
    return site.id, site.latitude, site.longitude


def _next(conn: sqlite3.Connection, site: Site, night: str, kind: str) -> str | None:
    row = conn.execute(
        f"SELECT night_date FROM moon_nights WHERE {_HERE} AND night_date >= ? AND event = ?"  # noqa: S608
        " ORDER BY night_date LIMIT 1",
        (*_here(site), night, kind),
    ).fetchone()
    return row["night_date"] if row else None


@router.get("/moon/calendar", response_model=MoonCalendarOut)
def moon_calendar(conn: sqlite3.Connection = Depends(get_db)) -> MoonCalendarOut:
    """The home site's Moon calendar as the background round wrote it (`spine/moon_calendar.py`):
    this month and the next, each night with its Moon, its dark hours, those without the Moon (the
    next nights say them even without a forecast), its step on the settings' Moon rule, whose two
    bounds travel along for the legend, and the nights shot that day from any site (SQL sums).
    Nothing is computed here: before the round has run, `nights` is empty."""
    prefs = config.read(conn)
    home = home_site(conn)
    rows = (
        conn.execute(
            f"SELECT * FROM moon_nights WHERE {_HERE} ORDER BY night_date",  # noqa: S608
            _here(home),
        ).fetchall()
        if home
        else []
    )
    shot = night_calendar.shots(conn, rows[0]["night_date"], rows[-1]["night_date"]) if rows else {}
    return MoonCalendarOut(
        today=night_date(now_iso(), home.timezone) if home else None,
        good_pct=prefs.moon_good_pct,
        limit_pct=prefs.moon_limit_pct,
        nights=[
            MoonCalendarNightOut(
                date=r["night_date"],
                phase_key=r["phase_key"],
                illumination_pct=r["illumination_pct"],
                dark_s=r["dark_s"],
                moonless_dark_s=r["moonless_dark_s"],
                event=r["event"],
                lit_side=moon.lit_side(r["phase_key"], home.latitude) if home else "right",
                level=r["moon_level"],
                shots=[MoonCalendarShotOut(**s) for s in shot.get(r["night_date"], [])],
            )
            for r in rows
        ],
    )


@router.get("/tonight", response_model=TonightOut)
def tonight(conn: sqlite3.Connection = Depends(get_db)) -> TonightOut:
    """Tonight's Moon from the home site, with the night's sky bands and its forecast summary.

    **The night is the app's**, noon to noon in the site's time zone (`clock.night_date`), not a
    calendar day: whoever looks at two in the morning is still in last night, and wants last
    night's Moon. The window is measured **between the two true noons**, not at a fixed
    twenty-four hours: the clock-change night lasts 23 or 25. The phase is the one at midnight.

    **Without a home site there is nothing to say**, and it says so: `night`, `site` and `moon`
    are `null`. A Moon computed on an invented place would be a number that looks true. The site,
    when there is one, **travels with its sky**: the bar's footer writes the place and its class in
    one line, and asking two routes for them would leave a moment when the page is half done. A
    site whose time zone is missing or no longer known still comes out, without its night and its
    Moon (`night` and `moon` `null`): falling back to Greenwich would give another place's Moon
    without anyone noticing. The same reply comes while the sky of the night is not written yet.

    **Nothing is computed here** (#96): the sky is the one `tonight_sky` wrote for this night and
    for where the site is now -- at start, every minute from the background round, and at once
    when the sites or the Moon rule change. The reply carries the night it refers to, so whoever
    shows it knows when it has expired without asking again at every breath."""
    home = home_site(conn)
    if home is None:
        return TonightOut(night=None, site=None, moon=None)
    the_night = night_date(now_iso(), home.timezone)
    row = (
        conn.execute(
            f"SELECT sky_json FROM tonight_sky WHERE {_HERE} AND timezone = ?"  # noqa: S608
            " AND night_date = ?",
            (*_here(home), home.timezone, the_night),
        ).fetchone()
        if the_night
        else None
    )
    if the_night is None or row is None:
        return TonightOut(night=None, site=_site_sky(home), moon=None)
    out = TonightOut.model_validate_json(row["sky_json"])
    out.site = _site_sky(home)
    out.weather = weather.brief_of(conn, home.id, the_night)
    out.next_good = weather.next_good_of(conn, home.id, the_night)
    if out.moon is not None:
        out.moon.next_new = _next(conn, home, the_night, "new")
        out.moon.next_full = _next(conn, home, the_night, "full")
    return out
