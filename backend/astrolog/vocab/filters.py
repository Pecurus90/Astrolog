"""Il vocabolario dei filtri: dal nome com'e' scritto nell'header al nome canonico, e da li'
alla banda. Un dato solo (`filters.json`), un modulo solo.

Vincolo non ovvio: il catalogo dei modelli risponde per primo (un prodotto e' piu' specifico
di una parola generica); marca e larghezza di banda si spogliano prima della mappa; la
spazzatura (posizione della ruota, trattini, "dslr") e' None; un nome conteso fra due marche
non e' un modello. Su una camera a colori un filtro a banda larga diventa OSC, ma uno che
si avvita davanti resta se stesso.
"""

import json
import re
from pathlib import Path

_DATA = json.loads(Path(__file__).with_name("filters.json").read_text(encoding="utf-8"))

FILTER_MAP = dict(_DATA["words"])
NARROWBAND_CLIP = frozenset(_DATA["clip"])
PASSBANDS = frozenset(_DATA["passbands"])
# Le bande larghe: su una camera a colori non ci sono, la matrice e' il filtro (diventano OSC).
BROADBAND = frozenset({"L", "R", "G", "B"}) & PASSBANDS
_PASSBAND_OF = dict(_DATA["passband_of"])
WIDTH_RE = re.compile(r"\b\d+(?:\.\d+)?\s*nm\b", re.IGNORECASE | re.ASCII)
JUNK_RE = re.compile(r"^(?:\d+|-+|dslr)$", re.IGNORECASE | re.ASCII)

_MODELS = sorted(
    (
        {
            "id": m["id"],
            "brand": m["brand"],
            "name": m["name"],
            "passband": m["passband"],
            "aliases": list(m.get("aliases") or ()),
        }
        for m in _DATA["models"]
    ),
    key=lambda m: (m["brand"].lower(), m["name"].lower()),
)
# Le marche da spogliare prima della mappa: quelle del catalogo, piu' le marche da ruota
# (Astrodon, Chroma) che non vendono filtri da avvitare e non stanno nei modelli.
BRAND_PREFIXES = frozenset({m["brand"].lower() for m in _MODELS} | {"astrodon", "chroma"})

# La banda di chi dichiara "nessun filtro davanti", e quella di chi non si sa: chi decide
# guarda queste, non una stringa scritta a mano altrove.
NO_FILTER = "NONE"
UNKNOWN = "UNKNOWN"
# Il nome canonico di chi non ha un vetro davanti, com'e' nei dati: la riga "nessun filtro" nasce
# con lui, e a tradurlo per lo schermo e' la pagina.
NO_FILTER_NAME = FILTER_MAP["none"]
_BY_NAME = {}
for _m in _MODELS:
    for _n in [_m["name"], *_m["aliases"]]:
        _key = _n.strip().lower()
        # gia' visto da un altro modello -> conteso, e resta conteso per sempre
        _BY_NAME[_key] = None if _key in _BY_NAME and _BY_NAME[_key] is not _m else _m


def models():
    """I filtri in commercio, ordinati per marca e nome: l'ordine con cui si cerca in tendina."""
    return list(_MODELS)


def model_by_id(model_id):
    """Il modello del catalogo con quell'id, o None."""
    return next((m for m in _MODELS if m["id"] == model_id), None)


def model_of(name):
    """Il modello che porta questo nome o alias (maiuscole e spazi ai bordi indifferenti),
    o None: anche quando il nome e' conteso fra due modelli."""
    if not name:
        return None
    return _BY_NAME.get(str(name).strip().lower())


def passband_of(canonical):
    """La banda di un nome canonico (parola generica o modello), o UNKNOWN."""
    if canonical in _PASSBAND_OF:
        return _PASSBAND_OF[canonical]
    m = model_of(canonical)
    return m["passband"] if m is not None else UNKNOWN


# Le bande FISICHE che un filtro puo' lasciar passare, e che quindi si dichiarano. Le altre
# voci di PASSBANDS (i duo, i tri, gli OSC, "nessun filtro") sono etichette che si RICAVANO
# da queste: dichiararle sarebbe come dire che un filtro lascia passare "duo".
BANDS = ("L", "R", "G", "B", "HA", "HB", "OIII", "SII")
_NARROW = frozenset({"HA", "HB", "OIII", "SII"})
# Le coppie che hanno un nome loro nel dominio chiuso: tutto il resto e' "piu' bande".
_DUO = {frozenset({"HA", "OIII"}): "DUO_HAOIII", frozenset({"SII", "OIII"}): "DUO_SIIOIII"}


def passband_from_bands(bands):
    """La banda canonica di un filtro dichiarato, dalle bande che lascia passare.

    E' l'unica strada dalle bande alla banda: la usa chi dichiara un filtro e chi lo
    rilegge, cosi' un duo Ha/OIII non si chiama in due modi diversi in due posti. Le parole
    che non sono bande fisiche non contano: `TRI_NB` e' per tre bande STRETTE, non per tre
    filtri qualsiasi."""
    chosen = [b for b in dict.fromkeys(bands) if b in BANDS]
    if not chosen:
        return UNKNOWN
    if len(chosen) == 1:
        return chosen[0]
    if not set(chosen) <= _NARROW:
        # `MULTI_NB` e `TRI_NB` vogliono dire "piu' bande STRETTE": un filtro che lascia
        # passare L, R e G non e' un tri-banda, e non ha un'etichetta nel dominio chiuso.
        return UNKNOWN
    if len(chosen) == 2:
        return _DUO.get(frozenset(chosen), "MULTI_NB")
    return "TRI_NB" if len(chosen) == 3 else "MULTI_NB"


def _strip_brand_and_width(value):
    s = WIDTH_RE.sub(" ", value)
    tokens = [t for t in s.split() if t not in BRAND_PREFIXES]
    return " ".join(tokens).strip()


def normalize_filter(raw, *, bayer):
    """Il nome canonico del filtro, o None se non c'e' o non e' un filtro.

    `bayer` dice se l'header ha dichiarato una matrice di Bayer (camera a colori). Un valore
    fuori da ogni vocabolario torna con la prima lettera maiuscola e il resto com'era."""
    canonical = None
    if raw:
        low = raw.lower().strip()
        model = model_of(low)
        if model is not None:
            return model["name"]
        core = _strip_brand_and_width(low)
        canonical = FILTER_MAP.get(core) or FILTER_MAP.get(low)
        if not canonical:
            canonical = None if JUNK_RE.match(low) else raw[0].upper() + raw[1:]
    if bayer:
        if canonical and model_of(canonical) is not None:
            return canonical
        if not canonical or canonical not in NARROWBAND_CLIP:
            return "OSC"
    return canonical


def is_broadband_word(raw):
    """Se il vocabolario conosce quella parola come una banda larga (`L`, `Lum`, `B`): su una camera
    a colori non c'e', perche' la matrice e' il filtro."""
    return passband_of(normalize_filter(raw, bayer=False)) in BROADBAND
