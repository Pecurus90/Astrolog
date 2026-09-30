"""Le coordinate dell'header, in gradi e in ICRS: decimali prima, sessagesimali poi, con
guardia di intervallo, e la conversione di sistema SOLO se l'header lo dichiara.

Vincolo non ovvio: senza dichiarazione le coordinate restano invariate (un file gia' J2000
non si tocca); fuori intervallo o inconvertibili -> None, mai una coordinata inventata.
Il placeholder 0/0 di un solve fallito lo giudica header_fields, che sa se c'e' un WCS.
"""

import astropy.units as u
from astropy.coordinates import FK4, FK5, Angle, SkyCoord
from astropy.time import Time

from .header_keys import KEYS, as_float, first, get, text


def coordinate(header, decimal_keys, sexagesimal_keys, unit, lo, hi):  # noqa: PLR0913
    """Una coordinata in gradi: prima le chiavi decimali, poi le sessagesimali via `Angle`.
    Dove le due forme hanno chiavi diverse (`RA` e `OBJCTRA`) decide la chiave; dove la stessa
    chiave porta l'una o l'altra (il sito) si passa la chiave due volte, e decide il valore."""
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
            continue  # sessagesimale illeggibile in questa chiave: si prova la prossima
        return deg if lo <= deg <= hi else None
    return None


def ra_dec(header):
    """`(ra, dec)` in gradi ICRS, o None dove l'header non sa."""
    ra = coordinate(header, KEYS["ra_deg"], KEYS["ra_sexagesimal"], u.hourangle, 0, 360)
    dec = coordinate(header, KEYS["dec_deg"], KEYS["dec_sexagesimal"], u.deg, -90, 90)
    return to_icrs(header, ra, dec)


def _equatorial_frame(radesys, equinox):
    """Il frame dichiarato, o None se e' gia' ICRS/J2000 (nessuna conversione)."""
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


def to_icrs(header, ra, dec):
    """Porta `(ra, dec)` a ICRS se l'header dichiara un altro sistema: equatoriale non J2000
    (FK4, FK5, equinozio dell'anno = coordinate apparenti) o WCS galattico (solo se le
    coordinate vengono da CRVAL: OBJCTRA resta equatoriale anche sotto un CTYPE galattico)."""
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
        return ra, dec  # conversione non riuscita: si tiene cio' che l'header diceva
    if not (0 <= ra2 <= 360 and -90 <= dec2 <= 90):
        return None, None
    return ra2, dec2


def site(header):
    """`(lat, lon, elev_m)` del sito scritti nell'header: un indizio, con guardia di intervallo.

    La stessa chiave porta i gradi decimali o i gradi-minuti-secondi (la forma di `OBJCTDEC`), e
    si leggono tutti e due. `SITELONG` e' la longitudine **est** (*FITS header format DR2*,
    APPLAUSE): contata da 0 a 360 e' la stessa, e si riporta fra -180 e 180."""
    lat = coordinate(header, KEYS["site_lat"], KEYS["site_lat"], u.deg, -90, 90)
    lon = coordinate(header, KEYS["site_lon"], KEYS["site_lon"], u.deg, -180, 360)
    elev = as_float(first(header, *KEYS["site_elev"]))
    if lon is not None and lon > 180:
        lon -= 360
    return lat, lon, elev
