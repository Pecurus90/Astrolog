"""Each measure's judgement, hour by hour and for the night. Only total cloud makes the verdict;
the others weigh beside it with their word and their hours, and never change it."""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .verdict import (
    CLOUD_GO_MAX_PCT,
    CLOUD_MARGINAL_MAX_PCT,
    Hour,
    Summary,
    Verdict,
    when,
    window,
)


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
    VISIBILITY = "visibility"
    CLOUD_MID = "cloud_mid"
    CLOUD_HIGH = "cloud_high"
    TEMPERATURE = "temperature"
    DEW_POINT = "dew_point"
    WIND_700 = "wind_700"
    DUST = "dust"


class NightValue(StrEnum):
    """How a measure says the night: the cold and the visibility at their lowest."""

    MEAN = "mean"
    TOTAL = "total"
    MIN = "min"


class Curve(StrEnum):
    """How a chart grows with its value: `sqrt` squeezes the high values, the low ones get room."""

    LINEAR = "linear"
    SQRT = "sqrt"


@dataclass(frozen=True, slots=True)
class Step:
    """From `bound` on the hour has `level` (`None`: no word); `strict` means beyond, not from."""

    level: Verdict | None
    bound: float
    strict: bool


type Read = Callable[[Hour], float | None]


@dataclass(frozen=True, slots=True)
class Scale:
    """How a measure reads an hour; `steps` worst first, an hour crossing none is go. Its chart runs
    from 0 to at least `axis_top` (no further when `axis_fixed`), else over its values."""

    code: Measure
    read: Read
    steps: list[Step]
    lower_is_worse: bool = False
    night: NightValue = NightValue.MEAN
    digits: int = 0
    axis_top: float | None = None
    axis_fixed: bool = False
    curve: Curve = Curve.LINEAR
    second: Read | None = None  # a second series on the same chart


def _field(name: str) -> Read:
    return lambda h: h.values.get(name)


def spread(h: Hour) -> float | None:
    temp, dew = h.values.get("temperature_c"), h.values.get("dew_point_c")
    return None if temp is None or dew is None else round(temp - dew, 1)


NOGO, MARGINAL, GO = Verdict.NOGO, Verdict.MARGINAL, Verdict.GO

_EIGHTHS = [  # okta bounds, source beside them in verdict
    Step(NOGO, CLOUD_MARGINAL_MAX_PCT, strict=True),
    Step(MARGINAL, CLOUD_GO_MAX_PCT, strict=True),
]

SCALES: dict[Measure, Scale] = {
    s.code: s
    for s in (
        # [T] chart axis, percent
        Scale(Measure.CLOUD, _field("cloud_total_pct"), _EIGHTHS, axis_top=100.0),
        # [T] chart axis, percent
        Scale(Measure.CLOUD_LOW, _field("cloud_low_pct"), _EIGHTHS, axis_top=100.0),
        # any rain in the dark ends the session; [C ASCOM ObservingConditions.RainRate: >0 is wet]
        Scale(
            Measure.RAIN,
            _field("precip_mm"),
            [Step(NOGO, 0.0, strict=True)],
            night=NightValue.TOTAL,
            axis_top=1.5,  # [T] chart axis
            digits=1,
        ),
        # [C RMetS Beaufort: force 5 "29-38", force 4 "20-28" km/h, 10 min mean at 10 m]
        # https://www.rmets.org/metmatters/beaufort-wind-scale
        Scale(
            Measure.GUST,
            _field("wind_gust_kmh"),
            [Step(NOGO, 29.0, strict=False)],  # [C RMetS Beaufort 5, a mean-wind scale]
            axis_top=45.0,  # [T] chart axis
        ),
        Scale(
            Measure.WIND,
            _field("wind_kmh"),
            # [C RMetS Beaufort 5 and 4]
            [Step(NOGO, 29.0, strict=False), Step(MARGINAL, 20.0, strict=False)],
            axis_top=45.0,  # [T] chart axis
            second=_field("wind_gust_kmh"),
        ),
        # [U imagers' usage: "worry about dew when the temperature-dewpoint spread is less than
        # about 3C"] https://app.astrobin.com/forum/topic/18055/dew-heater/dew-dos-snicker-and-donts
        Scale(
            Measure.CONDENSATION,
            spread,
            [Step(NOGO, 3.0, strict=True)],  # [U imagers' usage, AstroBin above]
            lower_is_worse=True,
            night=NightValue.MIN,
            axis_top=10.0,  # [T] chart axis
        ),
        # [C meteoblue: "(>35m/s) usually correspond to bad seeing"] 126 km/h; no marginal.
        # https://content.meteoblue.com/en/private-customers/website-help/outdoor-and-sports/astronomy-seeing
        Scale(
            Measure.JET,
            _field("wind_250hpa_kmh"),
            [Step(NOGO, 126.0, strict=False)],  # [C meteoblue, 35 m/s]
            axis_top=160.0,  # [T] chart axis
        ),
        # [U Astronomy Tools CCD suitability: good 1-2", OK 2-4", poor 4-5"] [C CMC class I: >4"]
        # https://astronomy.tools/calculators/ccd_suitability
        Scale(
            Measure.SEEING,
            _field("seeing_arcsec"),
            # [C CMC class I: >4"] [U Astronomy Tools: OK 2-4"]
            [Step(NOGO, 4.0, strict=True), Step(MARGINAL, 2.0, strict=True)],
            axis_top=5.0,  # [T] chart axis
            digits=1,
        ),
        # [C NASA: "less than 0.1 ... crystal clear sky", "1 ... very hazy"]; between, no word.
        # https://science.nasa.gov/earth/earth-observatory/global-maps/aerosol-optical-depth
        Scale(
            Measure.AEROSOL,
            _field("aerosol_optical_depth"),
            [Step(NOGO, 1.0, strict=False), Step(None, 0.1, strict=False)],  # [C NASA]
            digits=2,  # [T] shown digits
            axis_top=0.2,  # [T] chart axis
        ),
        # [C ING dark time: lit fraction under 0.25] [P docs/domini/meteo.md: 50 %]
        # Only the hours with the Moon up carry a value.
        Scale(
            Measure.MOON,
            _field("moon_pct"),
            # [C ING dark time under 25 %] [P docs/domini/meteo.md: 50 %]
            [Step(NOGO, 50.0, strict=True), Step(MARGINAL, 25.0, strict=True)],
            digits=0,
            axis_top=100.0,  # [T] chart axis, percent
        ),
        # [C FAA-H-8083-28 18.1.1: fog "reduces horizontal visibility to less than 5/8 sm (1 km)";
        # METAR FG under 1000 m]
        Scale(
            Measure.VISIBILITY,
            _field("visibility_km"),
            [Step(NOGO, 1.0, strict=True)],
            lower_is_worse=True,
            night=NightValue.MIN,
            # [T] Design sheet v36: up to 20 km on a square root, else the 1 km line sits on floor
            axis_top=20.0,
            axis_fixed=True,
            digits=1,
            curve=Curve.SQRT,
        ),
    )
}

