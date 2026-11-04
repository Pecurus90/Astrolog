"""The Moon and the Sun on a shot (Image Analysis par. 2.1.1): what the sky stage writes beside
each frame. One astropy call per site, for all its frames."""

import datetime as dt
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from astropy.coordinates import (
    ICRS,
    AltAz,
    EarthLocation,
    NonRotationTransformationWarning,
    SkyCoord,
    get_body,
    get_sun,
)

from . import bodies, moon


@dataclass(frozen=True, slots=True)
class MoonAndSun:
    moon_altitude_deg: float  # topocentric, geometric: no refraction
    moon_separation_deg: float | None  # from the frame centre; None: centre unknown
    moon_illumination: float  # 0 new, 1 full; geocentric, as the phase
    sun_altitude_deg: float


def moon_and_sun(
    instants: Sequence[dt.datetime],
    sites: Sequence[tuple[float, float]],
    centres: Sequence[tuple[float, float] | None],
) -> list[MoonAndSun]:
    """One per frame: its instant, its site (lat, lon East +), its centre (RA, Dec J2000)."""
    found: list[MoonAndSun | None] = [None] * len(instants)
    for site in dict.fromkeys(sites):
        at = [i for i, s in enumerate(sites) if s == site]
        for i, seen in zip(at, _from_site([instants[i] for i in at], site,
                                          [centres[i] for i in at]), strict=True):  # fmt: skip
            found[i] = seen
    return [f for f in found if f is not None]


def _from_site(
    instants: list[dt.datetime],
    site: tuple[float, float],
    centres: list[tuple[float, float] | None],
) -> list[MoonAndSun]:
    """The Moon seen from the site (its parallax is nearly a degree); the centre taken into the
    Moon's frame, so the separation is topocentric too."""
    location = EarthLocation(lat=site[0], lon=site[1])
    times = bodies.as_times(instants)
    local = AltAz(obstime=times, location=location)
    seen = get_body("moon", times, location)
    moon_alt: Any = bodies.transformed(seen, local).alt.deg  # pyright: ignore[reportOptionalMemberAccess]
    sun_alt: Any = bodies.transformed(get_sun(times), local).alt.deg  # pyright: ignore[reportOptionalMemberAccess]
    placed = [c or (0.0, 0.0) for c in centres]
    sky = SkyCoord([c[0] for c in placed], [c[1] for c in placed], unit="deg", frame=ICRS())
    with warnings.catch_warnings():  # the direction is the point: a star has no parallax
        warnings.simplefilter("ignore", NonRotationTransformationWarning)
        separation: Any = seen.separation(sky).deg  # pyright: ignore[reportArgumentType]
    lit = moon.lit_fractions(instants)
    return [
        MoonAndSun(float(moon_alt[k]), None if centres[k] is None else float(separation[k]),
                   lit[k], float(sun_alt[k]))
        for k in range(len(instants))
    ]  # fmt: skip
