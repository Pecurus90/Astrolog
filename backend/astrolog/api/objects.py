"""An Archive row for its window: the row is the Archive's, the rest from the spine
(`spine/object_detail.py`)."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db.config import read as read_settings
from ..spine import archive, nights
from ..spine import object_detail as object_detail_read
from ..spine.counts import Scope
from ..weather import history
from .archive import items_of
from .deps import get_db
from .models_object_detail import ObjectDetail

router = APIRouter(prefix="/api/v1", tags=["archive"])


@router.get("/objects/{key:path}", response_model=ObjectDetail)
def object_detail(
    key: str,
    production: str | None = Query(None, pattern=r"^(\d{1,9}|none):(\d{1,9}|none)$"),  # [T]
    conn: sqlite3.Connection = Depends(get_db),
) -> ObjectDetail:
    """One Archive row -- an object or a mosaic, by its `key` -- for its window: the row as the
    Archive gives it, the nights that took it (each the Nights page's row, with the frames and
    hours the row took in it), its first and last night, its sites, the setups that took it and
    what the catalog says of it, with its size beside the full Moon.

    `production` narrows everything to one of the row's productions: `optics_id:camera_id` as
    the row gives them, `none` for a piece the frames do not say.

    404 `object_not_found`: no row with that key."""
    scope = Scope(production=_pieces(production)) if production else Scope()
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


def _pieces(production: str) -> tuple[int | None, int | None]:
    optics, camera = (None if p == "none" else int(p) for p in production.split(":"))
    return optics, camera
