"""Con che filtri hai ripreso qualcosa: per notte, per oggetto, per un lotto di soggetti.

Sta in una casa sola perche' la stessa domanda la fanno le Notti e l'Archivio sulle **stesse
pose**: due copie sarebbero due modi di contare lo stesso tempo, e il giorno che una delle due
cambia, la notte e l'oggetto direbbero numeri diversi dello stesso scatto. Il legame e l'ordine
li da' `counts`, che e' la casa del "quanto e' servito".
"""

from ..db import idlist
from . import counts


def of(conn, soggetto, ids, *, alone=False):
    """`{id del soggetto: [{name, passband, frames, integration_s}]}`, dal filtro a cui e' andato
    piu' tempo. `alone` guarda solo le pose fuori dai mosaici confermati, come la riga di un
    oggetto nell'Archivio (`counts.ALONE`).

    La **banda** viaggia col nome perche' e' lei a dire di che colore si disegna la pastiglia: il
    nome lo sceglie l'utente e non dice niente a una macchina.

    Il soggetto e' una **chiave** di un elenco chiuso (`counts.column_of`), mai un pezzo di SQL che
    arriva da fuori. Le copie riscritte non contano, come ovunque si sommino delle ore."""
    dove = counts.column_of(soggetto)  # da un elenco chiuso: una chiave che non c'e' e' un KeyError
    solo = f" AND {counts.ALONE}" if alone else ""
    sql = f"""
    SELECT f.{dove} AS soggetto, x.name, x.passband, {counts.AGGREGATE}
    FROM frames f JOIN filters x ON x.id = f.filter_id
    WHERE f.{dove} IN {{dentro}} AND f.copy_of IS NULL{solo}
    GROUP BY f.{dove}, x.id
    {counts.ORDER_BY_TIME}, x.id
    """  # noqa: S608 - `dove` viene dall'elenco chiuso, `dentro` e' un segnaposto
    return idlist.grouped(
        conn,
        sql,
        ids,
        "soggetto",
        lambda r: {
            "name": r["name"],
            "passband": r["passband"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
        },
    )
