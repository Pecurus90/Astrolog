"""The Moon: phase and illumination (geocentric, the same for everyone on Earth), rise, set and
the night's curve (topocentric), and how high it can ever climb from a site."""

import datetime as dt
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

# Half-width of new, quarters and full: "full moon" is a word, not an instant, so each of the
# four covers twelve degrees and the other four share what is left.
_HALF_WIDTH_DEG = 6.0


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
    """A None rise or set means "not in this window", not "never"; `highest` is always there."""

    rise: dt.datetime | None
    set: dt.datetime | None
    highest: TrackPoint
    track: list[TrackPoint]


def phase_name(offset_deg: float) -> MoonPhase:
    """From the Moon-Sun ecliptic longitude difference: 0 new, 90 first quarter, 180 full, 270 last
    quarter. Public so the rule is tested directly, not by sampling a real month."""
    d = offset_deg % 360
    if d < _HALF_WIDTH_DEG or d > 360 - _HALF_WIDTH_DEG:
        return MoonPhase.NEW
    for center, name in (
        (90, MoonPhase.FIRST_QUARTER),
        (180, MoonPhase.FULL),
        (270, MoonPhase.LAST_QUARTER),
    ):
        if abs(d - center) < _HALF_WIDTH_DEG:
            return name
    if d < 90:
        return MoonPhase.WAXING_CRESCENT
    if d < 180:
        return MoonPhase.WAXING_GIBBOUS
    if d < 270:
        return MoonPhase.WANING_GIBBOUS
    return MoonPhase.WANING_CRESCENT


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
    """All in one astropy call. Empty in, empty out: astropy rejects `Time([])`."""
    if not instants:
        return []
    offsets, elongations = _offsets_and_elongations(instants)
    # Illuminated fraction from the elongation: 0 with Moon and Sun together, 1 when opposite.
    return [
        Phase(
            phase_name(float(offset)),
            round((1 - math.cos(math.radians(float(elongation)))) / 2 * 100),
        )
        for offset, elongation in zip(offsets, elongations, strict=True)
    ]


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
    )


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
    hours = int((end - start).total_seconds() // 3600)
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
    nights: Sequence[tuple[str, dt.datetime, float]], latitude: float, longitude: float
) -> list[CalendarNight]:
    """For each night (date, window start, hours): the Moon at mid-window, and how long the sky is
    astronomically dark with the Moon below the rise/set altitude. One call per body for all."""
    grids = [night_grid(start, hours=h, step_min=CALENDAR_STEP_MIN) for _, start, h in nights]
    everything = [i for g in grids for i in g]
    if not everything:
        return []
    suns = bodies.body_altitudes("sun", everything, latitude, longitude)
    moons = bodies.body_altitudes("moon", everything, latitude, longitude)
    middles = phases([start + dt.timedelta(hours=h / 2) for _, start, h in nights])
    step_s = CALENDAR_STEP_MIN * 60
    out, at = [], 0
    for (date, _, _), grid, phase_now in zip(nights, grids, middles, strict=True):
        span = range(at, at + len(grid) - 1)  # the last sample closes the window
        dark = [k for k in span if suns[k] < ASTRO_DEG]
        out.append(
            CalendarNight(
                night=date,
                phase_key=phase_now.phase_key,
                illumination_pct=phase_now.illumination_pct,
                dark_s=len(dark) * step_s,
                moonless_dark_s=sum(1 for k in dark if moons[k] < RISESET_DEG) * step_s,
            )
        )
        at += len(grid)
    return out
