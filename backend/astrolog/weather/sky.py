"""Chi scrive il cielo in quota: chiede a ogni fonte, divide le sue ore in notti, e le scrive nelle
righe di quella fonte. Il vento in quota no: arriva coi modelli, nella previsione.

Vincolo non ovvio: **ogni fonte e' per conto suo**. Una che tace, o risponde storto, tiene le sue
righe di prima e non ferma le altre; e nessuna tocca le righe della previsione.
"""

import json
import logging
import zoneinfo
from datetime import UTC, datetime

from .. import net
from ..clock import iso_z, night_date
from ..db import config
from . import cams, meteoblue, nights, seventimer
from .forecast import BAD_ANSWER, KIND, OK, UNREACHABLE, write_rows
from .openmeteo import BadAnswerError

log = logging.getLogger(__name__)

# La fonte, e come la si chiede e la si legge. Il nome e' quello che finisce nelle righe.
SOURCES = {"7timer": seventimer, "cams": cams}
# Tutte le fonti del cielo. Il seeing di una notte viene da una sola: Meteoblue quando c'e'.
ALL_SOURCES = (*SOURCES, meteoblue.SOURCE)

# La chiamata vera: un nome di questo modulo, cosi' le prove delle rotte la sostituiscono qui.
_fetch = net.fetch


def _scrivi(conn, site, nome, parse, risposta, adesso):  # noqa: PLR0913
    """Legge la risposta di una fonte e scrive le sue notti: l'esito."""
    try:
        tempi, serie = parse(risposta)
    except BadAnswerError:
        log.info(
            "meteo: una fonte del cielo non ha risposto una previsione", extra={"source": nome}
        )
        return BAD_ANSWER
    fuso = zoneinfo.ZoneInfo(site["timezone"])
    in_corso = night_date(iso_z(adesso), site["timezone"])
    righe = []
    for data, coppie in nights.covered(site["timezone"], tempi, in_corso, whole=False):
        ore = nights.hours(serie, coppie, fuso)
        if not nights.empty(ore):
            righe.append((site["id"], data, KIND, nome, iso_z(adesso), json.dumps(ore), None))
    if not righe:
        log.info("meteo: una fonte del cielo non porta nessuna notte", extra={"source": nome})
        return BAD_ANSWER
    write_rows(conn, site["id"], [nome], righe)
    return OK


def _una(conn, site, nome, fonte, fetch, adesso):  # noqa: PLR0913
    risposta = net.ask(fetch, fonte.url(site["latitude"], site["longitude"]))
    if risposta is None:
        return UNREACHABLE
    return _scrivi(conn, site, nome, fonte.parse, risposta, adesso)


def _meteoblue(conn, site, fetch, adesso):
    """Il seeing Meteoblue, se c'e' la chiave e se tocca: l'esito, scritto col suo tentativo."""
    chiave = config.read(conn)["meteoblue_key"]
    if not chiave or not meteoblue.due(conn, site["id"], adesso):
        return None
    risposta, perche = net.ask_why(
        fetch, meteoblue.url(site["latitude"], site["longitude"], chiave)
    )
    esito = perche or _scrivi(conn, site, meteoblue.SOURCE, meteoblue.parse, risposta, adesso)
    if esito == meteoblue.REFUSED:
        meteoblue.drop_seeing(conn)
    meteoblue.record(conn, site["id"], esito, adesso)
    return esito


def refresh(conn, site, *, fetch=None, now=None):
    """Chiede ogni fonte del cielo per il sito e scrive le sue righe: `{fonte: esito}`. Meteoblue
    c'e' solo quando e' stato chiesto."""
    adesso = now or datetime.now(UTC)
    esiti = {
        nome: _una(conn, site, nome, fonte, fetch or _fetch, adesso)
        for nome, fonte in SOURCES.items()
    }
    esito = _meteoblue(conn, site, fetch or _fetch, adesso)
    if esito is not None:
        esiti[meteoblue.SOURCE] = esito
    return esiti
