"""An Archive row for its window (tavola v76, `componenti/Riepilogo.dc.html` tipo oggetto): the
row, its nights and setups, what the catalog says, ready for the screen."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_archive import ArchiveObject
from .models_night_detail import NightRig, ObjectFacts
from .models_nights import Night


class BesideTheMoon(BaseModel):
    """Its larger size against the full Moon's 31'."""

    compare: Literal["more", "like", "less"] = Field(
        description="`more` from 1.5 Moons, `like` from 0.9, `less` below."
    )
    moons: int | None = Field(description="Whole Moons with `more`, null otherwise.")


class ObjectWindowFacts(ObjectFacts):
    """What the catalog says of the row, with its size on the sky; all null outside the catalog."""

    distance_pc: float | None = Field(
        description="Parsecs to the ten; null from a million light years."
    )
    size_arcmin: float | None = Field(description="Its larger size on the sky, arcminutes.")
    moon: BesideTheMoon | None


class ObjectNight(BaseModel):
    """A night that took the row: the Nights page's row, and what the row took in it."""

    night: Night
    frames: int
    integration_s: float
    untimed: int


class ObjectDetail(BaseModel):
    row: ArchiveObject = Field(description="The Archive's row, narrowed as asked.")
    nights: list[ObjectNight] = Field(description="In shooting order, the first night first.")
    first_night: str | None = Field(description="`YYYY-MM-DD`, the site's night; null: no night.")
    last_night: str | None
    sites: list[str] = Field(description="The sites' names, in the order of their first night.")
    rigs: list[NightRig] = Field(
        description="Most time first, with the row's frames; frames with no known rig are out."
    )
    facts: ObjectWindowFacts
