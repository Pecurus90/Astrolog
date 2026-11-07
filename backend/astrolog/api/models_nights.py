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
    bar_pct: int = Field(
        description="Its hours as a share of the night's longest object, 0-100; at least 2 when "
        "it has any time, so a bar never vanishes; 0 without time."
    )


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
    lit_side: Literal["left", "right"] = Field(
        description="Which side of the disc is lit, from the phase and the site's hemisphere."
    )


class Shooting(BaseModel):
    """What the Moon left of the night's astronomical dark (`docs/domini/notti.md`). **Computed**
    like the Moon, with the calendar's threshold."""

    kind: Literal["broadband", "narrowband", "mixed"]
    broadband_hours: float = Field(description="Hours of dark good for broadband, tenths.")
    dark_hours: float = Field(description="Hours of astronomical dark, tenths.")


class NightWeather(WeatherSkyOut):
    """The actual weather of that night, from the archive: `ok` with its sky; `waiting` until it
    has arrived (a young night waits for the reanalysis); `unknown` if the site's time zone is not
    recognised."""

    state: Literal["ok", "waiting", "unknown"]
    sky_word: Literal["clear", "scattered", "broken", "overcast"] | None = Field(
        default=None,
        description="The mean cover in the dark in okta classes (WMO 2700), written with the "
        "history; null without the clouds.",
    )
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
    site_from: Literal["frames", "home", "answer"] = Field(
        description="Where the site comes from: the frames' coordinates, home for frames without "
        "them, or your answer in To confirm."
    )
    shooting: Shooting | None = Field(
        description="Null without the site's zone or without astronomical dark."
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
    objects: int = Field(
        description="The objects named so far, in a night or still waiting for one."
    )


class WaitingPoses(BaseModel):
    """Frames no night has gathered, grouped by **where the answer is given**: a question in
    *To confirm* (`review`), the site to choose (`site`), the date to write (`date`), or nowhere
    (`never`) for a reason the app does not map."""

    answer_at: Literal["review", "site", "date", "never"]
    frames: int


class CriterionOption(BaseModel):
    """A value of a criterion: a year, a site id, a setup id, a filter's name, a constellation's
    IAU code, a verdict or `unknown`."""

    value: str
    nights: int = Field(
        description="How many nights it would give with the other criteria's choices applied; "
        "at zero the page shows it off."
    )
    chosen: bool
    name: str | None = Field(default=None, description="A site's or a named setup's name.")
    optics: str | None = Field(default=None, description="A setup's optics, for an unnamed one.")
    camera: str | None = Field(default=None, description="A setup's camera, for an unnamed one.")
    passband: str | None = Field(default=None, description="A filter's band: its colour.")


class Criterion(BaseModel):
    key: Literal["year", "site", "setup", "filter", "constellation", "sky"]
    options: list[CriterionOption] = Field(description="In the order the page shows them.")


class MonthSum(BaseModel):
    """A month of the list: every night that passes the criteria, not only the loaded ones."""

    month: str = Field(description="`YYYY-MM`.")
    nights: int
    integration_s: float
    untimed: int


class NightList(Page[Night]):
    criteria: list[Criterion] = Field(description="In the sheet's order.")
    empty: Literal["no_folders", "no_frames", "no_site", "reading", "waiting"] | None = Field(
        description="Why the archive has no nights at all; null when it has some. The site comes "
        "before the answers, the answers before the wait."
    )
    months: list[MonthSum] = Field(description="Newest first.")
    totals: ArchiveTotals | None = Field(
        description="The whole archive's, on the first page only (`offset` 0)."
    )
    waiting: list[WaitingPoses]
    waiting_frames: int = Field(
        description="The frames of `waiting` together, except those of `review`: To confirm counts "
        "them already."
    )
    still_reading: int = Field(
        description="How many frames the spine still has to work through: work, not a question."
    )
    reading_done_pct: int | None = Field(
        description="How far that work has gone, 0-99, rounded down; null when nothing is left."
    )


class DayNight(BaseModel):
    id: int
    site: str
    verdict: Literal["go", "marginal", "nogo"] | None = Field(
        description="Null without the night's weather."
    )


class CalendarDay(BaseModel):
    day: int
    nights: list[DayNight] = Field(description="Two sites the same day: two signs.")


class NightMonth(BaseModel):
    """A month of the Nights' calendar."""

    month: str = Field(description="`YYYY-MM`.")
    days: list[CalendarDay] = Field(description="Only the days with nights, in order.")
    nights: int
    good: int = Field(description="Nights whose verdict is `go`.")
    integration_s: float
    untimed: int
    first_month: str | None = Field(description="The first month with nights; null without any.")
    last_month: str = Field(description="Tonight's month at home: the calendar stops there.")
