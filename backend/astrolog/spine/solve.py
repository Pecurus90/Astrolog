"""Lo stadio `solve`: il cielo di ogni posa, misurato da ASTAP e non letto dall'header.

Vincolo non ovvio: **due giri**. Il primo risolve una posa per sessione -- basta per
orientare, raggruppare e disegnare il campo, e sono 300 solve invece di 10.000 per vedere un
archivio intero; il secondo prende tutte le altre dalle piu' recenti, e li' una posa senza
puntamento nell'header **eredita l'indizio dalla sorella gia' risolta**, che e' cio' che la
salva dai 23 secondi della ricerca cieca. Il FITS non si tocca mai: cio' che ASTAP scrive va
nella cache, e una soluzione trovata una volta non si ricalcola.
"""

import contextlib
import logging
import os
from functools import partial
from typing import cast

from .. import astap
from ..clock import now_iso
from ..db import config
from ..db.paths import cache_dir
from ..db.transaction import transaction
from ..fits.walk import long_path
from ..units import field_deg, scale_arcsec_px
from . import camera_sky, gear_usage, typeless_folders
from . import solve_store as store
from .stage_run import frame_safely, receipt, watched
from .stages import ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("solved", "cached", "unsolved", "waiting", "measured", "errors")

# ASTAP c'e' ma il suo catalogo stellare no: il programma parte e **non riconosce niente**. E' un
# download separato -- dai 101 MB del D05 a 1,25 GB del D80 -- e la stessa parola
# serve in tre punti -- il motivo di una posa fallita, cio' che ferma la corsa, e la riga di
# `missing` che lo dice prima di far aspettare una scansione intera.
NO_STAR_DATABASE = "no_star_database"

# Cio' che si riprova da solo: la posa NON si segna `failed`, resta da fare, e la corsa dopo
# ci ritorna. Segnarla fallita e' un vicolo cieco -- nessuno la rimetterebbe in coda, e chi
# installa ASTAP il giorno dopo, riattacca il disco o scarica il catalogo non risolverebbe mai
# piu' niente: l'unica uscita sarebbe cancellare il database dell'app.
RETRIABLE = ("astap_missing", "file_missing", NO_STAR_DATABASE)

# E cio' che ferma la corsa invece di ripetersi posa per posa: senza il catalogo **ogni** posa
# fallira' identica, e lanciare ASTAP cinquemila volte per scoprirlo e' un'ora buttata. Si
# ferma alla prima e lo dichiara: lo stadio risulta in errore col suo motivo, non completato.
ABORTS_THE_RUN = (NO_STAR_DATABASE,)

# "cercalo tu" e "non c'e'" sono due cose diverse, e `None` non puo' dirle tutte e due:
# un test che vuole provare l'assenza del solver passa `exe=None` e deve ottenere
# l'assenza, non una ricerca che sulla macchina di chi sviluppa lo trova davvero.
FIND_IT = object()

# Cosa manca all'app quando il solver non si trova, come codice e non come frase: e' la parola
# che `GET /settings` mette fra le cose che mancano. Sta qui, con lo stadio che ne soffre, come
# `NO_ACTIVE_SITE` sta con `group`.
NO_SOLVER = "no_solver"


def solver_path(conn):
    """Dove sta ASTAP per questa installazione: il percorso dichiarato dall'utente se c'e',
    altrimenti la ricerca automatica.

    Una casa sola perche' la domanda si fa in due punti -- questa corsa, e la riga di `missing`
    che avvisa l'utente -- e due ricerche scritte a parte divergerebbero: l'avviso direbbe che
    il solver c'e' mentre la corsa non lo trova, o il contrario. Che `find_exe` e `where_exe`
    diano lo stesso percorso lo tiene fermo una prova che le confronta su **ogni ramo** della
    ricerca (`tests/test_astap.py`), non questa catena: farle passare una dall'altra renderebbe
    cieco il recinto della suite, che le sostituisce tutte e due."""
    return astap.find_exe(config.read(conn).get("astap_path"))


def solver_where(conn):
    """Dove sta ASTAP **e da quale canale arriva**: (percorso, canale) o (None, None).

    Il canale lo mostra la sezione *Il riconoscitore*: chi legge "trovato" deve poter dire "no,
    non quello" -- e la ricerca automatica sbaglia proprio quando trova qualcosa."""
    return astap.where_exe(config.read(conn).get("astap_path"))


