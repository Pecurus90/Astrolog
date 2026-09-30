"""Chi scrive la previsione: chiede al servizio, divide le ore in notti, e scrive ogni notte per
ogni modello col suo riassunto gia' fatto.

Vincoli non ovvi:

* **Chi legge non ricalcola**: verdetto, fattori e ore utili si scrivono qui, per ogni modello,
  e lo switch della pagina legge soltanto.
* **Un servizio che tace non cancella niente**, e nemmeno uno che risponde senza una notte intera:
  la previsione di prima resta con la sua ora, e chi ha chiesto riceve il perche' come codice.
* **Si riscrive la previsione di quel sito e basta**: gli altri siti e il meteo osservato restano.
* **Una notte si scrive solo intera**: da mezzogiorno a mezzogiorno nel fuso del sito, tutte le
  sue ore nella risposta. Oltre l'orizzonte del modello meglio nessuna notte che una a meta'.
"""

import json
import logging
import zoneinfo
from datetime import UTC, datetime

from .. import net
from ..clock import iso_z, night_date
from ..db.replace_table import replace_rows
from . import nights, openmeteo, position, verdict

log = logging.getLogger(__name__)

# Ogni quanto la previsione si rinnova da sola: i modelli globali escono ogni sei ore, e tre
# prendono ogni uscita entro poche ore da quando e' pronta.
REFRESH_EVERY_S = 3 * 3600
# Dopo un giro andato male si riprova prima del giro pieno, ma non a ogni minuto: un NAS senza rete
# martellerebbe il servizio per niente.
RETRY_S = 15 * 60

OK = "ok"
NO_SITE = "no_site"
NO_TIMEZONE = "no_timezone"
UNREACHABLE = net.UNREACHABLE
BAD_ANSWER = "bad_answer"

KIND = "forecast"

# La chiamata vera: un nome di questo modulo, cosi' le prove delle rotte la sostituiscono qui.
_fetch = net.fetch


def source_of(model):
    return f"open-meteo/{model}"


def _accordo(verdetti):
    """Quanti modelli dicono si fa, incerta, no, o non lo sanno, e su quanti."""
    conta = {"go": 0, "marginal": 0, "nogo": 0, "unknown": 0}
    for v in verdetti:
        conta[v or "unknown"] += 1
    return {**conta, "total": sum(conta.values())}


def write_rows(conn, site_id, sources, righe):
    """Riscrive le righe previste di queste fonti per il sito, tutto o niente: le altre fonti, gli
    altri siti e il meteo osservato restano."""
    segnaposto = ", ".join("?" * len(sources))  # segnaposto-ok: le fonti, costanti di chi chiama
    replace_rows(
        conn,
        "weather_nights",
        ("site_id", "night_date", "kind", "source", "fetched_at", "hourly_json", "summary_json"),
        righe,
        where=f"site_id = ? AND kind = ? AND source IN ({segnaposto})",
        args=(site_id, KIND, *sources),
    )


def refresh(conn, site, *, fetch=None, now=None):  # noqa: C901
    """Chiede la previsione per il sito e la scrive; torna un codice che dice com'e' andata."""
    if site is None:
        return NO_SITE
    if not site["timezone"]:
        return NO_TIMEZONE
    risposta = net.ask(fetch or _fetch, openmeteo.forecast_url(site["latitude"], site["longitude"]))
    if risposta is None:
        return UNREACHABLE  # il servizio muto lo scrive gia' `net` nel log
    try:
        tempi, modelli = openmeteo.parse(risposta)
    except openmeteo.BadAnswerError:
        log.info("meteo: il servizio non ha risposto una previsione")
        return BAD_ANSWER
    adesso = now or datetime.now(UTC)
    in_corso = night_date(iso_z(adesso), site["timezone"])
    fuso = zoneinfo.ZoneInfo(site["timezone"])
    scritto = iso_z(adesso)
    notti = nights.covered(site["timezone"], tempi, in_corso, whole=True)
    if not notti:
        log.info("meteo: la risposta non porta nessuna notte intera")
        return BAD_ANSWER
    # Il cielo di ogni ora in una chiamata sola, per tutte le notti e tutti i modelli.
    cielo = nights.sky(site["latitude"], site["longitude"], notti)
    percentili = position.percentiles(conn, site)
    scritte = []  # (data, modello, ore, riassunto)
    for modello, serie in modelli.items():
        for data, coppie in notti:
            ore = nights.hours(serie, coppie, fuso, sky=cielo)
            if not nights.empty(ore):
                riassunto = verdict.assess(ore)
                vento = riassunto["wind_700hpa_kmh"]
                riassunto["wind_700hpa_tenths"] = (
                    position.tenths_below(percentili, vento)
                    if percentili and vento is not None
                    else None
                )
                scritte.append((data, modello, ore, riassunto))
    if not scritte:
        log.info("meteo: la risposta porta solo ore vuote")
        return BAD_ANSWER
    # L'accordo di una notte e' uguale in ogni modello, e si scrive in ognuno: chi legge un modello
    # solo non deve leggere gli altri per contarlo.
    for data in {d for d, *_ in scritte}:
        detti = [r["verdict"] for d, _, _, r in scritte if d == data]
        # un modello che quella notte non ha scritto niente e' uno che non lo sa, non uno in meno
        accordo = _accordo(detti + [None] * (len(modelli) - len(detti)))
        for d, _, _, riassunto in scritte:
            if d == data:
                riassunto["agreement"] = accordo
    righe = [
        (site["id"], d, KIND, source_of(m), scritto, json.dumps(o), json.dumps(r))
        for d, m, o, r in scritte
    ]
    write_rows(conn, site["id"], [source_of(m) for m in openmeteo.MODELS], righe)
    return OK


class Cadence:
    """Quando tocca al giro in sottofondo: appena c'e' un sito di casa o cambia, poi ogni
    `every_s`, e prima dopo un giro andato male. Un sito senza fuso non si riprova: resta senza
    finche' qualcuno non lo corregge, e correggerlo cambia il sito."""

    def __init__(self, every_s):
        self.every_s = every_s
        self._fatto_per = None
        self._prossimo = 0.0

    def due(self, site, adesso):
        if site is None:
            return False
        return self._chiave(site) != self._fatto_per or adesso >= self._prossimo

    def done(self, site, esito, adesso):
        self._fatto_per = self._chiave(site)
        attesa = self.every_s if esito in (OK, NO_TIMEZONE) else min(self.every_s, RETRY_S)
        self._prossimo = adesso + attesa

    @staticmethod
    def _chiave(site):
        return (site["id"], site["latitude"], site["longitude"], site["timezone"])
