"""La riscrittura di una tabella derivata, o della parte che si rifa', tutto o niente.

Chi scrive un derivato a fine giro -- l'uso dell'attrezzatura, i candidati degli oggetti in
dubbio -- lo rifa' intero: seguire le righe una per una vorrebbe dire sbagliarne una. Ma chi legge
a meta' deve vedere la tabella di prima, mai vuota, e una riscrittura che cade deve lasciarla
com'era.

Vincolo non ovvio: un **savepoint**, non un `BEGIN`. La connessione salva ogni istruzione da sola,
e il savepoint apre una transazione se non ce n'e'; ma chi risponde "sono file di calibrazione"
in Da confermare e' gia' dentro quella dell'Applica, e li' il savepoint si annida e la conferma
resta di chi l'ha aperta.
"""


def replace_rows(conn, table, columns, rows, where="1", args=()):  # noqa: PLR0913
    """Svuota `table` -- o la sua parte che risponde a `where` -- e ci scrive `rows`, una tupla per
    riga nell'ordine di `columns`. Tabella, colonne e condizione sono costanti di chi chiama, mai
    valori dell'utente: i valori viaggiano in `args`."""
    elenco = ", ".join(columns)
    segnaposto = ", ".join("?" * len(columns))  # segnaposto-ok: le colonne, non le righe
    conn.execute("SAVEPOINT replace_rows")
    try:
        conn.execute(f"DELETE FROM {table} WHERE {where}", args)  # noqa: S608 - costanti di chi chiama
        conn.executemany(
            f"INSERT INTO {table}({elenco}) VALUES({segnaposto})",  # noqa: S608 - costanti
            rows,
        )
    except Exception:
        conn.execute("ROLLBACK TO replace_rows")
        conn.execute("RELEASE replace_rows")
        raise
    conn.execute("RELEASE replace_rows")
