"""Every weather number may be missing, and missing means "the model does not say", never zero:
the verdict is missing without cloud cover, the window when the Sun does not set."""

from typing import Literal

from pydantic import BaseModel, Field


class WeatherFactorOut(BaseModel):
    """A reason that weighs on the night: the value, the threshold it exceeds, and when it bites.
    `hours` next to `since`/`until` tells whether the window is full or patchy."""

    code: Literal["rain", "cloud_low", "cloud", "gust", "condensation"]
    value: float
    threshold: float
    since: str | None
    until: str | None
    hours: int


class WeatherHourOut(BaseModel):
    """An hour of the night, in the site's time zone, with the sky it has at that moment."""

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


class WeatherAloftOut(BaseModel):
    """An hour of the upper air: the wind at 700, 250 and 200 hPa from the chosen model; seeing as
    a range -- 7Timer's bands, or Meteoblue's value with both ends equal, when the key is there --
    and 7Timer's transparency (an open end is `None`, and both `None` means the source says nothing
    for that hour); aerosol and dust from CAMS."""

    at: str
    wind_700hpa_kmh: float | None
    wind_250hpa_kmh: float | None
    wind_200hpa_kmh: float | None
    seeing_from: float | None
    seeing_to: float | None
    transparency_from: float | None
    transparency_to: float | None
    aerosol_optical_depth: float | None
    dust_ugm3: float | None


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
    wind_700hpa_kmh: float | None
    wind_700hpa_tenths: int | None


class WeatherNightOut(WeatherBriefOut):
    """A forecast night: the summary, the factors, and its hours from noon to noon. A `trend`
    night carries the summary without usable hours: no factors, no hours, no upper air."""

    night: str
    trend: bool
    factors: list[WeatherFactorOut]
    hours: list[WeatherHourOut]
    aloft: list[WeatherAloftOut]


class WeatherSourceOut(BaseModel):
    """An upper-air source that wrote something, and when: the page cites it only if present, and
    the CAMS licence wants the year of the data."""

    source: str = Field(
        description="A name from `weather.sky.ALL_SOURCES`; not listed here, so the names have "
        "one home."
    )
    fetched_at: str


class WeatherSeeingOut(BaseModel):
    """Where seeing comes from (`meteoblue`, `7timer`, or `None` if nowhere) and, when the
    Meteoblue key is there, how its last attempt went: `ok`, `refused`, `unreachable`,
    `bad_answer`, or `None` if it has not been asked yet."""

    source: Literal["meteoblue", "7timer"] | None
    meteoblue: Literal["ok", "refused", "unreachable", "bad_answer"] | None


class WeatherOut(BaseModel):
    """The next nights of the home site for the chosen model. `fetched_at` is when the site's
    latest forecast arrived, for all models together: `None` until the first one arrives. `missing`
    tells what prevents having one."""

    site: str | None
    missing: Literal["no_timezone"] | None
    model: str
    models: list[str]
    fetched_at: str | None
    full_nights: int
    seeing: WeatherSeeingOut
    sources: list[WeatherSourceOut]
    nights: list[WeatherNightOut]


# Repeated rather than imported from `weather`, so the route contract does not change shape with
# an internal module.
RefreshStatus = Literal["ok", "no_site", "no_timezone", "unreachable", "bad_answer"]


class WeatherRefreshOut(BaseModel):
    """How the request went: arrived, or why not."""

    status: RefreshStatus
