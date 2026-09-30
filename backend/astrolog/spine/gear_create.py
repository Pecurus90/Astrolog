"""Far nascere un pezzo o un filtro dell'attrezzatura: la casa sola dei due modi in cui nascono --
la spina li trova nei file, oppure li scrivi tu. Il filtro scritto da te riceve la scheda da
`gear.declare_filter`, come una correzione.

La spina lo riconosce leggendo un header, oppure lo scrivi tu dalla pagina Attrezzatura -- e in
tutti e due i casi e' la stessa riga, perche' un pezzo e' il suo **nome dentro il suo genere**
(`instruments_kind_name` e' unico). Cosa c'e' scritto nella sua scheda lo decide chi dichiara
(`gear.declare_instrument`); qui si scrive solo cio' che lo fa esistere.

Vincolo non ovvio: `detected` dice **chi** l'ha fatto nascere e lo passa il chiamante, che e'
l'unico a saperlo. Non si indovina dalla scheda: un pezzo trovato dalla spina e poi corretto
diventa dichiarato, e un pezzo scritto a mano lo e' dal primo istante.
"""

from ..vocab.filters import UNKNOWN, normalize_filter
from ..vocab.header_value import normalize_header_value
from . import declarations, gear


def instrument(conn, kind, name, now, *, detected):
    """La riga di un pezzo, col solo nome: pixel e colore di una camera li scrive `camera_specs`
    a fine giro, il resto lo compila chi dichiara."""
    return conn.execute(
        "INSERT INTO instruments(kind, name, detected, created_at) VALUES(?, ?, ?, ?)",
        (kind, name, int(detected), now),
    ).lastrowid


def filter_id_by_name(conn, name):
    row = conn.execute("SELECT id FROM filters WHERE name = ?", (name,)).fetchone()
    return None if row is None else row["id"]


def create_filter(conn, name, passband, now, is_none=False):
    """La riga di un filtro, rilevato o scritto da te; `is_none` per la riga "nessun filtro", una
    sola nell'archivio."""
    return conn.execute(
        "INSERT INTO filters(name, passband, is_none, created_at) VALUES(?, ?, ?, ?)",
        (name, passband, int(is_none), now),
    ).lastrowid


class SpellingTakenError(ValueError):
    """Quel nome e' gia' una grafia di un altro tuo filtro: la scansione lo porta li'."""


def filter_declared(conn, name, bands, now, *, brand=None, model=None):  # noqa: PLR0913
    """Un filtro che scrivi tu. Nasce come il rilevato e riceve la scheda come una correzione.

    Se il vocabolario ne farebbe un altro nome -- `L` diventa `Lum` -- impara che quel nome e' lui:
    e' la regola di una rinomina, che si legge **dopo il colore**, cosi' le pose mono vengono a lui
    e quelle a colori restano OSC. Si rifiuta se quel nome e' gia' un tuo filtro, o la grafia di un
    altro: le pose che lo dicono ci stanno gia', e un secondo filtro dividerebbe le ore -- si
    rinomina quello."""
    mono = normalize_filter(name, bayer=False)
    for grafia in {name, mono} - {None}:
        gia = declarations.alias_target(conn, "filter", normalize_header_value(grafia))
        if gia is not None and gia != name:
            raise SpellingTakenError(f"{grafia} e' una grafia di {gia}")
    if mono and mono != name and filter_id_by_name(conn, mono) is not None:
        raise SpellingTakenError(f"{name} e' il tuo {mono}")
    filter_id = create_filter(conn, name, UNKNOWN, now)
    scheda = {k: v for k, v in (("brand", brand), ("model", model)) if v}
    gear.declare_filter(conn, filter_id, scheda, bands=bands, now=now)
    if mono and mono != name:
        declarations.learn(conn, "filter", mono, name, now)
    return filter_id
