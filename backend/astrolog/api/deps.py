"""La connessione per richiesta: si apre, si usa, si chiude. Una rotta che tocca SQLite e'
`def`, non `async def`, e riceve la connessione da qui.

Vincolo non ovvio: `check_same_thread=False` perche' FastAPI esegue la **dipendenza** e il
**corpo della rotta** su due thread diversi del threadpool. La connessione e' di una richiesta
sola e nessuno la condivide, quindi il cambio di thread e' sicuro; col valore di fabbrica due
chiamate partite insieme prendono un 500 (`sqlite3.ProgrammingError`) mentre le stesse due in
fila passano -- il difetto si vede solo sotto concorrenza, cioe' solo dal browser.
"""

from fastapi import Request

from ..db.connect import connect


def get_db(request: Request):
    conn = connect(request.app.state.db_path, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()
