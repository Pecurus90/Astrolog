"""La forma di cio' che l'app dice sul meteo delle prossime notti.

Vincolo non ovvio: **ogni numero puo' mancare, e mancare vuol dire "il modello non lo dice"**, mai
zero. Il verdetto manca quando manca la copertura, la finestra quando il Sole non tramonta.
"""

from typing import Literal

from pydantic import BaseModel


class WeatherFactorOut(BaseModel):
    """Un motivo che pesa sulla notte: il valore, la soglia che supera, e quando morde. `hours`
    accanto a `since`/`until` dice se la finestra e' piena o a tratti."""

    code: Literal["rain", "cloud_low", "cloud", "gust", "condensation"]
    value: float
    threshold: float
    since: str | None
    until: str | None
    hours: int


class WeatherHourOut(BaseModel):
    """Un'ora della notte, nel fuso del sito, col cielo che ha in quel momento."""

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
    """Un'ora del cielo in quota: il vento a 700, 250 e 200 hPa del modello scelto; il seeing come
    intervallo -- le fasce di 7Timer, o il valore di Meteoblue coi due estremi uguali, quando c'e'
    la chiave -- e la trasparenza di 7Timer (un estremo aperto e' `None`, e tutti e due `None`
    vuol dire che per quell'ora la fonte non dice niente); l'aerosol e le polveri di CAMS."""

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
    """Quanti modelli dicono si fa, incerta, no, o non lo sanno, per quella notte, e su quanti."""

    go: int
    marginal: int
    nogo: int
    unknown: int
    total: int


class WeatherSkyOut(BaseModel):
    """Il cielo di una notte, come lo riassume il verdetto: la parola, la copertura media, e le ore
    utili su quelle della notte. `window` dice su quali ore si e' giudicato: il buio, o -- dove il
    buio non arriva -- l'arco col Sole sotto l'orizzonte; `None` dove il Sole non tramonta. E' la
    stessa forma per la previsione (Meteo) e per lo storico (Notti)."""

    verdict: Literal["go", "marginal", "nogo"] | None
    cloud_total_pct: float | None
    usable_hours: int | None
    window: Literal["dark", "sun_down"] | None
    window_hours: int | None


class WeatherBriefOut(WeatherSkyOut):
    """Una notte della previsione in breve: il suo cielo, l'accordo dei modelli, e il vento in quota
    medio della notte col suo posto fra le notti dell'ultimo anno del sito -- quante su dieci ne
    avevano meno (`None` finche' la climatologia del sito non c'e'). E' cio' che dice Stanotte."""

    agreement: WeatherAgreementOut
    wind_700hpa_kmh: float | None
    wind_700hpa_tenths: int | None


class WeatherNightOut(WeatherBriefOut):
    """Una notte della previsione: il riassunto, i fattori, e le sue ore da mezzogiorno a
    mezzogiorno. Una notte di `trend` porta il riassunto senza ore utili: niente fattori, niente
    ore ne' cielo in quota."""

    night: str
    trend: bool
    factors: list[WeatherFactorOut]
    hours: list[WeatherHourOut]
    aloft: list[WeatherAloftOut]


class WeatherSourceOut(BaseModel):
    """Una fonte del cielo in quota che ha scritto qualcosa, e quando: la pagina la cita solo se
    c'e', e la licenza di CAMS vuole l'anno dei dati."""

    source: str  # un nome di `weather.sky.SOURCES`: scritto qui, sarebbe una seconda casa
    fetched_at: str


class WeatherSeeingOut(BaseModel):
    """Da dove viene il seeing (`meteoblue`, `7timer`, o `None` se da nessuna parte) e, quando c'e'
    la chiave Meteoblue, com'e' andato il suo ultimo tentativo: `ok`, `refused`, `unreachable`,
    `bad_answer`, o `None` se non si e' ancora chiesto."""

    source: Literal["meteoblue", "7timer"] | None
    meteoblue: Literal["ok", "refused", "unreachable", "bad_answer"] | None


class WeatherOut(BaseModel):
    """Le prossime notti del sito di casa per il modello scelto. `fetched_at` e' l'ora in cui e'
    arrivata l'ultima previsione del sito, per tutti i modelli insieme: `None` finche' non ne e'
    arrivata nessuna. `missing` dice cosa impedisce di averne una."""

    site: str | None
    missing: Literal["no_timezone"] | None
    model: str
    models: list[str]
    fetched_at: str | None
    full_nights: int
    seeing: WeatherSeeingOut
    sources: list[WeatherSourceOut]
    nights: list[WeatherNightOut]


class WeatherRefreshOut(BaseModel):
    """Com'e' andata la richiesta: arrivata, o perche' no."""

    status: Literal["ok", "no_site", "no_timezone", "unreachable", "bad_answer"]
