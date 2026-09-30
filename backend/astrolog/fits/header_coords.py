"""Header coordinates in ICRS degrees, converted only when the header declares another system: an
undeclared file is left as is. Out of range or unconvertible -> None, never an invented value."""

import astropy.units as u
from astropy.coordinates import FK4, FK5, Angle, SkyCoord
from astropy.time import Time

from .header_keys import KEYS, HeaderLike, as_float, first, get, text


def coordinate(
    header: HeaderLike,
    decimal_keys: tuple[str, ...],
    sexagesimal_keys: tuple[str, ...],
    unit: u.UnitBase,
    bounds: tuple[float, float],
) -> float | None:
    """Decimal keys first, then sexagesimal via `Angle`. Where both forms share a key (the site),
    pass it twice and the value decides."""
    lo, hi = bounds
    for k in decimal_keys:
        x = as_float(header.get(k))
        if x is not None:
            return x if lo <= x <= hi else None
    for k in sexagesimal_keys:
        v = header.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        try:
            deg = float(Angle(str(v), unit=unit).deg)  # pyright: ignore[reportArgumentType]
        except (ValueError, TypeError, u.UnitsError):
            continue  # unreadable sexagesimal in this key: try the next one
        return deg if lo <= deg <= hi else None
    return None


def ra_dec(header: HeaderLike) -> tuple[float | None, float | None]:
    ra = coordinate(header, KEYS["ra_deg"], KEYS["ra_sexagesimal"], u.hourangle, (0, 360))
    dec = coordinate(header, KEYS["dec_deg"], KEYS["dec_sexagesimal"], u.deg, (-90, 90))
    return to_icrs(header, ra, dec)


def _equatorial_frame(radesys: str | None, equinox: float | None) -> FK4 | FK5 | None:
    """None when already ICRS/J2000: no conversion."""
    if radesys == "FK4":
        eq = equinox if equinox is not None else 1950.0
        return FK4(equinox=Time(eq, format="byear"))
    if radesys in ("FK5", None):
        if equinox is None or equinox == 2000:
            return None
        return FK5(equinox=Time(equinox, format="jyear"))
    if radesys == "ICRS":
        return None
    if equinox is not None and equinox != 2000:
        return FK5(equinox=Time(equinox, format="jyear"))
    return None


def to_icrs(
    header: HeaderLike, ra: float | None, dec: float | None
) -> tuple[float | None, float | None]:
    """An equinox of the date means apparent coordinates. Galactic only when the values come from
    CRVAL: OBJCTRA stays equatorial even under a galactic CTYPE."""
    if ra is None or dec is None:
        return ra, dec
    radesys = text(get(header, "radesys"))
    radesys = radesys.upper() if radesys else None
    equinox = as_float(get(header, "equinox"))
    ctype1 = (text(header.get("CTYPE1")) or "").upper()
    ctype2 = (text(header.get("CTYPE2")) or "").upper()
    galactic = radesys == "GALACTIC" or ctype1.startswith("GLON") or ctype2.startswith("GLAT")
    galactic = galactic and header.get("CRVAL1") is not None and header.get("CRVAL2") is not None
    try:
        if galactic:
            sc = SkyCoord(l=ra * u.deg, b=dec * u.deg, frame="galactic")
        else:
            frame = _equatorial_frame(radesys, equinox)
            if frame is None:
                return ra, dec
            sc = SkyCoord(ra * u.deg, dec * u.deg, frame=frame)
        icrs = sc.transform_to("icrs")
        ra2, dec2 = float(icrs.ra.deg), float(icrs.dec.deg)  # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]
    except (ValueError, TypeError, u.UnitsError):
        return ra, dec  # conversion failed: keep what the header said
    if not (0 <= ra2 <= 360 and -90 <= dec2 <= 90):
        return None, None
    return ra2, dec2


def site(header: HeaderLike) -> tuple[float | None, float | None, float | None]:
    """A hint, range-guarded; one key carries decimal or DMS degrees. `SITELONG` is east longitude
    (*FITS header format DR2*, APPLAUSE): counted 0-360 it is the same, folded to -180..180."""
    lat = coordinate(header, KEYS["site_lat"], KEYS["site_lat"], u.deg, (-90, 90))
    lon = coordinate(header, KEYS["site_lon"], KEYS["site_lon"], u.deg, (-180, 360))
    elev = as_float(first(header, *KEYS["site_elev"]))
    if lon is not None and lon > 180:
        lon -= 360
    return lat, lon, elev
