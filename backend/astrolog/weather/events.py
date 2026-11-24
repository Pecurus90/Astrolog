"""The night's events in the Meteo (step 13.1, board v82 Meteo.dc.html:460-499): sunset to
sunrise, one per row, in time order. The writer calls it; the page only says them."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from ..ephemeris import RISESET_DEG
from ..ephemeris.moon import MoonNight
from ..ephemeris.planets import Planet, PlanetNight, within
from ..ephemeris.sun import Sky, SkyBand
from ..levels import MoonRule, Verdict, moon_level
from . import dew, judge, score
from .judge import Measure
from .verdict import Hour, window

# A planet culminates for the page from the height it is worth shooting. [P ADR 0022]
PLANET_TOP_MIN_DEG = 30.0


class Group(StrEnum):
    SUN = "sun"
    SKY = "sky"
    VERDICT = "verdict"
    MEASURE = "measure"
    MOON = "moon"
    SHOOTING = "shooting"
    PLANET = "planet"


class Kind(StrEnum):
    SUNSET = "sunset"
    DARK_START = "dark_start"
    DARK_END = "dark_end"
    SUNRISE = "sunrise"
    VERDICT = "verdict"
    SKY_UNKNOWN = "sky_unknown"
    CLOUDS_OVER = "clouds_over"
    CLOUDS_UNDER = "clouds_under"
    RAIN_START = "rain_start"
    RAIN_END = "rain_end"
    CONDENSATION = "condensation"
    GUST_PEAK = "gust_peak"
    SEEING_BEST = "seeing_best"
    MOON_RISE = "moon_rise"
    MOON_SET = "moon_set"
    MOON_ABOVE = "moon_above"
    MOON_BELOW = "moon_below"
    PLANET_RISE = "planet_rise"
    PLANET_SET = "planet_set"
    PLANET_TOP = "planet_top"


# Same minute: the sky first, then the verdict, then the rest (board :489).
_ORDER = {Group.SUN: 0, Group.SKY: 0, Group.VERDICT: 1}
# The phone's short list, "I momenti che contano" (board :497).
_KEY = frozenset({Group.SKY, Group.VERDICT, Group.MOON, Group.SHOOTING})


@dataclass(frozen=True, slots=True)
class NightEvent:
    """`value` is the event's number (Transparency, percent, mm, km/h, arcsec, degrees); `bound`
    the class edge a cloud event crosses; `until` where a stretch ends; `level` its word."""

    at: str
    kind: Kind
    group: Group
    key_moment: bool
    level: Verdict | None = None
    value: float | None = None
    bound: float | None = None
    until: str | None = None
    body: Planet | None = None


def _event(at: datetime | str, kind: Kind, group: Group, **rest: object) -> NightEvent:
    stamp = at if isinstance(at, str) else at.isoformat(timespec="minutes")
    return NightEvent(at=stamp, kind=kind, group=group, key_moment=group in _KEY, **rest)  # type: ignore[arg-type]


def _sun(bands: Sequence[SkyBand]) -> list[NightEvent]:
    """Sunset and sunrise are the day band's inner edges; the dark, each dark band's edges."""
    out = []
    for prev, band in zip(bands, bands[1:], strict=False):
        if prev.kind == Sky.DAY:
            out.append(_event(band.starts_at, Kind.SUNSET, Group.SUN))
        if band.kind == Sky.DAY:
            out.append(_event(band.starts_at, Kind.SUNRISE, Group.SUN))
    for band in bands:
        if band.kind == Sky.DARK:
            until = band.ends_at.isoformat(timespec="minutes")
            out.append(_event(band.starts_at, Kind.DARK_START, Group.SKY, until=until))
            out.append(_event(band.ends_at, Kind.DARK_END, Group.SKY))
    return out


def _next(hours: Sequence[Hour], hour: Hour) -> str:
    """The hour after, as the night has it: clocks jump on change night."""
    later = [h.at for h in hours if datetime.fromisoformat(h.at) > datetime.fromisoformat(hour.at)]
    if later:
        return later[0]
    return (datetime.fromisoformat(hour.at) + timedelta(hours=1)).isoformat(timespec="minutes")


def _stretches[T](hours: Sequence[Hour], key: Callable[[Hour], T]) -> list[list[Hour]]:
    """Consecutive hours with the same key."""
    out: list[list[Hour]] = []
    for h in hours:
        if out and key(out[-1][-1]) == key(h):
            out[-1].append(h)
        else:
            out.append([h])
    return out


def _verdicts(night: Sequence[Hour], hours: Sequence[Hour]) -> list[NightEvent]:
    """One event per stretch of one Transparency word, with its lowest; unknown hours a stretch."""
    out = []
    for run in _stretches(night, lambda h: score.verdict_of(score.transparency(h))):
        lights = [t for h in run if (t := score.transparency(h)) is not None]
        if not lights:
            out.append(
                _event(run[0].at, Kind.SKY_UNKNOWN, Group.VERDICT, until=_next(hours, run[-1]))
            )
            continue
        low = round(min(lights), 1)
        out.append(
            _event(run[0].at, Kind.VERDICT, Group.VERDICT, level=score.verdict_of(low), value=low)
        )
    return out


_RANK = {Verdict.GO: 0, Verdict.MARGINAL: 1, Verdict.NOGO: 2}  # [T] worse is higher


def _cloud_bound(word: Verdict) -> float:
    """The okta bound that opens `word`, from the clouds' own scale."""
    steps = judge.SCALES[Measure.CLOUD].steps
    return next(s.bound for s in steps if s.level == word)


