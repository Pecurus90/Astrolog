"""L'aria dal servizio Air Quality di Open-Meteo, coi dati CAMS di Copernicus: lo spessore ottico
degli aerosol e le polveri, ora per ora, gratis e ovunque.

Vincolo non ovvio: **si mostrano come arrivano**, senza soglie: una scala "aria tersa / velata"
dall'aerosol non l'abbiamo trovata su una fonte, e non si inventa. Dove il servizio manda
`null` -- le ultime ore della previsione -- resta "non lo dice".
"""

import urllib.parse

from . import openmeteo

URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
VARIABLES = {"aerosol_optical_depth": "aerosol_optical_depth", "dust": "dust_ugm3"}


def url(latitude, longitude):
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


def parse(payload):
    """`(istanti UTC, {aerosol_optical_depth, dust_ugm3})`; `BadAnswerError` se non e' una serie."""
    return openmeteo.parse_single(payload, VARIABLES)
