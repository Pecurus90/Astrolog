"""Every field of tonight's sky may be missing, and missing means something precise (no home site,
a moon that does not rise): whoever shows it writes a sentence, not a zero."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .models_weather import WeatherBriefOut

# Repeated rather than imported from `ephemeris`, so the route contract does not change shape with
# an internal module.
PhaseKey = Literal[
    "new",
    "waxing_crescent",
    "first_quarter",
    "waxing_gibbous",
    "full",
    "waning_gibbous",
    "last_quarter",
    "waning_crescent",
]
SkyKind = Literal["day", "civil", "nautical", "astronomical", "dark"]
Compass = Literal[
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]  # fmt: skip


class MoonCalendarShotOut(BaseModel):
    """A night shot on that day, from any site: the calendar's star."""

    night_id: int
    site: str
    objects: list[str] = Field(description="Display names, the most shot first.")
    frames: int
    integration_s: int
    untimed: int = Field(description="Frames that do not say how long they lasted.")


class MoonCalendarNightOut(BaseModel):
    date: str
    phase_key: "PhaseKey"
    illumination_pct: int
    dark_s: int = Field(description="Astronomical dark of the night, Moon or not.")
    moonless_dark_s: int
    event: Literal["new", "full"] | None
    lit_side: Literal["left", "right"] = Field(
        description="As `MoonOut.lit_side`, for the day's disc."
    )
    level: Literal["go", "marginal", "nogo"] = Field(
        description="The Moon's step on the settings' Moon rule (factory ING 25/65): broadband "
        "good, broadband marginal, narrowband only.",
    )
    shots: list[MoonCalendarShotOut] = Field(default=[], description="Empty: nothing shot.")


class MoonCalendarOut(BaseModel):
    """This month and the next as the background round wrote them: empty `nights` until it has."""

    today: str | None
    good_pct: int = Field(description="The rule's bound of broadband good, for the legend.")
    limit_pct: int = Field(description="The rule's bound of broadband marginal, for the legend.")
    nights: list[MoonCalendarNightOut]


IlluminationPct = Annotated[int, Field(ge=0, le=100)]  # [T] percent


class SkyPointOut(BaseModel):
    """An instant of the night and how high the Moon was, in degrees above the horizon.

    The altitude is **negative below the horizon**, and is not clipped to zero: that is what lets
    the chart draw where the Moon comes in and goes out instead of a curve resting on the edge.
    """

    at: str
    altitude_deg: float


class MoonPointOut(SkyPointOut):
    moonless_dark_left_s: int = Field(
        description="From this instant to the window's end, how long the sky stays astronomically "
        "dark with the Moon down: the chart's reader writes it under the pointer."
    )


class MoonOut(BaseModel):
    phase_key: PhaseKey
    illumination_pct: IlluminationPct
    rise: str | None = Field(
        description="ISO instant with its time zone. `None` when the crossing does not happen "
        "within the night, as above the polar circle, where a written time would be invented."
    )
    set: str | None = Field(description="ISO instant with its time zone; `None` as for `rise`.")
    rise_compass: Compass | None = Field(
        default=None, description="Where it rises, on sixteen points; `None` without a rise."
    )
    age_days: int = Field(default=0, description="Whole days since new Moon, at midnight.")
    distance_km: int = Field(
        default=0, description="Centre to centre at midnight, rounded to a hundred kilometres."
    )
    next_new: str | None = Field(
        default=None,
        description="The night (`YYYY-MM-DD`) of the next new Moon from tonight, from the written "
        "calendar; `None` until the background round has written it.",
    )
    next_full: str | None = Field(default=None, description="As `next_new`, for the full Moon.")
    lit_side: Literal["left", "right"] = Field(
        description="Which side the lit limb is seen on **from this site**: it depends on the "
        "phase and on the hemisphere, since a crescent is lit on the right in the north and on "
        "the left in Australia. The backend says it because it knows both: deducing it while "
        "drawing would put a computation in the layout, and half the world would see the Moon "
        "mirrored."
    )
    highest: SkyPointOut = Field(
        description="The highest point of the night. **Never absent**, not even without rise "
        "and set times: a Moon that does not rise still climbs, below the horizon, and how "
        "little it climbs is the answer."
    )
    highest_in_chart: SkyPointOut | None = Field(
        default=None,
        description="The highest drawn point inside the chart's span: what the Dashboard says "
        "it climbs to tonight. `None` without a chart.",
    )
    track: list[MoonPointOut] = Field(
        description="The altitude curve along the night, for whoever draws it. The first and "
        "last points are the two ends of the night: a chart that closed earlier would lose the "
        "last half hour."
    )
    ceiling_deg: int = Field(
        gt=0,
        le=90,  # [T] zenith
        description="How high the Moon can get **from this site**, never more: it is the top "
        "edge of the chart. It depends on the latitude and not on the night, so the scale never "
        "changes at one place and two nights compare at a glance. It arrives already rounded up "
        "to a multiple of fifteen, because that is the number on the tick mark: rounding it up "
        "on screen would be a computation in the layout.",
    )


