"""Dove cade il vento in quota di una notte rispetto al solito del suo sito: quante notti su dieci
dell'ultimo anno ne avevano meno.

Vincolo non ovvio: **e' una posizione, non una soglia**. Non dice se la notte e' buona: dice se e'
insolita per quel posto. La distribuzione la scrive `climate.py`; qui la si legge soltanto.
"""

import json


def percentiles(conn, site):
    """I 101 percentili del vento in quota delle notti dell'ultimo anno del sito, o `None` se non
    ci sono o sono di un altro posto: un sito spostato non si confronta col solito di prima."""
    riga = conn.execute(
        "SELECT latitude, longitude, percentiles_json FROM weather_climate WHERE site_id = ?",
        (site["id"],),
    ).fetchone()
    if riga is None or (riga["latitude"], riga["longitude"]) != (
        site["latitude"],
        site["longitude"],
    ):
        return None
    return json.loads(riga["percentiles_json"])


def tenths_below(percentili, valore):
    """Quante notti su dieci avevano meno vento di `valore`, da 0 a 10."""
    sotto = sum(p < valore for p in percentili)
    return round(sotto / len(percentili) * 10)
