"""What the header knows of the sky: hints only, the solver measures it. `OBJCTROT` is never read:
it is a sentinel more than a measurement, and its sign against CROTA2 is unknown."""

import math

from .header_keys import KEYS, HeaderLike, as_float, first


def solved(header: HeaderLike) -> bool:
    """`PLTSOLVD` true, `WCSAXES`, or the CD matrix. A bare `CRVAL1` is the mount's pointing, not a
    solution."""
    plt = header.get("PLTSOLVD")
    if plt is True or (isinstance(plt, str) and plt.strip().upper() in ("T", "TRUE")):
        return True
    if header.get("WCSAXES") is not None:
        return True
    return any(header.get(k) is not None for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2"))


def wcs_scale(header: HeaderLike) -> float | None:
    """Arcseconds per pixel, binning included: from the CD matrix, falling back to `CDELT1`."""
    cd11 = as_float(header.get("CD1_1"))
    cd21 = as_float(header.get("CD2_1"))
    if cd11 is not None and cd21 is not None:
        return math.sqrt(cd11 * cd11 + cd21 * cd21) * 3600.0
    cdelt1 = as_float(header.get("CDELT1"))
    if cdelt1 is not None:
        return abs(cdelt1) * 3600.0
    return None


def wcs_rotation_deg(header: HeaderLike) -> float | None:
    """CROTA2 convention in [0, 360). A matrix without `CD1_2` reads 0 (WCS Paper I); with `CD1_2`
    and `CD2_2` both zero it is degenerate and the angle stays unknown."""
    cells = {k: as_float(header.get(k)) for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2")}
    if any(v is not None for v in cells.values()):
        cd12, cd22 = cells["CD1_2"] or 0.0, cells["CD2_2"] or 0.0
        if cd12 or cd22:
            return round(math.degrees(math.atan2(-cd12, cd22)) % 360.0, 2)
    crota = as_float(first(header, *KEYS["rotation"]))
    if crota is not None:
        return round(crota % 360.0, 2)
    return None
