"""The Sun's altitude through the night and the sky bands it yields, sent already split (contract:
docs/domini/effemeridi.md, "Le fasce arrivano gia' divise")."""

import datetime as dt
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum

from . import ASTRO_DEG, CIVIL_DEG, NAUTICAL_DEG, RISESET_DEG, bodies
from .grid import between


class Sky(StrEnum):
    DAY = "day"
    CIVIL = "civil"
    NAUTICAL = "nautical"
    ASTRONOMICAL = "astronomical"
    DARK = "dark"


# Brightest to darkest, each with the floor that holds it up; below the last floor it is dark.
FLOORS = (
    (Sky.DAY, RISESET_DEG),
    (Sky.CIVIL, CIVIL_DEG),
    (Sky.NAUTICAL, NAUTICAL_DEG),
    (Sky.ASTRONOMICAL, ASTRO_DEG),
)


@dataclass(frozen=True, slots=True)
class SkyBand:
    starts_at: dt.datetime
    ends_at: dt.datetime
    kind: Sky


def altitudes(instants: Sequence[dt.datetime], latitude: float, longitude: float) -> list[float]:
    return bodies.body_altitudes("sun", instants, latitude, longitude)


def night_bands(
    start: dt.datetime, latitude: float, longitude: float, hours: float
) -> list[SkyBand]:
    """The bands of a whole night, back in the zone they were asked in."""
    instants, alts = bodies.sampled_night("sun", start, latitude, longitude, hours)
    return [
        SkyBand(b.starts_at.astimezone(start.tzinfo), b.ends_at.astimezone(start.tzinfo), b.kind)
        for b in sky_bands(instants, alts)
    ]


def sky_at(instants: Sequence[dt.datetime], latitude: float, longitude: float) -> list[Sky]:
    """The band of each instant, without paying for a sampled night."""
    return [_band_of(a) for a in altitudes(instants, latitude, longitude)]


def sky_bands(instants: Sequence[dt.datetime], alts: Sequence[float]) -> list[SkyBand]:
    """Read from altitudes, not crossings, so polar cases come out by themselves. The first band
    starts and the last ends at the window's edges: an unfinished dark still counts."""
    if len(instants) < 2:
        return []
    bands = []
    start, kind = instants[0], _band_of(alts[0])
    for i in range(len(instants) - 1):
        for edge, after in _crossings(instants[i], instants[i + 1], alts[i], alts[i + 1]):
            bands.append(SkyBand(start, edge, kind))
            start, kind = edge, after
    bands.append(SkyBand(start, instants[-1], kind))
    return bands


def _band_of(altitude: float) -> Sky:
    for name, floor in FLOORS:
        if altitude > floor:
            return name
    return Sky.DARK


def _crossings(
    t0: dt.datetime, t1: dt.datetime, a0: float, a1: float
) -> Iterator[tuple[dt.datetime, Sky]]:
    """Every threshold crossed between two samples, in crossing order: a coarse step can jump a
    whole band, and a rule that holds only on a fine grid is not a rule."""
    falling = a1 < a0
    thresholds = [s for _, s in FLOORS if min(a0, a1) <= s < max(a0, a1)]
    for threshold in sorted(thresholds, reverse=falling):
        # The threshold lies strictly between the two altitudes, so the denominator is not zero.
        at = between(t0, t1, (threshold - a0) / (a1 - a0))
        yield at, _band_of(threshold if falling else threshold + _HAIR)


# A threshold is the floor of the band above and `_band_of` compares with `>`: rising, the band
# above is asked for by stepping just over the threshold.
_HAIR = 1e-9
