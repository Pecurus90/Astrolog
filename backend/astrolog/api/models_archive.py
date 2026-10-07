"""The Archive arrives ready for the screen. Hours can be zero even when time is unknown, so they
travel with `untimed` and the frontend never writes "0 h" from them."""

from pydantic import BaseModel, Field

from .models_nights import FilterUsed
from .models_page import Page


class ArchivePanel(BaseModel):
    """A panel of a mosaic: the framing, what you shot in it and how much."""

    object: str | None = Field(
        description="The object (or objects) of its frames; null if the sky knows of none."
    )
    ra_deg: float = Field(
        description="The centre: it tells WHICH panel, when two have the same object."
    )
    dec_deg: float
    frames: int
    integration_s: float
    untimed: int


class ArchiveObject(BaseModel):
    """A row of the Archive: a group of frames -- an object, or a confirmed mosaic -- and what you
    put into it. An object's row carries only the frames no mosaic has taken."""

    key: str = Field(
        description="Stable: the slug or the primary name of an object, the key of a mosaic."
    )
    name: str | None = Field(
        description="Already resolved by the backend; null only on a row that should not exist."
    )
    slug: str | None = Field(
        description="The catalog slug of the object, or of the mosaic's target."
    )
    frames: int = Field(description="How many frames, rewritten copies excluded.")
    integration_s: float = Field(
        description="The sum of the frames' time, in seconds; on screen it reads in hours."
    )
    untimed: int = Field(
        description="How many of those frames do not say how long they lasted: they do not "
        "count as zero."
    )
    constellation: str | None = Field(description="Three-letter IAU code, from the catalog.")
    type_code: str | None = Field(
        description="What it is (GALAXY, DARK_NEBULA...), from the catalog."
    )
    filters: list[FilterUsed] = Field(
        description="Which filters you shot it with, most used first; empty if unknown."
    )
    panels: int | None = Field(description="How many panels, for a mosaic; null for an object.")
    panel_list: list[ArchivePanel] = Field(
        description="The panels, most shot first; empty for an object."
    )


class ArchivePick(BaseModel):
    """A site or a piece of gear to narrow by: its id goes back to the route, its name on screen."""

    id: int
    name: str


class ArchiveChoices(BaseModel):
    """What the toolbar dropdowns offer: **what is in the archive**, not what the catalog knows:
    someone who uses two catalogs must not scroll through every one the catalog carries."""

    catalogs: list[str] = Field(
        description="The prefixes of the catalogs your objects belong to (`M`, `NGC`...)."
    )
    constellations: list[str] = Field(description="The three-letter IAU codes, in order.")
    filters: list[str] = Field(
        description="The names of the filters you shot at least one object with."
    )
    years: list[str] = Field(
        description="The years of your nights, latest first: the period dropdown offers them."
    )
    sites: list[ArchivePick] = Field(
        description="The sites you shot from; empty if only one, which would narrow nothing."
    )
    optics: list[ArchivePick] = Field(description="The optics you shot with; empty if only one.")
    cameras: list[ArchivePick] = Field(description="The cameras you shot with; empty if only one.")
    mosaics: bool = Field(
        description='Whether you have at least one confirmed mosaic: without one, "mosaics '
        'only" is not offered.'
    )


class ArchiveFound(BaseModel):
    """How many of the rows found are objects and how many mosaics: the count on screen does not
    call a mosaic an "object"."""

    objects: int
    mosaics: int


class ArchiveList(Page[ArchiveObject]):
    """`total` counts the rows that pass the filter, not every row in the archive."""

    found: ArchiveFound = Field(description="The same rows, split between objects and mosaics.")
    choices: ArchiveChoices
