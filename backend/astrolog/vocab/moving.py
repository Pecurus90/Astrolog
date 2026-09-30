"""Comete e asteroidi riconosciuti dal nome, per non cercarli nel catalogo.

Un oggetto mobile non sta due notti nello stesso punto: cercarlo per coordinate darebbe una
risposta sbagliata e **sicura di se'**. Qui si riconosce dal solo nome e si mette da parte.
Portata da `old/backend/astrolog/catalogs/identify.py:33-76`.

Vincoli non ovvi -- ognuno e' un falso positivo vero, e la guardia e' cresciuta un errore alla
volta:

* **Vuole la designazione intera.** Un falso positivo qui e' peggio di un buco: dichiarare
  mobile un oggetto fisso lo toglie da ogni coda e nessuno lo rivede piu'. Chi cade fuori
  resta visibile e correggibile, ed e' il verso giusto in cui sbagliare.
* **Lo slash non basta come unica porta**: e' illegale nei nomi di file, e il nome che arriva
  qui e' lo stesso che N.I.N.A. usa per la cartella. Spazio, `_` e `-` valgono quanto lo
  slash -- ma solo se il resto della designazione c'e' davvero.
* **Dopo la sigla cometaria non puo' esserci una cifra**, altrimenti le survey di Cambridge
  (`3C 273`, `4C-21.53`) diventano comete.
* **La provvisoria vuole l'anno**, non "sigla piu' numero": senza quell'ancora il Caldwell
  `C 109` diventa una cometa, e senza l'ancora di fine stringa la cartella `2022 IC 1396`
  diventa l'asteroide `2022 IC`.
* **Senza slash, le lettere di mezzo-mese B, C e M non si accettano**: la cartella `C 2023 M31`
  e la cometa `C/2023 M31` hanno la stessa forma, e il lessico non le separa. Con lo slash
  passano tutte, perche' li' l'ambiguita' non c'e'.

Il prezzo, dichiarato: l'asteroide scritto **a numero nudo** (`433 Eros`) non e' mobile
d'ufficio -- ha la stessa forma di una Flamsteed per esteso (`104 Herculis`) e di mezza
tavolozza di nomi di lavoro (`600 Second Darks`), e fra le tre il lessico non decide.
"""

import re

_MOVING = re.compile(
    r"^\s*("
    # cometa numerata: 12P/Pons-Brooks, 12P Pons-Brooks, 12P_Pons-Brooks, 73P-C, 12P
    r"\d{1,4}[PDCI](?:/|[\s_-]+[A-Z][a-z]|-[A-Z](?![0-9A-Za-z])|\s*$)"
    r"|[PDCXAI]/\s*\d{3,4}\b"  # provvisoria con lo slash: C/2023, P/2010
    # e senza: C 2023 A3, C-2020 F3 (le lettere ambigue B, C, M restano fuori: vedi sopra)
    r"|[PDCXAI][\s_-]\s*(?:1[89]|20)\d{2}[\s_-]+[ADEFGHJKLNOPQRSTUVWXY]\d"
    r"|\(\d{1,7}\)"  # asteroide numerato fra parentesi: (4) Vesta
    r"|\d{4}\s+[A-Z]{2}\d*\s*$"  # provvisoria di asteroide: 2023 DZ2
    r")",
    re.IGNORECASE,
)


def is_moving_designation(name):
    """`True` se il nome e' una cometa o un asteroide. Un nome vuoto non lo e'."""
    return bool(name) and bool(_MOVING.match(name.strip()))
