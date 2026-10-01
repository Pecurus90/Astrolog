"""The Sun's altitude through the night and the sky bands it yields, sent already split (contract:
docs/domini/effemeridi.md, "Le fasce arrivano gia' divise")."""

import datetime as dt
from collections.abc import Iterator, Sequence
from typing import Any

from . import ASTRO_DEG, CIVIL_DEG, GRID_STEP_MIN, NAUTICAL_DEG, RISESET_DEG, corpi
from .grid import night_grid

# Brightest to darkest, each with the floor that holds it up; below the last floor it is dark.
FASCE = (
    ("day", RISESET_DEG),
    ("civil", CIVIL_DEG),
    ("nautical", NAUTICAL_DEG),
    ("astronomical", ASTRO_DEG),
)
BUIO = "dark"


def altitudes(istanti: Sequence[dt.datetime], latitude: float, longitude: float) -> list[float]:
    return corpi.altezze("sun", istanti, latitude, longitude)


def night_bands(
    inizio: dt.datetime, latitude: float, longitude: float, hours: float
) -> list[dict[str, Any]]:
    """The bands of a whole night, back in the zone they were asked in."""
    istanti = night_grid(inizio, hours=hours, step_min=GRID_STEP_MIN)
    fasce = sky_bands(istanti, altitudes(istanti, latitude, longitude))
    return [
        {
            **f,
            "starts_at": f["starts_at"].astimezone(inizio.tzinfo),
            "ends_at": f["ends_at"].astimezone(inizio.tzinfo),
        }
        for f in fasce
    ]


def sky_at(istanti: Sequence[dt.datetime], latitude: float, longitude: float) -> list[str]:
    """The band of each instant, without paying for a sampled night."""
    return [_fascia(a) for a in altitudes(istanti, latitude, longitude)]


def sky_bands(istanti: Sequence[dt.datetime], altezze: Sequence[float]) -> list[dict[str, Any]]:
    """Read from altitudes, not crossings, so polar cases come out by themselves. The first band
    starts and the last ends at the window's edges: an unfinished dark still counts."""
    if len(istanti) < 2:
        return []
    fasce = []
    inizio, quale = istanti[0], _fascia(altezze[0])
    for i in range(len(istanti) - 1):
        for confine, dopo in _confini(istanti[i], istanti[i + 1], altezze[i], altezze[i + 1]):
            fasce.append({"starts_at": inizio, "ends_at": confine, "kind": quale})
            inizio, quale = confine, dopo
    fasce.append({"starts_at": inizio, "ends_at": istanti[-1], "kind": quale})
    return fasce


def _fascia(altezza: float) -> str:
    for nome, pavimento in FASCE:
        if altezza > pavimento:
            return nome
    return BUIO


def _confini(
    t0: dt.datetime, t1: dt.datetime, a0: float, a1: float
) -> Iterator[tuple[dt.datetime, str]]:
    """Every threshold crossed between two samples, in crossing order: a coarse step can jump a
    whole band, and a rule that holds only on a fine grid is not a rule."""
    scendendo = a1 < a0
    soglie = [s for _, s in FASCE if min(a0, a1) <= s < max(a0, a1)]
    for soglia in sorted(soglie, reverse=scendendo):
        # The threshold lies strictly between the two altitudes, so the denominator is not zero.
        quota = (soglia - a0) / (a1 - a0)
        yield t0 + (t1 - t0) * quota, _fascia(soglia if scendendo else soglia + _UN_FILO)


# A threshold is the floor of the band above and `_fascia` compares with `>`: rising, the band
# above is asked for by stepping just over the threshold.
_UN_FILO = 1e-9
