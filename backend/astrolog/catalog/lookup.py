"""The cone search goes through the unit vector: a circle on the sky becomes an indexed box on
x, y, z, then the dot product decides, with no right ascension wrap at 0/360 to remember."""

import math
import sqlite3
from typing import Any

from .. import units
from . import designation
from .load import unit_vector

_FIELDS = (
    "slug, name, common_name, ra_deg, dec_deg, constellation, type_code, kinds_json,"
    " size_major_arcmin, size_minor_arcmin, position_angle_deg, magnitude, magnitude_band,"
    " surface_brightness, distance_ly, opacity"
)


def by_designation(conn: sqlite3.Connection, raw: str | None) -> dict[str, Any] | None:
    """Also `is_primary`, whether the name searched is the entry's own: `NGC 224` and `M 31` are
    one object, and identify tells `exact_name` from `historic_name` by it."""
    key = designation.key(raw)
    if key is None:
        return None
    fields = ", ".join("e." + f.strip() for f in _FIELDS.split(","))
    row = conn.execute(
        f"SELECT {fields}, n.is_primary FROM catalog_entries e"  # noqa: S608 - constant columns
        " JOIN catalog_names n ON n.slug = e.slug WHERE n.key = ?",
        (key,),
    ).fetchone()
    return dict(row) if row else None


def by_slug(conn: sqlite3.Connection, slug: str) -> dict[str, Any] | None:
    fields = ", ".join(f.strip() for f in _FIELDS.split(","))
    row = conn.execute(
        f"SELECT {fields} FROM catalog_entries WHERE slug = ?",  # noqa: S608 - constant columns
        (slug,),
    ).fetchone()
    return dict(row) if row else None


def in_cone(
    conn: sqlite3.Connection, ra_deg: float, dec_deg: float, radius_deg: float
) -> list[dict[str, Any]]:
    """Nearest first, each with its `sep_deg`: choosing the subject needs the offset, not only the
    list."""
    radius_deg = min(max(radius_deg, 0.0), 180.0)  # beyond half the sky the cone is the whole sky
    cx, cy, cz = unit_vector(ra_deg, dec_deg)
    # The chord subtending the angle: the side of the box that narrows the search.
    chord = 2 * math.sin(math.radians(radius_deg) / 2)
    min_cos = math.cos(math.radians(radius_deg))

    out = []
    for row in conn.execute(
        f"SELECT {_FIELDS}, x, y, z FROM catalog_entries"  # noqa: S608 - constant columns
        " WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?",
        (cx - chord, cx + chord, cy - chord, cy + chord, cz - chord, cz + chord),
    ):
        entry = dict(row)
        cos_sep = entry.pop("x") * cx + entry.pop("y") * cy + entry.pop("z") * cz
        if cos_sep < min_cos:
            continue  # inside the box but outside the circle: the corners of the square
        entry["sep_deg"] = units.separation_deg_from_cosine(cos_sep)
        out.append(entry)
    return sorted(out, key=lambda e: e["sep_deg"])
