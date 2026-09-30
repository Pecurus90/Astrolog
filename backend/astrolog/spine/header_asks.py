"""Tre giudizi sul grezzo di una posa, scritti dalla scansione quando la legge: il file non dice la
camera, non dice il filtro, nomina l'ottica. Da confermare li filtra in SQL invece di rileggere
l'archivio intero a ogni apertura.

Vincolo non ovvio: dipendono solo da cio' che il file dice -- `INSTRUME`, `FILTER`, `TELESCOP` e il
programma che ha scritto il file -- e dal vocabolario, quindi una volta scritti nessuno li deve
riscrivere. Le regole restano nelle loro case (`night_rig`, `unfiltered`, `rig_optics`): qui si
chiamano e basta.
"""

from ..vocab.software import normalize_software
from .night_rig import asks_camera
from .rig_optics import names_the_optics
from .unfiltered import says_no_filter


def of(fields):
    """`{colonna: 0 o 1}` per i campi grezzi di una posa (`fits.header_fields.extract_fields`)."""
    software = normalize_software(fields.get("software_raw"))
    return {
        "asks_camera": int(asks_camera(fields.get("instrument_raw"))),
        "asks_filter": int(says_no_filter(fields.get("filter_raw"))),
        "names_optics": int(names_the_optics(software, fields.get("telescope_raw"))),
    }
