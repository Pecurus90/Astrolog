"""The search reads in SQL (`spine/search.py`), with the Archive's way of folding names."""

import sqlite3

from fastapi import APIRouter, Depends, Query

from ..spine import search
from .deps import get_db
from .models_search import SearchResult

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search", response_model=SearchResult)
def search_archive(
    q: str = Query("", max_length=200),
    limit: int = Query(5, ge=1, le=20),
    conn: sqlite3.Connection = Depends(get_db),
) -> SearchResult:
    """Objects, nights, gear and sites of the archive matching `q`, at most `limit` per kind, each
    kind with its `total`.

    - **Objects** by any name: their own, the catalog's designations, the common name; ordered as
      the Archive by hours.
    - **Nights** by date in the common forms (ISO; day/month with or without the year, read
      both ways when both fit; day and month name; month name and year; Italian or English
      months) or by an object shot in them; newest first.
    - **Gear** and **sites** by name.

    A blank `q` finds nothing, not everything. Not paged: it is a menu of a few per kind, and
    `total` says how many more the page that shows them holds."""
    return SearchResult.model_validate(search.find(conn, q, limit))
