"""Che cos'e' questo file: un light, un file di calibrazione, uno stack, o non lo dice -- e se
dichiara di essere gia' calibrato, e quali programmi nomina.

Vincolo non ovvio: assente o non riconosciuto -> `unknown`, mai "assumiamo light" -- c'e' chi
non scrive IMAGETYP (ASI Studio, SharpCap: software-ok, sono la RAGIONE del ramo `unknown`, non
una fonte) e quei frame entrano, non si perdono: la domanda sul tipo in Da confermare e' in
coda. Uno stack si riconosce solo da segnali forti (chiavi di conteggio, parola a confine di
parola), mai dall'esposizione: un light lungo non deve sparire.
"""

import re

from .header_keys import ACQUISITION_KEYS, WRITER_KEYS, as_int, get, text

# Il vocabolario, scritto **senza separatori**: le grafie si confrontano dopo averli tolti
# (`_type_of_word`), percio' `Dark Frame`, `DARK-FRAME`, `dark_frame` e `darkframe` sono una
# voce sola invece di quattro. Dei quattro software supportati abbiamo l'header vero solo di
# N.I.N.A. e ASIAIR (scrivono `DARK`): di Voyager e SGP non sappiamo la grafia, e la grafia
# non deve decidere se una calibrazione entra in archivio.
FRAME_TYPES = {
    "light": "light",
    "lightframe": "light",
    "science": "light",
    "scienceframe": "light",
    "object": "light",
    "objectframe": "light",
    "exposure": "light",
    "dark": "dark",
    "darkframe": "dark",
    "flat": "flat",
    "flatframe": "flat",
    "flatfield": "flat",
    "bias": "bias",
    "biasframe": "bias",
    "offset": "bias",
    "zero": "bias",
    "darkflat": "dark_flat",
    "flatdark": "dark_flat",
}

CALIBRATION_TYPES = frozenset({"dark", "flat", "bias", "dark_flat"})
# Il tipo che l'header non ha detto: lo scrive `image_type` qui sotto, lo cerca la domanda
# "che file e'" (`spine/typeless.py`) e lo cerca la spina per sapere chi aspetta una
# risposta (`spine/stages.py`). Una parola, una casa.
UNKNOWN = "unknown"

SEPARATORS_RE = re.compile(r"[\s_\-]+", re.ASCII)

STACK_COUNT_KEYS = ("STACKCNT", "NCOMBINE", "NIMAGES")
STACK_WORD_RE = re.compile(r"\b(?:master|integration|stack|stacked)\b", re.IGNORECASE | re.ASCII)
# Chi non conta i frame sommati li ELENCA nella storia dell'header, uno per riga. Non e' una
# parola in mezzo a una frase: e' una chiave numerata, e la si cerca cosi'. `CALSTAT` e
# `CALIBRAT` restano fuori da qui apposta -- dicono "calibrato", non "sommato", e una posa
# calibrata e' una posa: fanno l'altro mestiere, qui sotto.
STACK_SOURCE_RE = re.compile(r"\bSOURCE\d+\b", re.ASCII)

# Lo stato di calibrazione del file lo dicono due chiavi, e NON si leggono allo stesso modo.
# `CALSTAT` e' un codice di **lettere** -- B bias, D dark, F flat -- e ognuna dice che quella
# calibrazione e' stata applicata. `CALIBRAT` e' un **si'/no**, e nel FITS il logico si scrive
# `T` o `F`: fra apici arriva come stringa, e li' `F` vuol dire falso, non flat. Leggerle con
# la stessa regola le inverte tutte e due. La convenzione delle lettere e' pubblica e non
# nomina nessun programma; la fonte si': *FITS File Header Definitions*, Diffraction Limited
# (aiuto di MaxIm DL).  <!-- software-ok: e' la fonte, non un software supportato -->
CALIBRATION_LETTERS = "bdf"
YES_WORDS = frozenset({"t", "true", "yes", "y"})
# Alfabeto e separatori sono CHIUSI: un `CALSTAT` con una lettera fuori convenzione (`BDX`) o
# separato da virgole (`B,D,F`) legge "non calibrato". E' una scommessa presa su zero prove:
# il ramo delle lettere non e' mai stato visto scattare su un header vero (sull'archivio di
# collaudo i cinque calibrati sono numeri). Quando un header vero mostrera' un'altra forma, si
# allarga di qui -- non a caso, e non perche' `BDX` sembra un difetto.


def is_stack(header):
    """True su una chiave che conta PIU' di un frame sommato, su una parola-stack in
    IMAGETYP/OBJECT, o sull'elenco dei sorgenti nella storia. Un conteggio di 1 e' una posa:
    la somma di se stessa."""
    if any((as_int(header.get(k)) or 0) > 1 for k in STACK_COUNT_KEYS):
        return True
    for key in ("IMAGETYP", "OBJECT"):
        v = header.get(key)
        if isinstance(v, str) and STACK_WORD_RE.search(v):
            return True
    return any(STACK_SOURCE_RE.search(str(riga)) for riga in header.get("HISTORY", []))


