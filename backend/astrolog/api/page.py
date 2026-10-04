"""The page and its files are served without the key, or nobody could open the app; what is open
is decided in `app.py`. The built page ships inside the package: after an install no `frontend/`."""

from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
PAGE_PATH = "/"
ASSETS_PATH = "/assets"  # the files the build emits next to the page, with their hashed names
TOKEN_META = '<meta name="astrolog-token" content="{chiave}">'  # noqa: S105 - template, not a key
API_PATH = "/api/"


def is_page(path: str) -> bool:
    """A rule, not a list: the addresses belong to the frontend router, and a copy here would
    answer 404 to the next page. Not the API and not a file, so no extra file becomes readable."""
    # `/api` without the slash too, or it would get the app page with a 200.
    if path == API_PATH.rstrip("/") or path.startswith(API_PATH):
        return False
    return "." not in path.rpartition("/")[2]


def with_key(html: str, token: str | None) -> str:
    """Injected per request, never written into the built file: the key is born with each start,
    and a file on disk would be a secret in a distributed package."""
    if not token:
        return html
    meta = TOKEN_META.format(chiave=escape(token, quote=True))
    return html.replace("<head>", "<head>" + meta, 1) if "<head>" in html else meta + html


def mount(app: FastAPI) -> None:
    """Assets are mounted only if the folder exists: a missing one would crash the start."""

    @app.get(PAGE_PATH, include_in_schema=False, response_class=HTMLResponse)
    def page() -> HTMLResponse:
        """Outside the OpenAPI: the frontend types are generated from it, and an HTML page there
        would be a type describing nothing."""
        return _servita(app)

    assets = app.state.web_dir / ASSETS_PATH.lstrip("/")
    if assets.is_dir():
        app.mount(ASSETS_PATH, StaticFiles(directory=assets), name="assets")


def mount_fallback(app: FastAPI) -> None:
    """Registered last, since FastAPI matches in order: earlier it would answer HTML to the API.
    It makes reload, bookmarks and cold-opened addresses work."""

    @app.get("/{percorso:path}", include_in_schema=False, response_class=HTMLResponse)
    def pagina_del_router(percorso: str) -> HTMLResponse:
        if not is_page("/" + percorso):
            raise HTTPException(status_code=404, detail={"code": "not_found"})
        return _servita(app)


def _servita(app: FastAPI) -> HTMLResponse:
    """One home for both routes, so they cannot disagree on the key or on the unbuilt page."""
    index = app.state.web_dir / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail={"code": "page_not_built"})
    return HTMLResponse(
        with_key(index.read_text(encoding="utf-8"), app.state.token),
        # The page carries the key: kept out of the browser's disk cache.
        headers={"Cache-Control": "no-store"},
    )
