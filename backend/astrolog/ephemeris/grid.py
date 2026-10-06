"""The time grid and the crossing of a threshold, with no astronomy: the same search serves rise,
set and twilights for the Sun and the Moon, and is testable without a sky."""

import datetime as dt
from collections.abc import Sequence
from typing import Literal


def require_zone(instant: dt.datetime) -> None:
    """Read as UTC, a naive instant would put a distant site's night half a day off."""
    if instant.tzinfo is None:
        raise ValueError(
            "un istante senza fuso non si indovina: sarebbe letto come UTC, e la notte di un"
            " sito lontano risulterebbe sbagliata di mezza giornata"
        )


def night_grid(start: dt.datetime, hours: float, step_min: int) -> list[dt.datetime]:
    """Instants every `step_min` minutes for `hours` real hours, both ends included. Built in UTC:
    wall-clock arithmetic across a DST change would bend the grid and invent crossings."""
    require_zone(start)
    base = start.astimezone(dt.UTC)
    count = round(hours * 60 / step_min)
    step = dt.timedelta(minutes=step_min)
    return [base + step * i for i in range(count + 1)]


def between(t0: dt.datetime, t1: dt.datetime, fraction: float) -> dt.datetime:
    """The instant at `fraction` of the way from `t0` to `t1`: crossings are interpolated."""
    return t0 + (t1 - t0) * fraction


def first_crossing(
    instants: Sequence[dt.datetime],
    altitudes: Sequence[float],
    threshold: float,
    direction: Literal["up", "down"],
) -> dt.datetime | None:
    """Interpolated between samples, so the step isn't the error. None, not a made-up time, when
    there is no crossing (above the polar circle the Moon can miss the horizon)."""
    offsets = [a - threshold for a in altitudes]
    for i in range(len(offsets) - 1):
        before, after = offsets[i], offsets[i + 1]
        crosses = before > 0 >= after if direction == "down" else before < 0 <= after
        if not crosses:
            continue
        # The two offsets have opposite signs, so the denominator is never zero.
        return between(instants[i], instants[i + 1], before / (before - after))
    return None
