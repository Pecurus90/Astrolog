"""I campi di un frame dall'header: grezzi ma tipati, con le catene di alias e la guardia di
intervallo. Niente normalizzazione di nomi: quella e' di vocab.

Vincolo non ovvio: `extract_fields` legge SOLO cio' che finisce in `frames`. Cio' che nessuno
scrive non si calcola: l'header intero e' salvato su ogni posa, e quel giorno si ricava da li'.
Il rumore della float32 si taglia qui, una volta, su dimensione del pixel e temperatura; le
coordinate no, sono double veri. Il placeholder 0/0 senza WCS diventa None: un solve fallito
non e' una coordinata.
"""

import re
from datetime import UTC

from astropy.time import Time

from ..clock import parse_iso
from ..units import strip_float32_noise
from .frame_type import image_type
from .header_coords import ra_dec, site
from .header_keys import as_float, as_int, get, text
from .header_wcs import solved

BAYER_RE = re.compile(r"^(RGGB|GRBG|BGGR|GBRG|CMYG|CYGM)$", re.IGNORECASE | re.ASCII)


def bayer_pattern(header):
    """La matrice di Bayer se l'header la dichiara (maiuscola), altrimenti None: None non vuol
    dire mono, vuol dire che l'header non lo dice."""
    raw = text(get(header, "bayer"))
    if raw and BAYER_RE.match(raw):
        return raw.upper()
    return None


def canonical_utc(iso):
    """Una data ISO qualunque (7 decimali di SGP, senza millisecondi di ASIAIR, con un fuso
    esplicito) -> UTC ISO con i millisecondi, la forma unica del DB. None se non e' una data."""
    dt = parse_iso(iso)
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)  # DATE-OBS senza fuso e' UTC per standard
    return dt.isoformat(timespec="milliseconds")


def date_obs(header):
    """L'istante in UTC canonico: DATE-OBS -> DATE-AVG, poi `MJD-OBS` convertito. Mai DATE-LOC
    (ora locale senza fuso) ne' DATE (e' la data del file)."""
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


def binning(header):
    """Il binning che l'header dichiara, o `None`. Assente, zero o illeggibile vuol dire "non si
    sa", non 1: il pixel fisico della camera si ricava dividendo per lui."""
    value = as_int(get(header, "binning"))
    return value if value is not None and value >= 1 else None


def extract_fields(header, path):
    """Il dizionario dei campi grezzi del frame (nomi = colonne di `frames` piu' gli indizi
    per gli stadi a valle). Mai un crash su una chiave mancante: None o il default."""
    focal = as_float(get(header, "focal"))
    pixel_um = strip_float32_noise(as_float(get(header, "pixel_size")))
    has_wcs = solved(header)
    ra, dec = ra_dec(header)
    if ra == 0 and dec == 0 and not has_wcs:
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
