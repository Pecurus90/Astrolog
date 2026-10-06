"""What a place's coordinates tell: time zone, elevation, sky brightness, and search by name. A
silent service gives `None` or an empty list, never a fallback zero: zero is sea level."""

import math
import threading
import time
import urllib.parse
import zoneinfo
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from tzfpy import get_tz

from . import net
from .db.row import Row
from .units import believable_sqm, sqm_from_brightness, sqm_of_bortle

# A degree of arc on the mean-radius Earth (2*pi*6371 km / 360): a constant, not a measure of
# the place.
_KM_PER_DEGREE = 111.2

# Elevation: Copernicus 90 m terrain model, free, no key, to be credited. Sky: World Atlas
# artificial zenith brightness, free personal key (500 requests a day), to be credited.
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
SKY_URL = "https://www.lightpollutionmap.info/QueryRaster/"
SEARCH_URL = "https://nominatim.openstreetmap.org/search"

# The search service's policy allows one request a second: a condition of the service, so it
# holds for every caller, not only the route.
SEARCH_MIN_INTERVAL_S = 1.0
_search_lock = threading.Lock()
_last_search = 0.0

_ZONES: set[str] | None = None


# How a place's sky brightness is known; `sky_of` says which way wins.
class SkySource(StrEnum):
    MEASURED = "measured"
    SERVICE = "service"
    SCALE = "scale"


# Moving the place redoes only what came from the coordinates: what the user wrote stays theirs.
class ElevationSource(StrEnum):
    DECLARED = "declared"
    SERVICE = "service"


@dataclass(frozen=True, slots=True)
class Place:
    """A place found by name: a candidate, not a site."""

    name: str
    latitude: float
    longitude: float


# The real call, named in this module so the tests replace it here.
_fetch = net.fetch


def _ask(fetch: net.Fetch | None, url: str) -> Any:
    return net.ask(fetch or _fetch, url)


def valid_timezone(name: str | None) -> bool:
    """Looked up in the list, not opened: "Europe" (a folder of the zone database) and a made-up
    name fail with different exceptions, and a guard chasing them gets them wrong."""
    global _ZONES  # noqa: PLW0603 - the list is a file on disk, read once
    if _ZONES is None:
        _ZONES = zoneinfo.available_timezones()
    return bool(name) and name in _ZONES


def distance_km(
    lat_a: float | None, lon_a: float | None, lat_b: float | None, lon_b: float | None
) -> float | None:
    """The flat formula: it decides whether two coordinates are the same place, and at those
    distances it differs from the spherical one by metres."""
    if lat_a is None or lon_a is None or lat_b is None or lon_b is None:
        return None
    north = (lat_a - lat_b) * _KM_PER_DEGREE
    east = (lon_a - lon_b) * _KM_PER_DEGREE * math.cos(math.radians((lat_a + lat_b) / 2))
    return math.hypot(north, east)


def by_distance[S: Row](
    latitude: float | None, longitude: float | None, sites: Iterable[S]
) -> list[tuple[float, S]]:
    """Sorted on the true distance: rounded ones would tie two near sites, and comparing the rows
    on a tie would raise instead of sorting. Sites without coordinates stay out."""
    measured = []
    for site in sites:
        km = distance_km(latitude, longitude, site["latitude"], site["longitude"])
        if km is not None:
            measured.append((km, site))
    return sorted(measured, key=lambda pair: pair[0])


def coordinates_key(latitude: float | None, longitude: float | None) -> str | None:
    """Two decimals, about a kilometre: the same scale as the same-place tolerance. Two frames
    either side of a boundary become two questions instead of one; nothing is lost."""
    if latitude is None or longitude is None:
        return None
    # A small negative such as -0.003 prints "-0.00", another key for the same point: normalised
    # on the number (below half a hundredth is zero), not on the string.
    lat = 0.0 if abs(latitude) < 0.005 else latitude
    lon = 0.0 if abs(longitude) < 0.005 else longitude
    return f"{lat:.2f},{lon:.2f}"


def timezone_of_frame(
    latitude: float | None, longitude: float | None, home_tz: str | None
) -> str | None:
    """The header coordinates' zone, or home's (`None`, i.e. UTC, without a home)."""
    return timezone_of(latitude, longitude) or home_tz


