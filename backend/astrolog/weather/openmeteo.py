"""La previsione di Open-Meteo: piu' modelli in una chiamata sola, e la risposta letta per modello.

Vincoli non ovvi:

* **Gli orari si chiedono in UTC** e il fuso lo mette chi scrive la notte: cosi' la notte del
  cambio d'ora ha le sue 23 o 25 ore, e nessuna ora doppia.
* **Un modello che il servizio non manda resta fuori**, non si riempie: con piu' modelli la
  risposta porta `<variabile>_<modello>` per ognuno.
* Dati CC BY 4.0: la pagina scrive "Weather data by Open-Meteo.com".
"""

import urllib.parse
from datetime import UTC, datetime

from ..db import config

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Il primo e' quello che Open-Meteo sceglie per il posto, e il modello di fabbrica. L'elenco sta
# con le scelte della configurazione, che non accetta un modello che qui non si chiede.
MODELS = config.CHOICES["weather_model"]

# La variabile di Open-Meteo -> il nome nostro. Il totale delle nuvole e' quello del modello,
# mai ricalcolato dagli strati.
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
    # il jet stream: si mostra com'e', nessuna stima di seeing ne esce
    "wind_speed_250hPa": "wind_250hpa_kmh",
    "wind_speed_200hPa": "wind_200hpa_kmh",
    # il vento a circa 3.000 metri: si confronta col solito del sito, non decide niente
    "wind_speed_700hPa": "wind_700hpa_kmh",
}

# Un giorno indietro perche' prima di mezzogiorno la notte in corso e' cominciata ieri; otto
# avanti per la notte in corso e le sei o sette dopo (sette prima di mezzogiorno, quando la notte
# in corso e' quella di ieri).
PAST_DAYS = 1
FORECAST_DAYS = 8


class BadAnswerError(ValueError):
    """Il servizio ha risposto, ma non una previsione."""


def forecast_url(latitude, longitude):
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


def parse(payload):
    """`(istanti UTC, {modello: {nome nostro: [valori]}})`: gli orari sono uno per tutti i modelli.
    `BadAnswerError` se non e' una previsione."""
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
        if all(isinstance(v, list) and len(v) == len(istanti) for v in serie.values()):
            letto[modello] = serie
    return istanti, letto


def parse_single(payload, variables):
    """`(istanti UTC, {nome nostro: [valori]})` di una risposta con una serie sola, senza modelli
    (l'archivio, l'aria di CAMS). `BadAnswerError` se non e' una serie oraria completa."""
    hourly = payload.get("hourly") if isinstance(payload, dict) else None
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise BadAnswerError("manca la serie oraria")
    try:
        istanti = [datetime.fromisoformat(t).replace(tzinfo=UTC) for t in hourly["time"]]
    except (TypeError, ValueError) as err:
        raise BadAnswerError("orari illeggibili") from err
    serie = {nostro: hourly.get(loro) for loro, nostro in variables.items()}
    if not all(isinstance(v, list) and len(v) == len(istanti) for v in serie.values()):
        raise BadAnswerError("serie incomplete")
    return istanti, serie
