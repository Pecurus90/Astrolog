"""I mosaici come Da confermare li mostra: letti, mai calcolati.

Vincoli non ovvi:

* **Qui non c'e' geometria** (una lettura non calcola, Marco, 22/9/2026): pannelli e mosaici li
  scrive `spine/mosaic.py`, e il contratto degli import vieta a chi legge di importarla.
* **Si risponde con la chiave del mosaico**, che non cambia quando cambia la camera: un gruppo
  risposto resta in pagina, perche' si deve poter cambiare idea.
"""

from . import counts
from . import declarations as decl
from . import object_answer as risposta
from . import objects as obj

# I mosaici che lo sono ancora: piu' di un pannello con pose, contando solo i pannelli che
# reggono una parte del lavoro (`mosaic_weight`). Un pannello solo e' un soggetto ripreso
# normalmente. E' la regola di chi legge, di chi risponde e di chi pulisce le chiavi.
LIVE = """
SELECT p.mosaic_id, COUNT(DISTINCT f.panel_id) AS panels
FROM panels p JOIN frames f ON f.panel_id = p.id AND f.copy_of IS NULL
WHERE p.mosaic_id IS NOT NULL AND p.counts_in_mosaic = 1
GROUP BY p.mosaic_id HAVING COUNT(DISTINCT f.panel_id) > 1
"""

_MOSAICS = f"""
SELECT m.id, m.key, m.ra_deg, m.dec_deg, m.proposed, d.value, r.panels,
       {counts.counts_on("proposal")}
FROM mosaics m
JOIN ({LIVE}) r ON r.mosaic_id = m.id
LEFT JOIN declarations d ON d.entity_type = ? AND d.entity_key = m.key AND d.field = ?
ORDER BY m.id
"""  # noqa: S608 - frammenti costanti

# I soggetti dei pannelli: ogni pannello inquadra una parte diversa del complesso, e l'app li
# identifica come oggetti diversi.
_SUBJECTS = obj.subjects_sql(
    "p.mosaic_id",
    "panels p JOIN frames f ON f.panel_id = p.id",
    "AND p.mosaic_id IS NOT NULL AND p.counts_in_mosaic = 1",
)


def candidates(conn):
    """I mosaici, dal piu' vecchio, con la risposta gia' data e il nome detto dall'utente. Le
    chiavi sono quelle della pagina (`MosaicCandidate`)."""
    soggetti = obj.subjects_of(conn.execute(_SUBJECTS))
    righe = []
    for r in conn.execute(_MOSAICS, (decl.MOSAIC, decl.MOSAIC_FIELD)):
        valore = r["value"]
        parola = risposta.mosaic_word(valore)
        detto = risposta.shown_target(conn, valore) if parola == decl.MOSAIC_YES else None
        nomi = soggetti.get(r["id"], [])
        righe.append(
            {
                "key": r["key"],
                "ra_deg": r["ra_deg"],
                "dec_deg": r["dec_deg"],
                "object": obj.together(nomi),
                "panels": r["panels"],
                "frames": r["frames"],
                "integration_s": r["integration_s"],
                "untimed": r["untimed"],
                "answer": parola,
                "answer_name": None if detto is None else detto[2],
                "names": sorted({*nomi, r["proposed"]} - {""}),
                "proposed": r["proposed"],
            }
        )
    return righe
