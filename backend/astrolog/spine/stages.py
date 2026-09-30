"""Lo stato di ogni frame in ogni stadio, e gli archi del grafo: chi dipende da chi.

Vincolo non ovvio: la ripresa e' "cio' che manca", mai "dal file N"; `invalidate` e' l'UNICA
via per rimettere `pending` uno stadio e tutti quelli a valle, ed e' cio' che ogni
dichiarazione dell'utente chiama. Non esiste `running` nel DB: l'"in corso" vive nel
worker, e un processo che muore non lascia righe appese.
"""

from ..clock import now_iso
from ..fits.frame_type import UNKNOWN
from . import declarations as decl
from . import frame_folder as folder

STAGES = ("solve", "normalize", "identify", "group", "measure")
STATUSES = ("pending", "done", "failed", "skipped")

# stadio -> gli stadi di cui ha bisogno. E' il disegno della spina come grafo.
DEPENDS = {
    "solve": (),
    "normalize": (),
    "identify": ("solve", "normalize"),
    "group": ("normalize", "identify"),
    "measure": ("solve",),
}


def downstream(stage):
    """Lo stadio e tutti quelli che, direttamente o no, dipendono da lui."""
    out, frontier = {stage}, [stage]
    while frontier:
        s = frontier.pop()
        for other, needs in DEPENDS.items():
            if s in needs and other not in out:
                out.add(other)
                frontier.append(other)
    return tuple(s for s in STAGES if s in out)


# Uno stadio a monte e' "concluso" quando e' `done`. Un'eccezione, dichiarata, e per una coppia
# sola: `identify` parte anche su una posa che il solver ha RINUNCIATO a risolvere. E' proprio
# la situazione "niente cielo" del contratto -- si aggancia dal nome dell'header -- e senza
# questa riga due delle otto situazioni non potrebbero mai accadere.
# `pending` invece NON passa, ed e' la meta' che conta: il solver lascia `pending` cio' che
# riprovera' da solo (l'elenco e' `solve.RETRIABLE`, e li' c'e' anche il perche'), e li'
# la posa avra' il suo cielo, quindi agganciarla adesso dal nome sarebbe una risposta data in
# fretta. Solo `failed` e' definitivo.
# La seconda eccezione, per la ragione opposta: `group` deve vedere anche le pose che
# `identify` ha SALTATO (nessun nome, nessun cielo). Non per raggrupparle -- non hanno un
# oggetto -- ma per fermarle col loro perche': se non arrivassero mai, resterebbero `pending`
# per sempre e il residuo dello stadio non scenderebbe a zero.
SETTLED = {("identify", "solve"): ("done", "failed"), ("group", "identify"): ("done", "skipped")}

# Un frame che non dice **che file e'** lo fa dire al cielo (Marco, 23/9/2026): va al solver come
# gli altri, e se il cielo lo risolve e' una foto. Senza stelle, o finche' il cielo non ha
# parlato, o dove non sa dire, **aspetta** davanti all'oggetto: e' il `failed` del cielo, che per
# un light manda avanti dal nome, a trasformare un dark in ore. Lo sblocca una risposta "foto del
# cielo" sulla sua cartella; "calibrazione" lo ferma anche se il cielo l'ha risolto (`spine/
# typeless.py`). La regola sta qui (`WAITING_RULE`), e il suo esito si scrive sulla posa
# (`frames.asks_type`), non fra gli stati degli stadi: quelli li cancella la prima `invalidate` che
# passa. Chi legge legge il segno (`WAITING_SQL`); chi cambia un ingresso della regola lo riscrive
# **subito**, con `refresh_waiting`: un segno rimasto a 0 su una posa senza tipo che il cielo ha
# rinunciato a risolvere la manderebbe a `identify`, e un dark diventerebbe ore.
# Chi aspetta non e' lavoro per nessuno stadio dopo il cielo. "Calibrazione" lo ferma da
# `identify`, il primo che da' un oggetto; "foto del cielo" lo lascia andare, e rimette in fila dal
# cielo chi ne aveva perso la soluzione (`spine/typeless_answer.py`).
WAITING_FROM = "identify"
WAITING_STAGES = frozenset(downstream("solve")) - {"solve"}


