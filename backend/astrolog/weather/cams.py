"""Aerosol and dust from Open-Meteo Air Quality (CAMS data), shown as they arrive: no sourced scale
for clear or hazy air was found, so none is invented; a `null` hour stays unknown."""

import urllib.parse
from datetime import datetime
from typing import Any

from . import openmeteo

URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
VARIABLES = {"aerosol_optical_depth": "aerosol_optical_depth", "dust": "dust_ugm3"}


def url(latitude: float, longitude: float) -> str:
    query = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(VARIABLES),
            "timezone": "UTC",
            "past_days": 1,
            "forecast_days": 7,
        }
    )
    return f"{URL}?{query}"


def parse(payload: Any) -> tuple[list[datetime], dict[str, list[Any]]]:
    return openmeteo.parse_single(payload, VARIABLES)
