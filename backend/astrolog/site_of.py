"""Which declared site a place belongs to (docs/domini/sito.md): one rule for the nights and for the
site's sky from the frames, below both pipelines (ADR 0030). Reads sites and declarations only."""

import datetime as dt
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from .clock import night_date, now_iso
from .db.declared import declared
from .place import by_distance, coordinates_key, distance_km

# Below this the header's coordinates and the site's are the same place: two decimals already
# move a coordinate by 1.1 km, and a consumer GPS errs by metres. Beyond it, ask.
SAME_PLACE_KM = 1.0

# The user's answer "these coordinates are that site", as `spine.declarations` writes it.
COORDINATES = "coordinates"
COORDINATES_SITE = "site"

_SITE = "SELECT id, name, latitude, longitude, timezone, sky_sqm FROM sites"


class SiteMiss(StrEnum):
    """Why a place has no site: the same codes the nights use."""

    NO_ACTIVE_SITE = "no_active_site"
    SITE_UNCLEAR = "site_unclear"


@dataclass(frozen=True, slots=True)
class Site:
    """A declared site as the rules read it: the columns of `_SITE`."""

    id: int
    name: str
    latitude: float
    longitude: float
    timezone: str | None
    sky_sqm: float | None

    @classmethod
    def of(cls, row: sqlite3.Row) -> Self:
        return cls(
            row["id"],
            row["name"],
            row["latitude"],
            row["longitude"],
            row["timezone"],
            row["sky_sqm"],
        )


def _site(row: sqlite3.Row | None) -> Site | None:
    return None if row is None else Site.of(row)


type Sites = tuple[Site | None, list[Site]]


def home_site(conn: sqlite3.Connection) -> Site | None:
    return _site(conn.execute(_SITE + " WHERE is_default = 1").fetchone())


def home_tonight(conn: sqlite3.Connection) -> dt.date:
    """Tonight's date at home, noon to noon: at two in the morning it is still last night. Without
    a home or its zone, today in UTC: the archive does not depend on the site."""
    home = home_site(conn)
    tonight = night_date(now_iso(), home.timezone) if home else None
    return dt.date.fromisoformat(tonight) if tonight else dt.datetime.now(dt.UTC).date()


def sites(conn: sqlite3.Connection) -> list[Site]:
    return [Site.of(row) for row in conn.execute(_SITE)]


def known_sites(conn: sqlite3.Connection) -> Sites:
    """Home and all: read once per round, nobody writes sites during one."""
    return home_site(conn), sites(conn)


def site_by_name(conn: sqlite3.Connection, name: str) -> Site | None:
    """By NAME: the user's answer travels on it, because ids are reused."""
    return _site(conn.execute(_SITE + " WHERE name = ?", (name,)).fetchone())


def site_for_coordinates(conn: sqlite3.Connection, key: str | None) -> str | None:
    value = declared(conn, COORDINATES, key, COORDINATES_SITE)
    return value if isinstance(value, str) and value else None


def site_at(
    conn: sqlite3.Connection, lat: float | None, lon: float | None, known: Sites
) -> tuple[Site, bool] | SiteMiss:
    """Home within 1 km (or anywhere without coordinates), then the user's answer for those
    coordinates, then the nearest within 1 km. True: the user said it."""
    home, all_sites = known
    away_km = None if home is None else distance_km(lat, lon, home.latitude, home.longitude)
    if home is not None and (away_km is None or away_km <= SAME_PLACE_KM):
        return home, False
    if lat is None or lon is None:
        return SiteMiss.NO_ACTIVE_SITE
    said_site = site_for_coordinates(conn, coordinates_key(lat, lon))
    if said_site:
        site = site_by_name(conn, said_site)
        if site is None:
            # The declared site was deleted (a rename carries the answer): ask again, not home.
            return SiteMiss.SITE_UNCLEAR
        return site, True
    near = [s for km, s in by_distance(lat, lon, all_sites) if km <= SAME_PLACE_KM]
    if near:
        return near[0], False
    return SiteMiss.SITE_UNCLEAR if home is not None else SiteMiss.NO_ACTIVE_SITE
