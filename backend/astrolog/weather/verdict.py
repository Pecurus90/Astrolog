"""A night's verdict and the factors behind it. The verdict looks only at total cover, the one
quantity that blocks every object alike; the rest are factors beside it, not a single score."""

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any

from ..ephemeris.sun import Sky

type Hour = dict[str, Any]
type Bites = Callable[[Hour], bool]

# Okta (WMO Code Table 2700) as METAR classes (ICAO Annex 3): go to FEW 2/8, marginal to SCT 4/8.
# https://www.nodc.noaa.gov/archive/arc0021/0000907/1.1/data/0-data/HTML/WMO-CODE/WMO2700.HTM
CLOUD_GO_MAX_PCT = 25.0
CLOUD_MARGINAL_MAX_PCT = 50.0
# Beaufort force 5, "fresh breeze": 8.0-10.7 m/s, that is 29-38 km/h.
# https://en.wikipedia.org/wiki/Beaufort_scale
GUST_KMH = 29.0
# Aviation rule: under 5 F (3 C) between temperature and dew point, expect fog.
# FAA, Aviation Weather Handbook (FAA-H-8083-28).
CONDENSATION_SPREAD_C = 3.0

SUN_DOWN = "sun_down"

# Most severe first: rain ends the session, low cloud blocks, total cloud veils, gusts shake the
# rig, condensation is fought with a dew heater.
_ORDINE = ("rain", "cloud_low", "cloud", "gust", "condensation")


def window(ore: Sequence[Hour]) -> tuple[list[Hour], str | None]:
    """The dark, else the hours with the Sun below the horizon, and which of the two; none where
    the Sun never sets. Afternoon clouds never weigh on the night."""
    buie = [o for o in ore if o["sky"] == Sky.DARK]
    if buie:
        return buie, Sky.DARK
    giu = [o for o in ore if o["sky"] != "day"]
    return (giu, SUN_DOWN) if giu else ([], None)


def _valori(ore: Sequence[Hour], campo: str) -> list[Any]:
    return [o[campo] for o in ore if o.get(campo) is not None]


def _media(valori: Sequence[float]) -> float | None:
    return round(sum(valori) / len(valori), 1) if valori else None


def _quando(
    ore: Sequence[Hour], morde: Bites, dopo: Mapping[str, str]
) -> tuple[str | None, str | None, int]:
    """Start of the first hit hour, end of the last, and the count, so a patchy window does not
    look full. The end is the next hour of the night, not +60 min: clocks jump on change night."""
    colpite = [o["at"] for o in ore if morde(o)]
    if not colpite:
        return None, None, 0
    ultima = colpite[-1]
    fine = dopo.get(ultima) or (datetime.fromisoformat(ultima) + timedelta(hours=1)).isoformat()
    return colpite[0], fine, len(colpite)


def _fattore(  # noqa: PLR0913
    code: str,
    value: float,
    threshold: float,
    ore: Sequence[Hour],
    morde: Bites,
    dopo: Mapping[str, str],
) -> dict[str, Any]:
    since, until, hours = _quando(ore, morde, dopo)
    return {
        "code": code,
        "value": value,
        "threshold": threshold,
        "since": since,
        "until": until,
        "hours": hours,
    }


def _con(campo: str, test: Callable[[Any], bool]) -> Bites:
    return lambda o: o.get(campo) is not None and test(o[campo])


def _spread(o: Hour) -> float | None:
    if o.get("temperature_c") is None or o.get("dew_point_c") is None:
        return None
    return o["temperature_c"] - o["dew_point_c"]


def _factors(ore: Sequence[Hour], dopo: Mapping[str, str]) -> list[dict[str, Any]]:
    fattori = []
    pioggia = _valori(ore, "precip_mm")
    if sum(pioggia) > 0:
        fattori.append(
            _fattore(
                "rain", round(sum(pioggia), 1), 0.0, ore, _con("precip_mm", lambda v: v > 0), dopo
            )
        )
    for code, campo in (("cloud_low", "cloud_low_pct"), ("cloud", "cloud_total_pct")):
        media = _media(_valori(ore, campo))
        if media is not None and media > CLOUD_GO_MAX_PCT:
            fattori.append(
                _fattore(
                    code,
                    media,
                    CLOUD_GO_MAX_PCT,
                    ore,
                    _con(campo, lambda v: v > CLOUD_GO_MAX_PCT),
                    dopo,
                )
            )
    raffiche = _valori(ore, "wind_gust_kmh")
    if raffiche and max(raffiche) >= GUST_KMH:
        fattori.append(
            _fattore(
                "gust",
                round(max(raffiche), 1),
                GUST_KMH,
                ore,
                _con("wind_gust_kmh", lambda v: v >= GUST_KMH),
                dopo,
            )
        )
    temp, rugiada = _media(_valori(ore, "temperature_c")), _media(_valori(ore, "dew_point_c"))
    if temp is not None and rugiada is not None and temp - rugiada < CONDENSATION_SPREAD_C:
        fattori.append(
            _fattore(
                "condensation",
                round(temp - rugiada, 1),
                CONDENSATION_SPREAD_C,
                ore,
                lambda o: (s := _spread(o)) is not None and s < CONDENSATION_SPREAD_C,
                dopo,
            )
        )
    return sorted(fattori, key=lambda f: _ORDINE.index(f["code"]))


def _verdict(nuvole: float | None) -> str | None:
    if nuvole is None:
        return None
    if nuvole <= CLOUD_GO_MAX_PCT:
        return "go"
    return "marginal" if nuvole <= CLOUD_MARGINAL_MAX_PCT else "nogo"


def assess(ore: Sequence[Hour]) -> dict[str, Any]:
    """Verdict and usable hours are `None` unless every night hour reports `cloud_total_pct`.
    Usable hours are the night's hours the verdict would call clear, so the two never disagree."""
    notte, finestra = window(ore)
    dopo = {o["at"]: p["at"] for o, p in zip(ore, ore[1:], strict=False)}
    copertura: list[Any] = [o.get("cloud_total_pct") for o in notte]
    completa = bool(notte) and None not in copertura
    nuvole = _media([c for c in copertura if c is not None]) if completa else None
    return {
        "verdict": _verdict(nuvole),
        "cloud_total_pct": nuvole,
        "usable_hours": sum(c <= CLOUD_GO_MAX_PCT for c in copertura) if completa else None,
        "window": finestra,
        "window_hours": len(notte),
        "wind_700hpa_kmh": _media(_valori(notte, "wind_700hpa_kmh")),
        "factors": _factors(notte, dopo),
    }
