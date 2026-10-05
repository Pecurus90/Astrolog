"""Filtering and order happen in SQL (`spine/archive.page`): a search over downloaded rows finds
only those; the backend orders even the user's sort, or two views would agree only by chance."""

import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, Query

from ..spine import archive, filters_used, objects
from .deps import get_db
from .models_archive import ArchiveChoices, ArchiveFound, ArchiveList, ArchiveObject, ArchivePanel

router = APIRouter(prefix="/api/v1", tags=["archivio"])

# A `Literal` so FastAPI rejects an unknown order before the spine, and the OpenAPI carries it.
Sort = Literal["name", "hours", "frames"]


@router.get("/archive", response_model=ArchiveList)
def archive_page(  # noqa: PLR0913
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, max_length=200),
    catalog: str | None = Query(None, max_length=40),
    constellation: str | None = Query(None, max_length=8),
    filter_name: str | None = Query(None, alias="filter", max_length=120),
    mosaic: bool = False,
    sort: Sort = "name",
    conn: sqlite3.Connection = Depends(get_db),
) -> ArchiveList:
    """The archive rows -- confirmed objects and mosaics -- with each one's filters, in the order
    `sort` chooses, narrowed by the search parameters.

    The factory cap is high (100) because this list is an **inventory**, not a feed to scroll:
    whoever has a hundred thousand frames still has a handful of objects, and asking for twenty at
    a time would be five rounds to see what fits in one."""
    criteri = {
        "q": q,
        "catalog": catalog,
        "constellation": constellation,
        "filter_name": filter_name,
        "mosaic": mosaic,
    }
    righe, quanti = archive.page(conn, limit=limit, offset=offset, sort=sort, **criteri)
    # One query per kind of row for the whole page; an object row carries only its frames outside
    # mosaics, like its hours.
    oggetti = [r["id"] for r in righe if r["mosaic_key"] is None]
    filtri = filters_used.of(conn, "object", oggetti, alone=True)
    mosaici = [r["mosaic_key"] for r in righe if r["mosaic_key"]]
    filtri |= filters_used.of(conn, "mosaic", mosaici)
    pannelli = archive.panels(conn, mosaici)
    return ArchiveList(
        items=[
            ArchiveObject(
                # a mosaic is named by its answer's key, which no object carries
                key=r["mosaic_key"] or objects.stable_key(r),
                name=objects.display_name(r),
                slug=r["catalog_slug"],
                frames=r["frames"],
                integration_s=r["integration_s"],
                untimed=r["untimed"],
                constellation=r["constellation"],
                type_code=r["type_code"],
                filters=filtri.get(r["mosaic_key"] or r["id"], []),
                panels=r["panels"],
                panel_list=[ArchivePanel(**p) for p in pannelli.get(r["mosaic_key"], [])],
            )
            for r in righe
        ],
        total=quanti,
        found=ArchiveFound(**archive.found(conn, **criteri)),
        limit=limit,
        offset=offset,
        choices=ArchiveChoices(**archive.choices(conn)),
    )
