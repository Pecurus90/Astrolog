"""Every weather number may be missing, and missing means "the model does not say", never zero:
the verdict is missing without cloud cover, the window when the Sun does not set."""

from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["go", "marginal", "nogo"]
# Repeated rather than imported from `weather.judge`, so the route contract does not change shape
# with an internal module; a test holds the two lists equal.
MeasureCode = Literal[
    "cloud", "cloud_low", "rain", "gust", "wind", "condensation", "jet", "seeing", "aerosol",
    "moon", "cloud_mid", "cloud_high", "humidity", "temperature", "dew_point", "wind_700",
    "wind_200", "dust",
]  # fmt: skip
JudgedCode = Literal[
    "cloud", "cloud_low", "rain", "gust", "wind", "condensation", "jet", "seeing", "aerosol", "moon"
]


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
    wind_700hpa_kmh: float | None
    wind_250hpa_kmh: float | None
    wind_200hpa_kmh: float | None
    seeing_arcsec: float | None
    aerosol_optical_depth: float | None
    dust_ugm3: float | None
    moon_pct: float | None
    dew_spread_c: float | None = Field(
        description="Air minus dew point, the quantity condensation is judged on."
    )
    levels: WeatherLevelsOut
    shown: bool = Field(
        description="Whether the page draws this hour (`shown_from`-`shown_until`)."
    )
    clear: bool = Field(
        description="One of the night's clear hours, the ones `usable_hours` counts."
    )


class WeatherSpanOut(BaseModel):
    """The hours with one word: from the first to the end of the last, and how many."""

    level: Level
    since: str
    until: str
    hours: int


class WeatherMeasureOut(BaseModel):
    """A measure over the night's window. `level` is its worst hour's word (for `cloud`, the
    verdict) and `since`/`until`/`hours` the hours with that word; `weighs` when it is marginal or
    no-go and is not the clouds, which make the verdict. `value` is the mean of the known hours
    (for `rain`, the total), `peak` the worst hour's value and when; `known_*` say which hours were
    known, so a mean over part of the night is said as such. Neutral measures have no `level`.
    `spans` gives each bad word its hours; `axis_*` is the chart's scale over the shown hours.
    `value` is the cold at its lowest (temperature, condensation), the damp at its highest."""

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
    since: str | None
    until: str | None
    hours: int
    known_hours: int
    known_since: str | None
    known_until: str | None


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
    out of the night's. `window` tells which hours were judged: the dark, or -- where the dark
    never comes -- the arc with the Sun below the horizon; `None` where the Sun does not set. The
    same shape serves the forecast (Weather) and the history (Nights)."""

    verdict: Literal["go", "marginal", "nogo"] | None
    cloud_total_pct: float | None
    usable_hours: int | None
    window: Literal["dark", "sun_down"] | None
    window_hours: int | None


class WeatherBriefOut(WeatherSkyOut):
    """A forecast night in brief: its sky, the models' agreement, and the night's mean upper-air
    wind with its rank among the site's nights of the last year -- how many in ten had less
    (`None` until the site's climatology exists). It is what Tonight says."""

    agreement: WeatherAgreementOut
    usable_since: str | None
    usable_until: str | None
    wind_700hpa_kmh: float | None
    wind_700hpa_tenths: int | None


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
    source, or `None`) and, with the key, how its last attempt went: `ok`, `refused`,
    `unreachable`, `bad_answer`, or `None` if it has not been asked yet for this site. `key` tells
    "no key" from "not asked yet", which `meteoblue` alone cannot."""

    key: bool
    source: Literal["meteoblue"] | None
    meteoblue: Literal["ok", "refused", "unreachable", "bad_answer"] | None


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
    seeing: WeatherSeeingOut
    sources: list[WeatherSourceOut]
    scales: list[WeatherScaleOut]
    nights: list[WeatherNightOut]


# Repeated rather than imported from `weather`, so the route contract does not change shape with
# an internal module.
RefreshStatus = Literal["ok", "no_site", "no_timezone", "unreachable", "bad_answer"]
KeyStatus = Literal["ok", "removed", "refused", "unreachable", "bad_answer"]


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
