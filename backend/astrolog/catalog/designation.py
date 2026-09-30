"""Da un nome scritto come capita alla coppia `(catalogo, numero)` con cui si cerca in
catalogo. Portata da `old/backend/astrolog/catalogs/classify.py` coi suoi casi.

E' un PARSER, non un test di esistenza: dice "questo nome sembra un `NGC 224`", non se quella
voce esista. L'esistenza la verifica chi interroga il database.

Vincoli non ovvi, tutti pagati:

* **Il prefisso non e' fatto solo di lettere.** `Sh2` porta una cifra dentro, e una regola
  "lettere, poi numero" spezza `Sh2 155` in `SH` + `2155`: 313 voci Sharpless irraggiungibili,
  e sono proprio quelle che si scrivono negli header a banda stretta (Cave, Cuore, Anima,
  Proboscide, Tulipano). Per questo il prefisso e' scritto, non dedotto.
* **Le forme estese si scrivono a mano, non si derivano.** Chi cerca digita il nome che sa --
  `Barnard 33`, non `B 33`. Derivarle dai titoli dei cataloghi darebbe alias sbagliati: `PK`
  e' Perek-Kohoutek ma il titolo dice "Acker+", `WR` e' Wolf-Rayet ma dice "van der Hucht".
* **`Lynds` non c'e', ed e' voluto.** E' l'autore sia di LBN (nebulose brillanti) sia di LDN
  (oscure): `Lynds 33` e' ambiguo, e indovinare manderebbe sull'oggetto sbagliato. Meglio
  nessun risultato che uno falso.
* **La lettera in coda fa parte del numero.** `NGC 7331A` e `WR 148A` sono oggetti diversi da
  `NGC 7331` e `WR 148`: perderla vorrebbe dire dare le ore al vicino sbagliato.
* **Lo zero iniziale no**: `NGC 0224` e `NGC 224` sono lo stesso oggetto.
"""

import re

_FLAGS = re.IGNORECASE | re.ASCII

# Codice del catalogo, e le grafie con cui lo si scrive: la sigla e -- dove esiste -- il nome
# per esteso, che e' quello che uno digita quando cerca. L'ordine e' quello di prova: conta
# solo dove una grafia e' il prefisso di un'altra.
_CATALOGS: list[tuple[str, tuple[str, ...]]] = [
    ("M", ("Messier", "M")),
    ("NGC", ("NGC",)),
    ("IC", ("IC",)),
    ("Sh2", ("Sharpless", "Sh2")),
    ("LBN", ("LBN",)),
    ("LDN", ("LDN",)),
    ("vdB", ("van den Bergh", "vdB")),
    ("Arp", ("Arp",)),
    ("HCG", ("HCG",)),
    ("RCW", ("RCW",)),
    ("Caldwell", ("Caldwell",)),
    ("Mel", ("Melotte", "Mel")),
    ("Cl", ("Cl",)),
    ("Barnard", ("Barnard",)),
    ("Abell", ("Abell",)),
    ("WR", ("Wolf-Rayet", "WR")),
    ("Ced", ("Cederblad", "Ced")),
    ("C", ("C",)),
    ("B", ("B",)),
]

# Il numero, con quel che gli si attacca: zeri davanti che non contano, e fino a due lettere
# in coda che invece contano.
_NUMBER = r"[\s-]*0*(\d+)([A-Za-z]{0,2})$"


def _pattern(forms):
    """Le grafie di un catalogo in un'alternativa sola.

    Dentro una forma estesa **spazio e trattino sono la stessa cosa, e possono mancare**:
    `Wolf-Rayet`, `Wolf Rayet` e `WolfRayet` sono tutti quel catalogo, e chi cerca non sa
    quale delle tre sia quella "giusta"."""
    alternative = "|".join(r"[\s-]*".join(re.split(r"[\s-]+", f)) for f in forms)
    return re.compile(f"^(?:{alternative}){_NUMBER}", _FLAGS)


_PATTERNS = [(code, _pattern(forms)) for code, forms in _CATALOGS]

# Perek-Kohoutek non ha un numero: ha una coordinata galattica (`PK 205+14.1`).
_PK = re.compile(r"^(?:Perek[\s-]*Kohoutek|PK)[\s-]*(\d+[+-]\d+(?:\.\d+)?)$", _FLAGS)

# Il codice con cui la designazione sta scritta nel catalogo, quando la grafia estesa e' quella
# che l'utente conosce ma il file impacchettato usa la sigla.
_AS_WRITTEN = {"Caldwell": "C", "Barnard": "B"}


def parse(raw):
    """`(catalogo, numero)` da un nome scritto come capita, o `None`.

    `M31`, `M 31`, `m  31`, `M 031` e `Messier 31` sono lo stesso oggetto: negli header un
    nome e' scritto in mille modi e nessuno di quei modi e' piu' giusto degli altri."""
    if not raw or not str(raw).strip():
        return None
    name = " ".join(str(raw).split())
    pk = _PK.match(name)
    if pk:
        return "PK", pk.group(1)
    for code, pattern in _PATTERNS:
        m = pattern.match(name)
        if m:
            return _AS_WRITTEN.get(code, code), m.group(1) + m.group(2).upper()
    return None


def key(raw):
    """La chiave con cui una sigla si cerca nel database: `NGC 224` -> `NGC|224`.

    Una chiave sola, scritta al caricamento e cercata qui, invece di normalizzare le colonne
    dentro la query: cosi' l'indice si usa davvero."""
    parsed = parse(raw)
    return f"{parsed[0].upper()}|{parsed[1]}" if parsed else None
