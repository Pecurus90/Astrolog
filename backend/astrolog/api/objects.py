"""An Archive row for its window: the row is the Archive's, the rest from the spine
(`spine/object_detail.py`)."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db.config import read as read_settings
from ..spine import archive, nights
from ..spine import object_detail as object_detail_read
from ..spine.counts import Scope
from ..spine.object_measures_read import object_measures as object_measures_read
from ..weather import history
from .archive import items_of
from .deps import get_db
from .models_night_measures import ObjectMeasures
from .models_object_detail import ObjectDetail

router = APIRouter(prefix="/api/v1", tags=["archive"])
_PRODUCTION = Query(None, pattern=r"^(\d{1,9}|none):(\d{1,9}|none)$")  # [T]
_PANEL = Query(None, ge=1, description="A panel of the mosaic, as `panel_list` gives its `id`.")


# Before the window's route: its `{key:path}` would take `.../measures` as the key.
@router.get("/objects/{key:path}/measures", response_model=ObjectMeasures)
def object_measures(
    key: str,
    production: str | None = _PRODUCTION,
    panel: int | None = _PANEL,
    conn: sqlite3.Connection = Depends(get_db),
) -> ObjectMeasures:
    """An Archive row's frame measures for its window: what `night_measures.py` wrote for it
    after each scan, its nights as the groups (in shooting order), its frames one by one.
    `production` and `panel` as in the window; without a production, all of the row's together,
    and `one_production` says whether the SNR and the FWHM in pixels compare across them.

    404 `object_not_found`: no row with that key, or no frame of it in that panel.
    422 `panel_with_production`: a panel is of all productions."""
    scope = _scope(production, panel)
    rows, _ = archive.page(conn, limit=1, offset=0, key=key, scope=scope)
    if not rows:
        raise HTTPException(status_code=404, detail="object_not_found")
    return ObjectMeasures.model_validate(object_measures_read(conn, rows[0], scope))


@router.get("/objects/{key:path}", response_model=ObjectDetail)
def object_detail(
    key: str,
    production: str | None = _PRODUCTION,
    panel: int | None = _PANEL,
    conn: sqlite3.Connection = Depends(get_db),
) -> ObjectDetail:
    """One Archive row -- an object or a mosaic, by its `key` -- for its window: the row as the
    Archive gives it, the nights that took it (each the Nights page's row, with the frames and
    hours the row took in it), its first and last night, its sites, the setups that took it and
    what the catalog says of it, with its size beside the full Moon.

    `production` narrows everything to one of the row's productions: `optics_id:camera_id` as
    the row gives them, `none` for a piece the frames do not say. `panel` narrows a mosaic to
    one of its panels, and the catalog is then its object's when it has one in the catalog.

    404 `object_not_found`: no row with that key, or no frame of it in that panel.
    422 `panel_with_production`: a panel is of all productions."""
    scope = _scope(production, panel)
    rows, _ = archive.page(conn, limit=1, offset=0, key=key, scope=scope)
    if not rows:
        raise HTTPException(status_code=404, detail="object_not_found")
    found = object_detail_read.detail(conn, rows[0], scope)
    taken = dict(found.pop("nights"))
    listed = nights.page(
        conn,
        ids=list(taken),
        weather=nights.Observed(history.KIND, history.arrives_on),
        max_pct=read_settings(conn).moon_broadband_max_pct,
    )
    by_id = {n["id"]: n for n in listed}
    return ObjectDetail.model_validate(
        {
            "row": items_of(conn, rows, scope)[0],
            "nights": [{"night": by_id[i], **counted} for i, counted in taken.items()],
            **found,
        }
    )


def _scope(production: str | None, panel: int | None) -> Scope:
    # a panel's tab is of all productions: its measures are written only so
    if production and panel is not None:
        raise HTTPException(status_code=422, detail="panel_with_production")
    return Scope(production=_pieces(production) if production else None, panel=panel)


def _pieces(production: str) -> tuple[int | None, int | None]:
    optics, camera = (None if p == "none" else int(p) for p in production.split(":"))
    return optics, camera
