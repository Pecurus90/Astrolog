"""The Moon: phase and illumination (geocentric, the same for everyone on Earth), rise, set and
the night's curve (topocentric), and how high it can ever climb from a site."""

import datetime as dt
import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, cast

from astropy.coordinates import (
    BaseCoordinateFrame,
    GeocentricMeanEcliptic,
    SkyCoord,
    get_body,
    get_sun,
)

from ..clock import night_span, seconds_between
from . import (
    ASTRO_DEG,
    CALENDAR_STEP_MIN,
    CEILING_STEP_DEG,
    GRID_STEP_MIN,
    MAX_DECLINATION_DEG,
    RISESET_DEG,
    SYNODIC_MONTH_DAYS,
    TRACK_STEP_MIN,
    bodies,
)
from .grid import first_crossing, night_grid


class MoonPhase(StrEnum):
    """In the order of the lunar month: the closed list of what this module can answer."""

    NEW = "new"
    WAXING_CRESCENT = "waxing_crescent"
    FIRST_QUARTER = "first_quarter"
    WAXING_GIBBOUS = "waxing_gibbous"
    FULL = "full"
    WANING_GIBBOUS = "waning_gibbous"
    LAST_QUARTER = "last_quarter"
    WANING_CRESCENT = "waning_crescent"


PHASES = tuple(MoonPhase)
_WAXING = frozenset({MoonPhase.WAXING_CRESCENT, MoonPhase.FIRST_QUARTER, MoonPhase.WAXING_GIBBOUS})

# Main phases are instants: the night holding one takes its name, between them half lit splits.
# [C USNO https://aa.usno.navy.mil/faq/moon_phases: phase angle 0, 90, 180, 270; crescent < half]
_MAIN_PHASES = ((0, MoonPhase.NEW), (90, MoonPhase.FIRST_QUARTER), (180, MoonPhase.FULL),
                (270, MoonPhase.LAST_QUARTER))  # fmt: skip


@dataclass(frozen=True, slots=True)
class Phase:
    phase_key: MoonPhase
    illumination_pct: int


@dataclass(frozen=True, slots=True)
class TrackPoint:
    at: dt.datetime
    altitude_deg: float


@dataclass(frozen=True, slots=True)
class MoonNight:
    """A None rise or set means "not in this window", not "never"; `highest` is always there.
    `grid` is every sample, unrounded; `track` picks from it."""

    rise: dt.datetime | None
    set: dt.datetime | None
    highest: TrackPoint
    track: list[TrackPoint]
    grid: list[TrackPoint]


def phase_name(start_deg: float, end_deg: float, lit_fraction: float) -> MoonPhase:
    """Moon-Sun longitude difference at night's start and end (end excluded), lit at the instant.
    Public so rule is tested directly."""
    start = start_deg % 360
    span = (end_deg - start_deg) % 360
    for centre, name in _MAIN_PHASES:
        if (centre - start) % 360 < span:
            return name
    if start < 180:
        return MoonPhase.WAXING_CRESCENT if lit_fraction < 0.5 else MoonPhase.WAXING_GIBBOUS
    return MoonPhase.WANING_CRESCENT if lit_fraction < 0.5 else MoonPhase.WANING_GIBBOUS


def _ecliptic_longitudes(body: SkyCoord, ecliptic: BaseCoordinateFrame) -> Any:
    """Degrees, one per instant asked: astropy types the angle as optional and the value loosely."""
    return bodies.transformed(body, ecliptic).lon.deg  # pyright: ignore[reportOptionalMemberAccess]


def phase(instant: dt.datetime) -> Phase:
    """Geocentric, so it takes no site."""
    return phases([instant])[0]


def _offsets_and_elongations(instants: Sequence[dt.datetime]) -> tuple[Any, Any]:
    times = bodies.as_times(instants)
    sun = get_sun(times)
    moon = get_body("moon", times)
    ecliptic = GeocentricMeanEcliptic(obstime=times)
    offsets = _ecliptic_longitudes(moon, ecliptic) - _ecliptic_longitudes(sun, ecliptic)
    elongations: Any = sun.separation(moon).deg  # pyright: ignore[reportArgumentType]
    return offsets, elongations


def phases(instants: Sequence[dt.datetime]) -> list[Phase]:
    """All in one astropy call, with each instant's night ends. Empty in, empty out: astropy
    rejects `Time([])`."""
    if not instants:
        return []
    spans = [night_span(i) for i in instants]
    n = len(instants)
    offsets, elongations = _offsets_and_elongations(
        [*instants, *(s for s, _ in spans), *(e for _, e in spans)]
    )
    out = []
    for start, end, elongation in zip(offsets[n : 2 * n], offsets[2 * n :], elongations[:n],
                                      strict=True):  # fmt: skip
        lit = _lit(elongation)
        out.append(Phase(phase_name(float(start), float(end), lit), round(lit * 100)))
    return out