def timezone_of(latitude: float | None, longitude: float | None) -> str | None:
    """From the real boundaries, offline, so it works at a dark site without network."""
    if latitude is None or longitude is None:
        return None
    name = get_tz(longitude, latitude)  # the library wants (longitude, latitude)
    return name if valid_timezone(name) else None


def elevation_of(
    latitude: float | None, longitude: float | None, *, fetch: net.Fetch | None = None
) -> float | None:
    if latitude is None or longitude is None:
        return None
    query = urllib.parse.urlencode({"latitude": latitude, "longitude": longitude})
    data = _ask(fetch, f"{ELEVATION_URL}?{query}")
    values = data.get("elevation") if isinstance(data, dict) else None
    if not values or values[0] is None:
        return None
    try:
        return float(values[0])
    except (TypeError, ValueError):
        return None


def sky_sqm_of(
    latitude: float | None,
    longitude: float | None,
    key: str | None,
    *,
    fetch: net.Fetch | None = None,
) -> float | None:
    """Without a key nothing is asked: the app works anyway, the sky is measured or chosen."""
    if not key or latitude is None or longitude is None:
        return None
    query = urllib.parse.urlencode(
        {"ql": "wa_2015", "qt": "point", "qd": f"{longitude},{latitude}", "key": key}
    )
    data = _ask(fetch, f"{SKY_URL}?{query}")
    if not isinstance(data, str | int | float):
        return None  # the service answers a bare number: anything else is a fault
    try:
        artificial = float(data)
    except ValueError:
        return None
    return believable_sqm(sqm_from_brightness(artificial))


def elevation_from(
    latitude: float | None,
    longitude: float | None,
    *,
    declared: float | None = None,
    fetch: net.Fetch | None = None,
) -> tuple[float | None, ElevationSource | None]:
    """Never an elevation without its source: an old number left on new coordinates would be
    indistinguishable from a measure."""
    if declared is not None:
        return declared, ElevationSource.DECLARED
    asked = elevation_of(latitude, longitude, fetch=fetch)
    return (asked, ElevationSource.SERVICE) if asked is not None else (None, None)


def sky_of(  # noqa: PLR0913
    latitude: float | None,
    longitude: float | None,
    *,
    sqm: float | None = None,
    bortle: int | None = None,
    key: str | None = None,
    fetch: net.Fetch | None = None,
) -> tuple[float | None, SkySource | None]:
    """In order of trust: the measure is a fact; the chosen class beats the service because who
    chooses it is looking at that sky, while the service looks at a 2015 map."""
    if sqm is not None:
        return sqm, SkySource.MEASURED
    if bortle is not None:
        return sqm_of_bortle(bortle), SkySource.SCALE
    asked = sky_sqm_of(latitude, longitude, key, fetch=fetch)
    return (asked, SkySource.SERVICE) if asked is not None else (None, None)


type Clock = Callable[[], float]
type Sleep = Callable[[float], object]


def _wait_turn(now: Clock, sleep: Sleep) -> None:
    """Clock and wait come from outside: a test must not stop a second to prove a rule."""
    global _last_search  # noqa: PLW0603 - the last call's instant is one per process
    with _search_lock:
        since = now() - _last_search
        if _last_search and since < SEARCH_MIN_INTERVAL_S:
            sleep(SEARCH_MIN_INTERVAL_S - since)
        _last_search = now()


def search(
    name: str | None,
    *,
    fetch: net.Fetch | None = None,
    limit: int = 5,
    now: Clock = time.monotonic,
    sleep: Sleep = time.sleep,
) -> list[Place]:
    """Empty when nothing is found or the service is silent: the manual way stays open."""
    if not name or not name.strip():
        return []
    _wait_turn(now, sleep)
    query = urllib.parse.urlencode({"q": name.strip(), "format": "jsonv2", "limit": limit})
    data = _ask(fetch, f"{SEARCH_URL}?{query}")
    if not isinstance(data, list):
        return []
    out = []
    for row in data:
        if not isinstance(row, dict) or not row.get("display_name"):
            continue
        try:
            latitude, longitude = float(row["lat"]), float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue  # a place without readable coordinates is not a place
        out.append(Place(row["display_name"], latitude, longitude))
    return out
