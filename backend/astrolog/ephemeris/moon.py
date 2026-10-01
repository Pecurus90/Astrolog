"""The Moon: phase and illumination (geocentric, the same for everyone on Earth), rise, set and
the night's curve (topocentric), and how high it can ever climb from a site."""

import datetime as dt
import math
from collections.abc import Sequence
from typing import Any, Literal

from astropy.coordinates import (
    BaseCoordinateFrame,
    GeocentricMeanEcliptic,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time

from . import (
    CEILING_STEP_DEG,
    GRID_STEP_MIN,
    MAX_DECLINATION_DEG,
    RISESET_DEG,
    TRACK_STEP_MIN,
    corpi,
)
from .grid import first_crossing, night_grid

# In the order of the lunar month: the closed list of what this module can answer.
PHASES = (
    "new",
    "waxing_crescent",
    "first_quarter",
    "waxing_gibbous",
    "full",
    "waning_gibbous",
    "last_quarter",
    "waning_crescent",
)

# Half-width of new, quarters and full: "full moon" is a word, not an instant, so each of the
# four covers twelve degrees and the other four share what is left.
_BANDA_DEG = 6.0


def phase_name(scarto_deg: float) -> str:
    """From the Moon-Sun ecliptic longitude difference: 0 new, 90 first quarter, 180 full, 270 last
    quarter. Public so the rule is tested directly, not by sampling a real month."""
    d = scarto_deg % 360
    if d < _BANDA_DEG or d > 360 - _BANDA_DEG:
        return "new"
    for centro, nome in ((90, "first_quarter"), (180, "full"), (270, "last_quarter")):
        if abs(d - centro) < _BANDA_DEG:
            return nome
    if d < 90:
        return "waxing_crescent"
    if d < 180:
        return "waxing_gibbous"
    if d < 270:
        return "waning_gibbous"
    return "waning_crescent"


def _longitudini_eclittiche(corpo: SkyCoord, eclittica: BaseCoordinateFrame) -> Any:
    """Degrees, one per instant asked: astropy types the angle as optional and the value loosely."""
    return corpi.convertito(corpo, eclittica).lon.deg  # pyright: ignore[reportOptionalMemberAccess]


def phase(istante: dt.datetime) -> dict[str, Any]:
    """`{"phase_key", "illumination_pct"}`; geocentric, so it takes no site."""
    return phases([istante])[0]


def phases(istanti: Sequence[dt.datetime]) -> list[dict[str, Any]]:
    """All in one astropy call. Empty in, empty out: astropy rejects `Time([])`."""
    if not istanti:
        return []
    quando = Time([corpi.quando(i) for i in istanti])
    sole = get_sun(quando)
    luna = get_body("moon", quando)
    eclittica = GeocentricMeanEcliptic(obstime=quando)
    scarti = _longitudini_eclittiche(luna, eclittica) - _longitudini_eclittiche(sole, eclittica)
    elongazioni: Any = sole.separation(luna).deg  # pyright: ignore[reportArgumentType]
    # Illuminated fraction from the elongation: 0 with Moon and Sun together, 1 when opposite.
    return [
        {
            "phase_key": phase_name(float(scarto)),
            "illumination_pct": round((1 - math.cos(math.radians(float(elongazione)))) / 2 * 100),
        }
        for scarto, elongazione in zip(scarti, elongazioni, strict=True)
    ]


def altitudes(istanti: Sequence[dt.datetime], latitude: float, longitude: float) -> list[float]:
    return corpi.altezze("moon", istanti, latitude, longitude)


def lit_side(phase_key: str, latitude: float) -> Literal["left", "right"]:
    """`"left"` or `"right"`: waxing is lit on the right, mirrored from the southern hemisphere,
    where the Moon is seen upside down."""
    cresce = phase_key in ("waxing_crescent", "first_quarter", "waxing_gibbous")
    return "right" if cresce != (latitude < 0) else "left"


def sky_ceiling(latitude: float) -> int:
    """The night chart's top: the highest the Moon can ever reach from this latitude, rounded up to
    the tick, capped at the zenith. It depends on the site only, so nights compare at a glance."""
    quanto_ci_manca = max(0.0, abs(latitude) - MAX_DECLINATION_DEG)
    return math.ceil((90 - quanto_ci_manca) / CEILING_STEP_DEG) * CEILING_STEP_DEG


def night_track(
    inizio: dt.datetime, latitude: float, longitude: float, hours: float
) -> dict[str, Any]:
    """`{"rise", "set", "highest", "track"}` from one sampling, the only costly thing here. A None
    rise or set means "not in this window", not "never"; `highest` is always there."""
    istanti = night_grid(inizio, hours=hours, step_min=GRID_STEP_MIN)
    alte = altitudes(istanti, latitude, longitude)

    # Computed in UTC, answered in the caller's zone, where astimezone knows about DST.
    def nel_fuso(quando: dt.datetime | None) -> dt.datetime | None:
        return quando.astimezone(inizio.tzinfo) if quando else None

    def punto(i: int) -> dict[str, Any]:
        return {"at": nel_fuso(istanti[i]), "altitude_deg": round(alte[i], 1)}

    # The last sample always closes the curve; a set, so a step that already lands on it adds no
    # duplicate point.
    passo = TRACK_STEP_MIN // GRID_STEP_MIN
    quali = sorted({*range(0, len(istanti), passo), len(istanti) - 1})

    return {
        "rise": nel_fuso(first_crossing(istanti, alte, RISESET_DEG, "up")),
        "set": nel_fuso(first_crossing(istanti, alte, RISESET_DEG, "down")),
        "highest": punto(alte.index(max(alte))),
        "track": [punto(i) for i in quali],
    }
