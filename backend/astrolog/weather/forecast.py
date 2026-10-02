"""Writes the forecast: asks the service, splits the hours into nights and writes each night per
model with its summary already made, so the page's model switch only reads."""

import json
import logging
import sqlite3
import zoneinfo
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Final, Literal, TypeGuard, cast

from .. import net
from ..clock import iso_z, night_date
from ..db.replace_table import replace_rows
from . import nights, openmeteo, position, verdict

log = logging.getLogger(__name__)

# Global models run every six hours; every three catches each run within a few hours of release.
REFRESH_EVERY_S = 3 * 3600
# Sooner after a failed round, but not every minute: a NAS without network would hammer the
# service for nothing.
RETRY_S = 15 * 60

type Outcome = Literal["ok", "no_site", "no_timezone", "unreachable", "bad_answer"]
OK: Final = "ok"
NO_SITE: Final = "no_site"
NO_TIMEZONE: Final = "no_timezone"
UNREACHABLE: Final = net.UNREACHABLE
BAD_ANSWER: Final = "bad_answer"

KIND = "forecast"

# The real call, named in this module so the route tests replace it here.
_fetch = net.fetch


def source_of(model: str) -> str:
    return f"open-meteo/{model}"


def _accordo(verdetti: Iterable[str | None]) -> dict[str, int]:
    """How many models say go, marginal, nogo or do not know, and out of how many."""
    conta = {"go": 0, "marginal": 0, "nogo": 0, "unknown": 0}
    for v in verdetti:
        conta[v or "unknown"] += 1
    return {**conta, "total": sum(conta.values())}


def write_rows(
    conn: sqlite3.Connection, site_id: int, sources: Sequence[str], righe: Iterable[Sequence[Any]]
) -> None:
    """All or nothing for these sources of the site: other sources, other sites and the observed
    weather stay."""
    segnaposto = ", ".join("?" * len(sources))  # segnaposto-ok: the sources, the caller's constants
    replace_rows(
        conn,
        "weather_nights",
        ("site_id", "night_date", "kind", "source", "fetched_at", "hourly_json", "summary_json"),
        righe,
        where=f"site_id = ? AND kind = ? AND source IN ({segnaposto})",
        args=(site_id, KIND, *sources),
    )


def refresh(  # noqa: C901
    conn: sqlite3.Connection,
    site: Mapping[str, Any] | None,
    *,
    fetch: net.Fetch | None = None,
    now: datetime | None = None,
) -> Outcome:
    """Asks the forecast for the site and writes it; a code says how it went. A silent or nightless
    answer deletes nothing: the previous forecast stays with its time."""
    if site is None:
        return NO_SITE
    if not site["timezone"]:
        return NO_TIMEZONE
    risposta = net.ask(fetch or _fetch, openmeteo.forecast_url(site["latitude"], site["longitude"]))
    if risposta is None:
        return UNREACHABLE  # `net` already logged the silence
    try:
        tempi, modelli = openmeteo.parse(risposta)
    except openmeteo.BadAnswerError:
        log.info("meteo: il servizio non ha risposto una previsione")
        return BAD_ANSWER
    adesso = now or datetime.now(UTC)
    in_corso = cast("str", night_date(iso_z(adesso), site["timezone"]))  # a valid instant and zone
    fuso = zoneinfo.ZoneInfo(site["timezone"])
    scritto = iso_z(adesso)
    # Whole nights only: beyond the model's horizon, better no night than half a night.
    notti = nights.covered(site["timezone"], tempi, in_corso, whole=True)
    if not notti:
        log.info("meteo: la risposta non porta nessuna notte intera")
        return BAD_ANSWER
    cielo = nights.sky(site["latitude"], site["longitude"], notti)
    percentili = position.percentiles(conn, site)
    scritte: list[tuple[str, str, list[dict[str, Any]], dict[str, Any]]] = []
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
    # A night's agreement is the same in every model and written in each, so a reader of one model
    # need not read the others.
    for data in {d for d, *_ in scritte}:
        detti = [r["verdict"] for d, _, _, r in scritte if d == data]
        # a model that wrote nothing that night does not know; it is not one model fewer
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
    """When the background round is due: at once for a new or changed home site, then every
    `every_s`, sooner after a failure. A site without timezone is not hurried like a failure."""

    def __init__(self, every_s: float) -> None:
        self.every_s = every_s
        self._fatto_per: tuple[Any, ...] | None = None
        self._prossimo = 0.0

    def due(self, site: Mapping[str, Any] | None, adesso: float) -> TypeGuard[Mapping[str, Any]]:
        if site is None:
            return False
        return self._chiave(site) != self._fatto_per or adesso >= self._prossimo

    def done(self, site: Mapping[str, Any], esito: str, adesso: float) -> None:
        self._fatto_per = self._chiave(site)
        attesa = self.every_s if esito in (OK, NO_TIMEZONE) else min(self.every_s, RETRY_S)
        self._prossimo = adesso + attesa

    @staticmethod
    def _chiave(site: Mapping[str, Any]) -> tuple[Any, ...]:
        return (site["id"], site["latitude"], site["longitude"], site["timezone"])
