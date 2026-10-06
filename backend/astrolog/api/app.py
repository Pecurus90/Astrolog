"""Nothing runs in the background unless the launcher asks (`scan_every_s`, `weather_every_s`).
No login still means a host guard and, on the desktop, a token."""

import logging
import secrets
import sqlite3
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.datastructures import State

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
)
from .deps import get_db
from .models import Health

log = logging.getLogger(__name__)

LOCAL_HOSTS = ("localhost", "127.0.0.1")
TOKEN_HEADER = "X-AstroLog-Token"  # noqa: S105 - the header's name, not the secret
OPEN_PATHS = ("/docs", "/redoc", "/openapi.json")


def _is_open(path: str) -> bool:
    """Docs, pages and the page's files are public artefacts, not data."""
    # The trailing slash keeps `/assets-other/x.js` closed while `/assets/x.js` is open.
    return path.startswith((*OPEN_PATHS, page.ASSETS_PATH + "/")) or page.is_page(path)


def _readable_id(route: APIRoute) -> str:
    """The client is generated from these ids: FastAPI's default (`review_api_v1_review_get`)
    would leak into it, and renaming later breaks its users."""
    return route.name


def _scheduler(state: State, every_s: float, stop_event: threading.Event) -> None:
    while not stop_event.wait(every_s):
        conn = connect(state.db_path)
        try:
            for folder_id in scan.active_folder_ids(conn):
                if state.worker.is_running():
                    break
                # A folder that cannot start is logged and skipped; the round goes on.
                try:
                    scan.start_scan(state, conn, folder_id)
                except Exception as err:  # noqa: BLE001
                    log.warning(
                        "cadenza: scansione non avviata",
                        extra={"folder_id": folder_id, "error": str(err)},
                    )
                state.worker.join()
        finally:
            conn.close()


# A site declared now gets its forecast at once, not at the next three-hour round.
_WEATHER_TICK_S = 60


def _weather_scheduler(db_path: str, every_s: float, stop_event: threading.Event) -> None:
    """Climate, forecast when `forecast.Cadence` says so, and one step of history: each on its own,
    so a fallen one is logged and what was there stays."""
    cadence = forecast.Cadence(every_s)
    while True:
        conn = connect(db_path)
        try:
            row = home_site(conn)
            site = None if row is None else dict(row)
            try:
                climate.step(conn, site)  # before the forecast, which reads it
            except Exception:
                log.exception("meteo: il giro della climatologia e' caduto")
            if cadence.due(site, time.monotonic()):
                cadence.done(site, rounds.refresh(conn, site), time.monotonic())
        except Exception:
            log.exception("meteo: il giro della previsione e' caduto")
        try:
            # also without a home site, and apart, so a fallen forecast does not stop it
            history.step(conn)
        except Exception:
            log.exception("meteo: il giro dello storico e' caduto")
        finally:
            conn.close()
        if stop_event.wait(_WEATHER_TICK_S):
            return


def _load_catalog(db_path: str | Path) -> None:
    """A catalog that fails to load does not stop the app: the archive still works without names
    (what is left in place is the contract of GET /api/health)."""
    conn = connect(db_path)
    try:
        if catalog_load.load_catalog(conn):
            # object names in gear usage and the candidates of the questions come from the catalog
            gear_usage.write(conn)
            object_candidates.write(conn)
    except Exception:
        log.exception("catalogo: non si e' potuto caricare, l'app parte lo stesso")
    finally:
        conn.close()


def _lifespan(
    scan_every_s: float | None, weather_every_s: float | None
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
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
    db_path: str | Path | None = None,
    *,
    data_root: str | None = None,
    scan_every_s: float | None = None,
    weather_every_s: float | None = None,
    hosts: Iterable[str] = (),
    token: str | None = None,
    web_dir: str | Path | None = None,
) -> FastAPI:
    """`hosts` are allowed besides localhost (the NAS's name and address); with `token` every API
    request must carry it in `X-AstroLog-Token` (desktop)."""
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
    app.state.last_scan = None  # (folder_id, run_id) of the last scan started
    app.state.scan_runs = ()  # the receipts of every folder of that gesture: its outcome

    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=[*LOCAL_HOSTS, *(h for h in hosts if h)]
    )

    @app.middleware("http")
    async def require_token(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
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
    def health(conn: sqlite3.Connection = Depends(get_db)) -> Health:
        """The service is up and the database answers. Returns the API version, how many of the
        app's own tables exist (SQLite's internal ones, such as `sqlite_sequence`, are left out so
        the number matches `schema.sql`), the confined data root (`null` when there is none), and
        the catalog's entries and version. A missing catalog shows as zero entries; a newer
        catalog that fails to load leaves the previous entries and `catalog_version` in place,
        and the failure is only logged."""
        n = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
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
    page.mount_fallback(app)  # last: `page.mount_fallback` says why
    return app
