"""Nights of a service's hourly series, noon to noon in the site's timezone. Whole or not depends
on the source: a sky source whose series starts late still gives the night under way."""

import json
import zoneinfo
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from ..clock import night_window
from ..ephemeris import ASTRO_DEG, RISESET_DEG, sun
from .verdict import Hour

# A night's date and its hours as `(index in the series, instant)`.
type Night = tuple[str, list[tuple[int, datetime]]]


def covered(timezone: str, times: Sequence[datetime], first: str, *, whole: bool) -> list[Night]:
    """From `first` on. `whole` stops at the first incomplete night; otherwise a night enters with
    whatever hours the series has."""
    if not times:
        return []
    index = {t: i for i, t in enumerate(times)}
    found = []
    day = date.fromisoformat(first)
    while True:
        start, count = night_window(day.isoformat(), timezone)
        instants = [start.astimezone(UTC) + timedelta(hours=h) for h in range(round(count))]
        pairs = [(index[t], t) for t in instants if t in index]
        if whole and len(pairs) < len(instants):
            return found
        if not whole and instants[0] > times[-1]:
            return found
        if pairs:
            found.append((day.isoformat(), pairs))
        day += timedelta(days=1)


@dataclass(frozen=True, slots=True)
class HourSky:
    """The band at the hour's instant; the share of the hour in the dark and with the Sun set."""

    band: sun.Sky
    dark: float
    down: float


def hours(
    series: Mapping[str, Sequence[Any]],
    pairs: Sequence[tuple[int, datetime]],
    tz: zoneinfo.ZoneInfo,
    sky: Mapping[datetime, HourSky] | None = None,
) -> list[Hour]:
    """`sky` adds each hour's band and shares, looked up by instant."""
    return [
        Hour(
            at=instant.astimezone(tz).isoformat(),
            sky=None if sky is None else sky[instant].band,
            values={name: values[i] for name, values in series.items()},
            dark=None if sky is None else sky[instant].dark,
            down=None if sky is None else sky[instant].down,
        )
        for i, instant in pairs
    ]


def hours_json(night: Sequence[Hour]) -> str:
    return json.dumps([h.row() for h in night])


def empty(night: Sequence[Hour]) -> bool:
    """No hour carries a value: such a night is not written."""
    return all(v is None for h in night for v in h.values.values())


# An hourly value stands for the hour around its instant; its shares are read on this grid. [T]
_STEP_MIN = 5
_OFFSETS = [timedelta(minutes=-30 + _STEP_MIN * (k + 0.5)) for k in range(60 // _STEP_MIN)]  # [T]


def sky(latitude: float, longitude: float, night_list: Sequence[Night]) -> dict[datetime, HourSky]:
    """Every hour's band and shares in a single ephemeris call."""
    instants = [t for _, pairs in night_list for _, t in pairs]
    bands = sun.sky_at(instants, latitude, longitude)
    grid = [t + d for t in instants for d in _OFFSETS]
    alts = sun.altitudes(grid, latitude, longitude)
    n = len(_OFFSETS)
    out = {}
    for i, t in enumerate(instants):
        mine = alts[i * n : (i + 1) * n]
        dark = sum(a <= ASTRO_DEG for a in mine) / n
        down = sum(a <= RISESET_DEG for a in mine) / n
        out[t] = HourSky(bands[i], dark, down)
    return out
