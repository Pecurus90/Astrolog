"""The ephemerides are imported at the top, not lazily: their import is what disarms astropy's
downloads, so a lazy import would leave the process online until this route first ran."""

import sqlite3
from datetime import datetime
from typing import Literal, cast

from fastapi import APIRouter, Depends

from ..clock import midnight_of, night_date, night_window, now_iso, seconds_between
from ..db import config
from ..ephemeris import moon, planets, sun
from ..levels import Verdict, moon_level
from ..site_of import Site, home_site
from ..spine import night_calendar
from ..units import bortle_of
from . import weather
from .deps import get_db
from .models_tonight import (
    ChartOut,
    Compass,
    DarkStretchOut,
    MoonCalendarNightOut,
    MoonCalendarOut,
    MoonCalendarShotOut,
    MoonInDarkOut,
    MoonOut,
    MoonPointOut,
    PhaseKey,
    PlanetKey,
    PlanetOut,
    ShootingStretchOut,
    SiteSkyOut,
    SkyBandOut,
    SkyKind,
    SkyPointOut,
    TonightOut,
)
from .models_weather import Level

router = APIRouter(prefix="/api/v1", tags=["tonight"])


def _iso(instant: datetime | None) -> str | None:
    return instant.isoformat() if instant else None


def _site_sky(row: Site) -> SiteSkyOut:
    return SiteSkyOut(name=row.name, sky_sqm=row.sky_sqm, bortle=bortle_of(row.sky_sqm))


def _sky_band(band: sun.SkyBand) -> SkyBandOut:
    return SkyBandOut(
        starts_at=band.starts_at.isoformat(),
        ends_at=band.ends_at.isoformat(),
        kind=cast(SkyKind, band.kind),
    )


def _sky_point(point: moon.TrackPoint) -> SkyPointOut:
    return SkyPointOut(at=point.at.isoformat(), altitude_deg=point.altitude_deg)


def _moon_in_dark(
    up: list[moon.Stretch], dark: list[moon.Stretch], word: Verdict
) -> MoonInDarkOut | None:
    if not up:
        return None
    return MoonInDarkOut(
        level=cast(Level, word),
        since=up[0][0].isoformat(),
        until=up[-1][1].isoformat(),
        from_start=up[0][0] == dark[0][0],
        to_end=up[-1][1] == dark[-1][1],
    )


def _planet(night: planets.PlanetNight, span: sun.ChartWindow | None) -> PlanetOut:
    track = [_sky_point(q) for q in night.track]
    out = PlanetOut(key=cast(PlanetKey, night.key.value), track=track)
    if span is None:
        return out
    inside = planets.within(night, span.starts_at, span.ends_at)
    out.rise, out.set = _iso(inside.rise), _iso(inside.set)
    out.highest = _sky_point(inside.highest)
    return out


def _highest_in(track: list[moon.TrackPoint], span: sun.ChartWindow | None) -> SkyPointOut | None:
    inside = [p for p in track if span and span.starts_at <= p.at <= span.ends_at]
    return _sky_point(max(inside, key=lambda p: p.altitude_deg)) if inside else None


def _highest_planet(out: list[PlanetOut]) -> PlanetKey | None:
    up = [p for p in out if p.highest and p.highest.altitude_deg > planets.PLANET_RISESET_DEG]
    if not up:
        return None
    return max(up, key=lambda p: p.highest.altitude_deg if p.highest else 0.0).key


