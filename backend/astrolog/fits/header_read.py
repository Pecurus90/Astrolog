"""Apre un FITS e ne legge l'header intero con astropy; l'impronta del frame (dimensioni e
64 KB di pixel dal centro del blocco dati) e il formato JSON dell'header per la colonna.

Vincolo non ovvio: un file a pagina primaria vuota (MEF, Rice) tiene i metadati nella prima
pagina con dati, che si combina col primario. Ogni errore di lettura e' `HeaderReadError`,
tipato, che il chiamante conta e segnala: mai inghiottito.
"""

import hashlib
import json
import math
from collections.abc import Iterator
from typing import Any, cast

from astropy.io import fits

# Chiavi strutturali della pagina: descrivono il contenitore, non il frame.
STRUCTURAL_KEYS = frozenset(
    {"SIMPLE", "XTENSION", "EXTEND", "BITPIX", "NAXIS", "PCOUNT", "GCOUNT", "EXTNAME"}
)


class HeaderReadError(Exception):
    """Lettura dell'header fallita: file mancante, illeggibile, corrotto, non FITS."""

    def __init__(self, path, cause):
        super().__init__(f"lettura header fallita per {path}: {cause}")
        self.path = path
        self.cause = cause


def _has_pixels(hdu):
    return isinstance(hdu, fits.CompImageHDU) or bool(hdu.header.get("NAXIS", 0))


def _with_data_page(primary, data_hdr):
    combined = primary.copy()
    for card in data_hdr.cards:
        kw = card.keyword
        if not kw or kw in ("COMMENT", "HISTORY") or kw in STRUCTURAL_KEYS:
            continue
        try:
            combined[kw] = (card.value, card.comment)
        except (ValueError, TypeError):
            continue  # card anomala: si salta, mai un crash
    return combined


def read_frame(path):
    """`(header, block)`: l'`astropy.io.fits.Header` intero del file e, se per leggerlo si e' gia'
    arrivati a una pagina con pixel dopo la primaria, `(inizio, lunghezza)` del suo blocco dati
    -- l'impronta lo usa invece di farlo rileggere ad astropy. `None` quando astropy non lo dice:
    la primaria ha i pixel, o nessuna pagina ne ha, o la pagina non sa dire dove sono; il blocco lo
    cerca allora chi fa l'impronta. Solleva `HeaderReadError`."""
    try:
        with fits.open(path, output_verify="silently", ignore_missing_end=True) as hdul:
            # una pagina alla volta, fino alla prima con pixel: `len(hdul)` e `hdul.fileinfo`
            # farebbero leggere ad astropy tutte le pagine del file, quella della pagina no. Un
            # file senza pagine lo rifiuta gia' `fits.open`.
            primary = None
            # i tipi di astropy dicono che si scorrono HDUList: si scorrono pagine
            pages = cast("Iterator[Any]", iter(hdul))
            for hdu in pages:
                if primary is None:
                    primary = hdu.header
                    if primary.get("NAXIS", 0):
                        return primary, None
                elif _has_pixels(hdu):
                    info = hdu.fileinfo()
                    block = (info["datLoc"], info["datSpan"]) if info else None
                    return _with_data_page(primary, hdu.header), block
            return primary, None  # il blocco lo decide `_data_block`, con la strada veloce prima
    except Exception as e:  # noqa: BLE001 - qualunque guasto e' un errore di dominio tipato
        raise HeaderReadError(path, e) from e


def read_header(path):
    """L'`astropy.io.fits.Header` intero del file. Solleva `HeaderReadError`."""
    return read_frame(path)[0]


FINGERPRINT_BYTES = 65536


BLOCK = 2880  # il blocco del FITS: header e dati ne occupano un numero intero
_CARD = 80
_CLEAN_END = b"END" + b" " * (_CARD - 3)
_KEY_CHARS = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
_BYTES_PER_PIXEL = {8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}
_STRUCTURAL = frozenset({b"SIMPLE", b"BITPIX", b"GROUPS", b"PCOUNT", b"GCOUNT"})  # e le NAXISn


def _data_block(path, known=None):
    """(inizio, lunghezza) del blocco dati della prima pagina con pixel, letti dal file:
    l'header combinato di `read_header` non e' quello su disco e non dice dove stanno. Prima la
    strada veloce, sempre: su un file rovinato le due strade possono non concordare, e l'impronta
    ha sempre deciso cosi'. `known` e' cio' che astropy ha gia' detto (`read_frame`), e sostituisce
    solo la sua seconda lettura."""
    fast = _primary_data_block(path)
    if fast is not None:
        return fast
    return known if known is not None else _data_block_astropy(path)


