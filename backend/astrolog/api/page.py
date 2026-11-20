"""The page and its files are served without the key, or nobody could open the app; what is open
is decided in `app.py`. The built page ships inside the package: after an install no `frontend/`."""

import mimetypes
import stat
from html import escape
from pathlib import Path

from anyio import to_thread
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.types import Scope

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
PAGE_PATH = "/"
ASSETS_PATH = "/assets"  # the files the build emits next to the page, with their hashed names
# Hash in the name: new content, new name, so kept for good (RFC 9111 max-age, RFC 8246 immutable).
ASSETS_CACHE = "public, max-age=31536000, immutable"
# Copies written by the build (vite.config.ts), best first: brotli is smaller than gzip.
PRECOMPRESSED = (("br", ".br"), ("gzip", ".gz"))
# Fonts already compressed inside (W3C WOFF2 5.2): never gzipped again. Types per RFC 8081;
# registered here since Windows mimetypes can miss them (octet-stream there).
FONT_TYPES = {".woff2": "font/woff2", ".woff": "font/woff"}
for _suffix, _mime in FONT_TYPES.items():
    mimetypes.add_type(_mime, _suffix)
TOKEN_META = '<meta name="astrolog-token" content="{key}">'  # noqa: S105 - template, not a key
API_PATH = "/api/"
# The page carries the key: only the backend's own files load and run, nothing inline (MDN, CSP).
# blob: for the previews, read with the key and shown from memory: an <img> sends no header.
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:;"
    " font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none';"
    " form-action 'self'; frame-ancestors 'none'"
)


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
    meta = TOKEN_META.format(key=escape(token, quote=True))
    return html.replace("<head>", "<head>" + meta, 1) if "<head>" in html else meta + html


def mount(app: FastAPI) -> None:
    """Assets are mounted only if the folder exists: a missing one would crash the start."""

    @app.get(PAGE_PATH, include_in_schema=False, response_class=HTMLResponse)
    def page() -> HTMLResponse:
        """Outside the OpenAPI: the frontend types are generated from it, and an HTML page there
        would be a type describing nothing."""
        return _served(app)

    assets = app.state.web_dir / ASSETS_PATH.lstrip("/")
    if assets.is_dir():
        app.mount(ASSETS_PATH, Assets(directory=assets), name="assets")


def accepted(accept_encoding: str) -> list[str]:
    """Codings the browser takes, q=0 excluded (RFC 9110 12.5.3)."""
    taken = []
    for part in accept_encoding.split(","):
        name, _, params = part.partition(";")
        q = params.strip().lower().removeprefix("q=").strip()
        try:
            refused = bool(q) and float(q) == 0
        except ValueError:
            refused = False
        if name.strip() and not refused:
            taken.append(name.strip().lower())
    return taken


class Assets(StaticFiles):
    """Serves the build's .br or .gz copy as it is: compressed once, not at every request.
    Content-Encoding set, so GZipMiddleware lets it pass."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        # the original goes through StaticFiles first: method, bad path, 404
        plain = await super().get_response(path, scope)
        compressed = (
            await self._compressed(path, scope, plain.headers["content-type"])
            if plain.status_code == 200
            else None
        )
        response = compressed or plain
        response.headers["Cache-Control"] = ASSETS_CACHE
        return response

    async def _compressed(self, path: str, scope: Scope, content_type: str) -> Response | None:
        taken = accepted(Headers(scope=scope).get("accept-encoding", ""))
        for coding, suffix in PRECOMPRESSED:
            if coding not in taken:
                continue
            full, found = await to_thread.run_sync(self.lookup_path, path + suffix)
            if found and stat.S_ISREG(found.st_mode):
                response = self.file_response(full, found, scope)  # 304 on a matching ETag
                # GZipMiddleware skips an encoded response, Vary included
                response.headers["Content-Encoding"] = coding
                response.headers["Vary"] = "Accept-Encoding"
                if response.status_code == 200:
                    response.headers["Content-Type"] = content_type  # the original's, charset too
                return response
        return None


def mount_fallback(app: FastAPI) -> None:
    """Registered last, since FastAPI matches in order: earlier it would answer HTML to the API.
    It makes reload, bookmarks and cold-opened addresses work."""

    @app.get("/{page_path:path}", include_in_schema=False, response_class=HTMLResponse)
    def router_page(page_path: str) -> HTMLResponse:
        if not is_page("/" + page_path):
            raise HTTPException(status_code=404, detail={"code": "not_found"})
        return _served(app)


def _served(app: FastAPI) -> HTMLResponse:
    """One home for both routes, so they cannot disagree on the key or on the unbuilt page."""
    index = app.state.web_dir / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail={"code": "page_not_built"})
    return HTMLResponse(
        with_key(index.read_text(encoding="utf-8"), app.state.token),
        # The page carries the key: kept out of the browser's disk cache.
        headers={"Cache-Control": "no-store", "Content-Security-Policy": CSP},
    )
