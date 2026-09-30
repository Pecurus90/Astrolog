"""Il marchio di riscrittura: che un file e' stato riscritto dopo la camera, e quanto somiglia a
un file appena uscito da lei. Lo usa `spine/copies.py` per scegliere l'originale fra due gemelli.

Vincolo non ovvio: il marchio dice **che** un file e' stato riscritto, mai da chi, e da solo non
toglie niente a nessuno. Due programmi sono diversi quando il vocabolario dei quattro li chiama
in due modi, mai perche' le stringhe non si somigliano.
"""

from ..fits.frame_type import program_names, says_calibrated
from ..fits.header_read import header_from_json
from ..vocab.software import normalize_software


def rewrite_mark(header):
    """Perche' questo file risulta riscritto dopo la camera (`calibrated` | `rewritten`), o
    `None`.

    Due segnali. Le **calibrazioni gia' applicate**, che il file dichiara da se'. E **due
    programmi diversi nominati insieme**: uno ha scattato, l'altro ha riscritto -- e sono
    diversi quando il vocabolario dei quattro li chiama in due modi, mai perche' le stringhe
    non si somigliano (`SGPro 4.4` e `Sequence Generator Pro v4.4` sono lo stesso programma, e
    solo il vocabolario lo sa: e' la ragione per cui questa regola sta nella spina e non in
    `fits`).

    Serve una chiave di chi ha **scritto** il file: un nome solo non e' un marchio -- sarebbe
    il grezzo di chi riprende con Voyager o SGP, che si presentano proprio li' -- e due chiavi
    di sola acquisizione nemmeno. Il marchio dice **che** un file e' stato riscritto, mai da
    chi, e da solo non toglie niente a nessuno: decide quale di due gemelli e' l'originale, e
    chi ha tenuto solo il file calibrato vede tutte le sue ore."""
    if says_calibrated(header):
        return "calibrated"
    acquirers, writers = program_names(header)
    if not writers:
        return None
    programmi = {normalize_software(n) for n in acquirers + writers}
    return "rewritten" if len(programmi) > 1 else None


def mark_of(row):
    return rewrite_mark(header_from_json(row["header_json"]))


# Quanto pesa un marchio: le calibrazioni applicate dicono che sono cambiati i **pixel**,
# due programmi nominati insieme dicono solo che qualcuno ha toccato l'**header** -- e a un
# grezzo l'header lo riscrive anche chi non lo calibra (un solutore, un correttore di
# metadati). Fra i due, il calibrato e' il file lavorato.
MARK_WEIGHT = {None: 0, "rewritten": 1, "calibrated": 2}


def originality(row, mark):
    """Quanto un frame somiglia a un file appena uscito dalla camera: piu' basso, piu'
    originale. Il marchio si passa gia' calcolato: leggerlo vuol dire rileggere l'header.

    Prima il marchio, che vale per qualunque programma; poi il software di ripresa fra i
    quattro, che sta solo su un grezzo di chi usa quei quattro -- e da solo non bastava,
    perche' chi elabora la chiave di chi ha acquisito spesso non la cancella (misurato su
    header veri)."""
    return (
        MARK_WEIGHT[mark],
        0 if normalize_software(row["software_raw"]) is not None else 1,
    )
