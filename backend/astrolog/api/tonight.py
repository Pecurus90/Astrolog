"""The ephemerides are imported at the top, not lazily: their import is what disarms astropy's
downloads, so a lazy import would leave the process online until this route first ran."""

import sqlite3
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends

from ..clock import midnight_of, night_date, night_window, now_iso
from ..ephemeris import moon, sun
from ..spine.group_store import home_site
from ..units import bortle_of
from . import weather
from .deps import get_db
from .models_tonight import (
    MoonOut,
    PhaseKey,
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

    **The computation is costly**, because it samples a night of sky twice, once per body. The
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
    return TonightOut(
        night=the_night,
        site=_site_sky(home),
        weather=weather.brief_of(conn, home["id"], the_night),
        sky_bands=[
            _sky_band(f)
            for f in sun.night_bands(
                window_start, home["latitude"], home["longitude"], hours=window_hours
            )
        ],
        moon=MoonOut(
            phase_key=cast(PhaseKey, moon_phase.phase_key),
            illumination_pct=moon_phase.illumination_pct,
            rise=_iso(moon_night.rise),
            set=_iso(moon_night.set),
            highest=_sky_point(moon_night.highest),
            track=[_sky_point(p) for p in moon_night.track],
            ceiling_deg=moon.sky_ceiling(home["latitude"]),
            lit_side=moon.lit_side(moon_phase.phase_key, home["latitude"]),
        ),
    )