def databases_next_to(exe):
    """I cataloghi stellari accanto a quell'eseguibile. L'eseguibile si passa perche' la domanda
    si fa anche su un programma **proposto** dalla ricerca, che non e' quello delle preferenze.

    Sta qui e non in `api/` perche' l'API non legge ASTAP: e' la spina a guardare il disco."""
    return astap.star_databases(exe)


def solver_found():
    """Cosa troverebbe l'app **ignorando cio' che e' scritto nelle preferenze**: e' il *cercalo
    tu* della sezione. Propone e basta -- adottarlo e' un gesto dell'utente, perche' sovrascrivere
    di nascosto un percorso scritto a mano toglierebbe l'unica via d'uscita quando questa ricerca
    prende il programma sbagliato."""
    return astap.where_exe(None)


def solve_frames(conn, *, exe=FIND_IT, run=None, cache=None):
    """Risolve i frame che aspettano questo stadio; un evento per frame, poi la ricevuta.

    `exe` e `run` si passano nei test; in produzione l'eseguibile si cerca una volta sola per
    corsa, non a ogni posa."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    status, reason = "ok", None
    errors, seen = [], 0
    exe = solver_path(conn) if exe is FIND_IT else exe
    cache = _cache_dir(cache)

    def at_end():
        if seen:  # la scala e' arrivata; e solo se qualche posa e' stata guardata: contare costa
            _at_round_end(conn)

    with watched("solve", counts, at_end, astap=exe) as outcome:
        frame_ids = _in_order(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            ferma = frame_safely(
                conn,
                "solve",
                frame_id,
                partial(_one_frame, conn, frame_id, counts, exe=exe, run=run, cache=cache),
                counts,
                errors,
            )
            seen += 1
            yield {"current": seen, "total": total, **counts}
            if ferma:
                status, reason = "aborted", ferma
                outcome.update(status=status, reason=reason)
                break
    yield receipt(status, reason, counts, errors, total=seen)


def _at_round_end(conn):
    camera_sky.write(conn)
    gear_usage.write(conn)
    typeless_folders.write(conn)  # il cielo decide quali pose senza tipo non sa dire


def _cache_dir(cache):
    """`<dati>/cache/solve`, creata se manca. La soluzione di un frame vive qui e non nel
    database: un azzeramento del DB la rilegge invece di ri-risolvere."""
    base = (cache or cache_dir()) / "solve"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _in_order(conn):
    """L'ordine dei due giri, deciso una volta all'inizio: prima una posa per sessione, poi
    tutte le altre dalle piu' recenti."""
    pending = ready(conn, "solve")
    first = store.first_per_order_key(conn, pending)
    rest = [i for i in pending if i not in set(first)]
    return first + store.newest_first(conn, rest)


def _one_frame(conn, frame_id, counts, *, exe, run, cache):  # noqa: PLR0913
    """Una posa, in una transazione: cio' che e' fatto e' fatto anche se ci si ferma dopo.

    Torna il motivo che ferma la corsa (`ABORTS_THE_RUN`), o None: un guasto della posa non la
    ferma mai, un guasto dell'installazione si'."""
    frame = store.frame(conn, frame_id)
    now = now_iso()
    solution, cached = _solution_for(conn, frame, exe=exe, run=run, cache=cache)
    hfd, stars = (None, None)
    # La cache risponde anche a disco staccato: senza il controllo sul percorso si lancerebbe
    # un processo per posa su un file che non c'e'.
    if solution.ok and _path_of(frame) and not store.has_metrics(conn, frame["id"]):
        # La qualita' costa una seconda passata e si prende subito: rileggere l'archivio
        # un'altra volta costerebbe di piu' del tempo che si risparmia adesso. Si chiede anche
        # quando il cielo viene dalla cache: dopo un azzeramento del database la soluzione
        # torna da li', ma HFD e stelle no -- e senza questo si perderebbero per sempre.
        hfd, stars = astap.analyse(cast("str", _path_of(frame)), exe=exe, run=run)  # checked above

    with transaction(conn):
        if not solution.ok:
            if solution.reason in RETRIABLE:
                counts["waiting"] += 1  # resta `pending`: si riprova da sola alla prossima
            else:
                set_status(conn, frame["id"], "solve", "failed", reason=solution.reason, now=now)
                counts["unsolved"] += 1
        else:
            width, height = _field_of(frame, solution.scale_arcsec_px)
            store.save_wcs(
                conn,
                frame["id"],
                ra_deg=solution.ra_deg,
                dec_deg=solution.dec_deg,
                scale=solution.scale_arcsec_px,
                rotation=solution.rotation_deg,
                width=width,
                height=height,
                now=now,
            )
            if hfd is not None or stars is not None:
                store.save_metrics(conn, frame["id"], hfd_px=hfd, stars=stars, now=now)
                counts["measured"] += 1
            set_status(conn, frame["id"], "solve", "done", now=now)
            counts["cached" if cached else "solved"] += 1
    return solution.reason if solution.reason in ABORTS_THE_RUN else None


