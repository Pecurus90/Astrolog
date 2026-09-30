"""Il file del catalogo impacchettato: dove sta, che versione ha, cosa contiene.

Vincolo non ovvio: legge e basta, non decide niente e non tocca il database. Un file che
manca o non si capisce non e' un'eccezione da propagare fino all'avvio dell'app: e' un
catalogo che non c'e', e l'app senza catalogo funziona lo stesso -- cataloga, cerca, mostra
le ore. Non sa dire cosa hai fotografato, e `/api/health` lo dichiara con `catalog_entries`
a zero.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

DATA = Path(__file__).with_name("data")


def path():
    """Il catalogo impacchettato, o `None` se non c'e'.

    Due file in cartella sono un guasto e non una scelta: si caricherebbe il primo in ordine
    alfabetico, che e' un modo silenzioso di usare un catalogo vecchio."""
    found = sorted(DATA.glob("catalogo-*.json"))
    if not found:
        log.warning("catalogo: nessun file in %s", DATA)
        return None
    if len(found) > 1:
        log.error("catalogo: piu' di un file in %s: %s", DATA, [p.name for p in found])
        return None
    return found[0]


def read(file=None) -> tuple[str | None, list[dict]]:
    """`(versione, voci)` dal file, o `(None, [])` se non si e' potuto leggere."""
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
