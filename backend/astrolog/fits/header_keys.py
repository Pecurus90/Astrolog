"""The keys each frame field is read from, kept short: FITS/SBFITSEXT and what the four supported
programs write. Another program's key enters only with a real header in `backend/tests/header/`."""

import math
from typing import Any, Protocol


class HeaderLike(Protocol):
    """An astropy header, or the dict read back from the database: only `.get` is used."""

    def get(self, key: str, default: Any = None, /) -> Any: ...


# Who ACQUIRED the file and who WROTE it: the second is the only trace of a processing program.
# SWMODIFY: *FITS File Header Definitions*, Diffraction Limited (MaxIm DL help). software-ok: source
ACQUISITION_KEYS = ("SWCREATE", "CREATOR")
WRITER_KEYS = ("PROGRAM", "SWMODIFY")

# Measurements written in the header (FWHM, SNR...) are not read: they are measured.
KEYS = {
    "object": ("OBJECT",),
    "date_obs": ("DATE-OBS", "DATE-AVG"),  # never DATE-LOC (local, no offset) nor DATE (the file's)
    "exposure": ("EXPTIME", "EXPOSURE"),
    "filter": ("FILTER",),
    "gain": ("GAIN", "GAINRAW"),  # GAINRAW: ASIAIR
    "offset": ("OFFSET",),
    "telescope": ("TELESCOP",),
    "instrument": ("INSTRUME",),
    # Other devices, when the program names them on the frame: N.I.N.A. the wheel and focuser,
    # the ASIAIR the guide camera (`backend/tests/header/`).
    "filter_wheel": ("FWHEEL",),
    "focuser": ("FOCNAME",),
    "guide_camera": ("GUIDECAM",),
    "bayer": ("BAYERPAT",),
    "focal": ("FOCALLEN",),
    "ccd_temp": ("CCD-TEMP", "SET-TEMP"),  # SET-TEMP is the setpoint: a fallback, not a reading
    "binning": ("XBINNING", "CCDXBIN"),  # CCDXBIN: ASIAIR, SGP
    "pixel_size": ("XPIXSZ",),
    "ra_deg": ("CRVAL1", "RA"),
    "ra_sexagesimal": ("OBJCTRA",),
    "dec_deg": ("CRVAL2", "DEC"),
    "dec_sexagesimal": ("OBJCTDEC",),
    "radesys": ("RADESYS", "RADECSYS"),  # RADECSYS: the standard's historic spelling
    "equinox": ("EQUINOX", "EPOCH"),
    "software": ACQUISITION_KEYS + WRITER_KEYS + ("ORIGIN",),
    "image_type": ("IMAGETYP",),
    "rotation": ("CROTA2", "CROTA1"),
    "site_lat": ("SITELAT",),
    "site_lon": ("SITELONG",),
    "site_elev": ("SITEELEV",),
}


def first(header: HeaderLike, *keys: str) -> Any:
    """The first present, non-blank value among `keys`, RAW (typed as astropy gives it)."""
    for k in keys:
        v = header.get(k)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def get(header: HeaderLike, field: str) -> Any:
    return first(header, *KEYS[field])


def as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def as_int(v: Any) -> int | None:
    """Accepts "100" and 100.0; "0x10" is not 16."""
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def text(v: Any) -> str | None:
    """Strips only the quote pair wrapping the value (astropy already removes FITS ones): quotes
    inside belong to the name, as in `Barnard's Loop`."""
    if v is None:
        return None
    cleaned = str(v).strip()
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1] == "'":
        cleaned = cleaned[1:-1].strip()
    return cleaned or None
