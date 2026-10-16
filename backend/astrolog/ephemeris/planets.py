"""The planets of the night chart. The builtin ephemeris has them all; the chart draws the four
bright ones a sky shows to the naked eye at night (Mercury stays in twilight)."""

import datetime as dt
from dataclasses import dataclass
from enum import StrEnum

from . import TRACK_STEP_MIN, bodies
from .grid import night_grid
from .moon import TrackPoint


class Planet(StrEnum):
    SATURN = "saturn"
    JUPITER = "jupiter"
    MARS = "mars"
    VENUS = "venus"


@dataclass(frozen=True, slots=True)
class PlanetNight:
    key: Planet
    track: list[TrackPoint]


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
