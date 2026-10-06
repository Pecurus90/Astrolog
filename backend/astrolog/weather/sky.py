"""Writes the sky aloft per source; the upper wind arrives with the models, in the forecast. Each
source is on its own: a silent or broken one keeps its old rows and stops none of the others."""

import json
import logging
import sqlite3
import zoneinfo
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from types import ModuleType
from typing import Any, cast

from .. import net
from ..clock import iso_z, night_date
from ..db import config
from . import cams, meteoblue, nights, seventimer
from .forecast import BAD_ANSWER, KIND, OK, UNREACHABLE, write_rows
from .openmeteo import BadAnswerError

log = logging.getLogger(__name__)

type Parse = Callable[[Any], tuple[list[datetime], dict[str, list[Any]]]]

# The source's name as written in its rows -> the module that asks and reads it.
SOURCES = {"7timer": seventimer, "cams": cams}
# Every sky source; the reader takes a night's seeing from Meteoblue when it is there, else 7Timer.
ALL_SOURCES = (*SOURCES, meteoblue.SOURCE)

# The real call, named in this module so the route tests replace it here.
_fetch = net.fetch


def _scrivi(  # noqa: PLR0913
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    nome: str,
    parse: Parse,
    risposta: Any,
    adesso: datetime,
) -> str:
    try:
        tempi, serie = parse(risposta)
    except BadAnswerError:
        log.info(
            "meteo: una fonte del cielo non ha risposto una previsione", extra={"source": nome}
        )
        return BAD_ANSWER
    fuso = zoneinfo.ZoneInfo(site["timezone"])
    in_corso = cast("str", night_date(iso_z(adesso), site["timezone"]))  # a valid instant and zone
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


def _una(  # noqa: PLR0913
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    nome: str,
    fonte: ModuleType,
    fetch: net.Fetch,
    adesso: datetime,
) -> str:
    risposta = net.ask(fetch, fonte.url(site["latitude"], site["longitude"]))
    if risposta is None:
        return UNREACHABLE
    return _scrivi(conn, site, nome, fonte.parse, risposta, adesso)


def _meteoblue(
    conn: sqlite3.Connection, site: Mapping[str, Any], fetch: net.Fetch, adesso: datetime
) -> str | None:
    """The outcome, recorded with its attempt; `None` without a key or before it is due."""
    chiave = config.read(conn).meteoblue_key
    if not chiave or not meteoblue.due(conn, site["id"], adesso):
        return None
    risposta, perche = net.ask_why(
        fetch, meteoblue.url(site["latitude"], site["longitude"], chiave)
    )
    esito = perche or _scrivi(conn, site, meteoblue.SOURCE, meteoblue.parse, risposta, adesso)
    # only a refusal speaks of the key; a silence keeps the seeing it gave last time
    if esito == meteoblue.REFUSED:
        meteoblue.drop_seeing(conn)
    meteoblue.record(conn, site["id"], esito, adesso)
    return esito


def refresh(
    conn: sqlite3.Connection,
    site: Mapping[str, Any],
    *,
    fetch: net.Fetch | None = None,
    now: datetime | None = None,
) -> dict[str, str]:
    """`{source: outcome}`; Meteoblue is there only when it was asked."""
    adesso = now or datetime.now(UTC)
    esiti = {
        nome: _una(conn, site, nome, fonte, fetch or _fetch, adesso)
        for nome, fonte in SOURCES.items()
    }
    esito = _meteoblue(conn, site, fetch or _fetch, adesso)
    if esito is not None:
        esiti[meteoblue.SOURCE] = esito
    return esiti
