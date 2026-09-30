"""Le chiavi FITS da cui si legge ogni campo del frame, e come si legge un valore senza
fidarsi del tipo.

Vincolo non ovvio: le catene sono DATI, e corte per scelta (Marco, 2026-09-06): lo standard
FITS/SBFITSEXT e cio' che scrivono N.I.N.A., ASIAIR, Voyager e SGP. Una chiave di un altro
software entra solo con un header vero nel corpus (`tests/header/`), e con un test. Le
misure scritte nell'header (FWHM, SNR...) non si leggono: si misurano.
"""

import math

# Chi ha ACQUISITO il file, e chi lo ha SCRITTO: due domande diverse, e la seconda e' l'unico
# modo di sapere che un file e' passato per le mani di un programma di elaborazione. `SWMODIFY`
# e' "software that modified the file": Diffraction Limited, *FITS File Header Definitions*
# (l'aiuto di MaxIm DL).  <!-- software-ok: e' la fonte della convenzione, non un supportato -->
# Il nome che ci sta dentro non si guarda mai: i software supportati restano quattro.
ACQUISITION_KEYS = ("SWCREATE", "CREATOR")
WRITER_KEYS = ("PROGRAM", "SWMODIFY")

KEYS = {
    "object": ("OBJECT",),
    "date_obs": ("DATE-OBS", "DATE-AVG"),  # mai DATE-LOC (locale, senza fuso) ne' DATE (del file)
    "exposure": ("EXPTIME", "EXPOSURE"),
    "filter": ("FILTER",),
    "gain": ("GAIN", "GAINRAW"),  # GAINRAW: ASIAIR
    "offset": ("OFFSET",),
    "telescope": ("TELESCOP",),
    "instrument": ("INSTRUME",),
    # Gli altri strumenti, quando il programma li nomina **sulla posa**: N.I.N.A. scrive la
    # ruota e il focheggiatore, l'ASIAIR la camera di guida (`backend/tests/header/`, gli unici
    # due programmi di cui abbiamo un header vero). Nessuno dei due nomina la guida.
    "filter_wheel": ("FWHEEL",),
    "focuser": ("FOCNAME",),
    "guide_camera": ("GUIDECAM",),
    "bayer": ("BAYERPAT",),
    "focal": ("FOCALLEN",),
    "ccd_temp": ("CCD-TEMP", "SET-TEMP"),  # SET-TEMP e' il setpoint: ripiego, non misura
    "binning": ("XBINNING", "CCDXBIN"),  # CCDXBIN: ASIAIR, SGP
    "pixel_size": ("XPIXSZ",),
    "ra_deg": ("CRVAL1", "RA"),
    "ra_sexagesimal": ("OBJCTRA",),
    "dec_deg": ("CRVAL2", "DEC"),
    "dec_sexagesimal": ("OBJCTDEC",),
    "radesys": ("RADESYS", "RADECSYS"),  # RADECSYS: grafia storica dello standard
    "equinox": ("EQUINOX", "EPOCH"),
    "software": ACQUISITION_KEYS + WRITER_KEYS + ("ORIGIN",),
    "image_type": ("IMAGETYP",),
    "rotation": ("CROTA2", "CROTA1"),
    "site_lat": ("SITELAT",),
    "site_lon": ("SITELONG",),
    "site_elev": ("SITEELEV",),
}


def first(header, *keys):
    """Il primo valore presente e non vuoto fra `keys`, GREZZO (tipato come lo da' astropy)."""
    for k in keys:
        v = header.get(k)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def get(header, field):
    """`first` sulla catena di alias del campo `field` di `KEYS`."""
    return first(header, *KEYS[field])


def as_float(v):
    """`float` con guardia NaN/inf; None o non parsabile -> None, mai un crash."""
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def as_int(v):
    """`int` che tollera "100" e 100.0; "0x10" non e' 16 (nessun parseInt esadecimale)."""
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def text(v):
    """Stringa ripulita ai bordi, o None se vuota.

    Gli apici che delimitano una stringa FITS li toglie gia' astropy: togliere **tutti** gli
    apici mangiava le lettere dei nomi veri -- `Barnard's Loop` entrava in archivio come
    `Barnards Loop`. Si toglie solo la coppia che avvolge il valore, quando c'e' (un header
    letto come testo, o un programma che scrive gli apici dentro il valore)."""
    if v is None:
        return None
    cleaned = str(v).strip()
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1] == "'":
        cleaned = cleaned[1:-1].strip()
    return cleaned or None
