"""Dire a una query "fra questi id" quando gli id sono decine di migliaia.

SQLite accetta un numero massimo di segnaposto in una query (`SQLITE_LIMIT_VARIABLE_NUMBER`), e
**quel numero dipende da come e' stato compilato**: 32.766 nella build di Python su Windows, 250.000
in quella di Ubuntu (misurato in CI). Una `WHERE id IN (?, ?, ...)` costruita su un id per posa non
"va piu' lenta" oltre il tetto: **non funziona piu'**, con `too many SQL variables`, e l'archivio si
ferma. Col tetto piu' basso e 11.005 pose il margine e' tre volte; un archivio di dieci anni ci
arriva.

Perche' una tabella temporanea e non lotti da trentamila: i lotti **cambiano il senso** di due
delle query che li userebbero. Un `GROUP BY` spezzato in lotti torna il primo di ogni gruppo
*per lotto*, e un `ORDER BY` spezzato ordina dentro il lotto e non sul totale. La tabella
temporanea non ha limiti e lascia la query identica a com'era.

Tre dettagli che sembrano pignoli e non lo sono:

* **La colonna e' un `INTEGER` semplice, non una chiave primaria.** Deve comportarsi come la
  lista di segnaposto che sostituisce: un id ripetuto e' innocuo, e un `None` non aggancia
  niente. Con una chiave primaria il doppio sollevava e il `None` si prendeva un rowid --
  cioe' `detach` avrebbe staccato l'oggetto della posa 1.
* **Si svuota all'INGRESSO, non all'uscita.** Svuotandola all'uscita, un cursore ancora aperto
  perdeva righe **in silenzio**; e un errore a meta' inserimento lasciava righe che il giro
  dopo scambiava per un elenco aperto.
* **La rientranza si guarda su chi la sta usando**, non su cosa c'e' nella tabella: due elenchi
  aperti insieme sulla stessa connessione si calpesterebbero, e la seconda query lavorerebbe
  sugli id della prima -- un guasto che darebbe un risultato plausibile e sbagliato.
"""

from contextlib import contextmanager

TABLE = "id_list"
IN_LIST = f"(SELECT id FROM {TABLE})"  # noqa: S608 - TABLE e una costante di questo file

_in_use = set()


@contextmanager
def holding(conn, ids):
    """Mette gli id in una tabella temporanea e da' il pezzo di SQL per dire "fra questi".

    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(f"UPDATE frames SET object_id = NULL WHERE id IN {listed}")
    """
    if conn in _in_use:
        raise RuntimeError("un elenco e' gia' aperto su questa connessione")
    _in_use.add(conn)
    try:
        conn.execute(  # ddl-ok: una tabella di appoggio per connessione, fuori dallo schema
            f"CREATE TEMP TABLE IF NOT EXISTS {TABLE} (id INTEGER)"
        )
        conn.execute(f"DELETE FROM {TABLE}")  # noqa: S608 - TABLE e una costante di questo file
        conn.executemany(f"INSERT INTO {TABLE}(id) VALUES(?)", [(i,) for i in ids])  # noqa: S608
        yield IN_LIST
    finally:
        _in_use.discard(conn)


def grouped(conn, sql, ids, key, row):
    """Una query sola per molti id, poi le righe **spartite** per una colonna: `{chiave: [riga]}`.

    E' l'idioma di ogni pagina che elenca dei gruppi -- gli oggetti di una notte, i filtri di un
    corredo -- e senza una casa comune ognuna se lo riscriveva. `sql` porta `{dentro}` dove vuole
    l'elenco; con nessun id non si chiede niente, che e' anche l'unico modo di non pagare una
    query per una pagina vuota."""
    if not ids:
        return {}
    fuori = {}
    with holding(conn, ids) as elencate:
        for r in conn.execute(sql.format(dentro=elencate)):
            fuori.setdefault(r[key], []).append(row(r))
    return fuori
