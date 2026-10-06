"""A night's verdict and the factors behind it. The verdict looks only at total cover, the one
quantity that blocks every object alike; the rest are factors beside it, not a single score."""

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
# Beaufort force 5, "fresh breeze": 8.0-10.7 m/s, that is 29-38 km/h.
# https://en.wikipedia.org/wiki/Beaufort_scale
GUST_KMH = 29.0
# Aviation rule: under 5 F (3 C) between temperature and dew point, expect fog.
# FAA, Aviation Weather Handbook (FAA-H-8083-28).
CONDENSATION_SPREAD_C = 3.0


class Verdict(StrEnum):
    GO = "go"
    MARGINAL = "marginal"
    NOGO = "nogo"


class Window(StrEnum):
    DARK = "dark"
    SUN_DOWN = "sun_down"


# Most severe first: rain ends the session, low cloud blocks, total cloud veils, gusts shake the
# rig, condensation is fought with a dew heater.
class FactorCode(StrEnum):
    RAIN = "rain"
    CLOUD_LOW = "cloud_low"
    CLOUD = "cloud"
    GUST = "gust"
    CONDENSATION = "condensation"


_ORDER = tuple(FactorCode)


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
class Factor:
    code: FactorCode
    value: float
    threshold: float
    since: str | None
    until: str | None
    hours: int


@dataclass(frozen=True, slots=True)
class Summary:
    verdict: Verdict | None
    cloud_total_pct: float | None
    usable_hours: int | None
    window: Window | None
    window_hours: int
    wind_700hpa_kmh: float | None
    factors: list[Factor]


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


def _when(
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


def _with(field: str, test: Callable[[Any], bool]) -> Bites:
    return lambda h: h.values.get(field) is not None and test(h.values[field])


def _spread(h: Hour) -> float | None:
    if h.values.get("temperature_c") is None or h.values.get("dew_point_c") is None:
        return None
    return h.values["temperature_c"] - h.values["dew_point_c"]


def _factors(hours: Sequence[Hour], after: Mapping[str, str]) -> list[Factor]:
    def factor(code: FactorCode, value: float, threshold: float, bites: Bites) -> Factor:
        return Factor(code, value, threshold, *_when(hours, bites, after))

    factors = []
    rain = _values(hours, "precip_mm")
    if sum(rain) > 0:
        factors.append(
            factor(FactorCode.RAIN, round(sum(rain), 1), 0.0, _with("precip_mm", lambda v: v > 0))
        )
    for code, field in (
        (FactorCode.CLOUD_LOW, "cloud_low_pct"),
        (FactorCode.CLOUD, "cloud_total_pct"),
    ):
        mean = _mean(_values(hours, field))
        if mean is not None and mean > CLOUD_GO_MAX_PCT:
            factors.append(
                factor(code, mean, CLOUD_GO_MAX_PCT, _with(field, lambda v: v > CLOUD_GO_MAX_PCT))
            )
    gusts = _values(hours, "wind_gust_kmh")
    if gusts and max(gusts) >= GUST_KMH:
        factors.append(
            factor(
                FactorCode.GUST,
                round(max(gusts), 1),
                GUST_KMH,
                _with("wind_gust_kmh", lambda v: v >= GUST_KMH),
            )
        )
    temp, dew = _mean(_values(hours, "temperature_c")), _mean(_values(hours, "dew_point_c"))
    if temp is not None and dew is not None and temp - dew < CONDENSATION_SPREAD_C:
        factors.append(
            factor(
                FactorCode.CONDENSATION,
                round(temp - dew, 1),
                CONDENSATION_SPREAD_C,
                lambda h: (s := _spread(h)) is not None and s < CONDENSATION_SPREAD_C,
            )
        )
    return sorted(factors, key=lambda f: _ORDER.index(f.code))


def _verdict(clouds: float | None) -> Verdict | None:
    if clouds is None:
        return None
    if clouds <= CLOUD_GO_MAX_PCT:
        return Verdict.GO
    return Verdict.MARGINAL if clouds <= CLOUD_MARGINAL_MAX_PCT else Verdict.NOGO


def assess(hours: Sequence[Hour]) -> Summary:
    """Verdict and usable hours are `None` unless every night hour reports `cloud_total_pct`.
    Usable hours are the night's hours the verdict would call clear, so the two never disagree."""
    night, span = window(hours)
    after = {h.at: n.at for h, n in zip(hours, hours[1:], strict=False)}
    cover: list[Any] = [h.values.get("cloud_total_pct") for h in night]
    complete = bool(night) and None not in cover
    clouds = _mean([c for c in cover if c is not None]) if complete else None
    return Summary(
        verdict=_verdict(clouds),
        cloud_total_pct=clouds,
        usable_hours=sum(c <= CLOUD_GO_MAX_PCT for c in cover) if complete else None,
        window=span,
        window_hours=len(night),
        wind_700hpa_kmh=_mean(_values(night, "wind_700hpa_kmh")),
        factors=_factors(night, after),
    )
