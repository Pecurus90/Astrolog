"""Open-Meteo forecast: several models in one call, read per model. Times are asked in UTC so the
clock-change night has its 23 or 25 hours and no doubled hour."""

import urllib.parse
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from ..db import config

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# The first is Open-Meteo's own pick for the place, and the default. The list lives with the
# config choices, which refuse a model not asked here.
MODELS = config.CHOICES["weather_model"]

# Open-Meteo variable -> our name. Total cloud is the model's, never recomputed from the layers.
VARIABLES = {
    "cloud_cover": "cloud_total_pct",
    "cloud_cover_low": "cloud_low_pct",
    "cloud_cover_mid": "cloud_mid_pct",
    "cloud_cover_high": "cloud_high_pct",
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "dew_point_2m": "dew_point_c",
    "wind_speed_10m": "wind_kmh",
    "wind_gusts_10m": "wind_gust_kmh",
    "precipitation": "precip_mm",
    # the jet stream: shown as it is, no seeing estimate comes out of it
    "wind_speed_250hPa": "wind_250hpa_kmh",
    "wind_speed_200hPa": "wind_200hpa_kmh",
    # wind at about 3,000 m: compared with the site's usual, it decides nothing
    "wind_speed_700hPa": "wind_700hpa_kmh",
}

# One day back because before noon the night under way began yesterday; eight ahead for it and
# the six or seven after.
PAST_DAYS = 1
FORECAST_DAYS = 8

# A single-series reading: the instants, and each quantity's values by our name.
type Series = tuple[list[datetime], dict[str, list[Any]]]


class BadAnswerError(ValueError):
    """The service answered, but not a forecast."""


def url(base: str, latitude: float, longitude: float, hourly: Iterable[str], **params: Any) -> str:
    """Every Open-Meteo service: the place, the hourly quantities in UTC, then its own `params`."""
    query = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(hourly),
        "timezone": "UTC",
        **params,
    }
    return f"{base}?{urllib.parse.urlencode(query)}"


def forecast_url(latitude: float, longitude: float) -> str:
    return url(
        FORECAST_URL,
        latitude,
        longitude,
        VARIABLES,
        models=",".join(MODELS),
        past_days=PAST_DAYS,
        forecast_days=FORECAST_DAYS,
    )


def _hourly(payload: Any) -> tuple[dict[str, Any], list[datetime]]:
    """The hourly block and its instants."""
    hourly = payload.get("hourly") if isinstance(payload, dict) else None
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise BadAnswerError("manca la serie oraria")
    try:
        instants = [datetime.fromisoformat(t).replace(tzinfo=UTC) for t in hourly["time"]]
    except (TypeError, ValueError) as err:
        raise BadAnswerError("orari illeggibili") from err
    return hourly, instants


def parse(payload: Any) -> tuple[list[datetime], dict[str, dict[str, list[Any]]]]:
    """One time axis for every model."""
    hourly, instants = _hourly(payload)
    read = {}
    for model in MODELS:
        series = {ours: hourly.get(f"{theirs}_{model}") for theirs, ours in VARIABLES.items()}
        # a model the service did not send stays out, never filled in
        if all(isinstance(v, list) and len(v) == len(instants) for v in series.values()):
            read[model] = series
    return instants, read


def parse_single(payload: Any, variables: Mapping[str, str]) -> Series:
    """An answer with a single series and no models (the archive, CAMS air)."""
    hourly, instants = _hourly(payload)
    series: dict[str, Any] = {ours: hourly.get(theirs) for theirs, ours in variables.items()}
    if not all(isinstance(v, list) and len(v) == len(instants) for v in series.values()):
        raise BadAnswerError("serie incomplete")
    return instants, series
