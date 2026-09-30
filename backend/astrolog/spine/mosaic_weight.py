"""Quanto pesa un pannello nel suo mosaico: conta solo se regge una parte del lavoro.

Un pannello nasce sulla sola geometria (`mosaic.place`), e dopo un giro al meridiano non
ricentrato poche pose spostate ne aprono un secondo, che sembrava un mosaico. Un mosaico vero ha
pannelli ripresi a lungo tutti: la pratica e' lo stesso tempo su ogni pannello, perche' con tempi
diversi il rumore cambia da un pannello all'altro e le giunzioni si vedono (Astrophotography
Magazine, *Mosaic Images*; Smart Scope Tonight, *Mosaic Mode Explained*; Chaotic Nebula,
l'articolo sulla fusione dei pannelli per gradiente).

Vincoli non ovvi:

* **La soglia e' il 25% del pannello piu' lungo** (Marco, 27/9/2026): nessuna fonte da' un numero,
  e il 25% e' dove il rumore di una pila, che scende come la radice del tempo, e' il doppio.
* **Si pesa il tempo, e le pose solo se il tempo non si sa**: basta una posa muta nel mosaico, e
  si contano le pose di tutti, o un pannello di pose mute peserebbe zero.
* **Lo scrive chi piazza o stacca le pose** (`mosaic.settle`), sui mosaici in cui le pose sono
  arrivate o da cui se ne sono andate, e chi legge guarda la colonna (`panels.counts_in_mosaic`).
"""

import json

MIN_SHARE = 0.25

# Il lavoro di ogni pannello dei mosaici chiesti: il tempo, le pose, e quante non dicono il tempo.
_WORK = """
SELECT p.id, p.mosaic_id, COUNT(f.id) AS frames, COALESCE(SUM(f.exposure_s), 0) AS seconds,
       SUM(f.exposure_s IS NULL) AS untimed
FROM panels p JOIN frames f ON f.panel_id = p.id AND f.copy_of IS NULL
WHERE p.mosaic_id IN (SELECT value FROM json_each(?))
GROUP BY p.id
"""


def weigh(conn, mosaic_ids):
    """Scrive su ogni pannello di quei mosaici se conta: almeno `MIN_SHARE` del lavoro del pannello
    piu' lungo dello stesso mosaico."""
    per_mosaico = {}
    for r in conn.execute(_WORK, (json.dumps(sorted(mosaic_ids)),)):
        per_mosaico.setdefault(r["mosaic_id"], []).append(r)
    for pannelli in per_mosaico.values():
        misura = "untimed" if any(p["untimed"] for p in pannelli) else "seconds"
        lavoro = {p["id"]: p["frames"] if misura == "untimed" else p["seconds"] for p in pannelli}
        soglia = MIN_SHARE * max(lavoro.values())
        conn.executemany(
            "UPDATE panels SET counts_in_mosaic = ? WHERE id = ?",
            [(int(peso >= soglia), pid) for pid, peso in lavoro.items()],
        )
