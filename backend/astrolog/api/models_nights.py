"""The Nights page arrives ready for the screen: what does not exist yet gets no empty field here,
it is born with its own piece (`docs/domini/notti.md`)."""

from typing import Literal

from pydantic import BaseModel, Field

from .models_page import Page
from .models_tonight import IlluminationPct, PhaseKey
from .models_weather import WeatherSkyOut


class NightObject(BaseModel):
    """An object shot during that night."""

    key: str = Field(description="The stable key, the same as the Archive's.")
    name: str | None
    frames: int
    integration_s: float
    untimed: int = Field(description="Its frames that do not say how long: they are not zero.")


class FilterUsed(BaseModel):
    """A filter you shot something with, with the time given to it.

    Born here, where the Nights asked for it first, and reused by the Archive: the place that
    counts them is a single one, and two shapes would state the same fact twice."""

    name: str = Field(description="The name you gave it, or the one the files carried.")
    passband: str = Field(
        description="The canonical passband (`vocab/filters`): it is what gives the colour."
    )
    frames: int
    integration_s: float


class MoonThatNight(BaseModel):
    """Which moon there was: the phase and how lit it was. **Computed**, not stored."""

    # The same phases and bound as tonight's route: it is the same Moon, and two OpenAPI shapes
    # for one fact would be two contracts to keep in agreement.
    phase_key: PhaseKey
    illumination_pct: IlluminationPct


class NightWeather(WeatherSkyOut):
    """The actual weather of that night, from the archive: `ok` with its sky; `waiting` until it
    has arrived (a young night waits for the reanalysis); `unknown` if the site's time zone is not
    recognised."""

    state: Literal["ok", "waiting", "unknown"]
    arrives_on: str | None = Field(
        description="`waiting` on a young night: the date (site zone) the reanalysis is asked. "
        "Null otherwise, also when it is due and only the service's answer is missing."
    )


class Night(BaseModel):
    """A row: **one night**, with what you did in it."""

    id: int = Field(description="The night's stable id.")
    night_date: str = Field(
        description="The date of the night, in the site's time zone; on screen it reads as a date."
    )
    site: str = Field(
        description="From where: two sites on the same date are two nights, and the row must "
        "say so."
    )
    site_source: str = Field(
        description="`declared` if you said it, `detected` if the app derived it."
    )
    frames: int = Field(description="How many frames, rewritten copies excluded.")
    integration_s: float = Field(description="The sum of the frames' time, in seconds.")
    untimed: int = Field(
        description="How many do not say how long they lasted: they do not count as zero."
    )
    objects: list[NightObject]
    filters: list[FilterUsed] = Field(
        description="In the one filter order of the app: the order the page shows them in."
    )
    moon: MoonThatNight | None = Field(
        description="Null when the site's time zone is not recognised: without a time zone there "
        "is no midnight, and the row stays silent instead of describing the sky of another place."
    )
    weather: NightWeather


class ArchiveTotals(BaseModel):
    """What the whole archive holds: it does not depend on how many rows are being looked at."""

    nights: int
    frames: int
    integration_s: float
    untimed: int


class WaitingPoses(BaseModel):
    """Frames no night has gathered, grouped by **where the answer is given**: a question in
    *To confirm* (`review`), the site to declare (`site`), or nowhere (`never`) -- the case of a
    frame without a date, which no answer can fix."""

    answer_at: Literal["review", "site", "never"]
    frames: int


class NightList(Page[Night]):
    totals: ArchiveTotals
    waiting: list[WaitingPoses]
    still_reading: int = Field(
        description="How many frames the spine still has to work through: work, not a question."
    )
    reading_done_pct: int | None = Field(
        description="How far that work has gone, 0-99, rounded down; null when nothing is left."
    )
