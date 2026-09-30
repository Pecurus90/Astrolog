"""L'app INSTALLATA parte davvero? Il difetto che in sviluppo non si vede mai.

Chi sviluppa gira dal sorgente, quindi un sotto-pacchetto o un file di dati che nella ruota
non entra non lo scopre nessuno -- fino al giorno del pacchetto. E' successo: `packages =
["astrolog"]` lasciava fuori `api`, `spine`, `vocab`, `fits`, `db` e `worker`, piu'
`filters.json` e `schema.sql`; la ruota conteneva sei moduli e nessuna rotta.

Si lancia **dentro un ambiente dove l'app e' installata e fuori dalla cartella del sorgente**,
altrimenti importerebbe quello e direbbe di si' sempre. In CI ci pensa il lavoro `pacchetto`.

    python tools/prova_pacchetto.py
"""

import sys
import tempfile
from pathlib import Path


def main():
    from astrolog.api.app import create_app
    from astrolog.api.page import WEB_DIR
    from astrolog.db.connect import create_database
    from astrolog.vocab import filters

    sorgente = Path(__file__).resolve().parents[1] / "backend"
    installato = Path(filters.__file__).resolve()
    if sorgente in installato.parents:
        print(f"NO: sto importando il sorgente ({installato}), non il pacchetto installato")
        return 1

    if not filters.FILTER_MAP:
        print("NO: il vocabolario dei filtri e' vuoto: `filters.json` non e' nella ruota")
        return 1

    db = Path(tempfile.mkdtemp()) / "prova.db"
    create_database(db)  # legge `schema.sql`: se non e' nella ruota, esplode qui
    app = create_app(db)
    # Le rotte vere non si contano da `app.routes`: li' ogni router incluso compare come **un
    # oggetto solo e senza percorso**, quindi da quell'elenco ne risulta una -- `/api/health` --
    # e la prova direbbe di si' anche a una ruota che ha perso tutti i domini. E' il difetto per
    # cui questo file e' nato, e fino al 14/9/2026 non lo prendeva. Si contano dall'OpenAPI, che
    # e' la stessa fonte da cui si generano i tipi del frontend.
    rotte = [p for p in app.openapi()["paths"] if p.startswith("/api/v1/")]
    if not rotte:
        print("NO: l'app installata non espone nessuna rotta di dominio, solo la salute")
        return 1

    # Dove stia la pagina lo dice **il codice che la serve**, non una copia di quel percorso: se
    # un giorno si sposta, questa prova si sposta con lui invece di guardare per sempre nel vuoto.
    # Il pacchetto la include gia' (`package-data`), ma la include solo se **esiste quando la
    # ruota si costruisce**: senza un build del frontend prima, la ruota esce muta e chi installa
    # trova un 404 sulla home. E' il difetto che in sviluppo non si vede mai, perche' li' la
    # pagina costruita sta sul disco accanto al sorgente.
    if not (WEB_DIR / "index.html").is_file():
        print(f"NO: la ruota non porta la pagina ({WEB_DIR}): chi installa trova un 404 su /")
        return 1

    print(
        f"OK: {len(filters.FILTER_MAP)} filtri, il database si crea, {len(rotte)} rotte in piedi,"
        " e la pagina e' dentro la ruota"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
