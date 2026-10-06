"""A mosaic's centre and proposed name, from the panels that count only (`mosaic_weight`): a few
stray frames beside it neither pull the centre nor name it."""

import math
import sqlite3

from .. import units
from ..catalog import lookup
from ..catalog.load import unit_vector
from . import objects as obj


def describe(conn: sqlite3.Connection, mosaic_id: int) -> None:
    """The catalog entry the centre falls in, or the nearest within the mosaic; without one, the
    subject with the most frames."""
    centres = conn.execute(
        "SELECT ra_deg, dec_deg, radius_deg FROM panels"
        " WHERE mosaic_id = ? AND counts_in_mosaic = 1",
        (mosaic_id,),
    ).fetchall()
    ra, dec = _mean_direction([(c["ra_deg"], c["dec_deg"]) for c in centres])
    reach = max(
        units.angular_separation_deg(ra, dec, c["ra_deg"], c["dec_deg"]) + c["radius_deg"]
        for c in centres
    )
    proposed = _catalog_name(conn, ra, dec, reach) or _most_poses(conn, mosaic_id)
    conn.execute(
        "UPDATE mosaics SET ra_deg = ?, dec_deg = ?, proposed = ? WHERE id = ?",
        (ra, dec, proposed, mosaic_id),
    )


def _catalog_name(conn: sqlite3.Connection, ra: float, dec: float, reach: float) -> str | None:
    """The nearest entry the centre falls in, else the nearest."""
    voci = lookup.in_cone(conn, ra, dec, reach)
    dentro = [
        v
        for v in voci
        if v.size_major_arcmin and v.sep_deg <= units.radius_deg(v.size_major_arcmin)
    ]
    scelta = (dentro or voci or [None])[0]
    return None if scelta is None else scelta.name


def _most_poses(conn: sqlite3.Connection, mosaic_id: int) -> str:
    righe = conn.execute(
        f"SELECT o.catalog_slug, o.id, {obj.NAME_COLUMNS} FROM frames f"  # noqa: S608
        " JOIN panels p ON p.id = f.panel_id JOIN objects o ON o.id = f.object_id"
        " WHERE p.mosaic_id = ? AND p.counts_in_mosaic = 1 AND f.copy_of IS NULL",
        (mosaic_id,),
    ).fetchall()
    nomi = [obj.label(r) for r in righe]
    return max(sorted(set(nomi)), key=nomi.count) if nomi else ""


def _mean_direction(points: list[tuple[float, float]]) -> tuple[float, float]:
    """The mean of unit vectors, which does not break at RA 0/360."""
    versori = [unit_vector(ra, dec) for ra, dec in points]
    x, y, z = (sum(v[i] for v in versori) for i in range(3))
    return math.degrees(math.atan2(y, x)) % 360.0, math.degrees(math.atan2(z, math.hypot(x, y)))
