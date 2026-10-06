"""Nights of a service's hourly series, noon to noon in the site's timezone. Whole or not depends
on the source: one not sampling every hour (7Timer) would never have a whole night."""

import json
import zoneinfo
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

from ..clock import night_window
from ..ephemeris import sun
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


def hours(
    series: Mapping[str, Sequence[Any]],
    pairs: Sequence[tuple[int, datetime]],
    tz: zoneinfo.ZoneInfo,
    sky: Mapping[datetime, sun.Sky] | None = None,
) -> list[Hour]:
    """`sky` adds each hour's band, looked up by instant (for the forecast)."""
    return [
        Hour(
            at=instant.astimezone(tz).isoformat(),
            sky=None if sky is None else sky[instant],
            values={name: values[i] for name, values in series.items()},
        )
        for i, instant in pairs
    ]


def hours_json(night: Sequence[Hour]) -> str:
    return json.dumps([h.row() for h in night])


def empty(night: Sequence[Hour]) -> bool:
    """No hour carries a value: such a night is not written."""
    return all(v is None for h in night for v in h.values.values())


def sky(latitude: float, longitude: float, night_list: Sequence[Night]) -> dict[datetime, sun.Sky]:
    """Every hour's sky band in a single ephemeris call."""
    instants = [t for _, pairs in night_list for _, t in pairs]
    bands = sun.sky_at(instants, latitude, longitude)
    return {t: bands[i] for i, t in enumerate(instants)}
