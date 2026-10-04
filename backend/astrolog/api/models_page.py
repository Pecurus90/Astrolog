"""`items` lives here and not in the subclasses: pydantic puts inherited fields first, and that
order is the OpenAPI order the frontend generates its types from."""

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel


class Page[Row](BaseModel):
    items: list[Row]
    total: int
    limit: int
    offset: int


def page_of[T](rows: Sequence[T], limit: int, offset: int) -> dict[str, Any]:
    return {
        "items": rows[offset : offset + limit],
        "total": len(rows),
        "limit": limit,
        "offset": offset,
    }
