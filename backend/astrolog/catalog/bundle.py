"""A missing or unreadable catalogue file is a missing catalogue, not an exception: the app works
without one, and `/api/health` says so with zero `catalog_entries`."""

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DATA = Path(__file__).with_name("data")


def path() -> Path | None:
    """Two files in the folder are a fault, not a choice: loading the first in alphabetical order
    would silently use an old catalogue."""
    found = sorted(DATA.glob("catalogo-*.json"))
    if not found:
        log.warning("catalogo: nessun file in %s", DATA)
        return None
    if len(found) > 1:
        log.error("catalogo: piu' di un file in %s: %s", DATA, [p.name for p in found])
        return None
    return found[0]


def read(file: str | Path | None = None) -> tuple[str | None, list[dict[str, Any]]]:
    file = file if file is not None else path()
    if file is None:
        return None, []
    try:
        data = json.loads(Path(file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        log.error("catalogo: non si e' potuto leggere %s: %s", file, err)
        return None, []
    entries = data.get("objects") or []
    version = data.get("version")
    if not version or not entries:
        log.error("catalogo: %s non ha versione o non ha voci", file)
        return None, []
    return version, entries