# No public threshold: shown as they are, after the judged ones, in the order of the page's cards.
NEUTRAL: dict[Measure, Scale] = {
    s.code: s
    for s in (
        Scale(
            Measure.TEMPERATURE,
            _field("temperature_c"),
            [],
            lower_is_worse=True,
            night=NightValue.MIN,
            second=_field("dew_point_c"),
        ),
        Scale(
            Measure.DEW_POINT, _field("dew_point_c"), [], lower_is_worse=True, night=NightValue.MIN
        ),
        Scale(Measure.DUST, _field("dust_ugm3"), []),
        Scale(Measure.WIND_700, _field("wind_700hpa_kmh"), []),
        # [T] chart axis, percent
        Scale(Measure.CLOUD_MID, _field("cloud_mid_pct"), [], axis_top=100.0),
        # [T] chart axis, percent
        Scale(Measure.CLOUD_HIGH, _field("cloud_high_pct"), [], axis_top=100.0),
    )
}

# No word sits between: on the aerosol scale it is the hazy middle, worse than clear. [T] order
_RANK = {NOGO: 0, MARGINAL: 1, None: 2, GO: 3}


@dataclass(frozen=True, slots=True)
class Span:
    """The hours with one word: from the first to the end of the last, and how many."""

    level: Verdict
    since: str
    until: str
    hours: int


@dataclass(frozen=True, slots=True)
class MeasureNight:
    """Over the night's window: the worst hour's level (the clouds': the verdict) and its hours,
    each bad word's hours, the night's value, the peak, the known hours and the chart's axis."""

    code: Measure
    level: Verdict | None
    weighs: bool
    value: float | None
    peak: float | None
    peak_at: str | None
    peak_until: str | None
    spans: list[Span]
    axis_min: float | None
    axis_max: float | None
    axis_curve: Curve
    since: str | None
    until: str | None
    hours: int
    known_hours: int
    known_since: str | None
    known_until: str | None
    # the known hours reach the window's first / last hour
    known_from_start: bool
    known_to_end: bool


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


def _value(scale: Scale, values: Sequence[float]) -> float | None:
    if not values:
        return None
    by = {
        NightValue.MEAN: lambda: sum(values) / len(values),
        NightValue.TOTAL: lambda: sum(values),
        NightValue.MIN: lambda: min(values),
    }
    return _shown(scale, by[scale.night]())


def _shown(scale: Scale, v: float) -> float:
    """To the measure's digits, on the side of the threshold where the true value sits: a spread
    of 2.6 written "3" would deny the fog its threshold calls, a jet at 125.6 as "126" claim it."""
    near = round(v, scale.digits)
    word = level(scale, v)
    if level(scale, near) == word:
        return near
    unit = 10**scale.digits
    sides = (math.floor(v * unit) / unit, math.ceil(v * unit) / unit)
    return next((s for s in sides if level(scale, s) == word), near)