def _clouds(night: Sequence[Hour]) -> list[NightEvent]:
    """A change of cloud class between known hours: over the new bound, or under the old one."""
    scale, out, before = judge.SCALES[Measure.CLOUD], [], None
    for h in night:
        value = scale.read(h)
        word = judge.level(scale, value)
        if word is None:
            continue
        if before is not None and word != before:
            up = _RANK[word] > _RANK[before]
            kind = Kind.CLOUDS_OVER if up else Kind.CLOUDS_UNDER
            bound = _cloud_bound(word if up else before)
            out.append(_event(h.at, kind, Group.MEASURE, value=value, bound=bound))
        before = word
    return out


def _rain(hours: Sequence[Hour]) -> list[NightEvent]:
    scale, out, raining = judge.SCALES[Measure.RAIN], [], False
    for h in hours:
        wet = judge.level(scale, scale.read(h)) == Verdict.NOGO
        if wet and not raining:
            out.append(_event(h.at, Kind.RAIN_START, Group.MEASURE, value=scale.read(h)))
        if raining and not wet:
            out.append(_event(h.at, Kind.RAIN_END, Group.MEASURE))
        raining = wet
    return out


def _condensation(hours: Sequence[Hour]) -> list[NightEvent]:
    scale = judge.SCALES[Measure.CONDENSATION]
    first = next((h for h in hours if judge.hour_level(scale, h) == Verdict.MARGINAL), None)
    if first is None:
        return []
    value = scale.read(first)
    bound = dew.shown_threshold(value, first.values.get("dew_threshold_c"))
    return [_event(first.at, Kind.CONDENSATION, Group.MEASURE, value=value, bound=bound)]


def _extreme(
    night: Sequence[Hour], measure: Measure, kind: Kind, pick: Callable
) -> list[NightEvent]:
    """The night's peak (or best) hour of a measure; none without a number."""
    read = judge.SCALES[measure].read
    known = [(v, h) for h in night if (v := read(h)) is not None]
    if not known:
        return []
    value, hour = pick(known, key=lambda p: p[0])
    return [_event(hour.at, kind, Group.MEASURE, value=value)]


def _threshold_deg(rule: MoonRule) -> float:
    """The setting's degrees: the horizon counts at refraction, but the page says 0."""
    return 0.0 if rule.floor_deg == RISESET_DEG else rule.floor_deg


