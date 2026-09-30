"""Lo storico: il meteo vero delle notti che hai ripreso, dall'archivio di Open-Meteo.

Vincoli non ovvi:

* **Definitivo dopo 5 giorni**: l'archivio unisce il modello ECMWF, subito, con la rianalisi ERA5,
  che arriva 5 giorni dopo (https://open-meteo.com/en/docs/historical-weather-api). Una notte
  aspetta finche' il suo **mattino** non ha cinque giorni, e una notte scritta non si riscrive.
* **Una chiamata per giro**, un sito alla volta e al massimo un anno: un archivio di anni si
  riempie in pochi minuti senza martellare il servizio. Un giro andato male aspetta prima di
  riprovare, e l'attesa e' scritta (`weather_fetches`), cosi' regge ai riavvii.
* **Il meteo di una notte e' quello del suo sito**; un sito senza fuso non ha notti da dividere.
"""

import json
import logging
import urllib.parse
import zoneinfo
from datetime import UTC, date, datetime, timedelta

from .. import net
from ..clock import iso_z, night_date
from . import fetches, forecast, nights, openmeteo, verdict

log = logging.getLogger(__name__)

URL = "https://archive-api.open-meteo.com/v1/archive"
SOURCE = "open-meteo/archive"
KIND = "observed"
DELAY_DAYS = 5
MAX_DAYS = 366

# Le stesse grandezze della previsione, senza il vento in quota: l'archivio non lo porta.
VARIABLES = {k: v for k, v in openmeteo.VARIABLES.items() if "hPa" not in k}

# La chiamata vera: un nome di questo modulo, cosi' le prove la sostituiscono qui.
_fetch = net.fetch

_MANCANTI = """
SELECT n.site_id, n.night_date, s.latitude, s.longitude, s.timezone
FROM nights n JOIN sites s ON s.id = n.site_id
WHERE s.timezone IS NOT NULL AND NOT EXISTS (
  SELECT 1 FROM weather_nights w
  WHERE w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
)
ORDER BY n.site_id, n.night_date
"""


def _url(site, dal, al):
    query = urllib.parse.urlencode(
        {
            "latitude": site["latitude"],
            "longitude": site["longitude"],
            "start_date": dal.isoformat(),
            "end_date": al.isoformat(),
            "hourly": ",".join(VARIABLES),
            "timezone": "UTC",
        }
    )
    return f"{URL}?{query}"


def parse(payload):
    """`(istanti UTC, {nome nostro: [valori]})`: una serie sola, senza modelli."""
    return openmeteo.parse_single(payload, VARIABLES)


def _in_attesa(conn, site_id, adesso):
    """Un giro andato male da poco: si aspetta prima di richiedere lo stesso sito."""
    ultimo = fetches.last(conn, site_id, SOURCE)
    if ultimo is None or ultimo["status"] == forecast.OK:
        return False
    return fetches.age(ultimo, adesso) < timedelta(seconds=forecast.RETRY_S)


def _da_chiedere(conn, adesso):
    """Il primo sito con notti di piu' di 5 giorni senza meteo, e quelle notti: `(sito, [date])`."""
    per_sito = {}
    for r in conn.execute(_MANCANTI, (KIND,)):
        oggi = night_date(iso_z(adesso), r["timezone"])
        # la notte finisce il mattino dopo: e' quel mattino che deve avere cinque giorni
        if (
            oggi is None
            or r["night_date"]
            >= (date.fromisoformat(oggi) - timedelta(days=DELAY_DAYS)).isoformat()
        ):
            continue
        per_sito.setdefault(r["site_id"], (dict(r), []))[1].append(r["night_date"])
    for site_id, (sito, date_) in per_sito.items():
        if not _in_attesa(conn, site_id, adesso):
            return sito, date_
    return None, []


def step(conn, *, fetch=None, now=None):
    """Un giro dello storico: una chiamata al massimo. L'esito, o `None` se non c'era niente da
    chiedere (o si sta aspettando dopo un giro andato male)."""
    adesso = now or datetime.now(UTC)
    sito, date_ = _da_chiedere(conn, adesso)
    if sito is None:
        return None
    dal = date.fromisoformat(date_[0])
    # fino all'ultima notte che serve, mai oltre un anno: l'archivio rifiuta i giorni futuri
    fino = min(dal + timedelta(days=MAX_DAYS - 1), date.fromisoformat(date_[-1]))
    volute = {d for d in date_ if date.fromisoformat(d) <= fino}
    # un giorno prima e due dopo in UTC: la notte va da mezzogiorno a mezzogiorno nel fuso del sito
    risposta, perche = net.ask_why(
        fetch or _fetch, _url(sito, dal - timedelta(days=1), fino + timedelta(days=2))
    )
    esito = perche or _scrivi(conn, sito, volute, risposta, adesso)
    fetches.record(conn, sito["site_id"], SOURCE, esito, adesso)
    return esito


def _scrivi(conn, sito, volute, risposta, adesso):
    try:
        tempi, serie = parse(risposta)
    except openmeteo.BadAnswerError:
        log.info("meteo: l'archivio non ha risposto una serie", extra={"site_id": sito["site_id"]})
        return forecast.BAD_ANSWER
    notti = [
        n
        for n in nights.covered(sito["timezone"], tempi, min(volute), whole=True)
        if n[0] in volute
    ]
    if not notti:
        log.info("meteo: l'archivio non copre le notti chieste", extra={"site_id": sito["site_id"]})
        return forecast.BAD_ANSWER
    cielo = nights.sky(sito["latitude"], sito["longitude"], notti)
    fuso = zoneinfo.ZoneInfo(sito["timezone"])
    scritto = iso_z(adesso)
    righe = []
    for data, coppie in notti:
        ore = nights.hours(serie, coppie, fuso, sky=cielo)
        righe.append(
            (
                sito["site_id"],
                data,
                KIND,
                SOURCE,
                scritto,
                json.dumps(ore),
                json.dumps(verdict.assess(ore)),
            )
        )
    # Lo storico e' definitivo: una notte gia' scritta non si tocca.
    conn.executemany(
        "INSERT INTO weather_nights(site_id, night_date, kind, source, fetched_at, hourly_json,"
        " summary_json) VALUES(?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
        righe,
    )
    return forecast.OK
