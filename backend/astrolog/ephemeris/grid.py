"""The time grid and the crossing of a threshold, with no astronomy: the same search serves rise,
set and twilights for the Sun and the Moon, and is testable without a sky."""

import datetime as dt
from collections.abc import Sequence
from typing import Literal


def night_grid(inizio: dt.datetime, hours: float, step_min: int) -> list[dt.datetime]:
    """Instants every `step_min` minutes for `hours` real hours, both ends included. Built in UTC:
    wall-clock arithmetic across a DST change would bend the grid and invent crossings."""
    if inizio.tzinfo is None:
        raise ValueError("una griglia senza fuso non si sa dove comincia")
    base = inizio.astimezone(dt.UTC)
    quanti = round(hours * 60 / step_min)
    passo = dt.timedelta(minutes=step_min)
    return [base + passo * i for i in range(quanti + 1)]


def first_crossing(
    istanti: Sequence[dt.datetime],
    altezze: Sequence[float],
    soglia: float,
    verso: Literal["up", "down"],
) -> dt.datetime | None:
    """Interpolated between samples, so the step isn't the error. None, not a made-up time, when
    there is no crossing (above the polar circle the Moon can miss the horizon)."""
    scarti = [a - soglia for a in altezze]
    for i in range(len(scarti) - 1):
        prima, dopo = scarti[i], scarti[i + 1]
        attraversa = prima > 0 >= dopo if verso == "down" else prima < 0 <= dopo
        if not attraversa:
            continue
        # The two offsets have opposite signs, so the denominator is never zero.
        quota = prima / (prima - dopo)
        return istanti[i] + (istanti[i + 1] - istanti[i]) * quota
    return None