def _moon_weighs(night: Sequence[Hour], rule: MoonRule) -> list[NightEvent]:
    """Where the Moon starts and stops weighing inside the dark, if it ever and not always does."""
    above = [h.values.get("moon_pct") is not None for h in night]
    if not any(above) or all(above):
        return []
    lit = [p for h in night if (p := h.values.get("moon_pct")) is not None]
    word = moon_level(max(lit), rule)
    if word == Verdict.GO:
        return []
    deg, out = _threshold_deg(rule), []
    for i in range(1, len(night)):
        if above[i] and not above[i - 1]:
            out.append(_event(night[i].at, Kind.MOON_ABOVE, Group.SHOOTING, level=word, value=deg))
        if above[i - 1] and not above[i]:
            out.append(_event(night[i].at, Kind.MOON_BELOW, Group.SHOOTING, level=word, value=deg))
    return out


def _moon(moon: MoonNight | None, lit_at_rise: float | None) -> list[NightEvent]:
    if moon is None:
        return []
    out = []
    if moon.rise is not None:
        lit = None if lit_at_rise is None else float(lit_at_rise)
        out.append(_event(moon.rise, Kind.MOON_RISE, Group.MOON, value=lit))
    if moon.set is not None:
        out.append(_event(moon.set, Kind.MOON_SET, Group.MOON))
    return out


def _planet(night: PlanetNight) -> list[NightEvent]:
    if not night.track:
        return []
    span = within(night, night.track[0].at, night.track[-1].at)
    out = []
    if span.rise is not None:
        out.append(_event(span.rise, Kind.PLANET_RISE, Group.PLANET, body=night.key))
    if span.set is not None:
        out.append(_event(span.set, Kind.PLANET_SET, Group.PLANET, body=night.key))
    top = span.highest
    inside = top.at not in (night.track[0].at, night.track[-1].at)
    if inside and top.altitude_deg >= PLANET_TOP_MIN_DEG:
        deg = float(round(top.altitude_deg))
        out.append(_event(top.at, Kind.PLANET_TOP, Group.PLANET, value=deg, body=night.key))
    return out


def _span(bands: Sequence[SkyBand]) -> tuple[datetime, datetime] | None:
    """Sunset to sunrise; where the Sun does not set, the bands' own reach."""
    if not bands:
        return None
    sets = [b.starts_at for p, b in zip(bands, bands[1:], strict=False) if p.kind == Sky.DAY]
    rises = [b.starts_at for b in bands[1:] if b.kind == Sky.DAY]
    return (sets[0] if sets else bands[0].starts_at, rises[-1] if rises else bands[-1].ends_at)


@dataclass(frozen=True, slots=True)
class NightSky:
    """A drawn window's sky: Sun bands to the minute, the Moon (None: not asked), the planets,
    the Moon's lit percentage at its rise. The models of a night share it."""

    bands: list[SkyBand]
    moon_night: MoonNight | None
    planet_nights: list[PlanetNight]
    lit_at_rise: int | None


def night_events(hours: Sequence[Hour], sky: NightSky, rule: MoonRule) -> list[NightEvent]:
    """The dark's hours say the verdict, clouds, gusts, seeing and the Moon's weight; every hour
    says rain and condensation; all cut to sunset-sunrise, ordered by the absolute instant."""
    reach = _span(sky.bands)
    if reach is None:
        return []
    night, _ = window(hours)
    found = [
        *_sun(sky.bands),
        *_verdicts(night, hours),
        *_clouds(night),
        *_rain(hours),
        *_condensation(hours),
        *_extreme(night, Measure.GUST, Kind.GUST_PEAK, max),
        *_extreme(night, Measure.SEEING, Kind.SEEING_BEST, min),
        *_moon_weighs(night, rule),
        *_moon(sky.moon_night, sky.lit_at_rise),
        *[e for p in sky.planet_nights for e in _planet(p)],
    ]
    # events say the minute: the sunset at 18:50:32 is written 18:50 and must stay in
    start, end = (t.replace(second=0, microsecond=0) for t in reach)
    kept = [e for e in found if start <= datetime.fromisoformat(e.at) <= end]
    return sorted(kept, key=lambda e: (datetime.fromisoformat(e.at), _ORDER.get(e.group, 2)))
