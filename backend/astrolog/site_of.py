"""Which declared site a place belongs to (docs/domini/sito.md): one rule for the nights and for the
site's sky from the frames, below both pipelines (ADR 0030). Reads sites and declarations only."""

import sqlite3
from enum import StrEnum

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


type Sites = tuple[sqlite3.Row | None, list[sqlite3.Row]]


def home_site(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(_SITE + " WHERE is_default = 1").fetchone()


def sites(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(_SITE).fetchall()


def known_sites(conn: sqlite3.Connection) -> Sites:
    """Home and all: read once per round, nobody writes sites during one."""
    return home_site(conn), sites(conn)


def site_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """By NAME: the user's answer travels on it, because ids are reused."""
    return conn.execute(_SITE + " WHERE name = ?", (name,)).fetchone()


def site_for_coordinates(conn: sqlite3.Connection, key: str | None) -> str | None:
    if key is None:
        return None
    row = conn.execute(
        "SELECT value FROM declarations WHERE entity_type = ? AND entity_key = ? AND field = ?",
        (COORDINATES, key, COORDINATES_SITE),
    ).fetchone()
    value = None if row is None else row["value"]
    return value if isinstance(value, str) and value else None


def site_at(
    conn: sqlite3.Connection, lat: float | None, lon: float | None, known: Sites
) -> tuple[sqlite3.Row, bool] | SiteMiss:
    """Home within 1 km (or anywhere without coordinates), then the user's answer for those
    coordinates, then the nearest within 1 km. True: the user said it."""
    home, all_sites = known
    away_km = None if home is None else distance_km(lat, lon, home["latitude"], home["longitude"])
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
