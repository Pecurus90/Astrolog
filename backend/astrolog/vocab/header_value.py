"""Un valore d'header reso confrontabile per gli alias (strumento, filtro, oggetto).

Vincolo non ovvio: la pulizia e' cosmetica e conservativa -- minuscole, via l'indice di
istanza ASCOM `(N)` in coda, punti in spazi, spazi collassati -- mai al punto di fondere due
pezzi diversi. Idempotente. La stessa funzione normalizza cio' che si scrive nell'alias e
cio' che si legge dal frame, altrimenti il confronto non e' deterministico.
"""

import re

_WS_RE = re.compile(r"\s+")
_TRAILING_INDEX_RE = re.compile(r"\s*\(\d+\)\s*$")


def normalize_header_value(value):
    """`"ZWO Focuser (1)"` -> `"zwo focuser"`, `"ASCOM.ToupTek.AAF"` -> `"ascom touptek aaf"`,
    None -> "". Una stringa che normalizza a "" non e' un alias: lo respinge chi scrive."""
    if value is None:
        return ""
    x = str(value).lower()
    x = _TRAILING_INDEX_RE.sub("", x)
    x = x.replace(".", " ")
    x = _WS_RE.sub(" ", x)
    return x.strip()