def _solution_for(conn, frame, *, exe, run, cache):
    """La soluzione e se veniva dalla cache. Si guarda prima li': la chiave e' l'impronta del
    frame, che sopravvive a uno spostamento del file, a una rinomina e a un reset del DB."""
    out_base = cache / frame["frame_hash"]
    saved = astap.from_ini(astap.read_ini(f"{out_base}.ini"))
    if saved.ok:
        return saved, True
    path = _path_of(frame)
    if path is None:
        return astap.Solution(ok=False, reason="file_missing"), False
    if exe:
        solution = _launch(conn, frame, path, out_base, exe=exe, run=run)
    else:
        # Senza il solver non parte niente: il suggerimento e la pulizia servono a un lancio, e
        # ogni corsa ripassa tutte le pose in attesa solo per chiedere alla cache.
        solution = astap.Solution(ok=False, reason="astap_missing")
    return solution, False


def _launch(conn, frame, path, out_base, *, exe, run):  # noqa: PLR0913
    """Lancia ASTAP su quella posa, col suggerimento di dove guardare."""
    # C'era un esito ma non e' una soluzione (troncato, o un fallimento di ieri): si butta prima
    # di lanciare, o un ASTAP che fallisce senza scrivere lascerebbe rileggere quello.
    _forget(out_base)
    ra, dec = _hint_for(conn, frame)
    solution = astap.solve(
        path,
        out_base,
        field_deg=_field_hint(frame),
        ra_deg=ra,
        dec_deg=dec,
        exe=exe,
        run=run,
    )
    if not solution.ok:
        # Un fallimento non si mette in cache: domani ASTAP puo' avere un database piu' fitto,
        # o la posa puo' ereditare un indizio da una sorella. Solo le soluzioni sono immutabili.
        _forget(out_base)
    return solution


def _forget(out_base):
    for suffix in (".ini", ".wcs"):
        # non c'era, o non si puo' togliere: la prossima corsa lo rifara' comunque
        with contextlib.suppress(OSError):
            (out_base.parent / f"{out_base.name}{suffix}").unlink()


def _path_of(frame):
    """Il percorso su disco della posa, o `None` se nessuna posizione e' presente."""
    if not frame["root_path"] or not frame["rel_path"]:
        return None
    return long_path(os.path.join(frame["root_path"], frame["rel_path"]))


def _hint_for(conn, frame):
    """Dove puntava il telescopio, per restringere la ricerca. Prima l'header; se tace, il
    cielo MISURATO di una sorella dello stesso gruppo -- e' lo stesso pezzo di cielo."""
    if frame["ra_hint_deg"] is not None and frame["dec_hint_deg"] is not None:
        return frame["ra_hint_deg"], frame["dec_hint_deg"]
    sister = store.sister_solution(conn, frame)
    return (sister["ra_deg"], sister["dec_deg"]) if sister else (None, None)


def _scale_of(frame):
    """La scala derivata dalle specifiche dell'header.

    Il binning NON si moltiplica: `XPIXSZ` per convenzione lo include gia' (le fonti stanno nel
    contratto, `docs/domini/spina.md`), e moltiplicare raddoppierebbe il campo su un archivio a
    bin 2."""
    return scale_arcsec_px(frame["pixel_size_um"], frame["focal_mm_raw"])


def _field_hint(frame):
    """L'altezza del campo in gradi: e' la leva della velocita' del solver (0,2 s contro 2,3 s
    sullo stesso frame). `None` dove l'header non dice focale o pixel: si cerca e si paga."""
    return field_deg(frame["naxis2"], _scale_of(frame))


def _field_of(frame, scale):
    """Larghezza e altezza del campo, dalla scala MISURATA: e' il rettangolo che si disegna
    sul cielo, e viene dalla soluzione, non dalle specifiche dichiarate."""
    return field_deg(frame["naxis1"], scale), field_deg(frame["naxis2"], scale)
