"""La fabbrica dell'app: il DB pronto, lo stato condiviso (worker, lock per cartella,
radice confinata), la guardia sull'host e il token del desktop, i router, la salute, la
previsione che si rinnova da sola, e sul NAS la scansione a cadenza.

Vincolo non ovvio: niente parte da solo se chi lancia l'app non lo chiede -- la scansione con
`scan_every_s` (`ASTROLOG_SCAN_EVERY_MIN`), la previsione con `weather_every_s` (sempre, da
`__main__`; mai nelle prove, che non escono di casa). Senza login non vuol dire senza
guardia: l'app risponde solo agli host ammessi, e sul desktop pretende il token per avvio.
"""

import logging
import secrets
import threading
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .. import __version__
from ..catalog import load as catalog_load
from ..db.connect import connect, ensure_database
from ..db.paths import data_root as env_data_root
from ..spine import gear_usage, object_candidates
from ..spine.group_store import home_site
from ..weather import climate, forecast, history, rounds
from ..worker.worker import Worker
from . import (
    archive,
    folders,
    gear,
    gear_write,
    nights,
    page,
    pipeline,
    review,
    scan,
    settings,
    sites,
    tonight,
    vocab,
    weather,
    weather_key,
)
from .deps import get_db
from .models import Health

log = logging.getLogger(__name__)

LOCAL_HOSTS = ("localhost", "127.0.0.1")
TOKEN_HEADER = "X-AstroLog-Token"  # noqa: S105 - e' il nome dell'header, non il segreto
OPEN_PATHS = ("/docs", "/redoc", "/openapi.json")  # pagine di consultazione, non dati


def _is_open(path):
    """Cosa si serve senza chiave: la documentazione, **le pagine** e i file che la pagina carica.

    Le pagine non si elencano qui: `page.is_page` risponde con una regola -- non e' dell'API e non
    e' un file -- perche' gli indirizzi li conosce il router, nel frontend, e un elenco doppio
    farebbe rispondere 404 alla prossima pagina finche' qualcuno non si ricorda di questa riga.
    Nessun percorso dell'API puo' entrarci: `is_page` esclude per primo tutto cio' che sta sotto
    `/api/`. I file della pagina sono invece un prefisso -- il build decide i loro nomi, con
    l'impronta dentro -- ed e' l'unico prefisso legittimo oltre alla documentazione: sono
    artefatti pubblici, non dati."""
    # La barra in fondo e' voluta: senza, `/assets-altro` sarebbe aperto quanto `/assets/x.js`
    # -- la stessa famiglia del difetto che questa funzione esiste per evitare.
    return path.startswith((*OPEN_PATHS, page.ASSETS_PATH + "/")) or page.is_page(path)


def _readable_id(route):
    """Il nome dell'operazione nell'OpenAPI: quello della funzione, e basta.

    Da quello schema si **generano** i tipi e le funzioni del client, e il nome di fabbrica di
    FastAPI ci arriva come `review_api_v1_review_get`. Si sceglie qui, una volta, prima che
    qualcuno ci scriva sopra: rinominarlo dopo rompe chi lo usa."""
    return route.name


def _scheduler(state, every_s, stop_event):
    """Ogni `every_s` secondi scansiona le cartelle attive, una per volta."""
    while not stop_event.wait(every_s):
        conn = connect(state.db_path)
        try:
            ids = [
                r[0]
                for r in conn.execute("SELECT id FROM folders WHERE retired_at IS NULL ORDER BY id")
            ]
            for folder_id in ids:
                if state.worker.is_running():
                    break
                try:
                    scan.start_scan(state, conn, folder_id)
                except Exception as err:  # noqa: BLE001 - un giro saltato si logga, non ferma la cadenza
                    log.warning(
                        "cadenza: scansione non avviata",
                        extra={"folder_id": folder_id, "error": str(err)},
                    )
                state.worker.join()
        finally:
            conn.close()


# Ogni quanto passa il giro del meteo: guarda se tocca alla previsione e fa un passo dello storico.
# Cosi' un sito dichiarato adesso ha la sua previsione subito, non al prossimo giro di tre ore.
_WEATHER_TICK_S = 60


def _weather_scheduler(db_path, every_s, stop_event):
    """A ogni giro la climatologia del sito di casa, la previsione quando `forecast.Cadence` dice
    che tocca, e un passo dello storico delle notti riprese. Ognuno per conto suo: un giro che cade
    si logga, e resta cio' che c'era."""
    cadenza = forecast.Cadence(every_s)
    while True:
        conn = connect(db_path)
        try:
            riga = home_site(conn)
            sito = None if riga is None else dict(riga)
            try:
                # prima della previsione, che la legge: una chiamata l'anno
                climate.step(conn, sito)
            except Exception:
                log.exception("meteo: il giro della climatologia e' caduto")
            if cadenza.due(sito, time.monotonic()):
                cadenza.done(sito, rounds.refresh(conn, sito), time.monotonic())
        except Exception:
            log.exception("meteo: il giro della previsione e' caduto")
        try:
            # lo storico delle notti riprese: una chiamata per giro, anche senza sito di casa, e
            # per conto suo, cosi' una previsione che cade non lo ferma
            history.step(conn)
        except Exception:
            log.exception("meteo: il giro dello storico e' caduto")
        finally:
            conn.close()
        if stop_event.wait(_WEATHER_TICK_S):
            return


