"""Open-Meteo forecast: several models in one call, read per model. Times are asked in UTC so the
clock-change night has its 23 or 25 hours and no doubled hour."""

import urllib.parse
from collections.abc import Mapping
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


class BadAnswerError(ValueError):
    """The service answered, but not a forecast."""


def forecast_url(latitude: float, longitude: float) -> str:
    query = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(VARIABLES),
            "models": ",".join(MODELS),
            "timezone": "UTC",
            "past_days": PAST_DAYS,
            "forecast_days": FORECAST_DAYS,
        }
    )
    return f"{FORECAST_URL}?{query}"


def parse(payload: Any) -> tuple[list[datetime], dict[str, dict[str, list[Any]]]]:
    """One time axis for every model."""
    hourly = payload.get("hourly") if isinstance(payload, dict) else None
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise BadAnswerError("manca la serie oraria")
    tempi = hourly["time"]
    try:
        istanti = [datetime.fromisoformat(t).replace(tzinfo=UTC) for t in tempi]
    except (TypeError, ValueError) as err:
        raise BadAnswerError("orari illeggibili") from err
    letto = {}
    for modello in MODELS:
        serie = {nostro: hourly.get(f"{loro}_{modello}") for loro, nostro in VARIABLES.items()}
        # a model the service did not send stays out, never filled in
        if all(isinstance(v, list) and len(v) == len(istanti) for v in serie.values()):
            letto[modello] = serie
    return istanti, letto


def parse_single(
    payload: Any, variables: Mapping[str, str]
) -> tuple[list[datetime], dict[str, list[Any]]]:
    """An answer with a single series and no models (the archive, CAMS air)."""
    hourly = payload.get("hourly") if isinstance(payload, dict) else None
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise BadAnswerError("manca la serie oraria")
    try:
        istanti = [datetime.fromisoformat(t).replace(tzinfo=UTC) for t in hourly["time"]]
    except (TypeError, ValueError) as err:
        raise BadAnswerError("orari illeggibili") from err
    serie: dict[str, Any] = {nostro: hourly.get(loro) for loro, nostro in variables.items()}
    if not all(isinstance(v, list) and len(v) == len(istanti) for v in serie.values()):
        raise BadAnswerError("serie incomplete")
    return istanti, serie
