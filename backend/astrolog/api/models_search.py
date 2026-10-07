"""The search in the bar. A result says who it is (`key`, `id`, `kind`), never a page address: the
pages and their parameters live in the frontend, and a second home would drift."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_review import InstrumentKind


class FoundObject(BaseModel):
    """An Archive row: an object, or a confirmed mosaic (`panels`)."""

    key: str = Field(description="The Archive row's key: `/archive?key=` narrows to it alone.")
    name: str | None = Field(description="As the Archive names it.")
    common_name: str | None = Field(
        description="The catalog's common name, when it is not already the name."
    )
    frames: int
    integration_s: float
    untimed: int
    panels: int | None = Field(description="A mosaic's panels; null for an object.")


class FoundNight(BaseModel):
    """A night, found by date or by an object shot in it; its counts are the whole night's."""

    id: int
    night_date: str
    site: str
    frames: int
    integration_s: float
    untimed: int


class FoundPiece(BaseModel):
    """A piece or a filter you own. Hours not counted yet (`counted` false) or that the files do
    not tell (`no_hours`) arrive null, never zero."""

    id: int
    kind: InstrumentKind | Literal["filter"]
    name: str
    counted: bool
    frames: int | None
    integration_s: float | None
    untimed: int | None
    no_hours: Literal["files_silent", "no_rig"] | None


class FoundSite(BaseModel):
    id: int
    name: str
    nights: int


class Found[Item](BaseModel):
    items: list[Item]
    total: int = Field(description="How many in all: `items` are the first few.")


class SearchResult(BaseModel):
    objects: Found[FoundObject]
    nights: Found[FoundNight]
    gear: Found[FoundPiece]
    sites: Found[FoundSite]