def _type_of_word(value):
    """La categoria che una parola dichiara, o `None`. E' l'unico posto dove si legge il
    vocabolario: `IMAGETYP` e `OBJECT` passano di qui, un fatto una casa.

    Il confronto e' a separatori tolti e al singolare, perche' la stessa cosa si scrive in
    molti modi e nessuno e' sbagliato: `Dark Frame`, `DARK-FRAME`, `dark_frame`, `darkframe`
    e `darks` sono tutti un dark."""
    parola = SEPARATORS_RE.sub("", (value or "").lower())
    for candidato in (parola, parola.removesuffix("es"), parola.removesuffix("s")):
        if candidato in FRAME_TYPES:
            return FRAME_TYPES[candidato]
    return None


def _calibration_in_object(header):
    """Il tipo di calibrazione che il campo OGGETTO dichiara, o `None`.

    E' la seconda spia, e serve: una libreria di calibrazione puo' scrivere `IMAGETYP = LIGHT`
    e `OBJECT = darkflat`, e senza guardare qui quei file entrano in archivio come un oggetto
    del cielo: misurati sull'archivio di collaudo, **56 file** -- 28 pose distinte piu' le loro
    copie in un'altra cartella.

    Il confronto e' sull'**intero campo**, mai su un pezzo: `Dark Nebula` e `Flaming Star`
    sono oggetti veri, e una ricerca per sottostringa li farebbe sparire. E' lo stesso
    vocabolario di `IMAGETYP`, letto da un'altra parte: un fatto, una casa."""
    kind = _type_of_word(text(get(header, "object")))
    return kind if kind in CALIBRATION_TYPES else None


def _as_flag(value):
    """Vero o falso quando il valore e' un numero (acceso o a zero) o quando la chiave non
    c'e'. `None` se e' una parola, e allora la chiave se la legge a modo suo.

    Arriva sempre come testo, perche' `text` normalizza tutto e toglie gli apici che avvolgono
    il valore: senza quel passaggio `'T'` e `'F'` si scambiano le risposte. Il logico del FITS
    arriva quindi come la parola `True` o `False`, e lo leggono i due rami delle parole."""
    if value is None:
        return False
    try:
        return bool(float(value))
    except ValueError:
        return None


def _calibrations_applied(value):
    """`CALSTAT`: un **codice**, non un testo libero. Vale se e' fatto SOLO di lettere della
    convenzione (`BDF`, `D`; in mezzo si tollerano spazi, trattini e underscore, una virgola
    no), piu' il si' del logico, che c'e' chi lo scrive li' (`T` non e' una lettera della
    convenzione: nessuna ambiguita').

    Cercare una lettera **dentro** il valore, invece che chiedere che il valore sia fatto solo
    di quelle, fa leggere `uncalibrated` come "calibrato" per la sua `d`: e un grezzo che
    dichiara di non essere calibrato perderebbe contro qualunque gemello. Nessun elenco di
    parole di rifiuto: sarebbe da allungare al primo programma che ne scrive un'altra."""
    flag = _as_flag(value)
    if flag is not None:
        return flag
    parola = value.casefold()
    if parola in YES_WORDS:
        return True
    lettere = SEPARATORS_RE.sub("", parola)
    return bool(lettere) and all(c in CALIBRATION_LETTERS for c in lettere)


def _says_true(value):
    """`CALIBRAT`: un si'/no, e basta -- le lettere non le legge. `F` e' il **falso** del FITS,
    non la lettera del flat: fra apici arriva come parola, e leggerla con le lettere
    invertirebbe la risposta."""
    flag = _as_flag(value)
    if flag is not None:
        return flag
    return value.casefold() in YES_WORDS


def says_calibrated(header):
    """L'header dichiara le calibrazioni gia' applicate: questo file non e' uscito cosi' dalla
    camera.

    Le due chiavi si leggono con due regole diverse, o si invertono a vicenda. Un marchio dove
    non ci vuole e' peggio di nessun marchio: farebbe passare per copia una posa vera, e quelle
    ore sparirebbero.

    E' la meta' del marchio di riscrittura che si legge senza sapere niente dei programmi;
    l'altra meta' (due programmi diversi nominati insieme) ha bisogno del vocabolario dei
    quattro, che vive fuori di qui, e la fa `spine/normalize`."""
    return _calibrations_applied(text(header.get("CALSTAT"))) or _says_true(
        text(header.get("CALIBRAT"))
    )


def program_names(header):
    """I programmi nominati nell'header, in due famiglie: chi ha ACQUISITO il file e chi lo ha
    SCRITTO. Si legge e basta, tutte le chiavi e non la prima di ciascuna -- chi riprende
    occupa la chiave che vuole, e chi elabora ci mette la propria accanto.

    Se due grafie siano lo stesso programma qui non si puo' sapere: `SGPro 4.4` e `Sequence
    Generator Pro v4.4` non si somigliano affatto, e a dire che sono la stessa cosa e' il
    vocabolario -- che sta in `vocab`, uno strato separato da `fits`."""
    return tuple(_named(header, ACQUISITION_KEYS)), tuple(_named(header, WRITER_KEYS))


def _named(header, keys):
    return (n for n in (text(header.get(k)) for k in keys) if n)


def image_type(header):
    """`light | dark | flat | bias | dark_flat | stack | unknown`."""
    if is_stack(header):
        return "stack"
    calibrazione = _calibration_in_object(header)
    if calibrazione is not None:
        return calibrazione
    return _type_of_word(text(get(header, "image_type"))) or UNKNOWN