def lit_fractions(instants: Sequence[dt.datetime]) -> list[float]:
    """0-1, unrounded: the light of `phases` without the name. Empty in, empty out."""
    if not instants:
        return []
    _, elongations = _offsets_and_elongations(instants)
    return [_lit(e) for e in elongations]


def _lit(elongation: Any) -> float:
    """Illuminated fraction from elongation: 0 with Moon and Sun together, 1 when opposite."""
    return (1 - math.cos(math.radians(float(elongation)))) / 2


def altitudes(instants: Sequence[dt.datetime], latitude: float, longitude: float) -> list[float]:
    return bodies.body_altitudes("moon", instants, latitude, longitude)


def lit_side(phase_key: str, latitude: float) -> Literal["left", "right"]:
    """`"left"` or `"right"`: waxing is lit on the right, mirrored from the southern hemisphere,
    where the Moon is seen upside down."""
    waxing = phase_key in _WAXING
    return "right" if waxing != (latitude < 0) else "left"


def sky_ceiling(latitude: float) -> int:
    """The night chart's top: the highest the Moon can ever reach from this latitude, rounded up to
    the tick, capped at the zenith. It depends on the site only, so nights compare at a glance."""
    beyond_deg = max(0.0, abs(latitude) - MAX_DECLINATION_DEG)
    return math.ceil((90 - beyond_deg) / CEILING_STEP_DEG) * CEILING_STEP_DEG


def night_track(start: dt.datetime, latitude: float, longitude: float, hours: float) -> MoonNight:
    """From one sampling, the only costly thing here."""
    instants, alts = bodies.sampled_night("moon", start, latitude, longitude, hours)

    # Computed in UTC, answered in the caller's zone, where astimezone knows about DST.
    def local(instant: dt.datetime | None) -> dt.datetime | None:
        return instant.astimezone(start.tzinfo) if instant else None

    def point(i: int) -> TrackPoint:
        return TrackPoint(instants[i].astimezone(start.tzinfo), round(alts[i], 1))

    # The last sample always closes the curve; a set, so a step that already lands on it adds no
    # duplicate point.
    stride = TRACK_STEP_MIN // GRID_STEP_MIN
    picked = sorted({*range(0, len(instants), stride), len(instants) - 1})

    return MoonNight(
        rise=local(first_crossing(instants, alts, RISESET_DEG, "up")),
        set=local(first_crossing(instants, alts, RISESET_DEG, "down")),
        highest=point(alts.index(max(alts))),
        track=[point(i) for i in picked],
        grid=[
            TrackPoint(at.astimezone(start.tzinfo), alt)
            for at, alt in zip(instants, alts, strict=True)
        ],
    )


def moonless_dark_left_s(
    night: MoonNight, dark: Sequence[tuple[dt.datetime, dt.datetime]], floor_deg: float
) -> list[int]:
    """For each track point: dark with the Moon below `floor_deg` from there to the end. A step
    with the Moon down counts its exact overlap with the bands, never more than they last."""
    # in UTC: the hour the clocks repeat has two instants with one wall-clock key
    utc = [(a.astimezone(dt.UTC), b.astimezone(dt.UTC)) for a, b in dark]
    total = 0.0
    left = {night.grid[-1].at.astimezone(dt.UTC): 0}
    for p, after in reversed(list(itertools.pairwise(night.grid))):
        start, end = p.at.astimezone(dt.UTC), after.at.astimezone(dt.UTC)
        if p.altitude_deg < floor_deg:
            total += sum(max(0.0, seconds_between(max(start, a), min(end, b))) for a, b in utc)
        left[start] = round(total)
    return [left[p.at.astimezone(dt.UTC)] for p in night.track]


Stretch = tuple[dt.datetime, dt.datetime]


@dataclass(frozen=True, slots=True)
class DarkSpans:
    """The dark split by the Moon: below the rule's floor, and above it."""

    moonless: list[Stretch]
    moon_up: list[Stretch]


def _join(spans: list[Stretch], start: dt.datetime, end: dt.datetime) -> None:
    if spans and spans[-1][1] == start:
        spans[-1] = (spans[-1][0], end)
    else:
        spans.append((start, end))


