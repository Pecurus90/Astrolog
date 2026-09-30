"""Raw but typed frame fields; name normalisation is vocab's. Only what lands in `frames` is read:
the whole header is stored on every frame, and anything else is derived from it when needed."""

import re
from datetime import UTC
from typing import Any

from astropy.time import Time

from ..clock import parse_iso
from ..units import strip_float32_noise
from .frame_type import image_type
from .header_coords import ra_dec, site
from .header_keys import HeaderLike, as_float, as_int, get, text
from .header_wcs import solved

BAYER_RE = re.compile(r"^(RGGB|GRBG|BGGR|GBRG|CMYG|CYGM)$", re.IGNORECASE | re.ASCII)


def bayer_pattern(header: HeaderLike) -> str | None:
    """Uppercased. None does not mean mono: it means the header does not say."""
    raw = text(get(header, "bayer"))
    if raw and BAYER_RE.match(raw):
        return raw.upper()
    return None


def canonical_utc(iso: object) -> str | None:
    """Any ISO date (SGP's seven decimals, ASIAIR's missing milliseconds, an explicit offset) ->
    UTC with milliseconds, the database's single form."""
    dt = parse_iso(iso)
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)  # DATE-OBS without offset is UTC by standard
    return dt.isoformat(timespec="milliseconds")


def date_obs(header: HeaderLike) -> str | None:
    """DATE-OBS, DATE-AVG, then `MJD-OBS`. Never DATE-LOC (local, no offset) nor DATE (the file's
    date)."""
    iso = text(get(header, "date_obs"))
    if iso is not None:
        return canonical_utc(iso)
    mjd = as_float(header.get("MJD-OBS"))
    if mjd is None:
        return None
    try:
        return canonical_utc(Time(mjd, format="mjd", scale="utc").isot)
    except (ValueError, TypeError):
        return None


def binning(header: HeaderLike) -> int | None:
    """Missing, zero or unreadable means unknown, not 1: the camera's physical pixel is derived by
    dividing by it."""
    value = as_int(get(header, "binning"))
    return value if value is not None and value >= 1 else None


def extract_fields(header: HeaderLike, path: str) -> dict[str, Any]:
    """`frames` columns plus hints for later stages; a missing key gives None, never a crash."""
    focal = as_float(get(header, "focal"))
    # float32 noise is cut here, once; coordinates are true doubles and are left alone
    pixel_um = strip_float32_noise(as_float(get(header, "pixel_size")))
    has_wcs = solved(header)
    ra, dec = ra_dec(header)
    if ra == 0 and dec == 0 and not has_wcs:  # the 0/0 placeholder of a failed solve
        ra = dec = None
    lat, lon, elev = site(header)
    return {
        "path": path,
        "image_type": image_type(header),
        "object_raw": text(get(header, "object")),
        "date_obs": date_obs(header),
        "exposure_s": as_float(get(header, "exposure")),
        "filter_raw": text(get(header, "filter")),
        "gain": as_float(get(header, "gain")),
        "offset": as_float(get(header, "offset")),
        "telescope_raw": text(get(header, "telescope")),
        "instrument_raw": text(get(header, "instrument")),
        "filter_wheel_raw": text(get(header, "filter_wheel")),
        "focuser_raw": text(get(header, "focuser")),
        "guide_camera_raw": text(get(header, "guide_camera")),
        "software_raw": text(get(header, "software")),
        "bayer_pattern": bayer_pattern(header),
        "focal_mm": focal,
        "ccd_temp_c": strip_float32_noise(as_float(get(header, "ccd_temp"))),
        "naxis1": as_int(header.get("NAXIS1")),
        "naxis2": as_int(header.get("NAXIS2")),
        "binning": binning(header),
        "pixel_size_um": pixel_um,
        "ra_deg": ra,
        "dec_deg": dec,
        "site_lat": lat,
        "site_lon": lon,
        "site_elev_m": elev,
    }
