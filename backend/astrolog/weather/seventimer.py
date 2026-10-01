"""7Timer ASTRO: keyless seeing and transparency from GFS, for the first nights and not hourly.
Bands stay bands: a number inside one would be a measurement the service never made."""

import urllib.parse
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from .openmeteo import BadAnswerError

URL = "https://www.7timer.info/bin/api.pl"

type FromTo = tuple[float | None, float | None]

# Seeing in arcsec and transparency in mag per airmass, bands 1..8, an open end as `None`
# (https://www.7timer.info/doc.php?lang=en).
SEEING_ARCSEC = (
    (None, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, 1.25),
    (1.25, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, None),
)  # fmt: skip
TRANSPARENCY_MAG = (
    (None, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6),
    (0.6, 0.7), (0.7, 0.85), (0.85, 1.0), (1.0, None),
)  # fmt: skip

__all__ = ["URL", "BadAnswerError", "parse", "url"]


def url(latitude: float, longitude: float) -> str:
    query = urllib.parse.urlencode(
        {
            "lat": round(latitude, 3),
            "lon": round(longitude, 3),
            "product": "astro",
            "output": "json",
        }
    )
    return f"{URL}?{query}"


def _fascia(scala: Sequence[FromTo], valore: Any) -> FromTo:
    return (
        scala[valore - 1] if isinstance(valore, int) and 1 <= valore <= len(scala) else (None, None)
    )


def parse(payload: Any) -> tuple[list[datetime], dict[str, list[Any]]]:
    """Instants are rebuilt from the run (`init`, UTC) plus each entry's `timepoint` hours."""
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