def _primary_data_block(path):
    """Il caso comune dai blocchi dell'header, senza astropy -- che per dirlo legge ogni pagina
    del file: una pagina primaria con pixel, non a gruppi, con un END pulito. `None` per tutto il
    resto, che decide astropy: questa strada si ritira, non stima, perche' da questi due numeri
    dipende l'impronta. Davanti a un `END` seguito da un carattere che non sta in un nome di chiave
    (spazio compreso) ma non pulito, astropy decide secondo i byte che seguono: li' si ritira, e
    calcola solo sull'END pulito. `ENDTIME` e simili sono chiavi, e la lettura prosegue."""
    values, start = {}, 0
    with open(path, "rb") as f:
        while True:
            block = f.read(BLOCK)
            if len(block) < BLOCK:
                return None  # un header senza END: lo decide astropy
            start += BLOCK
            for i in range(0, BLOCK, _CARD):
                card = block[i : i + _CARD]
                if card[:3] == b"END" and card[3] not in _KEY_CHARS:
                    return _span(values, start) if card == _CLEAN_END else None
                key = card[:8].rstrip()
                if (key in _STRUCTURAL or key.startswith(b"NAXIS")) and card[8:10] == b"= ":
                    values[key] = card[10:].split(b"/")[0].strip()


def _span(values, start):
    try:
        if values.get(b"SIMPLE") != b"T" or b"GROUPS" in values:
            return None
        if int(values.get(b"PCOUNT", 0)) != 0 or int(values.get(b"GCOUNT", 1)) != 1:
            return None  # astropy li mette nella lunghezza: e' il caso raro, e lo decide lui
        pixel = _BYTES_PER_PIXEL.get(int(values[b"BITPIX"]))
        axes = int(values[b"NAXIS"])
        if pixel is None or axes <= 0:
            return None
        size = pixel * math.prod(int(values[b"NAXIS%d" % n]) for n in range(1, axes + 1))
    except (KeyError, ValueError):
        return None
    return start, size + (-size % BLOCK)


def _data_block_astropy(path):
    with fits.open(
        path, output_verify="silently", ignore_missing_end=True, memmap=False, lazy_load_hdus=False
    ) as hdul:
        for i, hdu in enumerate(hdul):
            info = hdul.fileinfo(i)
            if info and _has_pixels(hdu):
                return info["datLoc"], info["datSpan"]
    return 0, 0


def frame_fingerprint(path, header, block=None):
    """L'identita' del frame: sha256 delle dimensioni e di 64 KB di pixel presi dal CENTRO
    del blocco dati, dove non stanno i bordi neri di un frame registrato ne' l'overscan.
    Stabile a una riscrittura dell'header. Un file senza blocco dati (troncato) ripiega
    sulle card dell'header: l'unica cosa che ha. `block` e' quello di `read_frame`, se c'e'."""
    try:
        # Dove stiano i pixel lo dice il FILE, mai l'header che abbiamo in mano: un header
        # riletto e riscritto puo' avere una lunghezza diversa da quella su disco (astropy
        # aggiunge END dove manca), e l'impronta guarderebbe altri byte.
        start, span = _data_block(path, block)
    except Exception as e:  # noqa: BLE001 - stesso ombrello di read_frame: si conta per file
        raise HeaderReadError(path, e) from e
    chunk = b""
    if span:
        with open(path, "rb") as f:
            f.seek(start + max(0, (span - FINGERPRINT_BYTES) // 2))
            chunk = f.read(FINGERPRINT_BYTES)
    dims = f"{header.get('NAXIS1')}x{header.get('NAXIS2')}:{header.get('BITPIX')}".encode()
    h = hashlib.sha256(dims)
    h.update(chunk if chunk else header.tostring().encode("ascii", "replace"))
    return h.hexdigest()


def header_from_json(header_json):
    """L'header salvato, com'era: la lista di coppie torna un dizionario. Le chiavi ripetute
    (`HISTORY`, `COMMENT`) collassano sull'ultima -- chi ha bisogno di tutte legge la lista.

    E' l'inverso di `header_to_json`, e sta qui accanto apposta: chi rilegge l'header dal
    database non deve conoscerne il formato."""
    return dict(json.loads(header_json or "[]"))


def header_to_json(header):
    """L'header come lista JSON di coppie `[chiave, valore]`; un valore non serializzabile
    diventa testo, cosi' il JSON e' sempre valido."""
    pairs = []
    for k, v in header.items():
        if v is None or isinstance(v, (str, int, bool)):
            pairs.append([k, v])
        elif isinstance(v, float):
            pairs.append([k, v if math.isfinite(v) else str(v)])
        else:
            pairs.append([k, str(v)])
    return json.dumps(pairs, ensure_ascii=False)
