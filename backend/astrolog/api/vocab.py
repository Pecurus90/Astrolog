"""Vocabularies ship with the program, so they never open the database: they answer on a fresh
install."""

from fastapi import APIRouter

from ..vocab import filters
from .models_review import FilterModelList, FilterModelOut

router = APIRouter(prefix="/api/v1", tags=["vocabolari"])


@router.get("/vocab/filter-models", response_model=FilterModelList)
def filter_models() -> FilterModelList:
    """The commercial filters a new filter is declared from: brand, name and passband, in the
    vocabulary's order. Not paginated: the vocabulary ships with the program
    and does not grow with the archive."""
    return FilterModelList(
        items=[
            FilterModelOut(id=m["id"], brand=m["brand"], name=m["name"], passband=m["passband"])
            for m in filters.models()
        ]
    )