class SiteSkyOut(BaseModel):
    """Where one observes from, and what sky it has: the toolbar footer writes it on one line.

    **The two sky fields go together, and together they can be missing.** The class is not a
    database column: it derives from the brightness, so without the measurement there is no
    class -- and that is the state of someone who skipped that question at first launch, not a
    fault. Whoever shows it writes "class not declared", not a zero.
    """

    name: str
    sky_sqm: float | None
    bortle: int | None


class SkyBandOut(BaseModel):
    """A stretch of night in which the sky is always the same thing: from when to when, and which.

    Why they come out **already split** instead of as eight times is told in
    `docs/domini/effemeridi.md`, entry *"Le fasce arrivano gia' divise"*."""

    starts_at: str
    ends_at: str
    kind: SkyKind


PlanetKey = Literal["saturn", "jupiter", "mars", "venus"]


class PlanetOut(BaseModel):
    """A planet of the night chart and its altitude through the whole night window."""

    key: PlanetKey
    track: list[SkyPointOut]
    rise: str | None = Field(
        default=None, description="Its first rise inside the chart's span; `None`: not there."
    )
    set: str | None = Field(default=None, description="As `rise`, its first set.")
    highest: SkyPointOut | None = Field(
        default=None, description="Its top inside the chart's span; `None` without a chart."
    )


class ChartOut(BaseModel):
    """The span the night chart draws and the instants it marks."""

    starts_at: str = Field(description="Half an hour before the sunset's hour.")
    ends_at: str = Field(description="Half an hour after the hour nearest the sunrise.")
    dark_from: str | None = Field(description="Where astronomical dark starts; `None` without it.")
    dark_until: str | None = Field(description="Where astronomical dark ends; `None` without it.")


class DarkStretchOut(BaseModel):
    starts_at: str
    ends_at: str


class MoonInDarkOut(BaseModel):
    """The Moon above the horizon in tonight's dark: from the first instant to the last, with the
    broadband word of its lit fraction on the Meteo's Moon scale (ING 25/65)."""

    level: Literal["go", "marginal", "nogo"]
    since: str
    until: str
    from_start: bool = Field(description="Already up when the dark starts.")
    to_end: bool = Field(description="Still up when the dark ends.")


class ShootingStretchOut(BaseModel):
    """A stretch of tonight's dark and what the Moon lets you shoot in it: broadband while it is
    down or below the Meteo's Moon scale's no-go (ING 65%), narrowband only above."""

    band: Literal["broadband", "narrowband"]
    starts_at: str
    ends_at: str
    seconds: int


class TonightOut(BaseModel):
    """The night it refers to (`YYYY-MM-DD` in the site's time zone), the site, the Moon and the
    sky."""

    night: str | None
    site: SiteSkyOut | None
    moon: MoonOut | None
    sky_bands: list[SkyBandOut] = Field(
        default=[],
        description="Empty when there is no night to split -- no site, or a time zone that does "
        "not resolve -- for the same reason the Moon is `None` there.",
    )
    dark_s: int | None = Field(
        default=None,
        description="How long tonight's astronomical dark lasts, in seconds: the sum of the `dark` "
        "bands. Computed, not forecast, so it is there when the weather is not; `None` without a "
        "night, never 0 in its place.",
    )
    weather: WeatherBriefOut | None = Field(
        default=None,
        description="The current night's weather from the chosen model, as the forecast wrote "
        "it; `None` until the forecast has arrived.",
    )
    chart: ChartOut | None = Field(default=None, description="`None` without a night.")
    planets: list[PlanetOut] = Field(default=[], description="Empty without a night.")
    moonless_dark: list[DarkStretchOut] = Field(
        default=[], description="The dark's stretches with the Moon down; empty without a night."
    )
    moon_in_dark: MoonInDarkOut | None = Field(
        default=None, description="`None` when the Moon is never up in the dark, or no night."
    )
    shooting: list[ShootingStretchOut] = Field(
        default=[],
        description="The dark in time order, split by band; together they make `dark_s`. "
        "Empty without a night.",
    )
    highest_planet: PlanetKey | None = Field(
        default=None,
        description="The planet whose top inside the chart is highest, among those that rise "
        "there (above the planets' rise altitude); `None` when none does.",
    )
    broadband_dark_s: int | None = Field(
        default=None, description="Of `dark_s`, the broadband stretches together; `None` as it."
    )
    narrowband_dark_s: int | None = Field(
        default=None, description="Of `dark_s`, the narrowband stretches together."
    )
    dark_returns: str | None = Field(
        default=None,
        description="When `dark_s` is 0 (midnight sun, white nights): the first night "
        "(`YYYY-MM-DD`) with astronomical dark again. `None` when tonight has dark, or no night.",
    )
