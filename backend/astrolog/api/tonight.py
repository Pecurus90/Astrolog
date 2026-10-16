"""The ephemerides are imported at the top, not lazily: their import is what disarms astropy's
downloads, so a lazy import would leave the process online until this route first ran."""

import sqlite3
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends

from ..clock import midnight_of, night_date, night_window, now_iso
from ..db import config
from ..ephemeris import moon, planets, sun
from ..spine.group_store import home_site
from ..units import bortle_of
from . import weather
from .deps import get_db
from .models_tonight import (
    ChartOut,
    Compass,
    MoonCalendarNightOut,
    MoonCalendarOut,
    MoonOut,
    MoonPointOut,
    PhaseKey,
    PlanetKey,
    PlanetOut,
    SiteSkyOut,
    SkyBandOut,
    SkyKind,
    SkyPointOut,
    TonightOut,
)

router = APIRouter(prefix="/api/v1", tags=["tonight"])


def _iso(instant: datetime | None) -> str | None:
    return instant.isoformat() if instant else None


def _site_sky(row: dict[str, Any]) -> SiteSkyOut:
    return SiteSkyOut(name=row["name"], sky_sqm=row["sky_sqm"], bortle=bortle_of(row["sky_sqm"]))


def _sky_band(band: sun.SkyBand) -> SkyBandOut:
    return SkyBandOut(
        starts_at=band.starts_at.isoformat(),
        ends_at=band.ends_at.isoformat(),
        kind=cast(SkyKind, band.kind),
    )


def _sky_point(point: moon.TrackPoint) -> SkyPointOut:
    return SkyPointOut(at=point.at.isoformat(), altitude_deg=point.altitude_deg)


def _next(conn: sqlite3.Connection, site_id: int, night: str, kind: str) -> str | None:
    row = conn.execute(
        "SELECT night_date FROM moon_nights WHERE site_id = ? AND night_date >= ? AND event = ?"
        " ORDER BY night_date LIMIT 1",
        (site_id, night, kind),
    ).fetchone()
    return row["night_date"] if row else None


@router.get("/moon/calendar", response_model=MoonCalendarOut)
def moon_calendar(conn: sqlite3.Connection = Depends(get_db)) -> MoonCalendarOut:
    """The home site's Moon calendar as the background round wrote it (`spine/moon_calendar.py`):
    this month and the next, each night with its Moon, the dark hours without it and whether it is
    good for broadband by the two thresholds in the settings, which travel along for the legend.
    Nothing is computed here: before the round has run, `nights` is empty."""
    prefs = config.read(conn)
    row = home_site(conn)
    home = dict(row) if row else None
    rows = (
        conn.execute(
            "SELECT * FROM moon_nights WHERE site_id = ? ORDER BY night_date", (home["id"],)
        ).fetchall()
        if home
        else []
    )
    return MoonCalendarOut(
        today=night_date(now_iso(), home["timezone"]) if home else None,
        max_pct=prefs.moon_broadband_max_pct,
        min_dark_h=prefs.moon_broadband_min_dark_h,
        nights=[
            MoonCalendarNightOut(
                date=r["night_date"],
                phase_key=r["phase_key"],
                illumination_pct=r["illumination_pct"],
                moonless_dark_s=r["moonless_dark_s"],
                event=r["event"],
                lit_side=moon.lit_side(r["phase_key"], home["latitude"]) if home else "right",
                good=bool(r["broadband_good"]),
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
    twenty-four hours: the clock-change night lasts 23 or 25. **The phase is asked at midnight**,
    not at noon: asked at the window's start, whoever looks at the bar at eleven in the evening
    would read the number of twelve hours earlier.

    **Without a home site there is nothing to say**, and it says so: `night`, `site` and `moon`
    are `null`. A Moon computed on an invented place would be a number that looks true. The site,
    when there is one, **travels with its sky**: the bar's footer writes the place and its class in
    one line, and asking two routes for them would leave a moment when the page is half done. A
    site whose time zone is missing or no longer known still comes out, without its night and its
    Moon (`night` and `moon` `null`): falling back to Greenwich would give another place's Moon
    without anyone noticing.

    **The computation is costly**, because it samples a night of sky once per body: the Sun and
    the Moon finely, the four planets of the chart at the curve's step. The
    reply carries the night it refers to, so whoever shows it knows when it has expired without
    asking again at every breath."""
    row = home_site(conn)
    if row is None:
        return TonightOut(night=None, site=None, moon=None)
    home = dict(row)

    the_night = night_date(now_iso(), home["timezone"])
    # Midnight as `clock` composes it, the instant the Nights page uses too: otherwise two screens
    # would ask the same night at two different moments.
    midnight = midnight_of(the_night, home["timezone"]) if the_night else None
    if the_night is None or midnight is None:
        # A moment later the computation would raise and the route would become a 500.
        return TonightOut(night=None, site=_site_sky(home), moon=None)
    window_start, window_hours = night_window(the_night, home["timezone"])

    moon_phase = moon.phase(midnight)
    moon_night = moon.night_track(
        window_start, home["latitude"], home["longitude"], hours=window_hours
    )
    bands = sun.night_bands(window_start, home["latitude"], home["longitude"], hours=window_hours)
    dark = [(b.starts_at, b.ends_at) for b in bands if b.kind == sun.Sky.DARK]
    moonless_left = moon.moonless_dark_left_s(moon_night, dark)
    tracks = planets.night_tracks(
        window_start, home["latitude"], home["longitude"], hours=window_hours
    )
    span = sun.chart_window(bands)
    return TonightOut(
        chart=ChartOut(
            starts_at=span.starts_at.isoformat(),
            ends_at=span.ends_at.isoformat(),
            dark_from=_iso(span.dark_from),
            dark_until=_iso(span.dark_until),
        )
        if span
        else None,
        planets=[
            PlanetOut(key=cast(PlanetKey, p.key.value), track=[_sky_point(q) for q in p.track])
            for p in tracks
        ],
        night=the_night,
        site=_site_sky(home),
        weather=weather.brief_of(conn, home["id"], the_night),
        sky_bands=[_sky_band(f) for f in bands],
        dark_s=round(sum((b - a).total_seconds() for a, b in dark)),
        moon=MoonOut(
            phase_key=cast(PhaseKey, moon_phase.phase_key),
            illumination_pct=moon_phase.illumination_pct,
            rise=_iso(moon_night.rise),
            set=_iso(moon_night.set),
            rise_compass=cast(
                Compass,
                moon.compass(
                    moon.azimuth_deg(moon_night.rise, home["latitude"], home["longitude"])
                ),
            )
            if moon_night.rise
            else None,
            age_days=round(moon.age_days(midnight)),
            distance_km=int(round(moon.distance_km(midnight), -2)),
            next_new=_next(conn, home["id"], the_night, "new"),
            next_full=_next(conn, home["id"], the_night, "full"),
            highest=_sky_point(moon_night.highest),
            track=[
                MoonPointOut(
                    at=p.at.isoformat(), altitude_deg=p.altitude_deg, moonless_dark_left_s=s
                )
                for p, s in zip(moon_night.track, moonless_left, strict=True)
            ],
            ceiling_deg=moon.sky_ceiling(home["latitude"]),
            lit_side=moon.lit_side(moon_phase.phase_key, home["latitude"]),
        ),
    )