# La risposta della cartella si legge UNA volta per frame: comporre la chiave e' la parte cara, e
# con due domande separate ("detta foto?", "detta calibrazione?") la si paga due volte.
FOLDER_SAYS = f"""(
  SELECT dc.value FROM declarations dc WHERE dc.entity_type = '{decl.FOLDER}'
    AND dc.field = '{decl.FOLDER_TYPE}' AND dc.entity_key = ({folder.KEY_OF_FRAME}))"""  # noqa: S608
# Riconosciuto dal cielo vuol dire risolto **e col cielo trovato**: quello che uno stacco ha tolto
# (`solve_store.detach`) lascia lo stadio fatto, e senza il cielo `identify` riprenderebbe il frame
# col nome dell'header. Lo rimette solo il solver, a cui lo rimanda `spine/typeless_answer.py`.
_SKY_SOLVED = """(EXISTS (
  SELECT 1 FROM frame_stages sv WHERE sv.frame_id = f.id AND sv.stage = 'solve'
    AND sv.status = 'done') AND EXISTS (SELECT 1 FROM frame_wcs w WHERE w.frame_id = f.id))"""
WAITING_RULE = f"""
f.image_type = '{UNKNOWN}' AND CASE {FOLDER_SAYS}
  WHEN '{decl.TYPE_LIGHT}' THEN 0 WHEN '{decl.TYPE_CALIBRATION}' THEN 1 ELSE NOT {_SKY_SOLVED} END
"""  # noqa: S608 - frammenti costanti della spina, nessun valore dell'utente
WAITING_SQL = "f.asks_type = 1"
_REFRESH = f"UPDATE frames AS f SET asks_type = ({WAITING_RULE})"  # noqa: S608 - costanti


def refresh_waiting(conn, frame_ids=None):
    """Riscrive il segno dell'attesa di quei frame, o di tutti quelli senza tipo: senza elenco lo
    chiede chi cambia una risposta o una cartella, che tocca ogni posa senza tipo che ci sta."""
    if frame_ids is None:
        conn.execute(_REFRESH + " WHERE f.image_type = ?", (UNKNOWN,))
    else:
        conn.executemany(_REFRESH + " WHERE f.id = ?", [(i,) for i in frame_ids])


def ready(conn, stage, limit=None, frame_id=None):
    """I frame `pending` per `stage` i cui stadi a monte sono tutti conclusi, dal piu' vecchio.
    Il giro "prima una posa per sessione" se lo calcola `solve`, che e' l'unico a cui serve.
    Fuori chi aspetta una risposta sul tipo di file (`WAITING_STAGES`).

    Con `frame_id`, se quel frame e' ancora pronto: uno stadio sceglie i frame all'inizio, e
    togliere una cartella mentre gira puo' rimandarne uno ad aspettare (`api/folders.py`)."""
    needs = DEPENDS[stage]
    sql = (
        "SELECT s.frame_id FROM frame_stages s JOIN frames f ON f.id = s.frame_id"
        " WHERE s.stage = ? AND s.status = 'pending'"
    )
    args = [stage]
    if frame_id is not None:
        sql += " AND s.frame_id = ?"
        args.append(frame_id)
    if stage in WAITING_STAGES:
        sql += f" AND NOT ({WAITING_SQL})"
    for dep in needs:
        settled = SETTLED.get((stage, dep), ("done",))
        marks = ",".join("?" * len(settled))  # segnaposto-ok: due stati, non una riga per posa
        sql += (
            " AND EXISTS (SELECT 1 FROM frame_stages d WHERE d.frame_id = s.frame_id"  # noqa: S608 - solo segnaposto
            f" AND d.stage = ? AND d.status IN ({marks}))"
        )
        args.append(dep)
        args.extend(settled)
    sql += " ORDER BY f.id"
    if limit is not None:
        sql += " LIMIT ?"
        args.append(limit)
    return [r[0] for r in conn.execute(sql, args)]


