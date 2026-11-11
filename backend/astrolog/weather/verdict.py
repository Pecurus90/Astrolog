"""A night's hours, its window and the shape of its summary. The verdict comes from the hourly
Transparency (`score`, ADR 0034); the clouds keep their own okta word beside it (`judge`)."""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from ..ephemeris.sun import Sky
from ..levels import Verdict

# [C WMO/ICAO code D-8: FEW 1-2 oktas, SCT 3-4] go to FEW 2/8, marginal to SCT 4/8.
# https://codes.wmo.int/49-2/CloudAmountReportedAtAerodrome
CLOUD_GO_MAX_PCT = 25.0
CLOUD_MARGINAL_MAX_PCT = 50.0  # [C WMO/ICAO code D-8: SCT up to 4 oktas]


class SkyWord(StrEnum):
    """The night's sky in words, from the mean cover in the dark in okta (WMO 2700, METAR classes;
    docs/domini/meteo.md): 0 clear, 1-4 scattered (FEW and SCT), 5-7 broken, 8 overcast."""

    CLEAR = "clear"
    SCATTERED = "scattered"
    BROKEN = "broken"
    OVERCAST = "overcast"


def sky_word(cloud_pct: float | None) -> SkyWord | None:
    """The nearest eighth of the sky, then its class; 0 and 8 only for a bare or full sky (WMO)."""
    if cloud_pct is None:
        return None
    if cloud_pct <= 0:
        return SkyWord.CLEAR
    if cloud_pct >= 100:
        return SkyWord.OVERCAST
    eighths = math.floor(cloud_pct / 12.5 + 0.5)
    return SkyWord.SCATTERED if eighths <= 4 else SkyWord.BROKEN


class Window(StrEnum):
    DARK = "dark"
    SUN_DOWN = "sun_down"


@dataclass(frozen=True, slots=True)
class Hour:
    """An hour: local instant, sky band, quantities by our names. `dark`/`down`: share of the hour
    around `at` in the dark and with the Sun set; without them the band at `at` stands for all."""

    at: str
    sky: Sky | None
    values: dict[str, Any]
    dark: float | None = None
    down: float | None = None

    @property
    def dark_share(self) -> float:
        return self.dark if self.dark is not None else float(self.sky == Sky.DARK)

    @property
    def down_share(self) -> float:
        return self.down if self.down is not None else float(self.sky not in (None, Sky.DAY))

    def row(self) -> dict[str, Any]:
        """As written in `hourly_json`: a source without sky bands has no `sky` key."""
        if self.sky is None:
            return {"at": self.at, **self.values}
        return {"at": self.at, "sky": self.sky, "dark": self.dark, "down": self.down, **self.values}


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
    # score v4 (ADR 0034, `score.py`): None without every window hour's clouds
    transparency: float | None = None
    exposure_hours: float | None = None
    broadband_exposure_hours: float | None = None
    narrowband_exposure_hours: float | None = None
    dark_hours: float = 0.0
    without_aerosol: bool = False


def window(hours: Sequence[Hour]) -> tuple[list[Hour], Window | None]:
    """The dark, else the hours with the Sun below the horizon, and which of the two; none where
    the Sun never sets. Afternoon clouds never weigh on the night."""
    dark = [h for h in hours if h.sky == Sky.DARK]
    if dark:
        return dark, Window.DARK
    down = [h for h in hours if h.sky != Sky.DAY]
    return (down, Window.SUN_DOWN) if down else ([], None)


def weighted(hours: Sequence[Hour]) -> tuple[list[tuple[Hour, float]], Window | None]:
    """Every hour holding some of the dark, with its share; else of the Sun set. Only the score
    weighs edge hours: the clear hours and the measures keep `window`."""
    dark = [(h, h.dark_share) for h in hours if h.dark_share > 0]
    if dark:
        return dark, Window.DARK
    down = [(h, h.down_share) for h in hours if h.down_share > 0]
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


def cloud_word(clouds: float | None) -> Verdict | None:
    """The clouds' own word, on the okta classes: no longer the night's verdict (`score`)."""
    if clouds is None:
        return None
    if clouds <= CLOUD_GO_MAX_PCT:
        return Verdict.GO
    return Verdict.MARGINAL if clouds <= CLOUD_MARGINAL_MAX_PCT else Verdict.NOGO


def is_clear(h: Hour) -> bool:
    """An hour the clouds call clear: one rule for the clear hours and the clear stretch."""
    return (c := h.values.get("cloud_total_pct")) is not None and c <= CLOUD_GO_MAX_PCT


def shown(hours: Sequence[Hour]) -> tuple[str | None, str | None]:
    night = [i for i, h in enumerate(hours) if h.sky != Sky.DAY]
    if not night:
        return None, None
    first, last = night[0], night[-1]
    return hours[max(first - 1, 0)].at, hours[min(last + 1, len(hours) - 1)].at


def mean_of(hours: Sequence[Hour], field: str) -> float | None:
    return _mean(_values(hours, field))
