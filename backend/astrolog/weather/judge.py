"""Each measure's judgement, hour by hour and for the night. Only total cloud makes the verdict;
the others weigh beside it with their word and their hours, and never change it."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from .verdict import Hour, Summary, Verdict, when, window


class Measure(StrEnum):
    CLOUD = "cloud"
    CLOUD_LOW = "cloud_low"
    RAIN = "rain"
    GUST = "gust"
    WIND = "wind"
    CONDENSATION = "condensation"
    JET = "jet"
    SEEING = "seeing"
    AEROSOL = "aerosol"
    MOON = "moon"
    CLOUD_MID = "cloud_mid"
    CLOUD_HIGH = "cloud_high"
    HUMIDITY = "humidity"
    TEMPERATURE = "temperature"
    DEW_POINT = "dew_point"
    WIND_700 = "wind_700"
    WIND_200 = "wind_200"
    DUST = "dust"


@dataclass(frozen=True, slots=True)
class Step:
    """From `bound` on the hour has `level` (`None`: no word); `strict` means beyond, not from."""

    level: Verdict | None
    bound: float
    strict: bool


@dataclass(frozen=True, slots=True)
class Scale:
    """How a measure reads an hour. `steps` go worst first; an hour that crosses none is go."""

    code: Measure
    read: Callable[[Hour], float | None]
    steps: list[Step]
    lower_is_worse: bool = False
    total: bool = False
    digits: int = 1


def _field(name: str) -> Callable[[Hour], float | None]:
    return lambda h: h.values.get(name)


def _spread(h: Hour) -> float | None:
    temp, dew = h.values.get("temperature_c"), h.values.get("dew_point_c")
    return None if temp is None or dew is None else round(temp - dew, 1)


NOGO, MARGINAL, GO = Verdict.NOGO, Verdict.MARGINAL, Verdict.GO

# Okta (WMO Code Table 2700) as METAR classes (ICAO Annex 3): go to FEW 2/8, marginal to SCT 4/8.
# https://www.nodc.noaa.gov/archive/arc0021/0000907/1.1/data/0-data/HTML/WMO-CODE/WMO2700.HTM
_EIGHTHS = [Step(NOGO, 50.0, strict=True), Step(MARGINAL, 25.0, strict=True)]

SCALES: dict[Measure, Scale] = {
    s.code: s
    for s in (
        Scale(Measure.CLOUD, _field("cloud_total_pct"), _EIGHTHS),
        Scale(Measure.CLOUD_LOW, _field("cloud_low_pct"), _EIGHTHS),
        # any rain in the dark ends the session
        Scale(Measure.RAIN, _field("precip_mm"), [Step(NOGO, 0.0, strict=True)], total=True),
        # Beaufort 5 "fresh breeze" from 29 km/h, 4 "moderate breeze" from 20 km/h.
        # https://en.wikipedia.org/wiki/Beaufort_scale
        Scale(Measure.GUST, _field("wind_gust_kmh"), [Step(NOGO, 29.0, strict=False)]),
        Scale(
            Measure.WIND,
            _field("wind_kmh"),
            [Step(NOGO, 29.0, strict=False), Step(MARGINAL, 20.0, strict=False)],
        ),
        # Under 5 F (3 C) between air and dew point, expect fog: FAA-H-8083-28.
        Scale(Measure.CONDENSATION, _spread, [Step(NOGO, 3.0, strict=True)], lower_is_worse=True),
        # meteoblue: "(>35m/s) usually correspond to bad seeing", nogo from 126 km/h; no marginal.
        # https://content.meteoblue.com/en/private-customers/website-help/outdoor-and-sports/astronomy-seeing
        Scale(Measure.JET, _field("wind_250hpa_kmh"), [Step(NOGO, 126.0, strict=False)]),
        # Canadian Meteorological Centre seeing classes: 1-2" fair, 2-4" moderate, >4" poor.
        # https://www.cleardarksky.com/csk/faq/seeing_catagories.html
        Scale(
            Measure.SEEING,
            _field("seeing_arcsec"),
            [Step(NOGO, 4.0, strict=True), Step(MARGINAL, 2.0, strict=True)],
        ),
        # "less than 0.1 ... a crystal clear sky", "a value of 1 ... very hazy"; between, no word.
        # https://science.nasa.gov/earth/earth-observatory/global-maps/aerosol-optical-depth
        Scale(
            Measure.AEROSOL,
            _field("aerosol_optical_depth"),
            [Step(NOGO, 1.0, strict=False), Step(None, 0.1, strict=False)],
            digits=2,
        ),
        # Broadband up to 25 % lit, the imagers' rule; the 50 % step is a product choice
        # (docs/domini/meteo.md). Only the hours with the Moon up carry a value.
        Scale(
            Measure.MOON,
            _field("moon_pct"),
            [Step(NOGO, 50.0, strict=True), Step(MARGINAL, 25.0, strict=True)],
            digits=0,
        ),
    )
}

# No public threshold: shown as they are, in this order after the judged ones.
NEUTRAL: dict[Measure, Scale] = {
    s.code: s
    for s in (
        Scale(Measure.CLOUD_MID, _field("cloud_mid_pct"), []),
        Scale(Measure.CLOUD_HIGH, _field("cloud_high_pct"), []),
        Scale(Measure.HUMIDITY, _field("humidity_pct"), []),
        Scale(Measure.TEMPERATURE, _field("temperature_c"), [], lower_is_worse=True),
        Scale(Measure.DEW_POINT, _field("dew_point_c"), [], lower_is_worse=True),
        Scale(Measure.WIND_700, _field("wind_700hpa_kmh"), []),
        Scale(Measure.WIND_200, _field("wind_200hpa_kmh"), []),
        Scale(Measure.DUST, _field("dust_ugm3"), []),
    )
}

# No word sits between: on the aerosol scale it is the hazy middle, worse than clear.
_RANK = {NOGO: 0, MARGINAL: 1, None: 2, GO: 3}


@dataclass(frozen=True, slots=True)
class MeasureNight:
    """Over the night's window: the worst hour's level (the clouds': the verdict) and its hours;
    the mean of the known hours (rain: the total); `known_*` so a partial mean says so."""

    code: Measure
    level: Verdict | None
    weighs: bool
    value: float | None
    peak: float | None
    peak_at: str | None
    since: str | None
    until: str | None
    hours: int
    known_hours: int
    known_since: str | None
    known_until: str | None


def _crosses(scale: Scale, step: Step, v: float) -> bool:
    if scale.lower_is_worse:
        return v < step.bound if step.strict else v <= step.bound
    return v > step.bound if step.strict else v >= step.bound


def level(scale: Scale, v: float | None) -> Verdict | None:
    if v is None:
        return None
    return next((s.level for s in scale.steps if _crosses(scale, s, v)), GO)


def hour_levels(hour: Hour) -> dict[str, Verdict | None]:
    """Every judged measure's word for the hour; `None` where the value is missing."""
    return {code: level(s, s.read(hour)) for code, s in SCALES.items()}


def _as_bad(scale: Scale, v: float | None, worst: Verdict | None) -> bool:
    return v is not None and _RANK[level(scale, v)] <= _RANK[worst]


def _night(
    scale: Scale, night: Sequence[Hour], after: dict[str, str], cloud: Verdict | None
) -> MeasureNight:
    known = [(h, v) for h in night if (v := scale.read(h)) is not None]
    values = [v for _, v in known]
    worst = (
        cloud
        if scale.code == Measure.CLOUD
        else min((level(scale, v) for v in values), key=_RANK.__getitem__, default=None)
        if scale.steps
        else None
    )
    peak_h, peak = (
        (min if scale.lower_is_worse else max)(known, key=lambda p: p[1]) if known else (None, None)
    )
    # as bad as the night's word or worse: for the clouds (word from the mean), the hours it saw
    at_level = when(night, lambda h: _as_bad(scale, scale.read(h), worst), after)
    known_span = when(night, lambda h: scale.read(h) is not None, after)
    value = (
        None
        if not values
        else round(sum(values) if scale.total else sum(values) / len(values), scale.digits)
    )
    return MeasureNight(
        code=scale.code,
        level=worst,
        weighs=scale.code != Measure.CLOUD and worst in (NOGO, MARGINAL),
        value=value,
        peak=peak,
        peak_at=peak_h.at if peak_h else None,
        since=at_level[0] if worst else None,
        until=at_level[1] if worst else None,
        hours=at_level[2] if worst else 0,
        known_hours=known_span[2],
        known_since=known_span[0],
        known_until=known_span[1],
    )


def measures(hours: Sequence[Hour], summary: Summary) -> list[MeasureNight]:
    """The clouds first, then the judged measures from the worst word, earliest first, then the
    neutral ones. The Moon is left out when it is never up in the window."""
    night, _ = window(hours)
    after = {h.at: n.at for h, n in zip(hours, hours[1:], strict=False)}
    judged = [_night(s, night, after, summary.verdict) for s in SCALES.values()]
    judged = [m for m in judged if m.code != Measure.MOON or m.known_hours]
    cloud, rest = judged[0], judged[1:]
    rest.sort(key=lambda m: (_RANK[m.level] if m.known_hours else len(_RANK), m.since or "~"))
    return [cloud, *rest, *(_night(s, night, after, None) for s in NEUTRAL.values())]


@dataclass(frozen=True, slots=True)
class ScaleOut:
    code: Measure
    steps: list[Step]
    lower_is_worse: bool


def scales() -> list[ScaleOut]:
    """The thresholds the judgement uses, for the page's scale ticks."""
    return [ScaleOut(s.code, s.steps, s.lower_is_worse) for s in SCALES.values()]
