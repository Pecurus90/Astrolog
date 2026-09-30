"""Le pose di cui non si sa **da dove** sono state riprese, raggruppate per coordinate.

E' la casa comune fra lo stadio che le ferma (`group`, col codice `site_unclear`) e la pagina
che le chiede: la sezione dei luoghi di Da confermare legge di qui, e la risposta si scrive come
dichiarazione sulle stesse coordinate.

Vincoli non ovvi:

* **Le notti sono nel fuso DI QUELLE COORDINATE**, non in quello di casa: sono le notti di dove
  l'utente era davvero. Le ha scritte `scan` (`frames.local_night`), e qui si leggono.
* **Un posto a cui si e' gia' risposto resta in elenco**, con la risposta accanto. Un clic
  sbagliato attribuisce centinaia di pose, e senza questa riga non ci sarebbe modo di tornare
  indietro: e' la stessa lezione della seconda risposta sugli oggetti.
* **Le copie calibrate non si contano**: e' la regola di questa pagina, e una copia riscritta
  non e' un'altra posa.
"""

from ..place import coordinates_key
from . import declarations as decl
from . import group_store as store
from . import objects as obj

# Le due strade -- ferma su quel posto, o in una notte dichiarata -- si cercano ognuna col suo
# indice e si uniscono: con un `OR` fra due tabelle SQLite passerebbe da ogni posa dell'archivio.
# L'id spareggia due pose della stessa ora: le coordinate del posto sono quelle della prima, e
# senza lo spareggio dipenderebbero dal piano che SQLite sceglie.
_ROWS = f"""
SELECT f.id, f.local_night, f.site_lat, f.site_lon, {obj.SUBJECT} AS subject
FROM frames f
{obj.SUBJECT_JOIN}
WHERE f.copy_of IS NULL AND f.site_lat IS NOT NULL AND f.site_lon IS NOT NULL AND f.id IN (
  SELECT s.frame_id FROM frame_stages s
  WHERE s.stage = 'group' AND s.status = 'skipped' AND s.reason = ?
  UNION
  SELECT d.id FROM nights n JOIN frames d ON d.night_id = n.id WHERE n.site_source = 'declared')
ORDER BY f.date_obs, f.id
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente


def _rows(conn, reason):
    """Le pose che riguardano la domanda: quelle ferme, e quelle che una risposta ha gia'
    sistemato -- che restano perche' la risposta si deve poter cambiare."""
    return conn.execute(_ROWS, (reason,)).fetchall()


def unclear_coordinates(conn, reason):
    """Le coordinate su cui l'app chiede, una riga per posto e mai una per posa.

    Ognuna porta la sua chiave stabile (le coordinate arrotondate), quante pose, le notti
    coinvolte e -- se qualcuno ha gia' risposto -- il nome del sito che ha detto. Si chiede per
    coordinate e non per notte perche' la risposta e' un fatto sul posto: vale per tutte le
    notti riprese li', anche quelle che verranno."""
    gruppi = {}
    for r in _rows(conn, reason):
        chiave = coordinates_key(r["site_lat"], r["site_lon"])
        posto = gruppi.setdefault(
            chiave,
            {
                "key": chiave,
                "latitude": r["site_lat"],
                "longitude": r["site_lon"],
                "frames": 0,
                "nights": set(),
            },
        )
        posto["frames"] += 1
        obj.count_subject(posto, r["subject"], 1)
        # la notte scritta da `scan`, nel fuso **delle coordinate della posa**: qui ci sono sempre
        if r["local_night"]:
            posto["nights"].add(r["local_night"])
    return [
        {**p, "nights": sorted(p["nights"]), "site": _answered(conn, p["key"])}
        for p in obj.subjects(conn, gruppi.values())
    ]


def _answered(conn, key):
    """Il nome del sito risposto per quel posto, **solo se quel sito esiste ancora**: con la stessa
    ricerca con cui lo stadio lo ritrova (`group_store.site_by_name`). Rinominato o cancellato, la
    risposta non aggancia piu', lo stadio torna a chiedere, e la pagina e il contatore con lui."""
    detto = decl.site_for_coordinates(conn, key)
    return detto if detto and store.site_by_name(conn, detto) else None


def frames_at(conn, coordinates, reason):
    """Le pose di quel posto: sono quelle che una risposta rimette in coda. Comprese quelle che
    una risposta precedente aveva gia' sistemato, o cambiare idea non sposterebbe niente."""
    return [
        r["id"]
        for r in _rows(conn, reason)
        if coordinates_key(r["site_lat"], r["site_lon"]) == coordinates
    ]
