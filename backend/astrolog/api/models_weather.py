"""Every weather number may be missing, and missing means "the model does not say", never zero:
the verdict is missing without cloud cover, the window when the Sun does not set."""

from typing import Literal

from pydantic import BaseModel, Field

from ..levels import MOON_BRIGHT_PCT
from ..weather.score import GOOD_FROM, UNCERTAIN_FROM

Level = Literal["go", "marginal", "nogo"]
SkyKind = Literal["day", "civil", "nautical", "astronomical", "dark"]


class SkyBandOut(BaseModel):
    """A stretch of night in which the sky is always the same thing: from when to when, and which.

    Why they come out **already split** instead of as eight times is told in
    `docs/domini/effemeridi.md`, entry *"Le fasce arrivano gia' divise"*."""

    starts_at: str
    ends_at: str
    kind: SkyKind


# Repeated rather than imported from `weather.judge`, so the route contract does not change shape
# with an internal module; a test holds the two lists equal.
MeasureCode = Literal[
    "cloud", "cloud_low", "rain", "gust", "wind", "condensation", "jet", "seeing", "aerosol",
    "moon", "visibility", "cloud_mid", "cloud_high", "temperature", "dew_point", "wind_700",
    "dust",
]  # fmt: skip
JudgedCode = Literal[
    "cloud", "cloud_low", "rain", "gust", "wind", "condensation", "jet", "seeing", "aerosol",
    "moon", "visibility",
]  # fmt: skip


class WeatherLevelsOut(BaseModel):
    """Each judged measure's word for the hour; `None` where the value is missing (the Moon: where
    it is below the horizon; the aerosol: also between clear and very hazy)."""

    cloud: Level | None
    cloud_low: Level | None
    rain: Level | None
    gust: Level | None
    wind: Level | None
    condensation: Level | None
    jet: Level | None
    seeing: Level | None
    aerosol: Level | None
    moon: Level | None
    visibility: Level | None


class WeatherHourOut(BaseModel):
    """An hour of the night, in the site's time zone, with the sky band it has, every source's
    value joined (the model's; Meteoblue's seeing in arcseconds, only with the key; CAMS aerosol
    and dust; the Moon's lit percentage while it is up) and each judged measure's word."""

    at: str
    sky: Literal["day", "civil", "nautical", "astronomical", "dark"]
    cloud_total_pct: float | None
    cloud_low_pct: float | None
    cloud_mid_pct: float | None
    cloud_high_pct: float | None
    temperature_c: float | None
    humidity_pct: float | None
    dew_point_c: float | None
    wind_kmh: float | None
    wind_gust_kmh: float | None
    precip_mm: float | None
    visibility_km: float | None
    wind_700hpa_kmh: float | None
    wind_250hpa_kmh: float | None
    seeing_arcsec: float | None
    aerosol_optical_depth: float | None
    dust_ugm3: float | None
    moon_pct: float | None
    dew_spread_c: float | None = Field(
        description="Air minus dew point, the quantity condensation is judged on."
    )
    levels: WeatherLevelsOut
    transparency: float | None = Field(
        default=None,
        description="0-100, tenths: the light the hour lets through (score v4, ADR 0034); zero "
        "when a rule blocks it, `None` without its clouds.",
    )
    exposure_hours: float | None = Field(
        default=None,
        description="The hour's Ore di posa, hundredths, weighed by its share of the window as "
        "the night's are: summed they make `exposure_hours` of the night. `None` outside the "
        "window or without clouds.",
    )
    shown: bool = Field(
        description="Whether the page draws this hour (`shown_from`-`shown_until`)."
    )
    clear: bool = Field(
        description="One of the night's clear hours, the ones `usable_hours` counts."
    )


class WeatherMoonPointOut(BaseModel):
    """The Moon at a local instant, altitude in degrees to the tenth."""

    at: str
    altitude_deg: float


class WeatherSpanOut(BaseModel):
    """An unbroken run of hours with one word: from its first to its end, and how many."""

    level: Level
    since: str
    until: str
    hours: int


class WeatherMeasureOut(BaseModel):
    """A measure over the night's window. `level` is its worst hour's word (for `cloud`, the
    verdict) and `since`/`until`/`hours` the hours with that word; `weighs` when it is marginal or
    no-go and is not the clouds, which make the verdict. `value` is the mean of the known hours
    (for `rain`, the total), `peak` the worst hour's value and when; `known_*` say which hours were
    known, so a mean over part of the night is said as such; `known_from_start`/`known_to_end`
    say whether they reach the window's first/last hour. Neutral measures have no `level`.
    `spans` gives each unbroken run of a bad word; `axis_*` is the chart's scale over the shown
    hours (`axis_curve` `sqrt`: the chart grows with the square root of the value).
    `value` is the cold at its lowest (temperature, condensation), and so the visibility.
    `estimated_from` `jet`: seeing without Meteoblue's number, its word from the jet stream's
    no-go hours, said "poor, estimated from the upper wind" (ADR 0034); no value, peak, axis or
    known hours: no seeing number is known; it does not weigh, the jet already does."""

    code: MeasureCode
    level: Level | None
    weighs: bool
    value: float | None
    peak: float | None
    peak_at: str | None
    peak_until: str | None
    spans: list[WeatherSpanOut]
    axis_min: float | None
    axis_max: float | None
    axis_curve: Literal["linear", "sqrt"]
    since: str | None
    until: str | None
    hours: int
    known_hours: int
    known_since: str | None
    known_until: str | None
    known_from_start: bool
    known_to_end: bool
    estimated_from: Literal["jet"] | None


