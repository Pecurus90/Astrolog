"""La forma di una risposta a pagine, scritta una volta: le righe della pagina, quante sono in
tutto, e dove comincia e quanto e' lunga la pagina chiesta.

Vincolo non ovvio: `items` sta qui e non nei modelli che ne ereditano, perche' pydantic mette i
campi ereditati prima dei propri -- e l'ordine e' quello dell'OpenAPI da cui il frontend genera i
suoi tipi.
"""

from pydantic import BaseModel


class Page[Row](BaseModel):
    items: list[Row]
    total: int
    limit: int
    offset: int


def page_of(rows, limit, offset):
    """La pagina chiesta di un elenco gia' tutto in memoria, con i campi di `Page`."""
    return {
        "items": rows[offset : offset + limit],
        "total": len(rows),
        "limit": limit,
        "offset": offset,
    }