def dark_spans(
    night: MoonNight, dark: Sequence[tuple[dt.datetime, dt.datetime]], floor_deg: float
) -> DarkSpans:
    """Each grid step's exact overlap with the bands, as `moonless_dark_left_s` counts it."""
    out = DarkSpans([], [])
    for p, after in itertools.pairwise(night.grid):
        side = out.moonless if p.altitude_deg < floor_deg else out.moon_up
        for a, b in dark:
            start, end = max(p.at, a), min(after.at, b)
            if start < end:
                _join(side, start, end)
    return out


_COMPASS = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")  # fmt: skip


def compass(azimuth_deg: float) -> str:
    """The sixteen points, each 22.5 degrees wide and centred on its direction."""
    return _COMPASS[int(((azimuth_deg + 11.25) % 360) // 22.5)]


def azimuth_deg(instant: dt.datetime, latitude: float, longitude: float) -> float:
    return bodies.body_azimuths("moon", [instant], latitude, longitude)[0]


def age_days(instant: dt.datetime) -> float:
    """Days since new Moon, from the phase angle on the mean synodic month: good to about half a
    day, and the screen says whole days."""
    offsets, _ = _offsets_and_elongations([instant])
    return float(offsets[0]) % 360 / 360 * SYNODIC_MONTH_DAYS


def distance_km(instant: dt.datetime) -> float:
    """Between the centres (geocentric), the figure the almanacs publish."""
    body = get_body("moon", bodies.as_time(instant))
    return float(body.distance.km)  # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]


@dataclass(frozen=True, slots=True)
class PhaseEvent:
    kind: Literal["new", "full"]
    at: dt.datetime


def main_phases(start: dt.datetime, end: dt.datetime) -> list[PhaseEvent]:
    """New and full Moon between two instants: the phase angle crossing 0 and 180, on an hourly
    grid and interpolated. In UTC."""
    hours = int(seconds_between(start, end) // 3600)
    instants = [start.astimezone(dt.UTC) + dt.timedelta(hours=h) for h in range(hours + 1)]
    offsets, _ = _offsets_and_elongations(instants)
    angles = [float(o) % 360 for o in offsets]
    events = []
    for i in range(1, len(angles)):
        before, after = angles[i - 1], angles[i]
        if before > 270 and after < 90:
            kind, gap = "new", (360 - before) / (360 - before + after)
        elif before < 180 <= after:
            kind, gap = "full", (180 - before) / (after - before)
        else:
            continue
        at = instants[i - 1] + (instants[i] - instants[i - 1]) * gap
        events.append(PhaseEvent(cast(Literal["new", "full"], kind), at))
    return events


@dataclass(frozen=True, slots=True)
class CalendarNight:
    night: str
    phase_key: MoonPhase
    illumination_pct: int
    dark_s: int
    moonless_dark_s: int


def calendar_nights(
    nights: Sequence[tuple[str, dt.datetime, float]],
    latitude: float,
    longitude: float,
    floor_deg: float,
) -> list[CalendarNight]:
    """For each night (date, window start, hours): the Moon at mid-window, and how long the sky is
    astronomically dark with the Moon below `floor_deg`. One call per body for all."""
    if not nights:
        return []
    darks = dark_seconds(nights, latitude, longitude, floor_deg)
    # Middle found in UTC, asked in site zone: the phase name takes the site's noon-to-noon night.
    middles = phases(
        [
            (start.astimezone(dt.UTC) + dt.timedelta(hours=h / 2)).astimezone(start.tzinfo)
            for _, start, h in nights
        ]
    )
    return [
        CalendarNight(date, p.phase_key, p.illumination_pct, dark_s, moonless_s)
        for (date, _, _), p, (dark_s, moonless_s) in zip(nights, middles, darks, strict=True)
    ]


def dark_seconds(
    nights: Sequence[tuple[str, dt.datetime, float]],
    latitude: float,
    longitude: float,
    floor_deg: float,
) -> list[tuple[int, int]]:
    """For each night: seconds of astronomical dark, and of those with the Moon below the floor."""
    grids = [night_grid(start, hours=h, step_min=CALENDAR_STEP_MIN) for _, start, h in nights]
    everything = [i for g in grids for i in g]
    if not everything:
        return [(0, 0) for _ in nights]
    suns = bodies.body_altitudes("sun", everything, latitude, longitude)
    moons = bodies.body_altitudes("moon", everything, latitude, longitude)
    step_s = CALENDAR_STEP_MIN * 60
    out, at = [], 0
    for grid in grids:
        span = range(at, at + len(grid) - 1)  # the last sample closes the window
        dark = [k for k in span if suns[k] < ASTRO_DEG]
        out.append((len(dark) * step_s, sum(1 for k in dark if moons[k] < floor_deg) * step_s))
        at += len(grid)
    return out
