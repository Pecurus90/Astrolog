"""A production's preview photo: put, read, removed (step 33.2). The photo is checked and shrunk in
`spine/previews.py`; here only which slot, and the HTTP around it."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool

from ..db.connect import connect
from ..db.transaction import transaction
from ..spine import archive, previews
from ..spine.counts import Scope
from .archive import PREVIEW_PATH, url_of
from .deps import get_db
from .models_archive import ArchivePreview
from .objects import _PRODUCTION, _pieces

router = APIRouter(prefix="/api/v1", tags=["archive"])
PATH = PREVIEW_PATH
_KEY = Query(..., max_length=200)  # [T] as the Archive's own `key`
_BINARY = {"schema": {"type": "string", "format": "binary"}}
_PUT_BODY = {
    "requestBody": {
        "required": True,
        "content": {t: _BINARY for t in ("image/jpeg", "image/png", "image/webp")},
    }
}


def slot_of(conn: sqlite3.Connection, key: str, production: str | None) -> previews.Slot:
    """The row by its key, the production by its ids as the row gives them; names in the slot. A
    mosaic has one place: no production."""
    rows, _ = archive.page(conn, limit=1, offset=0, key=key)
    if not rows:
        raise HTTPException(status_code=404, detail={"code": "object_not_found"})
    row = rows[0]
    if row["mosaic_key"] is not None:
        if production:
            raise HTTPException(status_code=422, detail={"code": "mosaic_has_one_preview"})
        return previews.Slot("mosaic", row["key"], None, None)
    if not production:
        raise HTTPException(status_code=422, detail={"code": "production_required"})
    optics_id, camera_id = _pieces(production)
    scope = Scope(production=(optics_id, camera_id))
    if not archive.page(conn, limit=1, offset=0, key=key, scope=scope)[0]:
        raise HTTPException(status_code=404, detail={"code": "production_not_found"})
    return previews.Slot("object", row["key"], _name(conn, optics_id), _name(conn, camera_id))


def _name(conn: sqlite3.Connection, instrument_id: int | None) -> str | None:
    if instrument_id is None:
        return None
    return conn.execute("SELECT name FROM instruments WHERE id = ?", (instrument_id,)).fetchone()[0]


# [C RFC 9110 15.3.1: 200 OK]
@router.get(PATH, response_class=Response, responses={200: {"content": {"image/jpeg": {}}}})
def get_preview(
    request: Request,
    key: str = _KEY,
    production: str | None = _PRODUCTION,
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    """The photo of a slot as a JPEG; the page reads it with its token and shows it from memory.
    Its ETag is the photo's hash: 304 when the page already has it.

    404 `object_not_found`, `production_not_found`, or `no_preview` when none was put.
    422 `production_required` on an object, `mosaic_has_one_preview` on a mosaic."""
    digest = previews.digest_in(conn, slot_of(conn, key, production))
    jpeg = None if digest is None else previews.read(request.app.state.db_path, digest)
    if digest is None or jpeg is None:
        raise HTTPException(status_code=404, detail={"code": "no_preview"})
    headers = {
        "ETag": f'"{digest}"',
        "Cache-Control": "private, no-cache",
        "X-Content-Type-Options": "nosniff",
    }
    if request.headers.get("if-none-match") == f'"{digest}"':
        return Response(status_code=304, headers=headers)
    return Response(content=jpeg, media_type="image/jpeg", headers=headers)


@router.put(PATH, response_model=ArchivePreview, openapi_extra=_PUT_BODY)
async def put_preview(
    request: Request, key: str = _KEY, production: str | None = _PRODUCTION
) -> ArchivePreview:
    """Puts or replaces the photo of a slot: the body is the image itself, JPEG, PNG or WebP; its
    bytes decide, not its declared type. It is kept shrunk, upright, without its EXIF.

    413 `too_large` past 40 MB. 422 `not_an_image`, or `too_many_pixels` past 60 megapixels.
    404 and 422 as the reading."""
    raw = bytearray()
    async for chunk in request.stream():
        raw += chunk
        if len(raw) > previews.MAX_BYTES:
            raise HTTPException(status_code=413, detail={"code": "too_large"})
    return await run_in_threadpool(_put, request.app.state.db_path, key, production, bytes(raw))


def _put(db_path: str, key: str, production: str | None, raw: bytes) -> ArchivePreview:
    """Its own connection, off the event loop: Pillow takes a while on a big photo."""
    conn = connect(db_path)
    try:
        with transaction(conn):
            slot = slot_of(conn, key, production)
            try:
                previews.put(conn, db_path, slot, raw)
            except previews.PreviewError as e:
                status = 413 if e.code == "too_large" else 422
                raise HTTPException(status_code=status, detail={"code": e.code}) from e
            return ArchivePreview(url=url_of(key, production), at=previews.updated_at(conn, slot))
    finally:
        conn.close()


# [C RFC 9110 15.3.5: 204 No Content]
@router.delete(PATH, status_code=204, response_class=Response)
def delete_preview(
    request: Request,
    key: str = _KEY,
    production: str | None = _PRODUCTION,
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    """Takes the photo off a slot; the file goes when no slot uses it.

    404 `no_preview` when there was none; the others as the reading."""
    with transaction(conn):
        if not previews.remove(conn, request.app.state.db_path, slot_of(conn, key, production)):
            raise HTTPException(status_code=404, detail={"code": "no_preview"})
    return Response(status_code=204)
