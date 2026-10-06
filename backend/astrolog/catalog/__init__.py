"""The object catalogue ships with the app and is rebuilt only by `tools/`, never by hand. An
entry's identity is its slug: ids are renumbered on every rebuild, slugs are not."""

from dataclasses import dataclass


# Here and not in `lookup`: the pure deciders of `identify` read the shape without the queries.
@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """A row of `catalog_entries`, without the unit vector only the cone search reads."""

    slug: str
    name: str
    common_name: str | None
    ra_deg: float
    dec_deg: float
    constellation: str
    type_code: str
    kinds_json: str | None
    size_major_arcmin: float | None
    size_minor_arcmin: float | None
    position_angle_deg: float | None
    magnitude: float | None
    magnitude_band: str | None
    surface_brightness: float | None
    distance_ly: float | None
    opacity: float | None


@dataclass(frozen=True, slots=True)
class NamedEntry(CatalogEntry):
    """Found by a designation: `is_primary` says whether it is the entry's own name."""

    is_primary: int


@dataclass(frozen=True, slots=True)
class NearEntry(CatalogEntry):
    """Found by the cone, with its distance from the centre."""

    sep_deg: float