def mark_pending(conn, frame_id, now=None):
    """Un frame nuovo: tutti gli stadi da fare."""
    now = now or now_iso()
    conn.executemany(
        "INSERT OR IGNORE INTO frame_stages(frame_id, stage, status, updated_at)"
        " VALUES(?, ?, 'pending', ?)",
        [(frame_id, s, now) for s in STAGES],
    )


def set_status(conn, frame_id, stage, status, reason=None, now=None):  # noqa: PLR0913
    if status not in STATUSES:
        raise ValueError(f"stato sconosciuto: {status}")
    conn.execute(
        "INSERT INTO frame_stages(frame_id, stage, status, reason, updated_at)"
        " VALUES(?, ?, ?, ?, ?)"
        " ON CONFLICT(frame_id, stage) DO UPDATE SET status = excluded.status,"
        " reason = excluded.reason, updated_at = excluded.updated_at",
        (frame_id, stage, status, reason, now or now_iso()),
    )
    if stage == "solve":
        refresh_waiting(conn, [frame_id])


def invalidate(conn, frame_ids, from_stage, now=None):
    """Rimette `pending` lo stadio `from_stage` e tutti quelli a valle, per i frame dati.
    E' l'unica via: una dichiarazione che cambia un filtro chiama `invalidate(..., "normalize")`
    e group/identify si rifanno da soli."""
    now = now or now_iso()
    stages = downstream(from_stage)
    conn.executemany(
        "UPDATE frame_stages SET status = 'pending', reason = NULL, updated_at = ?"
        " WHERE frame_id = ? AND stage = ?",
        [(now, frame_id, s) for frame_id in frame_ids for s in stages],
    )
    if "solve" in stages:
        refresh_waiting(conn, frame_ids)


# I frame che aspettano una risposta sul tipo, per stadio: **lo stesso predicato di `WAITING_SQL`**,
# non una copia, perche' `ready` e questo conto devono parlare della stessa popolazione, o il
# residuo non scenderebbe mai a zero. Il `CROSS JOIN` fa partire dalle pose segnate: dagli stadi in
# fila partirebbe da `measure`, che ha in fila ogni posa, anche in un archivio senza attese.
_WAITING_BY_STAGE = f"""
SELECT s.stage, COUNT(*) FROM frames f CROSS JOIN frame_stages s ON s.frame_id = f.id
WHERE {WAITING_SQL} AND s.status = 'pending' GROUP BY s.stage
"""  # noqa: S608 - lo stesso frammento costante


def _waiting_by_stage(conn):
    """`{stage: quanti aspettano}`: chi non e' lavoro da fare, ma una domanda aperta."""
    return {r[0]: r[1] for r in conn.execute(_WAITING_BY_STAGE)}


def count_pending(conn, stage):
    """Quanti frame aspettano il loro turno in quello stadio. **Non** chi aspetta una risposta:
    un frame che non dice che file e' non e' lavoro da fare, e contarlo terrebbe il residuo sopra
    lo zero per sempre -- ogni Avvia ripartirebbe per niente, e sul NAS la cadenza girerebbe a
    vuoto."""
    quanti = conn.execute(
        "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'pending'", (stage,)
    ).fetchone()[0]
    if stage not in WAITING_STAGES:
        return quanti
    return quanti - _waiting_by_stage(conn).get(stage, 0)


def pending_by_stage(conn):
    """`{stage: quanti}`: il residuo della spina in una domanda sola -- due, a dirla tutta: i
    `pending` per stadio, meno chi aspetta una risposta. Chi aspetta si conta **una volta** per
    tutti gli stadi, non una per ognuno."""
    totali = {
        s: conn.execute(
            "SELECT COUNT(*) FROM frame_stages WHERE stage = ? AND status = 'pending'", (s,)
        ).fetchone()[0]
        for s in STAGES
    }  # cinque conti con l'indice `frame_stages_pending`, non una spazzata con GROUP BY
    aspettano = _waiting_by_stage(conn)
    return {s: totali[s] - (aspettano.get(s, 0) if s in WAITING_STAGES else 0) for s in STAGES}
