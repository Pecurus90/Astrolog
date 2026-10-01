"""Nights of a service's hourly series, noon to noon in the site's timezone. Whole or not depends
on the source: one not sampling every hour (7Timer) would never have a whole night."""

import zoneinfo
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

from ..clock import night_window
from ..ephemeris import sun

# A night's date and its hours as `(index in the series, instant)`.
type Night = tuple[str, list[tuple[int, datetime]]]


def covered(timezone: str, tempi: Sequence[datetime], dalla: str, *, whole: bool) -> list[Night]:
    """From `dalla` on. `whole` stops at the first incomplete night; otherwise a night enters with
    whatever hours the series has."""
    if not tempi:
        return []
    indice = {t: i for i, t in enumerate(tempi)}
    notti = []
    giorno = date.fromisoformat(dalla)
    while True:
        comincia, quante = night_window(giorno.isoformat(), timezone)
        istanti = [comincia.astimezone(UTC) + timedelta(hours=h) for h in range(round(quante))]
        coppie = [(indice[t], t) for t in istanti if t in indice]
        if whole and len(coppie) < len(istanti):
            return notti
        if not whole and istanti[0] > tempi[-1]:
            return notti
        if coppie:
            notti.append((giorno.isoformat(), coppie))
        giorno += timedelta(days=1)


def hours(
    serie: Mapping[str, Sequence[Any]],
    coppie: Sequence[tuple[int, datetime]],
    fuso: zoneinfo.ZoneInfo,
    **per_istante: Mapping[datetime, Any],
) -> list[dict[str, Any]]:
    """Each `per_istante` map adds a field looked up by instant (the sky, for the forecast)."""
    ore = []
    for i, istante in coppie:
        riga = {"at": istante.astimezone(fuso).isoformat()}
        riga.update({nome: mappa[istante] for nome, mappa in per_istante.items()})
        riga.update({nome: valori[i] for nome, valori in serie.items()})
        ore.append(riga)
    return ore


def empty(ore: Sequence[Mapping[str, Any]]) -> bool:
    """No hour carries a value: such a night is not written."""
    return all(v is None for o in ore for k, v in o.items() if k not in ("at", "sky"))


def sky(latitude: float, longitude: float, notti: Sequence[Night]) -> dict[datetime, str]:
    """Every hour's sky band in a single ephemeris call."""
    istanti = [t for _, coppie in notti for _, t in coppie]
    fasce = sun.sky_at(istanti, latitude, longitude)
    return {t: fasce[i] for i, t in enumerate(istanti)}
