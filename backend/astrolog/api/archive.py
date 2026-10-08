"""Filtering and order happen in SQL (`spine/archive.page`): a search over downloaded rows finds
only those. The user's sort too, for the reason in `api/nights`."""

import sqlite3
from datetime import date
from typing import Literal, cast

from fastapi import APIRouter, Depends, Query

from ..spine import archive, filters_used, objects, productions
from ..spine.counts import Scope, Subject
from .deps import get_db
from .models_archive import (
    ArchiveChoices,
    ArchiveFound,
    ArchiveList,
    ArchiveObject,
    ArchivePanel,
    ArchiveProduction,
)

router = APIRouter(prefix="/api/v1", tags=["archive"])

# A `Literal` so FastAPI rejects an unknown order before the spine, and the OpenAPI carries it.
Sort = Literal["name", "hours", "frames"]


@router.get("/archive", response_model=ArchiveList)
def archive_page(  # noqa: PLR0913
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, max_length=200),
    key: str | None = Query(None, max_length=200),
    catalog: str | None = Query(None, max_length=40),
    constellation: str | None = Query(None, max_length=8),
    filter_name: str | None = Query(None, alias="filter", max_length=120),
    mosaic: bool = False,
    since: date | None = None,
    until: date | None = None,
    site: int | None = None,
    optics: int | None = None,
    camera: int | None = None,
    sort: Sort = "name",
    conn: sqlite3.Connection = Depends(get_db),
) -> ArchiveList:
    """The archive rows -- confirmed objects and mosaics -- with each one's filters, in the order
    `sort` chooses, narrowed by the search parameters.

    `since`/`until` (night dates, both included), `site`, `optics` and `camera` narrow the
    **frames**: a row passes with one of its frames in them, and its hours, filters, productions
    and panels are those frames' only -- narrowed to 2025, a row tells 2025.

    `key` narrows to the one row with that key (`items[].key`): the search opens an object so,
    where `q` would also find `M 10` and `M 101` for `M 1`.

    The factory cap is high (100) because this list is an **inventory**, not a feed to scroll:
    whoever has a hundred thousand frames still has a handful of objects, and asking for twenty at
    a time would be five rounds to see what fits in one."""
    scope = Scope(
        since=since.isoformat() if since else None,
        until=until.isoformat() if until else None,
        site=site,
        optics=optics,
        camera=camera,
    )
    criteria = {
        "q": q,
        "key": key,
        "catalog": catalog,
        "constellation": constellation,
        "filter_name": filter_name,
        "mosaic": mosaic,
        "scope": scope,
    }
    rows, count = archive.page(
        conn, limit=limit, offset=offset, sort=cast(archive.Order, sort), **criteria
    )
    # One query per kind of row for the whole page; an object row carries only its frames outside
    # mosaics, like its hours.
    object_ids = [r["id"] for r in rows if r["mosaic_key"] is None]
    filters_by_key = filters_used.of(conn, Subject.OBJECT, object_ids, alone=True, scope=scope)
    mosaic_keys = [r["mosaic_key"] for r in rows if r["mosaic_key"]]
    filters_by_key |= filters_used.of(conn, Subject.MOSAIC, mosaic_keys, scope=scope)
    made_by_key = productions.of(conn, Subject.OBJECT, object_ids, alone=True, scope=scope)
    made_by_key |= productions.of(conn, Subject.MOSAIC, mosaic_keys, scope=scope)
    panels_by_key = archive.panels(conn, mosaic_keys, scope)
    return ArchiveList(
        items=[
            ArchiveObject(
                key=r["key"],
                name=objects.display_name(r),
                slug=r["catalog_slug"],
                frames=r["frames"],
                integration_s=r["integration_s"],
                untimed=r["untimed"],
                constellation=r["constellation"],
                type_code=r["type_code"],
                filters=filters_by_key.get(r["mosaic_key"] or r["id"], []),
                productions=[
                    ArchiveProduction(**p) for p in made_by_key.get(r["mosaic_key"] or r["id"], [])
                ],
                panels=r["panels"],
                panel_list=[ArchivePanel(**p) for p in panels_by_key.get(r["mosaic_key"], [])],
            )
            for r in rows
        ],
        total=count,
        found=ArchiveFound(**archive.found(conn, **criteria)),
        limit=limit,
        offset=offset,
        choices=ArchiveChoices(**archive.choices(conn)),
    )
