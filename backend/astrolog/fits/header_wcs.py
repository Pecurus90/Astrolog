"""Cio' che l'header sa del cielo del frame: se c'e' un WCS vero, la scala e la rotazione
dalla matrice CD. `solved` la chiede la scansione su ogni posa (decide il placeholder 0/0);
scala e rotazione le legge il solver sull'esito di ASTAP.

Vincolo non ovvio: nel nuovo il cielo lo misura il solver; questi valori sono l'indizio
iniziale. La rotazione e' in convenzione CROTA2 (`atan2(-CD1_2, CD2_2)`), e `OBJCTROT` non
si legge mai: e' una sentinella piu' che una misura -- sull'archivio vero lo scrivono 11.975
file su 14.148, e in 6.984 di quelli vale zero (58%). Nessuno di essi porta anche CROTA2,
quindi che sia di segno opposto non lo sappiamo: non si scrive.
"""

import math

from .header_keys import KEYS, as_float, first


def solved(header):
    """True se c'e' vera presenza di un WCS: `PLTSOLVD` vero, `WCSAXES`, o la matrice `CD`.
    Un `CRVAL1` nudo non basta: e' il puntamento della montatura, non una soluzione."""
    plt = header.get("PLTSOLVD")
    if plt is True or (isinstance(plt, str) and plt.strip().upper() in ("T", "TRUE")):
        return True
    if header.get("WCSAXES") is not None:
        return True
    return any(header.get(k) is not None for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2"))


def wcs_scale(header):
    """Arcosecondi per pixel dalla soluzione astrometrica (binning compreso): dalla matrice
    CD `sqrt(CD1_1^2 + CD2_1^2) * 3600`, ripiego `|CDELT1| * 3600`. None senza WCS."""
    cd11 = as_float(header.get("CD1_1"))
    cd21 = as_float(header.get("CD2_1"))
    if cd11 is not None and cd21 is not None:
        return math.sqrt(cd11 * cd11 + cd21 * cd21) * 3600.0
    cdelt1 = as_float(header.get("CDELT1"))
    if cdelt1 is not None:
        return abs(cdelt1) * 3600.0
    return None


def wcs_rotation_deg(header):
    """L'orientamento del campo in convenzione CROTA2, in [0, 360), due decimali; None se
    l'header non lo dice. Con la matrice presente e `CD1_2` assente si legge 0 (WCS Paper I);
    con `CD1_2` e `CD2_2` entrambe nulle la matrice e' degenere e l'angolo resta ignoto."""
    cells = {k: as_float(header.get(k)) for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2")}
    if any(v is not None for v in cells.values()):
        cd12, cd22 = cells["CD1_2"] or 0.0, cells["CD2_2"] or 0.0
        if cd12 or cd22:
            return round(math.degrees(math.atan2(-cd12, cd22)) % 360.0, 2)
    crota = as_float(first(header, *KEYS["rotation"]))
    if crota is not None:
        return round(crota % 360.0, 2)
    return None
