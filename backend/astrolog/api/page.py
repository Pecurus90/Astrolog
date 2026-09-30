"""La pagina dell'app: chi la serve, e come le consegna la chiave di avvio.

"L'app si apre e basta" (Marco, 13/9/2026): la pagina e i file che carica si servono **senza
chiave** -- altrimenti nessuno potrebbe aprirla -- mentre l'API continua a pretenderla. Cosa sia
aperto lo decide `app.py`, accanto alla guardia: e' l'unico posto dove i due elenchi si vedono
insieme, e qui stanno solo i percorsi, perche' chi serve e chi apre non possano divergere.

La pagina costruita vive **dentro il pacchetto** (`astrolog/web/`): dopo un'installazione
`frontend/` non esiste piu', e "il frontend si serve da se'" resterebbe vero solo dal sorgente.
"""

from html import escape
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
PAGE_PATH = "/"
ASSETS_PATH = "/assets"  # i file che il build produce accanto alla pagina, coi loro nomi
TOKEN_META = '<meta name="astrolog-token" content="{chiave}">'  # noqa: S105 - guscio, non chiave
API_PATH = "/api/"  # sotto cui vive tutta l'API: il resto degli indirizzi e' roba della pagina


def is_page(path):
    """E' un **indirizzo di pagina**, cioe' qualcosa che il router del frontend sa mostrare?

    Non e' un elenco, ed e' voluto: gli indirizzi li conosce il router, che vive nel frontend.
    Tenerne una copia qui vorrebbe dire che una pagina nuova risponde 404 finche' qualcuno non si
    ricorda di aggiungerla **anche** di qua -- lo stesso fatto in due case, e il 404 lo vedrebbe
    l'utente invece di chi ha dimenticato.

    La regola e' una sola: **non e' dell'API, e non e' un file**. Un file ha un'estensione
    (`/assets-altro/x.js`), e gli unici file aperti restano quelli che la pagina carica: cosi'
    servire la pagina su piu' indirizzi non allarga di un byte cio' che si legge senza chiave."""
    # Anche `/api` **senza** la barra: con la sola `startswith` quell'indirizzo riceveva la pagina
    # dell'app con un 200. Non e' un dato che esce, e' una risposta che mente su cosa c'e' li' --
    # e una stranezza si toglie con un confronto, non si spiega a chi la trova.
    if path == API_PATH.rstrip("/") or path.startswith(API_PATH):
        return False
    # `rpartition` invece di un indice: l'ultimo segmento si prende senza scrivere `[-1]`, che su
    # un percorso -- che comincia sempre con `/` -- vale quanto `[1]`. Era una differenza che non
    # esiste, quindi nessuna prova avrebbe potuto difenderla: l'ha trovata la mutazione del
    # cancello, sopravvivendo al sabotaggio.
    return "." not in path.rpartition("/")[2]


def with_key(html, token):
    """La pagina con la chiave di avvio dentro, o com'e' se chiave non ce n'e' (il NAS).

    Si inietta **a ogni richiesta** e non una volta all'avvio: la chiave nasce con l'avvio, il
    file costruito e' sempre lo stesso, e scriverla dentro vorrebbe dire un segreto su disco in
    un pacchetto che si distribuisce. La chiave si **sfugge** prima di entrare in un attributo:
    oggi ne esce una che non ha caratteri da sfuggire, ma dipendere di nascosto da come un'altra
    funzione genera i suoi caratteri e' una sicurezza che nessuno vede."""
    if not token:
        return html
    meta = TOKEN_META.format(chiave=escape(token, quote=True))
    return html.replace("<head>", "<head>" + meta, 1) if "<head>" in html else meta + html


def mount(app):
    """Aggancia la pagina e i suoi file all'app. I file si montano solo se ci sono: una cartella
    che non esiste farebbe esplodere l'avvio, e senza build non c'e' niente da servire."""

    @app.get(PAGE_PATH, include_in_schema=False, response_class=HTMLResponse)
    def page():
        """La pagina, con la chiave gia' dentro. Sta **fuori dall'OpenAPI**: da quello schema si
        generano i tipi del frontend, e un file HTML in mezzo ai modelli sarebbe un tipo che non
        descrive niente. Senza la pagina costruita l'app parte lo stesso e lo dice."""
        return _servita(app)

    assets = app.state.web_dir / ASSETS_PATH.lstrip("/")
    if assets.is_dir():
        app.mount(ASSETS_PATH, StaticFiles(directory=assets), name="assets")


def mount_fallback(app):
    """La pagina anche sugli **altri indirizzi del router**, e si aggancia per **ultima**.

    Va dopo le rotte dell'API perche' FastAPI sceglie in ordine di registrazione: messa prima,
    questa risponderebbe HTML anche a `/api/health` -- in silenzio, con le prove dell'API rosse
    per la ragione sbagliata. Serve a far funzionare il tasto ricarica, un segnalibro e un
    indirizzo aperto a freddo: prima di questa, `/da-confermare` rispondeva 401 in JSON."""

    @app.get("/{percorso:path}", include_in_schema=False, response_class=HTMLResponse)
    def pagina_del_router(percorso: str):
        if not is_page("/" + percorso):
            raise HTTPException(status_code=404, detail={"code": "not_found"})
        return _servita(app)


def _servita(app):
    """La pagina da mandare, una volta sola: la servono due rotte, e scriverla due volte vorrebbe
    dire che un giorno solo una delle due porta la chiave, o solo una dice che non e' costruita."""
    index = app.state.web_dir / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail={"code": "page_not_built"})
    return HTMLResponse(
        with_key(index.read_text(encoding="utf-8"), app.state.token),
        # La pagina porta la chiave, quindi non deve restare nella cache su disco del browser:
        # sarebbe il segreto scritto in un file, che e' cio' che l'iniezione evita.
        headers={"Cache-Control": "no-store"},
    )
