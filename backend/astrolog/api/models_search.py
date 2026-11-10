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


class DateRead(BaseModel):
    """A date the text was read as; `year` and `day` null where it did not write them."""

    year: int | None
    month: int
    day: int | None


class NightsWhy(BaseModel):
    """Why these nights (Cerca v77): the dates read (`5/6` both ways), the one object shot
    (`object`, its Archive name), or several objects."""

    by: Literal["dates", "object", "objects"]
    dates: list[DateRead]
    object: str | None


class FoundNights(Found[FoundNight]):
    why: NightsWhy | None = Field(description="Null when no night is found.")


class SearchExamples(BaseModel):
    """The empty field's hints, from your own archive; null when there is none to show."""

    gear: str | None = Field(
        description="The piece or filter with the most time; none counted yet, the first by name."
    )
    site: str | None = Field(description="The default site.")


class SearchResult(BaseModel):
    objects: Found[FoundObject]
    nights: FoundNights
    gear: Found[FoundPiece]
    sites: Found[FoundSite]
    archive_empty: bool = Field(
        description="No frame read yet: the four groups stay empty until the first scan."
    )
    examples: SearchExamples
