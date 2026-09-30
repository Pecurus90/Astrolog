"""Le **notti** dell'archivio in lettura: quando hai ripreso, da dove, e cosa hai fatto.

Le scrive `group` (`nights` e `sessions`); qui si leggono, per la pagina Notti. Un fatto, una
casa: i tre numeri di una riga vengono da `counts`, gli stessi dell'Archivio, e il residuo della
spina da `stages`, lo stesso della scansione.

Vincoli non ovvi:

* **Una notte e' una data PIU' un sito**, ed e' una riga sola: gli oggetti e i filtri stanno
  dentro, non la moltiplicano. Moltiplicarla spezzerebbe le ore fra le righe, e due righe con la
  stessa data sembrerebbero un doppione.
* **Oggetti e filtri costano due query per PAGINA, non per riga**: si chiedono per le notti che
  si stanno mostrando, tutte insieme.
* **Le pose ferme si contano per DOVE si risponde**, non per motivo: i cinque codici arrivano da
  `group`, che e' chi li scrive -- ricopiarli qui sarebbe la stessa regola in due case -- e
  diventano tre gesti -- una domanda di *Da confermare*, il sito da dichiarare, o niente da
  rispondere -- e il conto lo fa questa casa, perche' e' un conto e non una forma da dare a
  schermo.
"""

import json

from ..clock import midnight_of
from ..db import idlist
from ..ephemeris import moon
from . import counts, filters_used, stages
from . import objects as obj
from .group import (
    NO_ACTIVE_SITE,
    NO_DATE,
    NO_OBJECT,
    SITE_NO_TIMEZONE,
    SITE_UNCLEAR,
)

# Dove si risponde a una posa che nessuna notte ha raccolto. E' un fatto sul motivo, non una
# scelta della pagina: mandare a *Da confermare* chi deve dichiarare il sito -- o chi non ha
# nessuna domanda da chiudere, come una posa senza data -- vuol dire mandarlo davanti a un elenco
# dove non trovera' niente.
REVIEW, SITE, NEVER = "review", "site", "never"
_DOVE = {
    SITE_UNCLEAR: REVIEW,
    NO_OBJECT: REVIEW,
    NO_ACTIVE_SITE: SITE,
    SITE_NO_TIMEZONE: SITE,
    NO_DATE: NEVER,
}

# Il meteo vero di quella notte si legge com'e' scritto; il suo tipo lo passa chi chiama.
_PAGINA = f"""
SELECT n.id, n.night_date, n.site_source, s.name AS site, s.timezone, w.summary_json AS meteo,
       {counts.counts_on("night")}
FROM nights n JOIN sites s ON s.id = n.site_id
LEFT JOIN weather_nights w
  ON w.site_id = n.site_id AND w.night_date = n.night_date AND w.kind = ?
ORDER BY n.night_date DESC, n.id DESC
LIMIT ? OFFSET ?
"""  # noqa: S608 - frammenti costanti della spina, non valori dell'utente

_QUANTE = "SELECT COUNT(*) FROM nights"

_TOTALI = f"SELECT{counts.counts_on('archive')}"

# Cosa hai ripreso in quelle notti: un oggetto per notte, col suo nome gia' composto.
_OGGETTI = f"""
SELECT f.night_id, o.id AS object_id, o.catalog_slug,{obj.NAME_COLUMNS},
       {counts.AGGREGATE}
FROM frames f JOIN objects o ON o.id = f.object_id
WHERE f.night_id IN {{dentro}} AND f.copy_of IS NULL
GROUP BY f.night_id, o.id
{counts.ORDER_BY_TIME}, o.id
"""  # noqa: S608 - `dentro` sono segnaposto, non valori

# Le pose che nessuna notte ha raccolto, per motivo. `group` e' l'ultimo stadio che le guarda:
# una posa che un altro stadio ha saltato arriva fin qui apposta e si ferma qui col suo codice.
_FERME = """
SELECT s.reason, COUNT(*) AS frames
FROM frame_stages s JOIN frames f ON f.id = s.frame_id
WHERE s.stage = 'group' AND s.status = 'skipped' AND f.copy_of IS NULL
GROUP BY s.reason ORDER BY frames DESC, s.reason
"""


