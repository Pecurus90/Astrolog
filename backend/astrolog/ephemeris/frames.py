"""The Moon and the Sun on a shot (Image Analysis par. 2.1.1): what the sky stage writes beside
each frame. One ephemeris call per body and site, for all its frames."""

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from skyfield.functions import angle_between

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
) -> list[MoonAndSun | None]:
    """One per frame: its instant, its site (lat, lon East +), its centre (RA, Dec J2000). None:
    an instant outside DE421, a header's wrong clock, so one frame never sinks the others."""
    found: list[MoonAndSun | None] = [None] * len(instants)
    for site in dict.fromkeys(sites):
        at = [i for i, s in enumerate(sites) if s == site and bodies.covers(instants[i])]
        if not at:
            continue
        for i, seen in zip(at, _from_site([instants[i] for i in at], site,
                                          [centres[i] for i in at]), strict=True):  # fmt: skip
            found[i] = seen
    return found


def _directions(centres: list[tuple[float, float] | None]) -> np.ndarray:
    """Unit vectors on ICRS axes, (3, n); an unknown centre points anywhere, its answer is None."""
    ra, dec = (np.radians([(c or (0.0, 0.0))[k] for c in centres]) for k in (0, 1))
    return np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])


def _from_site(
    instants: list[dt.datetime],
    site: tuple[float, float],
    centres: list[tuple[float, float] | None],
) -> list[MoonAndSun]:
    """The Moon seen from the site (parallax nearly a degree). Separation without aberration on
    both sides: a catalogue star has none, and the Moon's light time is in."""
    toward = bodies.astrometric("moon", instants, site)
    moon_alt = np.asarray(toward.apparent().altaz()[0].degrees)
    sun_alt = np.asarray(bodies.observed("sun", instants, site).altaz()[0].degrees)
    separation = np.degrees(angle_between(toward.position.au, _directions(centres)))
    lit = moon.lit_fractions(instants)
    return [
        MoonAndSun(float(moon_alt[k]), None if centres[k] is None else float(separation[k]),
                   lit[k], float(sun_alt[k]))
        for k in range(len(instants))
    ]  # fmt: skip
