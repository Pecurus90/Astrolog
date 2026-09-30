"""Il software di ripresa dal valore grezzo dell'header al nome canonico: i quattro
supportati e basta (Marco, 2026-09-06). Tutto il resto resta com'e' scritto, in
`software_raw`, che si conserva sempre.

Vincolo non ovvio: la ricerca e' per sottostringa, in ordine: "n.i.n.a" e "nina" prima di
qualunque altra cosa che le contenga.
"""

# I quattro nomi canonici, ognuno con la sua costante: una regola che altrove deve dire "questo
# file lo ha scritto l'ASIAIR" la nomina invece di ripetere la stringa, o lo stesso nome finirebbe
# in due case che possono divergere in silenzio.
NINA = "N.I.N.A."
ASIAIR = "ASIAIR"
VOYAGER = "Voyager"
SGP = "Sequence Generator Pro"

SOFTWARE_PATTERNS = (
    ("nina", NINA),
    ("n.i.n.a", NINA),
    ("asiair", ASIAIR),
    ("voyager", VOYAGER),
    ("sequence generator", SGP),
    ("sgpro", SGP),
    ("sgp", SGP),
)


def telescope_is_mount(software):
    """Se quel software (canonico) scrive la **montatura** in `TELESCOP`, e l'ottica da nessuna
    parte: l'ASIAIR. Chi legge `TELESCOP` chiede qui, o una casa lo prende per ottica e l'altra
    per montatura."""
    return software == ASIAIR


def normalize_software(raw):
    """Il nome canonico del software, o None se il valore e' vuoto o non e' uno dei quattro."""
    if not raw:
        return None
    low = str(raw).lower()
    for needle, canonical in SOFTWARE_PATTERNS:
        if needle in low:
            return canonical
    return None
