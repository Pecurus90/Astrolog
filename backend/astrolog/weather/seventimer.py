"""7Timer ASTRO: keyless seeing and transparency from GFS, for the first nights and not hourly.
Bands stay bands: a number inside one would be a measurement the service never made."""

import urllib.parse
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from .openmeteo import BadAnswerError, Series

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


def _band(scale: Sequence[FromTo], value: Any) -> FromTo:
    return scale[value - 1] if isinstance(value, int) and 1 <= value <= len(scale) else (None, None)


def parse(payload: Any) -> Series:
    """Instants are rebuilt from the run (`init`, UTC) plus each entry's `timepoint` hours."""
    series = payload.get("dataseries") if isinstance(payload, dict) else None
    if not isinstance(series, list):
        raise BadAnswerError("manca la serie ASTRO")
    try:
        run = datetime.strptime(str(payload.get("init")), "%Y%m%d%H").replace(tzinfo=UTC)
    except ValueError as err:
        raise BadAnswerError("run illeggibile") from err
    entries = [e for e in series if isinstance(e, dict) and isinstance(e.get("timepoint"), int)]
    seeing = [_band(SEEING_ARCSEC, e.get("seeing")) for e in entries]
    transparency = [_band(TRANSPARENCY_MAG, e.get("transparency")) for e in entries]
    return [run + timedelta(hours=e["timepoint"]) for e in entries], {
        "seeing_from": [s[0] for s in seeing],
        "seeing_to": [s[1] for s in seeing],
        "transparency_from": [t[0] for t in transparency],
        "transparency_to": [t[1] for t in transparency],
    }
