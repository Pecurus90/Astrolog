"""Where a solar-system body stands as seen from a site: shared by the Moon and the Sun, so the
most delicate computation exists once."""

import datetime as dt
from collections.abc import Sequence
from typing import Literal

from astropy.coordinates import (
    AltAz,
    BaseCoordinateFrame,
    EarthLocation,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time

from . import GRID_STEP_MIN
from .grid import night_grid, require_zone

Body = Literal["sun", "moon"]


def as_time(instant: dt.datetime) -> Time:
    require_zone(instant)
    return Time(instant.astimezone(dt.UTC))


def as_times(instants: Sequence[dt.datetime]) -> Time:
    """One `Time` for the whole list: built instant by instant it costs fifteen times more."""
    for instant in instants:
        require_zone(instant)
    return Time([i.astimezone(dt.UTC) for i in instants])


def transformed(body: SkyCoord, frame: BaseCoordinateFrame) -> SkyCoord:
    """astropy declares the transform may return nothing: checked here, so callers get a
    `SkyCoord` and don't silence the stub one by one."""
    result = body.transform_to(frame)
    if result is None:
        raise RuntimeError(f"astropy non ha convertito in {type(frame).__name__}")
    return result


def body_altitudes(
    body: Body, instants: Sequence[dt.datetime], latitude: float, longitude: float
) -> list[float]:
    """Topocentric (the Moon's parallax is nearly a degree) and geometric: refraction lives in
    `RISESET_DEG`, a threshold, not in the altitude. One astropy call for the whole grid."""
    site = EarthLocation(lat=latitude, lon=longitude)
    times = as_times(instants)
    # get_sun is the cheaper path and agrees with get_body("sun"); the Moon needs the site.
    astro = get_sun(times) if body == "sun" else get_body(body, times, site)
    local = transformed(astro, AltAz(obstime=times, location=site))
    degrees = local.alt.deg  # pyright: ignore[reportOptionalMemberAccess]
    return [float(a) for a in degrees]  # pyright: ignore[reportArgumentType, reportOptionalIterable]


def sampled_night(
    body: Body, start: dt.datetime, latitude: float, longitude: float, hours: float
) -> tuple[list[dt.datetime], list[float]]:
    """The grid of a night and the body's altitude on it, in UTC: the one costly step."""
    instants = night_grid(start, hours=hours, step_min=GRID_STEP_MIN)
    return instants, body_altitudes(body, instants, latitude, longitude)
