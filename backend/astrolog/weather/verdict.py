"""Il verdetto di una notte e i fattori che lo decidono, dalle sue ore.

Vincoli non ovvi:

* **La notte e' il buio** (Sole sotto i diciotto gradi). Dove il buio non arriva -- d'estate al
  nord -- e' l'arco col Sole sotto l'orizzonte, e lo si dice; dove il Sole non tramonta non c'e'
  verdetto. Le nuvole del pomeriggio non tolgono la notte.
* **Il verdetto guarda solo la copertura totale**: e' l'unica grandezza che blocca ogni soggetto
  allo stesso modo. Gli altri motivi sono fattori accanto, non un voto unico.
* **Le soglie sono convenzioni pubbliche**, con la fonte accanto al numero. Le prove ne tengono
  i confini (`tests/test_weather_verdict.py`).
"""

from datetime import datetime, timedelta

from ..ephemeris.sun import BUIO

# Okta, cioe' ottavi di cielo (WMO Code Table 2700, colonna in okta) e classi dei METAR (ICAO
# Annex 3): FEW 1-2 okta, SCT 3-4, BKN 5-7. Si fa fino a 2/8 = 25%, incerta fino a 4/8 = 50%, no
# oltre. La colonna in decimi della stessa tabella e' un'altra scala, per chi osserva in decimi.
# https://www.nodc.noaa.gov/archive/arc0021/0000907/1.1/data/0-data/HTML/WMO-CODE/WMO2700.HTM
CLOUD_GO_MAX_PCT = 25.0
CLOUD_MARGINAL_MAX_PCT = 50.0
# Beaufort, forza 5 ("fresh breeze"): 8,0-10,7 m/s, cioe' 29-38 km/h -- la scala che si legge in
# km/h. https://en.wikipedia.org/wiki/Beaufort_scale
GUST_KMH = 29.0
# Regola aeronautica: sotto i 5 gradi Fahrenheit (3 Celsius) fra temperatura e rugiada, aspettati
# nebbia. FAA, Aviation Weather Handbook (FAA-H-8083-28).
CONDENSATION_SPREAD_C = 3.0

SUN_DOWN = "sun_down"

# Dal piu' grave: la pioggia chiude la serata, le nuvole basse bloccano, il totale vela, la raffica
# fa vibrare, la condensa si combatte con una fascia anticondensa.
_ORDINE = ("rain", "cloud_low", "cloud", "gust", "condensation")


def window(ore):
    """Le ore della notte e come le si e' scelte: il buio, o il Sole sotto l'orizzonte."""
    buie = [o for o in ore if o["sky"] == BUIO]
    if buie:
        return buie, BUIO
    giu = [o for o in ore if o["sky"] != "day"]
    return (giu, SUN_DOWN) if giu else ([], None)


def _valori(ore, campo):
    return [o[campo] for o in ore if o.get(campo) is not None]


def _media(valori):
    return round(sum(valori) / len(valori), 1) if valori else None


def _quando(ore, morde, dopo):
    """Quando un fattore morde: l'inizio della prima ora colpita, la **fine** dell'ultima, e quante
    sono. Il conteggio accanto dice se la finestra e' piena o a tratti: "dalle 20 alle 23" con due
    ore vuol dire che in mezzo ce n'e' una libera. La fine e' l'ora che viene dopo nella notte, non
    l'ultima piu' sessanta minuti: la notte del cambio d'ora l'orologio a muro salta."""
    colpite = [o["at"] for o in ore if morde(o)]
    if not colpite:
        return None, None, 0
    ultima = colpite[-1]
    fine = dopo.get(ultima) or (datetime.fromisoformat(ultima) + timedelta(hours=1)).isoformat()
    return colpite[0], fine, len(colpite)


def _fattore(code, value, threshold, ore, morde, dopo):  # noqa: PLR0913
    since, until, hours = _quando(ore, morde, dopo)
    return {
        "code": code,
        "value": value,
        "threshold": threshold,
        "since": since,
        "until": until,
        "hours": hours,
    }


def _con(campo, test):
    return lambda o: o.get(campo) is not None and test(o[campo])


def _spread(o):
    if o.get("temperature_c") is None or o.get("dew_point_c") is None:
        return None
    return o["temperature_c"] - o["dew_point_c"]


def _factors(ore, dopo):
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


def _verdict(nuvole):
    if nuvole is None:
        return None
    if nuvole <= CLOUD_GO_MAX_PCT:
        return "go"
    return "marginal" if nuvole <= CLOUD_MARGINAL_MAX_PCT else "nogo"


def assess(ore):
    """Il riassunto della notte: verdetto, copertura media, ore utili, fattori, e su quali ore.

    Il verdetto e le ore utili sono `None` quando manca la copertura: senza il dato che decide
    non si inventa una parola. Le ore utili sono le ore della notte che il verdetto direbbe
    serene, cosi' "notte buona" e "ore utili" non possono contraddirsi."""
    notte, finestra = window(ore)
    dopo = {o["at"]: p["at"] for o, p in zip(ore, ore[1:], strict=False)}
    copertura = [o.get("cloud_total_pct") for o in notte]
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
