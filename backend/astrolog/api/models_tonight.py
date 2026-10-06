"""Every field of tonight's sky may be missing, and missing means something precise (no home site,
a moon that does not rise): whoever shows it writes a sentence, not a zero."""

from typing import Literal

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


class SkyPointOut(BaseModel):
    """An instant of the night and how high the Moon was, in degrees above the horizon.

    The altitude is **negative below the horizon**, and is not clipped to zero: that is what lets
    the chart draw where the Moon comes in and goes out instead of a curve resting on the edge.
    """

    at: str
    altitude_deg: float


class MoonOut(BaseModel):
    phase_key: PhaseKey
    illumination_pct: int = Field(ge=0, le=100)
    rise: str | None = Field(
        description="ISO instant with its time zone. `None` when the crossing does not happen "
        "within the night, as above the polar circle, where a written time would be invented."
    )
    set: str | None = Field(description="ISO instant with its time zone; `None` as for `rise`.")
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
    track: list[SkyPointOut] = Field(
        description="The altitude curve along the night, for whoever draws it. The first and "
        "last points are the two ends of the night: a chart that closed earlier would lose the "
        "last half hour."
    )
    ceiling_deg: int = Field(
        gt=0,
        le=90,
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
    weather: WeatherBriefOut | None = Field(
        default=None,
        description="The current night's weather from the chosen model, as the forecast wrote "
        "it; `None` until the forecast has arrived.",
    )
