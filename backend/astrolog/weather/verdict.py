"""A night's verdict, its clear hours and the hours worth showing. Only total cover makes the
verdict, blocking every object alike; the other measures weigh beside it (`judge`)."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from ..ephemeris.sun import Sky

# Okta (WMO Code Table 2700) as METAR classes (ICAO Annex 3): go to FEW 2/8, marginal to SCT 4/8.
# https://www.nodc.noaa.gov/archive/arc0021/0000907/1.1/data/0-data/HTML/WMO-CODE/WMO2700.HTM
CLOUD_GO_MAX_PCT = 25.0
CLOUD_MARGINAL_MAX_PCT = 50.0


class Verdict(StrEnum):
    GO = "go"
    MARGINAL = "marginal"
    NOGO = "nogo"


class Window(StrEnum):
    DARK = "dark"
    SUN_DOWN = "sun_down"


@dataclass(frozen=True, slots=True)
class Hour:
    """An hour of a night: its local instant, its sky band when the source needs one, and the
    source's quantities by our names."""

    at: str
    sky: Sky | None
    values: dict[str, Any]

    def row(self) -> dict[str, Any]:
        """As written in `hourly_json`: a source without sky bands has no `sky` key."""
        head = {"at": self.at} if self.sky is None else {"at": self.at, "sky": self.sky}
        return {**head, **self.values}


type Bites = Callable[[Hour], bool]


@dataclass(frozen=True, slots=True)
class Summary:
    """`usable_*` is the clear hours as an interval and a count; `shown_*` runs from the last hour
    of day before twilight to the first after dawn, the stretch the page draws."""

    verdict: Verdict | None
    cloud_total_pct: float | None
    usable_hours: int | None
    usable_since: str | None
    usable_until: str | None
    window: Window | None
    window_hours: int
    shown_from: str | None
    shown_until: str | None
    wind_700hpa_kmh: float | None


def window(hours: Sequence[Hour]) -> tuple[list[Hour], Window | None]:
    """The dark, else the hours with the Sun below the horizon, and which of the two; none where
    the Sun never sets. Afternoon clouds never weigh on the night."""
    dark = [h for h in hours if h.sky == Sky.DARK]
    if dark:
        return dark, Window.DARK
    down = [h for h in hours if h.sky != Sky.DAY]
    return (down, Window.SUN_DOWN) if down else ([], None)


def _values(hours: Sequence[Hour], field: str) -> list[Any]:
    return [h.values[field] for h in hours if h.values.get(field) is not None]


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def when(
    hours: Sequence[Hour], bites: Bites, after: Mapping[str, str]
) -> tuple[str | None, str | None, int]:
    """Start of the first hit hour, end of the last, and the count, so a patchy window does not
    look full. The end is the next hour of the night, not +60 min: clocks jump on change night."""
    hit = [h.at for h in hours if bites(h)]
    if not hit:
        return None, None, 0
    last = hit[-1]
    end = after.get(last) or (datetime.fromisoformat(last) + timedelta(hours=1)).isoformat()
    return hit[0], end, len(hit)


def _verdict(clouds: float | None) -> Verdict | None:
    if clouds is None:
        return None
    if clouds <= CLOUD_GO_MAX_PCT:
        return Verdict.GO
    return Verdict.MARGINAL if clouds <= CLOUD_MARGINAL_MAX_PCT else Verdict.NOGO


def _shown(hours: Sequence[Hour]) -> tuple[str | None, str | None]:
    night = [i for i, h in enumerate(hours) if h.sky != Sky.DAY]
    if not night:
        return None, None
    first, last = night[0], night[-1]
    return hours[max(first - 1, 0)].at, hours[min(last + 1, len(hours) - 1)].at


def assess(hours: Sequence[Hour]) -> Summary:
    """Verdict and usable hours are `None` unless every night hour reports `cloud_total_pct`.
    Usable hours are the night's hours the verdict would call clear, so the two never disagree."""
    night, span = window(hours)
    after = {h.at: n.at for h, n in zip(hours, hours[1:], strict=False)}
    cover: list[Any] = [h.values.get("cloud_total_pct") for h in night]
    complete = bool(night) and None not in cover
    clouds = _mean([c for c in cover if c is not None]) if complete else None
    since, until, clear = when(
        night,
        lambda h: (c := h.values.get("cloud_total_pct")) is not None and c <= CLOUD_GO_MAX_PCT,
        after,
    )
    shown_from, shown_until = _shown(hours)
    return Summary(
        verdict=_verdict(clouds),
        cloud_total_pct=clouds,
        usable_hours=clear if complete else None,
        usable_since=since if complete else None,
        usable_until=until if complete else None,
        window=span,
        window_hours=len(night),
        shown_from=shown_from,
        shown_until=shown_until,
        wind_700hpa_kmh=_mean(_values(night, "wind_700hpa_kmh")),
    )
