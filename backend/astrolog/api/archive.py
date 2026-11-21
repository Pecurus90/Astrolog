"""Filtering and order happen in SQL (`spine/archive.page`): a search over downloaded rows finds
only those. The user's sort too, for the reason in `api/nights`."""

import sqlite3
from typing import Annotated, Any, Literal, cast
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query

from ..db import derived_fresh
from ..spine import (
    archive,
    archive_criteria,
    archive_rows,
    filters_used,
    objects,
    previews,
    productions,
)
from ..spine.archive import Family, Form
from ..spine.counts import Scope, Subject
from ..spine.solve import solver_where
from .deps import get_db
from .models_archive import (
    ArchiveCriterion,
    ArchiveFound,
    ArchiveList,
    ArchiveObject,
    ArchivePanel,
    ArchivePreview,
    ArchiveProduction,
    ArchiveUnresolved,
    ArchiveWhole,
)

router = APIRouter(prefix="/api/v1", tags=["archive"])

# A `Literal` so FastAPI rejects an unknown order before the spine, and the OpenAPI carries it.
Sort = Literal["name", "hours", "recent"]
# Repeated parameters, each value bounded: `?year=2024&year=2025`.
Texts = Annotated[list[Annotated[str, Query(max_length=120)]], Query(max_length=60)]  # [T]
Ids = Annotated[list[int], Query(max_length=60)]  # [T]


@router.get("/archive", response_model=ArchiveList)
def archive_page(  # noqa: PLR0913
    limit: int = Query(20, ge=1, le=500),  # [P docs/domini/archivio.md]
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, max_length=200),  # [T]
    key: str | None = Query(None, max_length=200),  # [T]
    year: Texts = [],  # noqa: B006 - FastAPI copies the default
    type_: Annotated[list[Family], Query(alias="type", max_length=10)] = [],  # noqa: B006
    constellation: Texts = [],  # noqa: B006
    filter_name: Annotated[
        list[Annotated[str, Query(max_length=120)]], Query(alias="filter", max_length=60)
    ] = [],  # noqa: B006
    form: Annotated[list[Form], Query(max_length=3)] = [],  # noqa: B006
    site: Ids = [],  # noqa: B006
    optics: Ids = [],  # noqa: B006
    camera: Ids = [],  # noqa: B006
    catalog: Texts = [],  # noqa: B006
    sort: Sort = "name",
    conn: sqlite3.Connection = Depends(get_db),
) -> ArchiveList:
    """The archive rows -- confirmed objects and mosaics -- with each one's filters, in the order
    `sort` chooses, narrowed by the criteria. A repeated criterion is either
    (`?year=2024&year=2025`), different criteria hold together.

    `year`, `site`, `optics` and `camera` narrow the **frames**: a row passes with one of its
    frames in them, and its hours, filters, productions and panels are those frames' only --
    narrowed to 2025, a row tells 2025. `filter` asks the same frames and leaves the hours.

    `key` narrows to the one row with that key (`items[].key`): the search opens an object so,
    where `q` would also find `M 10` and `M 101` for `M 1`. With `key`, `q` is not applied.

    `criteria` counts each option with the other choices on, on the first page only (`offset` 0):
    "Mostra altri" does not change them, and they read the frames. `whole` is the whole archive, and
    `unresolved` the light frames no object took. Twenty rows a page (the sheet's "Mostra altri
    20")."""
    scope = Scope(years=tuple(year), sites=tuple(site), optics=tuple(optics), cameras=tuple(camera))
    criteria = archive.Criteria(
        # the row the search opens: words left in the bar must not hide it
        q=None if key else q,
        key=key,
        catalogs=tuple(catalog),
        constellations=tuple(constellation),
        types=tuple(type_),
        forms=tuple(form),
        filters=tuple(filter_name),
        scope=scope,
    )
    asked = vars(criteria)
    rows, count = archive.page(
        conn, limit=limit, offset=offset, sort=cast(archive.Order, sort), **asked
    )
    left = archive.unresolved(conn)
    return ArchiveList(
        items=items_of(conn, rows, scope),
        total=count,
        found=ArchiveFound(**archive.found(conn, **asked)),
        limit=limit,
        offset=offset,
        whole=ArchiveWhole(**archive.totals(conn)),
        criteria=[ArchiveCriterion(**c) for c in archive_criteria.offered(conn, criteria)]
        if offset == 0
        else [],
        unresolved=None
        if left is None
        else ArchiveUnresolved(**left, solver_missing=solver_where(conn)[0] is None),
    )


