"""The Archive arrives ready for the screen. Hours can be zero even when time is unknown, so they
travel with `untimed` and the frontend never writes "0 h" from them."""

from pydantic import BaseModel, Field

from ..spine.archive_criteria import Key as ArchiveKey
from .models_nights import FilterUsed
from .models_page import Page


class ArchivePanel(BaseModel):
    """A panel of a mosaic: the framing, what you shot in it and how much."""

    id: int = Field(description="To narrow the mosaic's window to this panel (`?panel=`).")
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


class ArchiveProduction(BaseModel):
    """The row shot with one optics and one camera: a production, until projects exist."""

    optics: str | None = Field(description="The optics' name; null if the frames do not say it.")
    camera: str | None = Field(description="The camera's name; null if the frames do not say it.")
    optics_id: int | None = Field(description="To narrow the object's window to this production.")
    camera_id: int | None
    frames: int = Field(description="Its frames, rewritten copies excluded.")
    integration_s: float = Field(description="The sum of its frames' time, in seconds.")
    untimed: int = Field(description="How many of its frames do not say how long they lasted.")
    filters: list[FilterUsed] = Field(
        description="The filters of these frames, in the one filter order; empty if unknown."
    )


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
    common_name: str | None = Field(
        description="The name the catalog knows it by, in English as the catalog writes it."
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
        description="Which filters you shot it with, in the one filter order; empty if unknown."
    )
    productions: list[ArchiveProduction] = Field(
        description="One per optics and camera, most time first: together they are the row. "
        "Frames that do not say their rig are one production with null optics and camera."
    )
    panels: int | None = Field(description="How many panels, for a mosaic; null for an object.")
    panel_list: list[ArchivePanel] = Field(
        description="The panels, most shot first; empty for an object."
    )


class ArchiveOption(BaseModel):
    """One option of a criterion, counted with the other choices on."""

    value: str = Field(
        description="What goes back to the route: a year, an id, a name, a family, a form."
    )
    label: str | None = Field(
        description="The name of a site or a piece of gear; null where the value says itself."
    )
    passband: str | None = Field(description="A filter's canonical passband: it gives the colour.")
    rows: int = Field(description="The rows this option would give: zero shows it off, not gone.")
    chosen: bool


class ArchiveCriterion(BaseModel):
    """A criterion the archive can narrow by: only from two options up, or while one is chosen."""

    key: ArchiveKey
    options: list[ArchiveOption] = Field(description="In the criterion's own order.")


class ArchiveFound(BaseModel):
    """How many of the rows found are objects and how many mosaics."""

    objects: int
    mosaics: int


class ArchiveWhole(BaseModel):
    """The whole archive, whatever the bar asks: the head of the page."""

    rows: int = Field(description="Objects and mosaics together.")
    mosaics: int = Field(description="How many of the rows are mosaics.")
    frames: int
    integration_s: float
    untimed: int
    nights: int


class ArchiveUnresolved(BaseModel):
    """Light frames that no object and no mosaic took, counted like a row."""

    frames: int
    integration_s: float
    untimed: int
    filters: list[FilterUsed]
    solver_missing: bool = Field(
        description="ASTAP is not there: the frames stay unsolved until it is."
    )


class ArchiveList(Page[ArchiveObject]):
    """`total` counts the rows that pass the filter, not every row in the archive."""

    found: ArchiveFound = Field(description="The same rows, split between objects and mosaics.")
    whole: ArchiveWhole
    criteria: list[ArchiveCriterion] = Field(description="In the sheet's order.")
    unresolved: ArchiveUnresolved | None = Field(
        description="The frames without an object; null when there are none."
    )