def _load_catalog(db_path):
    """Il catalogo nelle sue tabelle, se manca o se il file impacchettato e' cambiato.

    Un catalogo che non si carica **non impedisce all'app di partire**: senza, l'archivio
    cataloga, cerca e conta le ore lo stesso -- non sa dire cosa hai fotografato, e
    `/api/health` lo dichiara con `catalog_entries` a zero."""
    conn = connect(db_path)
    try:
        if catalog_load.load_catalog(conn):
            # i nomi degli oggetti scritti nell'uso dell'attrezzatura, e i candidati dei dubbi,
            # vengono dal catalogo
            gear_usage.write(conn)
            object_candidates.write(conn)
    except Exception:
        log.exception("catalogo: non si e' potuto caricare, l'app parte lo stesso")
    finally:
        conn.close()


def _lifespan(
    scan_every_s: float | None, weather_every_s: float | None
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Il ciclo di vita dell'app: i giri in sottofondo e la connessione che resta aperta."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Never the last close: that one locks the file to delete the WAL, and an antivirus on
        # Windows can stretch it past the busy timeout of whoever opens meanwhile.
        keepalive = connect(app.state.db_path, check_same_thread=False)
        stop_event = threading.Event()
        if scan_every_s:
            threading.Thread(
                target=_scheduler,
                args=(app.state, scan_every_s, stop_event),
                name="astrolog-scheduler",
                daemon=True,
            ).start()
        if weather_every_s:
            threading.Thread(
                target=_weather_scheduler,
                args=(app.state.db_path, weather_every_s, stop_event),
                name="astrolog-weather",
                daemon=True,
            ).start()
        try:
            yield
        finally:
            stop_event.set()
            keepalive.close()

    return lifespan


def create_app(  # noqa: PLR0913
    db_path=None,
    *,
    data_root=None,
    scan_every_s=None,
    weather_every_s=None,
    hosts=(),
    token=None,
    web_dir=None,
):
    """L'app FastAPI legata a `db_path` (creato da schema.sql se non c'e').

    `hosts`: gli host ammessi oltre a localhost (sul NAS, il suo nome e il suo indirizzo).
    `token`: se dato, ogni richiesta all'API deve portarlo in `X-AstroLog-Token` (desktop).
    `web_dir`: dove sta la pagina costruita; senza, quella impacchettata (`WEB_DIR`)."""
    if db_path is None:
        from ..db.paths import db_path as default_db_path

        db_path = default_db_path()
    ensure_database(db_path)
    _load_catalog(db_path)

    app = FastAPI(
        title="AstroLog API",
        version=__version__,
        lifespan=_lifespan(scan_every_s, weather_every_s),
        generate_unique_id_function=_readable_id,
    )
    app.state.web_dir = Path(web_dir) if web_dir else page.WEB_DIR
    app.state.db_path = str(db_path)
    app.state.data_root = data_root if data_root is not None else env_data_root()
    app.state.worker = Worker()
    app.state.folder_locks = set()
    app.state.folder_locks_mutex = threading.Lock()
    app.state.token = token
    app.state.last_scan = None  # (folder_id, run_id) dell'ultima scansione avviata
    app.state.scan_runs = ()  # le ricevute di tutte le cartelle di quel gesto: il suo esito

    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=[*LOCAL_HOSTS, *(h for h in hosts if h)]
    )

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        expected = request.app.state.token
        if (
            expected
            and not _is_open(request.url.path)
            and not secrets.compare_digest(request.headers.get(TOKEN_HEADER, ""), expected)
        ):
            return JSONResponse(status_code=401, content={"detail": {"code": "token_required"}})
        return await call_next(request)

    page.mount(app)

    @app.get("/api/health", response_model=Health)
    def health(conn=Depends(get_db)):
        """Il servizio e' su, il DB risponde, la radice confinata se c'e'."""
        # Le tabelle NOSTRE: SQLite si tiene le sue (`sqlite_sequence`, che nasce con
        # AUTOINCREMENT), e a schermo sarebbero un numero che non torna con `schema.sql`.
        n = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        # Il catalogo puo' mancare senza che l'app smetta di funzionare: qui si vede, invece
        # di scoprirlo quando `identify` non riconosce niente.
        entries = conn.execute("SELECT COUNT(*) FROM catalog_entries").fetchone()[0]
        return Health(
            status="ok",
            api_version=__version__,
            schema_tables=n,
            data_root=app.state.data_root,
            catalog_entries=entries,
            catalog_version=catalog_load.loaded_version(conn),
        )

    app.include_router(archive.router)
    app.include_router(gear.router)
    app.include_router(gear_write.router)
    app.include_router(nights.router)
    app.include_router(folders.router)
    app.include_router(scan.router)
    app.include_router(pipeline.router)
    app.include_router(review.router)
    app.include_router(sites.router)
    app.include_router(settings.router)
    app.include_router(tonight.router)
    app.include_router(vocab.router)
    app.include_router(weather.router)
    app.include_router(weather_key.router)
    # Per **ultima**: cattura gli indirizzi che restano, e messa prima mangerebbe l'API.
    page.mount_fallback(app)
    return app
