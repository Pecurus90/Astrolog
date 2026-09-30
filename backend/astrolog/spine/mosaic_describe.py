"""Il centro di un mosaico e il nome che propone: cio' che Da confermare scrive nel campo del si'.

Vincolo non ovvio: **si guardano i soli pannelli che contano** (`mosaic_weight`): pochi frame
spostati accanto a un mosaico non tirano il centro verso di se', ne' gli danno il nome. Lo chiede
`mosaic.settle`, dopo il peso.
"""

import math

from .. import units
from ..catalog import lookup
from ..catalog.load import unit_vector
from . import objects as obj


def describe(conn, mosaic_id):
    """Il centro del mosaico e il nome che propone: la voce del catalogo in cui cade il centro, o
    la piu' vicina entro il mosaico; senza catalogo, il soggetto con piu' pose."""
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


def _catalog_name(conn, ra, dec, reach):
    """La voce in cui cade il centro -- la piu' vicina, se sono piu' d'una -- o la piu' vicina."""
    voci = lookup.in_cone(conn, ra, dec, reach)
    dentro = [
        v
        for v in voci
        if v["size_major_arcmin"] and v["sep_deg"] <= units.radius_deg(v["size_major_arcmin"])
    ]
    scelta = (dentro or voci or [None])[0]
    return None if scelta is None else scelta["name"]


def _most_poses(conn, mosaic_id):
    righe = conn.execute(
        f"SELECT o.catalog_slug, o.id, {obj.NAME_COLUMNS} FROM frames f"  # noqa: S608
        " JOIN panels p ON p.id = f.panel_id JOIN objects o ON o.id = f.object_id"
        " WHERE p.mosaic_id = ? AND p.counts_in_mosaic = 1 AND f.copy_of IS NULL",
        (mosaic_id,),
    ).fetchall()
    nomi = [obj.label(r) for r in righe]
    return max(sorted(set(nomi)), key=nomi.count) if nomi else ""


def _mean_direction(points):
    """Il centro di punti sul cielo: la media dei versori, che non si rompe a RA 0/360."""
    versori = [unit_vector(ra, dec) for ra, dec in points]
    x, y, z = (sum(v[i] for v in versori) for i in range(3))
    return math.degrees(math.atan2(y, x)) % 360.0, math.degrees(math.atan2(z, math.hypot(x, y)))