class WeatherStepOut(BaseModel):
    """From `bound` on (beyond it when `strict`) an hour has `level`; `None`: no word."""

    level: Level | None
    bound: float
    strict: bool


class WeatherScaleOut(BaseModel):
    """A judged measure's thresholds, worst first, the same the judgement uses: an hour that
    crosses none is `go`. `lower_is_worse`: the steps count downwards (condensation)."""

    code: JudgedCode
    steps: list[WeatherStepOut]
    lower_is_worse: bool


class WeatherAgreementOut(BaseModel):
    """How many models say go, marginal, no-go, or do not know, for that night, and out of how
    many."""

    go: int
    marginal: int
    nogo: int
    unknown: int
    total: int


class WeatherSkyOut(BaseModel):
    """A night's sky as the verdict sums it up: the word, the mean cloud cover, and the usable hours
    out of the night's. `window` tells which hours were judged: the dark; where the dark never
    comes, the nautical dark (Sun below -12, ADR 0035); without that either, the arc with the Sun
    below the horizon; `None` where the Sun does not set. The
    same shape serves the forecast (Weather) and the history (Nights)."""

    verdict: Literal["go", "marginal", "nogo"] | None = Field(
        description=f"From the night's Transparency (score v4, ADR 0034): go from {GOOD_FROM:g}, "
        f"marginal from {UNCERTAIN_FROM:g}, nogo below; null without every window hour's clouds."
    )
    cloud_total_pct: float | None
    usable_hours: int | None
    window: Literal["dark", "nautical", "sun_down"] | None
    window_hours: int | None
    transparency: float | None = Field(
        default=None,
        description="0-100: the light the night let through, its window hours weighted by their "
        "minutes of dark; zero in the hours a rule blocks.",
    )
    exposure_hours: float | None = Field(
        default=None,
        description="Ore di posa: the Transparency / 100 summed over the window's hours, tenths.",
    )
    broadband_exposure_hours: float | None = Field(
        default=None, description="Of `exposure_hours`, the hours good for broadband too."
    )
    narrowband_exposure_hours: float | None = Field(
        default=None,
        description="Of `exposure_hours`, the hours with the Moon up past the Moon rule of the "
        f"Settings (factory ING, from {MOON_BRIGHT_PCT:g}%): narrowband only. The two add up "
        "to `exposure_hours`; `None` where the hours do not know the Moon (the history).",
    )
    dark_hours: float = Field(
        default=0.0,
        description="The window's length in hours, tenths: the dark, the nautical dark, or the "
        "Sun down.",
    )
    without_aerosol: bool = Field(
        default=False,
        description="Some window hour has no aerosol: the Transparency is the clouds' alone.",
    )


class WeatherBriefOut(WeatherSkyOut):
    """A forecast night in brief: its sky, the models' agreement, and the night's mean upper-air
    wind with its rank among the site's nights of the last year -- how many in ten had less
    (`None` until the site's climatology exists). It is what Tonight says."""

    agreement: WeatherAgreementOut
    usable_since: str | None
    usable_until: str | None
    wind_700hpa_kmh: float | None
    wind_700hpa_tenths: int | None
    sky_word: Literal["clear", "scattered", "broken", "overcast"] | None = Field(
        default=None,
        description="The sky in words from the mean cover in the dark, in okta classes (WMO "
        "2700): 0 clear, 1-4 scattered, 5-7 broken, 8 overcast; 0 and 8 only for a bare or full "
        "sky. `None` without the clouds.",
    )
    moonless_dark_hours: int | None = Field(
        default=None, description="Hours of dark with the Moon below the horizon."
    )
    moon_event: Literal["rise", "set", "up", "down"] | None = Field(
        default=None,
        description="The Moon over the shown hours: up at the first, it `set`s at "
        "`moon_event_at` or stays `up`; down, it `rise`s or stays `down`. `None` without them.",
    )
    moon_event_at: str | None = None
    moon_track: list[WeatherMoonPointOut] = Field(
        default_factory=list,
        description="The Moon's altitude every quarter hour over the shown hours, both ends "
        "included, for the dashed line; empty without them.",
    )
    sky_bands: list[SkyBandOut] = Field(
        default_factory=list,
        description="The Sun's bands to the minute over the shown hours, edge to edge, for the "
        "chart's twilight; written with the forecast. Empty without them.",
    )