def items_of(
    conn: sqlite3.Connection, rows: list[dict[str, Any]], scope: Scope
) -> list[ArchiveObject]:
    """One query per kind of row for the whole page; an object row carries only its frames outside
    mosaics, like its hours. Nothing narrowing, what `archive_rows` wrote while fresh."""
    mosaic_keys = [r["mosaic_key"] for r in rows if r["mosaic_key"]]
    filters_by_key, made_by_key = _filters_and_productions(conn, rows, scope)
    panels_by_key = archive.panels(conn, mosaic_keys, scope)
    put = previews.of(conn, (r["key"] for r in rows))
    return [
        ArchiveObject(
            key=r["key"],
            name=objects.display_name(r),
            slug=r["catalog_slug"],
            common_name=r["common_name"],
            frames=r["frames"],
            integration_s=r["integration_s"],
            untimed=r["untimed"],
            constellation=r["constellation"],
            type_code=r["type_code"],
            filters=filters_by_key.get(r["row_key"], []),
            productions=[ArchiveProduction(**p) for p in made_by_key.get(r["row_key"], [])],
            panels=r["panels"],
            panel_list=[ArchivePanel(**p) for p in panels_by_key.get(r["mosaic_key"], [])],
            previews=_previews(r, made_by_key.get(r["row_key"], []), put),
        )
        for r in rows
    ]


type ByRow = dict[Any, list[Any]]


def _filters_and_productions(
    conn: sqlite3.Connection, rows: list[dict[str, Any]], scope: Scope
) -> tuple[ByRow, ByRow]:
    """`({row key: filters}, {row key: productions})`: written ones with nothing narrowing."""
    if scope == Scope() and derived_fresh.is_fresh(conn):
        keys = [r["row_key"] for r in rows]
        return archive_rows.filters_of(conn, keys), archive_rows.productions_of(conn, keys)
    object_ids = [r["id"] for r in rows if r["mosaic_key"] is None]
    mosaic_keys = [r["mosaic_key"] for r in rows if r["mosaic_key"]]
    filters = filters_used.of(conn, Subject.OBJECT, object_ids, alone=True, scope=scope)
    filters |= filters_used.of(conn, Subject.MOSAIC, mosaic_keys, scope=scope)
    made = productions.of(conn, Subject.OBJECT, object_ids, alone=True, scope=scope)
    made |= productions.of(conn, Subject.MOSAIC, mosaic_keys, scope=scope)
    key_of = {r["mosaic_key"] or r["id"]: r["row_key"] for r in rows}
    return (
        {key_of[k]: v for k, v in filters.items()},
        {key_of[k]: v for k, v in made.items()},
    )


def _previews(
    row: dict[str, Any], made: list[dict[str, Any]], put: dict[Any, str]
) -> list[ArchivePreview]:
    """One place per production, in their order; a mosaic's one place is of all of them."""
    if row["mosaic_key"] is not None:
        at = put.get(("mosaic", row["key"], None, None))
        return [ArchivePreview(url=url_of(row["key"], None), at=at)]
    return [
        ArchivePreview(
            url=url_of(row["key"], f"{_id(p['optics_id'])}:{_id(p['camera_id'])}"),
            at=put.get(("object", row["key"], p["optics"], p["camera"])),
        )
        for p in made
    ]


PREVIEW_PATH = "/archive/preview"


def url_of(key: str, production: str | None) -> str:
    """The one address of a photo place, for reading, putting and removing (`api/previews.py`):
    the page never builds it."""
    query = {"key": key} | ({"production": production} if production else {})
    return f"/api/v1{PREVIEW_PATH}?{urlencode(query)}"


def _id(instrument_id: int | None) -> str:
    return "none" if instrument_id is None else str(instrument_id)
