"""A camera's pixel derived from the SKY, when the files do not say it: written by whoever changes
what it depends on, read by the page. The files' or the user's value always wins on the page."""

import sqlite3

from ..units import hundredths, median, pixel_um_from_scale

# Every camera is there even without solved frames, so it can forget a pixel it had derived.
# Rewritten copies do not vote: they are not another frame.
_SKY_VOTES = """
SELECT i.id AS camera_id, w.scale_arcsec_px, r.focal_mm, f.binning
FROM instruments i
LEFT JOIN rigs r ON r.camera_id = i.id
LEFT JOIN frames f ON f.rig_id = r.id AND f.copy_of IS NULL
LEFT JOIN frame_wcs w ON w.frame_id = f.id
WHERE i.kind = 'camera'
"""


def write(conn: sqlite3.Connection) -> None:
    """The median, to the hundredth of a micron as makers declare it: further digits would be
    measurement noise."""
    pixels: dict[int, list[float | None]] = {}
    for r in conn.execute(_SKY_VOTES):
        uno = pixel_um_from_scale(r["scale_arcsec_px"], r["focal_mm"], r["binning"])
        pixels.setdefault(r["camera_id"], []).append(uno)
    for camera_id, valori in pixels.items():
        mezzo = median(valori)
        pixel = hundredths(mezzo)
        conn.execute(
            "UPDATE instruments SET pixel_from_sky_um = ?"
            " WHERE id = ? AND pixel_from_sky_um IS NOT ?",
            (pixel, camera_id, pixel),
        )
