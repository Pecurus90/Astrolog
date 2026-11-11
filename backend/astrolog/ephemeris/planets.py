"""The planets of the night chart. The builtin ephemeris has them all; the chart draws the four
bright ones a sky shows to the naked eye at night (Mercury stays in twilight)."""

import datetime as dt
from dataclasses import dataclass
from enum import StrEnum

from . import TRACK_STEP_MIN, bodies
from .grid import first_crossing, night_grid
from .moon import TrackPoint

# A point source rises at refraction 34' alone, no radius.
# [C USNO https://aa.usno.navy.mil/faq/RST_defs: stars and planets at zenith distance 90d 34m]
PLANET_RISESET_DEG = -0.5667


class Planet(StrEnum):
    SATURN = "saturn"
    JUPITER = "jupiter"
    MARS = "mars"
    VENUS = "venus"


@dataclass(frozen=True, slots=True)
class PlanetNight:
    key: Planet
    track: list[TrackPoint]


@dataclass(frozen=True, slots=True)
class PlanetSpan:
    """A planet inside a stretch: its first rise and set there (None: not there), and its top."""

    rise: dt.datetime | None
    set: dt.datetime | None
    highest: TrackPoint


def within(night: PlanetNight, start: dt.datetime, end: dt.datetime) -> PlanetSpan:
    """On the drawn track, interpolated: the chart and its legend read the same curve."""
    points = [p for p in night.track if start <= p.at <= end] or night.track
    instants = [p.at for p in points]
    alts = [p.altitude_deg for p in points]
    return PlanetSpan(
        rise=first_crossing(instants, alts, PLANET_RISESET_DEG, "up"),
        set=first_crossing(instants, alts, PLANET_RISESET_DEG, "down"),
        highest=max(points, key=lambda p: p.altitude_deg),
    )


def night_tracks(
    start: dt.datetime, latitude: float, longitude: float, hours: float
) -> list[PlanetNight]:
    """Sampled straight at the curve's step: no rise or set is searched, so the fine grid the Moon
    needs would cost five times more for nothing. Answered in `start`'s zone."""
    instants = night_grid(start, hours=hours, step_min=TRACK_STEP_MIN)
    local = [i.astimezone(start.tzinfo) for i in instants]
    return [
        PlanetNight(
            key=planet,
            track=[
                TrackPoint(at, round(alt, 1))
                for at, alt in zip(
                    local,
                    bodies.body_altitudes(planet.value, instants, latitude, longitude),
                    strict=True,
                )
            ],
        )
        for planet in Planet
    ]