def _lune(righe):
    """Che luna c'era in ognuna di quelle notti, **in una domanda sola al cielo**: `{id: luna}`,
    e chi non ha un fuso riconoscibile non c'e'.

    Si chiede alla **mezzanotte** della notte nel fuso del sito (`clock.midnight_of`): la Luna
    cambia mentre la notte passa, e un istante va scelto. Non si conserva in nessuna colonna --
    un numero che si sa derivare non si congela, o il giorno che la formula si corregge
    l'archivio resta pieno di numeri vecchi."""
    quando = {r["id"]: midnight_of(r["night_date"], r["timezone"]) for r in righe}
    certe = {i: q for i, q in quando.items() if q is not None}
    return dict(zip(certe, moon.phases(list(certe.values())), strict=True))


def page(conn, *, limit, offset, observed):
    """Una pagina di notti, dalla piu' recente, con dentro oggetti, filtri, che luna c'era e il
    meteo vero (`observed` e' il tipo delle sue righe, e lo sa chi lo scrive)."""
    righe = conn.execute(_PAGINA, (observed, limit, offset)).fetchall()
    ids = [r["id"] for r in righe]
    lune = _lune(righe)
    oggetti = idlist.grouped(conn, _OGGETTI, ids, "night_id", obj.counted)
    filtri = filters_used.of(conn, "night", ids)
    return [
        {
            "id": r["id"],
            "night_date": r["night_date"],
            "site": r["site"],
            "site_source": r["site_source"],
            "frames": r["frames"],
            "integration_s": r["integration_s"],
            "untimed": r["untimed"],
            "objects": oggetti.get(r["id"], []),
            "filters": filtri.get(r["id"], []),
            "moon": lune.get(r["id"]),
            "weather": _meteo(r, fuso_riconosciuto=r["id"] in lune),
        }
        for r in righe
    ]


def _meteo(riga, *, fuso_riconosciuto):
    """Il meteo vero di quella notte, come lo storico l'ha scritto: `ok` col suo riassunto,
    `unknown` se il fuso del sito non si riconosce (le sue notti non si dividono), `waiting`
    altrimenti -- la notte e' troppo giovane per la rianalisi, o lo storico non ci e' ancora
    arrivato."""
    if riga["meteo"] is not None:
        return {"state": "ok", **json.loads(riga["meteo"])}
    # lo stesso criterio della Luna, che l'ha gia' chiesto: un fuso che non si riconosce non ha
    # notti da dividere
    return {"state": "waiting" if fuso_riconosciuto else "unknown", **_SENZA_CIELO}


# Un cielo che non c'e': tutti i campi, vuoti, come li vuole la forma della risposta.
_SENZA_CIELO = dict.fromkeys(
    ("verdict", "cloud_total_pct", "usable_hours", "window", "window_hours")
)


def how_many(conn):
    """Quante notti ci sono in tutto: il totale della pagina, che non dipende da quante righe si
    stanno guardando."""
    return conn.execute(_QUANTE).fetchone()[0]


def archive_totals(conn):
    """Cosa tiene l'archivio intero: notti, pose, ore e pose senza tempo. Conta solo cio' che sta
    **dentro** una notte, o il numero in cima non tornerebbe con la somma delle righe."""
    r = conn.execute(_TOTALI).fetchone()
    return {
        "nights": how_many(conn),
        "frames": r["frames"],
        "integration_s": r["integration_s"],
        "untimed": r["untimed"],
    }


def waiting(conn):
    """Le pose fuori da ogni notte, **per dove si risponde**: `[{"answer_at", "frames"}]`, dal
    gruppo piu' grosso. Un motivo che nessuno ha ancora mappato vale `never`: meglio non mandare
    l'utente da nessuna parte che mandarlo nel posto sbagliato."""
    somme = {}
    for r in conn.execute(_FERME):
        dove = _DOVE.get(r["reason"], NEVER)
        somme[dove] = somme.get(dove, 0) + r["frames"]
    ordinati = sorted(somme.items(), key=lambda voce: (-voce[1], voce[0]))
    return [{"answer_at": dove, "frames": quanti} for dove, quanti in ordinati]


def still_reading(conn):
    """Quante pose devono ancora arrivare a essere una notte.

    E' il residuo di **`group`** e non la somma di tutti gli stadi: una posa ferma a `solve` ha
    anche `group` da fare, e sommare gli stadi la conterebbe tre volte; e `measure`, che nessuno
    esegue ancora, terrebbe il numero sopra lo zero per sempre. `count_pending` toglie gia' chi
    aspetta una risposta invece di aspettare il suo turno."""
    return stages.count_pending(conn, "group")