# An hour's fields by the judged measure that reads them; the others have no word to keep.
_READ_BY = {
    "cloud_total_pct": Measure.CLOUD,
    "cloud_low_pct": Measure.CLOUD_LOW,
    "precip_mm": Measure.RAIN,
    "wind_kmh": Measure.WIND,
    "wind_gust_kmh": Measure.GUST,
    "dew_spread_c": Measure.CONDENSATION,
    "wind_250hpa_kmh": Measure.JET,
    "seeing_arcsec": Measure.SEEING,
    "aerosol_optical_depth": Measure.AEROSOL,
    "moon_pct": Measure.MOON,
    "visibility_km": Measure.VISIBILITY,
}


def shown_values(values: Mapping[str, Any]) -> dict[str, Any]:
    """An hour's values as the page writes them, like the night's: a judged one to its measure's
    digits on its word's side of the threshold, any other number to the unit."""
    return {
        k: (_shown(SCALES[_READ_BY[k]], v) if k in _READ_BY else float(round(v)))
        if isinstance(v, float)
        else v
        for k, v in values.items()
    }


def _axis(scale: Scale, shown: Sequence[Hour]) -> tuple[float | None, float | None]:
    """From 0 to the floor or the highest value; a line without a floor spans its values."""
    reads = [scale.read] if scale.second is None else [scale.read, scale.second]
    seen = [v for h in shown for r in reads if (v := r(h)) is not None]
    if scale.axis_top is not None:
        return 0.0, scale.axis_top if scale.axis_fixed else max([scale.axis_top, *seen])
    return (min(seen), max(seen)) if seen else (None, None)


def _spans(scale: Scale, night: Sequence[Hour], after: dict[str, str]) -> list[Span]:
    found = []
    for word in (MARGINAL, NOGO):
        since, until, count = when(night, lambda h, w=word: level(scale, scale.read(h)) == w, after)
        if since is not None and until is not None:
            found.append(Span(word, since, until, count))
    return sorted(found, key=lambda s: s.since)


def _night(
    scale: Scale,
    night: Sequence[Hour],
    shown: Sequence[Hour],
    after: dict[str, str],
    cloud: Verdict | None,
) -> MeasureNight:
    """`after` maps each hour to the next of the whole night: an end is read, not +60 min."""
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
    peak_span = when(night, lambda h: peak_h is not None and h.at == peak_h.at, after)
    axis_min, axis_max = _axis(scale, shown)
    return MeasureNight(
        code=scale.code,
        level=worst,
        weighs=scale.code != Measure.CLOUD and worst in (NOGO, MARGINAL),
        value=_value(scale, values),
        peak=None if peak is None else _shown(scale, peak),
        peak_at=peak_h.at if peak_h else None,
        peak_until=peak_span[1],
        spans=_spans(scale, night, after) if scale.steps else [],
        axis_min=axis_min,
        axis_max=axis_max,
        axis_curve=scale.curve,
        since=at_level[0] if worst else None,
        until=at_level[1] if worst else None,
        hours=at_level[2] if worst else 0,
        known_hours=known_span[2],
        known_since=known_span[0],
        known_until=known_span[1],
        known_from_start=bool(known) and known[0][0].at == night[0].at,
        known_to_end=bool(known) and known[-1][0].at == night[-1].at,
    )


def shown_hours(hours: Sequence[Hour], summary: Summary) -> list[Hour]:
    """From `shown_from` to `shown_until`: the stretch the page draws."""
    if summary.shown_from is None or summary.shown_until is None:
        return []
    ats = [h.at for h in hours]
    return list(hours[ats.index(summary.shown_from) : ats.index(summary.shown_until) + 1])


def measures(hours: Sequence[Hour], summary: Summary) -> list[MeasureNight]:
    """The clouds and the low clouds first, then the judged measures from the worst word, earliest
    first, then the neutral ones. The Moon is left out when it is never up in the window."""
    night, _ = window(hours)
    shown = shown_hours(hours, summary)
    after = {h.at: n.at for h, n in zip(hours, hours[1:], strict=False)}
    judged = [_night(s, night, shown, after, summary.verdict) for s in SCALES.values()]
    judged = [m for m in judged if m.code != Measure.MOON or m.known_hours]
    clouds, rest = judged[:2], judged[2:]
    rest.sort(key=lambda m: (_RANK[m.level] if m.known_hours else len(_RANK), m.since or "~"))
    return [*clouds, *rest, *(_night(s, night, shown, after, None) for s in NEUTRAL.values())]


@dataclass(frozen=True, slots=True)
class ScaleOut:
    code: Measure
    steps: list[Step]
    lower_is_worse: bool


def scales() -> list[ScaleOut]:
    """The thresholds the judgement uses, for the page's scale ticks."""
    return [ScaleOut(s.code, s.steps, s.lower_is_worse) for s in SCALES.values()]
