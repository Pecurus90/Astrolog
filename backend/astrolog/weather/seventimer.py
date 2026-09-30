"""7Timer ASTRO: il seeing e la trasparenza senza chiave, dal modello GFS, per le prime notti e non
ogni ora. Servizio volontario, e si cita.

Vincolo non ovvio: **arrivano in otto fasce, e restano fasce**. Ogni fascia diventa l'intervallo
che la documentazione del servizio le da' (https://www.7timer.info/doc.php?lang=en), con l'estremo
aperto a `None`: un numero in mezzo alla fascia sarebbe una misura che il servizio non ha fatto.
"""

import urllib.parse
from datetime import UTC, datetime, timedelta

from .openmeteo import BadAnswerError

URL = "https://www.7timer.info/bin/api.pl"

# seeing in arcosecondi e trasparenza in magnitudini per massa d'aria, fascia 1..8
SEEING_ARCSEC = (
    (None, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, 1.25),
    (1.25, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, None),
)  # fmt: skip
TRANSPARENCY_MAG = (
    (None, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6),
    (0.6, 0.7), (0.7, 0.85), (0.85, 1.0), (1.0, None),
)  # fmt: skip

__all__ = ["URL", "BadAnswerError", "parse", "url"]


def url(latitude, longitude):
    query = urllib.parse.urlencode(
        {
            "lat": round(latitude, 3),
            "lon": round(longitude, 3),
            "product": "astro",
            "output": "json",
        }
    )
    return f"{URL}?{query}"


def _fascia(scala, valore):
    return (
        scala[valore - 1] if isinstance(valore, int) and 1 <= valore <= len(scala) else (None, None)
    )


def parse(payload):
    """`(istanti UTC, {seeing_from, seeing_to, transparency_from, transparency_to})`. Gli istanti
    si ricostruiscono dal run (`init`, in UTC) e dalle ore di ogni voce (`timepoint`)."""
    serie = payload.get("dataseries") if isinstance(payload, dict) else None
    if not isinstance(serie, list):
        raise BadAnswerError("manca la serie ASTRO")
    try:
        run = datetime.strptime(str(payload.get("init")), "%Y%m%d%H").replace(tzinfo=UTC)
    except ValueError as err:
        raise BadAnswerError("run illeggibile") from err
    voci = [v for v in serie if isinstance(v, dict) and isinstance(v.get("timepoint"), int)]
    seeing = [_fascia(SEEING_ARCSEC, v.get("seeing")) for v in voci]
    trasparenza = [_fascia(TRANSPARENCY_MAG, v.get("transparency")) for v in voci]
    return [run + timedelta(hours=v["timepoint"]) for v in voci], {
        "seeing_from": [s[0] for s in seeing],
        "seeing_to": [s[1] for s in seeing],
        "transparency_from": [t[0] for t in trasparenza],
        "transparency_to": [t[1] for t in trasparenza],
    }
