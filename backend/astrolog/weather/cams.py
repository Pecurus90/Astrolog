"""Aerosol (550 nm) and dust from Open-Meteo Air Quality (CAMS data); `judge` reads aerosol on
NASA's scale, dust stays unjudged; a `null` hour stays unknown."""

from typing import Any

from . import openmeteo

URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
VARIABLES = {"aerosol_optical_depth": "aerosol_optical_depth", "dust": "dust_ugm3"}


def url(latitude: float, longitude: float) -> str:
    return openmeteo.url(URL, latitude, longitude, VARIABLES, past_days=1, forecast_days=7)


def parse(payload: Any) -> openmeteo.Series:
    return openmeteo.parse_single(payload, VARIABLES)
