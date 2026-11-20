"""Where a solar-system body stands, from the Earth's centre or from a site: shared by the Moon,
the Sun and the planets, so the most delicate computation exists once (ADR 0046)."""

import atexit
import datetime as dt
import functools
from collections.abc import Sequence
from importlib.resources import files
from typing import Literal

from skyfield.api import load, load_file, wgs84
from skyfield.jpllib import SpiceKernel
from skyfield.positionlib import Apparent, Astrometric
from skyfield.timelib import Time, Timescale

from . import GRID_STEP_MIN
from .grid import night_grid, require_zone

Body = Literal["sun", "moon", "saturn", "jupiter", "mars", "venus"]

# DE421 has Jupiter and Saturn only as barycentres; their moons move them by milliarcseconds.
_TARGET = {"sun": "sun", "moon": "moon", "venus": "venus", "mars": "mars",
           "jupiter": "jupiter barycenter", "saturn": "saturn barycenter"}  # fmt: skip


@functools.cache
def kernel() -> SpiceKernel:
    """DE421 from the skyfield-data wheel: no download, no folder. Path built by hand, since
    `get_skyfield_data_path` warns about a file of the wheel the app never reads."""
    opened = load_file(str(files("skyfield_data") / "data" / "de421.bsp"))
    atexit.register(opened.close)  # else an unclosed-file warning at every exit
    return opened


@functools.cache
def covered() -> tuple[dt.datetime, dt.datetime]:
    """The span every DE421 segment holds, a day in from each edge for the light time. Outside
    it the kernel raises: a caller asks only inside."""
    segments = [s.spk_segment for s in kernel().segments]  # pyright: ignore[reportAttributeAccessIssue]
    first = max(s.start_jd for s in segments) + 1
    last = min(s.end_jd for s in segments) - 1
    return tuple(_timescale().tt_jd(jd).utc_datetime() for jd in (first, last))  # pyright: ignore[reportReturnType]


def covers(instant: dt.datetime) -> bool:
    """A frame's date comes from its header, and a wrong clock says 1970 or 2099."""
    start, end = covered()
    return start <= instant <= end


@functools.cache
def _timescale() -> Timescale:
    # Bundled Earth-rotation table and delta T; past its end, the long-term parabola.
    return load.timescale(builtin=True)


def as_times(instants: Sequence[dt.datetime]) -> Time:
    """One `Time` for the whole list. An instant without a zone is refused, never read as UTC."""
    for instant in instants:
        require_zone(instant)
    return _timescale().from_datetimes(list(instants))


def astrometric(
    body: Body, instants: Sequence[dt.datetime], site: tuple[float, float] | None = None
) -> Astrometric:
    """Light time in, aberration not: from the site (lat, lon East +) when given, else
    geocentric."""
    earth = kernel()["earth"]
    observer = earth if site is None else earth + wgs84.latlon(site[0], site[1])
    return observer.at(as_times(instants)).observe(kernel()[_TARGET[body]])  # pyright: ignore[reportAttributeAccessIssue]


def observed(
    body: Body, instants: Sequence[dt.datetime], site: tuple[float, float] | None = None
) -> Apparent:
    """Apparent: aberration and light bending in too. The call every altitude and phase goes
    through."""
    return astrometric(body, instants, site).apparent()


def _altaz(
    body: Body, instants: Sequence[dt.datetime], latitude: float, longitude: float
) -> tuple[list[float], list[float]]:
    """Topocentric (the Moon's parallax is nearly a degree), geometric: no refraction."""
    alt, az, _ = observed(body, instants, (latitude, longitude)).altaz()
    return [float(a) for a in alt.degrees], [float(a) for a in az.degrees]  # pyright: ignore[reportOptionalIterable, reportGeneralTypeIssues]


def body_altitudes(
    body: Body, instants: Sequence[dt.datetime], latitude: float, longitude: float
) -> list[float]:
    """Refraction lives in `RISESET_DEG`, a threshold, not in the altitude."""
    return _altaz(body, instants, latitude, longitude)[0]


def body_azimuths(
    body: Body, instants: Sequence[dt.datetime], latitude: float, longitude: float
) -> list[float]:
    """Degrees east of north."""
    return _altaz(body, instants, latitude, longitude)[1]


def sampled_night(
    body: Body, start: dt.datetime, latitude: float, longitude: float, hours: float
) -> tuple[list[dt.datetime], list[float]]:
    """The grid of a night and the body's altitude on it, in UTC: the one costly step."""
    instants = night_grid(start, hours=hours, step_min=GRID_STEP_MIN)
    return instants, body_altitudes(body, instants, latitude, longitude)