def _shooting(spans: moon.DarkSpans, word: Verdict) -> list[ShootingStretchOut]:
    """Moonless and Moon-up stretches in time order, each with its band; neighbours of one band
    join, so a dim Moon rising adds no seam."""
    narrow = word == Verdict.NOGO
    marked = sorted(
        [(a, b, "broadband") for a, b in spans.moonless]
        + [(a, b, "narrowband" if narrow else "broadband") for a, b in spans.moon_up]
    )
    joined: list[tuple[datetime, datetime, str]] = []
    for a, b, band in marked:
        if joined and joined[-1][2] == band and joined[-1][1] == a:
            joined[-1] = (joined[-1][0], b, band)
        else:
            joined.append((a, b, band))
    return [
        ShootingStretchOut(
            band=cast(Literal["broadband", "narrowband"], band),
            starts_at=a.isoformat(),
            ends_at=b.isoformat(),
            seconds=round(seconds_between(a, b)),
        )
        for a, b, band in joined
    ]


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
    home = home_site(conn)
    if home is None:
        return TonightOut(night=None, site=None, moon=None)

    the_night = night_date(now_iso(), home.timezone)
    # Midnight as `clock` composes it, the instant the Nights page uses too: otherwise two screens
    # would ask the same night at two different moments.
    midnight = midnight_of(the_night, home.timezone) if the_night else None
    if the_night is None or midnight is None:
        # A moment later the computation would raise and the route would become a 500.
        return TonightOut(night=None, site=_site_sky(home), moon=None)
    window_start, window_hours = night_window(the_night, home.timezone)

    moon_phase = moon.phase(midnight)
    moon_night = moon.night_track(window_start, home.latitude, home.longitude, hours=window_hours)
    bands = sun.night_bands(window_start, home.latitude, home.longitude, hours=window_hours)
    dark = [(b.starts_at, b.ends_at) for b in bands if b.kind == sun.Sky.DARK]
    rule = config.moon_rule(config.read(conn))
    moonless_left = moon.moonless_dark_left_s(moon_night, dark, rule.floor_deg)
    spans = moon.dark_spans(moon_night, dark, rule.floor_deg)
    tracks = planets.night_tracks(window_start, home.latitude, home.longitude, hours=window_hours)
    span = sun.chart_window(bands)
    shooting = _shooting(spans, moon_level(moon_phase.illumination_pct, rule))
    planets_out = [_planet(p, span) for p in tracks]
    dark_s = round(sum(seconds_between(a, b) for a, b in dark))
    return TonightOut(
        dark_returns=None if dark_s else sun.dark_returns(the_night, home.latitude, home.longitude),
        highest_planet=_highest_planet(planets_out),
        shooting=shooting,
        broadband_dark_s=sum(s.seconds for s in shooting if s.band == "broadband"),
        narrowband_dark_s=sum(s.seconds for s in shooting if s.band == "narrowband"),
        chart=ChartOut(
            starts_at=span.starts_at.isoformat(),
            ends_at=span.ends_at.isoformat(),
            dark_from=_iso(span.dark_from),
            dark_until=_iso(span.dark_until),
        )
        if span
        else None,
        planets=planets_out,
        night=the_night,
        site=_site_sky(home),
        weather=weather.brief_of(conn, home.id, the_night),
        sky_bands=[_sky_band(f) for f in bands],
        dark_s=dark_s,
        moonless_dark=[
            DarkStretchOut(starts_at=a.isoformat(), ends_at=b.isoformat())
            for a, b in spans.moonless
        ],
        moon_in_dark=_moon_in_dark(
            spans.moon_up, dark, moon_level(moon_phase.illumination_pct, rule)
        ),
        moon=MoonOut(
            phase_key=cast(PhaseKey, moon_phase.phase_key),
            illumination_pct=moon_phase.illumination_pct,
            rise=_iso(moon_night.rise),
            set=_iso(moon_night.set),
            rise_compass=cast(
                Compass,
                moon.compass(moon.azimuth_deg(moon_night.rise, home.latitude, home.longitude)),
            )
            if moon_night.rise
            else None,
            age_days=round(moon.age_days(midnight)),
            distance_km=int(round(moon.distance_km(midnight), -2)),
            next_new=_next(conn, home, the_night, "new"),
            next_full=_next(conn, home, the_night, "full"),
            highest=_sky_point(moon_night.highest),
            highest_in_chart=_highest_in(moon_night.track, span),
            track=[
                MoonPointOut(
                    at=p.at.isoformat(), altitude_deg=p.altitude_deg, moonless_dark_left_s=s
                )
                for p, s in zip(moon_night.track, moonless_left, strict=True)
            ],
            ceiling_deg=moon.sky_ceiling(home.latitude),
            lit_side=moon.lit_side(moon_phase.phase_key, home.latitude),
        ),
    )
