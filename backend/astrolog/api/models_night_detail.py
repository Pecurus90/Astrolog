"""A night for its window (`docs/domini/notti.md`, *Tutto della notte*): the Nights page's row and
what only the window shows, ready for the screen."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_gear import RigPart
from .models_nights import Night


class NightRig(BaseModel):
    """A setup that took the night: as the Gear page names it, with that night's frames."""

    id: int
    name: str | None = Field(description="The name you gave it, if you gave it one.")
    optics: str | None
    camera: str | None
    focal_mm: float | None
    scale_arcsec_px: float | None = Field(description="Measured on its solved frames, median.")
    width_deg: float | None
    height_deg: float | None
    parts: list[RigPart] = Field(description="As in the Gear page, in the card's order.")
    frames: int = Field(description="Its frames that night.")
    integration_s: float
    untimed: int


class Distance(BaseModel):
    value: float = Field(description="Whole light years, or millions with one decimal under ten.")
    unit: Literal["ly", "million_ly"]


class ObjectFacts(BaseModel):
    """What the catalog says of an object of the night; all null outside the catalog."""

    key: str = Field(description="The stable key, the same as the night's objects.")
    common_name: str | None = Field(description="The catalog's common name, as the search's.")
    type_code: str | None
    constellation: str | None = Field(description="Three-letter IAU code.")
    distance: Distance | None
    extent_ly: float | None = Field(
        description="How big it really is, two figures: distance times its larger size."
    )


class NightDetail(BaseModel):
    night: Night
    first_start: str | None = Field(
        description="The first frame's start, in the site's zone with its offset; null when no "
        "frame says when."
    )
    last_end: str | None = Field(description="The last frame's end: its start plus its exposure.")
    rigs: list[NightRig] = Field(description="Most time first; frames with no known rig are out.")
    objects: list[ObjectFacts] = Field(description="In the order of the night's objects.")
