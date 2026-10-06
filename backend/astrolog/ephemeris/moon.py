"""The Moon: phase and illumination (geocentric, the same for everyone on Earth), rise, set and
the night's curve (topocentric), and how high it can ever climb from a site."""

import datetime as dt
import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from astropy.coordinates import (
    BaseCoordinateFrame,
    GeocentricMeanEcliptic,
    SkyCoord,
    get_body,
    get_sun,
)

from . import (
    CEILING_STEP_DEG,
    GRID_STEP_MIN,
    MAX_DECLINATION_DEG,
    RISESET_DEG,
    TRACK_STEP_MIN,
    bodies,
)
from .grid import first_crossing


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


def phases(instants: Sequence[dt.datetime]) -> list[Phase]:
    """All in one astropy call. Empty in, empty out: astropy rejects `Time([])`."""
    if not instants:
        return []
    times = bodies.as_times(instants)
    sun = get_sun(times)
    moon = get_body("moon", times)
    ecliptic = GeocentricMeanEcliptic(obstime=times)
    offsets = _ecliptic_longitudes(moon, ecliptic) - _ecliptic_longitudes(sun, ecliptic)
    elongations: Any = sun.separation(moon).deg  # pyright: ignore[reportArgumentType]
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