# Repeated from `weather.events`, held equal by a test, as `MeasureCode`.
EventKind = Literal[
    "sunset", "dark_start", "dark_end", "sunrise", "verdict", "sky_unknown", "clouds_over",
    "clouds_under", "rain_start", "rain_end", "condensation", "gust_peak", "seeing_best",
    "moon_rise", "moon_set", "moon_above", "moon_below", "planet_rise", "planet_set", "planet_top",
]  # fmt: skip
EventGroup = Literal["sun", "sky", "verdict", "measure", "moon", "shooting", "planet"]


class WeatherEventOut(BaseModel):
    """One event of the night's story (step 13.1), to the minute. `value` is the event's number in
    its measure's unit (Transparency 0-100 for `verdict`, percent for the clouds and the lit Moon,
    mm, km/h, arcsec, degrees for the Moon's threshold and a planet's top); `bound` the scale's
    edge the event names (the clouds' 25 or 50 percent, the condensation's degrees of spread);
    `until` the end of the dark or of the hours without clouds;
    `level` the stretch's word, or the Moon's for `moon_above`/`moon_below`; `body` the planet."""

    at: str
    kind: EventKind
    group: EventGroup
    key_moment: bool = Field(
        description="Among the moments that matter, the phone's short list: the dark, the "
        "verdict, the Moon and where it starts or stops weighing."
    )
    level: Level | None
    value: float | None
    bound: float | None
    until: str | None
    body: Literal["saturn", "jupiter", "mars", "venus"] | None


class WeatherNightOut(WeatherBriefOut):
    """A forecast night: the summary, its measures in order of importance (the clouds, then the
    worst word earliest first, then the neutral ones), and its hours from noon to noon. `shown_*`
    is the stretch the page draws, from the last hour of day before twilight to the first after
    dawn. A `trend` night carries the summary without usable hours, measures or hours."""

    night: str
    trend: bool
    shown_from: str | None
    shown_until: str | None
    measures: list[WeatherMeasureOut]
    hours: list[WeatherHourOut]
    events: list[WeatherEventOut] = Field(
        description="The night's story from sunset to sunrise, in time order, the dark first at "
        "the same minute; written with the forecast. Empty for a trend night.",
    )


class WeatherSourceOut(BaseModel):
    """An upper-air source that wrote something, and when: the page cites it only if present, and
    the CAMS licence wants the year of the data."""

    source: str = Field(
        description="A name from `weather.sky.ALL_SOURCES`; not listed here, so the names have "
        "one home."
    )
    fetched_at: str


class WeatherSeeingOut(BaseModel):
    """Whether the user has a Meteoblue key, whether seeing is there (`meteoblue`, its only
    source, or `None`) and, with the key, how its last attempt went: `ok`, `refused`, `limited`
    (credits or requests run out, the key holds), `unreachable`, `bad_answer`, or `None` if it has
    not been asked yet for this site. `key` tells "no key" from "not asked yet", which
    `meteoblue` alone cannot."""

    key: bool
    source: Literal["meteoblue"] | None
    meteoblue: Literal["ok", "refused", "limited", "unreachable", "bad_answer"] | None


class WeatherRequestOut(BaseModel):
    """The last request for the forecast and how it went: a silent service keeps the forecast that
    was there, and the page says since when no answer came."""

    at: str
    status: Literal["ok", "unreachable", "bad_answer"]


class WeatherOut(BaseModel):
    """The next nights of the home site for the chosen model. `fetched_at` is when the site's
    latest forecast arrived, for all models together: `None` until the first one arrives. `missing`
    tells what prevents having one."""

    site: str | None
    missing: Literal["no_timezone"] | None
    model: str
    models: list[str]
    fetched_at: str | None
    last_request: WeatherRequestOut | None
    full_nights: int
    retry_s: int = Field(description="How often a silent service is asked again, in seconds.")
    seeing: WeatherSeeingOut
    sources: list[WeatherSourceOut]
    scales: list[WeatherScaleOut]
    nights: list[WeatherNightOut]


# Repeated rather than imported from `weather`, so the route contract does not change shape with
# an internal module.
RefreshStatus = Literal["ok", "no_site", "no_timezone", "unreachable", "bad_answer"]
KeyStatus = Literal["ok", "removed", "refused", "limited", "unreachable", "bad_answer"]


class WeatherRefreshOut(BaseModel):
    """How the request went: arrived, or why not."""

    status: RefreshStatus


class MeteoblueKeyIn(BaseModel):
    key: str | None


class MeteoblueKeyOut(BaseModel):
    """How it went: saved (`ok`), removed (`removed`), or why not; and the hint of the key that is
    there now."""

    status: KeyStatus
    hint: str | None
