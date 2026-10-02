"""La corsa: quali stadi, in che ordine. Oggi scansione, normalizzazione, solve, identify e
group; measure si accoda qui quando nasce, e nessuna rotta deve saperlo.

Vincolo non ovvio: uno stadio e' `(nome, fabbrica)`: la fabbrica apre la sua connessione
al DB e la chiude nel proprio finally, cosi' il worker (che non sa cosa sia uno stadio) puo'
costruire un generatore fresco a ogni corsa. Gli stadi non si conoscono fra loro: a metterli
in fila e' questo file, e solo questo.
"""

from typing import cast

from ..db.connect import connect
from ..db.transaction import transaction
from . import typeless_answer
from .group import group_frames
from .identify import identify_frames
from .normalize import normalize_frames
from .scan import COUNTS, scan_folder
from .solve import solve_frames
from .stage_run import receipt
from .stages import downstream

STAGE_SCAN = "scan"
STAGE_NORMALIZE = "normalize"
STAGE_SOLVE = "solve"
STAGE_IDENTIFY = "identify"
STAGE_GROUP = "group"

# L'ordine della catena: chi chiede degli stadi li riceve sempre in quest'ordine, chiunque sia
# a chiedere. `measure` si accoda qui quando nasce.
ORDER = (STAGE_SCAN, STAGE_NORMALIZE, STAGE_SOLVE, STAGE_IDENTIFY, STAGE_GROUP)


def _with_conn(db_path, work):
    def factory():
        conn = connect(db_path, check_same_thread=False)
        try:
            yield from work(conn)
        finally:
            conn.close()

    return factory


def _detach_waiting(conn):
    """Dopo la scansione, chi e' finito in una cartella che lo ferma torna ad aspettare senza le
    sue ore, e chi ne e' uscito senza il suo cielo, in una cartella viva, torna in fila dal cielo
    (`typeless_answer.detach_waiting`). Sta qui perche' la scansione non arriva agli store degli
    altri stadi."""
    with transaction(conn):
        typeless_answer.detach_waiting(conn)


def _then_detach(conn, eventi):
    """Gli eventi della scansione, con lo stacco prima del `done`: il worker si ferma li'."""
    for evento in eventi:
        if evento.get("done"):
            _detach_waiting(conn)
        yield evento


def queue(db_path, stages, *, folder_id=None, run_id=None):
    """La fila dei lavori: gli stadi chiesti, piu' quelli che devono seguirli, nell'ordine
    della catena. E' l'unica porta -- chi chiama dice **cosa** serve, mai in che ordine.

    Chiede `scan` chi scansiona una cartella (e allora servono `folder_id` e la ricevuta gia'
    aperta); chiede cio' che ha residuo il pulsante Avvia; chiede cio' che ha toccato l'Applica
    di Da confermare. La catena e' sempre la stessa: prima la lettura dei file, poi la
    normalizzazione (l'archivio diventa consultabile), poi il cielo in sottofondo, poi il nome
    -- che vuole il cielo e i vocabolari -- e per ultime le notti.

    **Chi tira dietro chi lo dice il grafo, non questo file**: `stages.downstream` e' la casa
    di quegli archi. Chiedere `normalize` accoda anche il nome e le notti, perche' rifare i
    vocabolari cambia cio' che quelle pose vogliono dire -- e infatti `invalidate` le rimette
    `pending`. Scritto qui una seconda volta, e per una coppia sola, lasciava fermi il nome e
    le notti dopo ogni risposta su un filtro, finche' l'utente non premeva Avvia."""
    chiesti = set(stages)
    lavoro = {
        # checked below, before any stage runs
        STAGE_SCAN: lambda c: _then_detach(
            c, scan_folder(c, cast("int", folder_id), run_id=run_id)
        ),
        STAGE_NORMALIZE: normalize_frames,
        STAGE_SOLVE: solve_frames,
        STAGE_IDENTIFY: identify_frames,
        STAGE_GROUP: group_frames,
    }
    ignoti = chiesti - set(lavoro)
    if ignoti:  # uno stadio senza lavoro e' un errore di chi chiama, non una fila piu' corta
        raise ValueError(f"stadi che non esistono: {sorted(ignoti)}")
    if STAGE_SCAN in chiesti and (folder_id is None or run_id is None):
        # Senza, l'errore esploderebbe dopo, dentro il generatore, nel thread del worker: la
        # scansione risulterebbe partita e morirebbe muta.
        raise ValueError("scan vuole folder_id e run_id")
    # `measure` e' nel grafo ma non ha ancora un lavoro: si accodera' da se' quando nascera'.
    voluti = chiesti | {d for s in chiesti for d in downstream(s) if d in lavoro}
    return [(s, _with_conn(db_path, lavoro[s])) for s in ORDER if s in voluti]


def queue_folders(db_path, cartelle, *, on_folder=None):
    """La fila per leggere PIU' cartelle in un gesto solo: **uno** stadio `scan` che le legge
    una dopo l'altra, e poi la catena a valle **una volta sola**.

    Uno stadio per cartella darebbe cinque fasi moltiplicate per le cartelle, e a schermo la
    catena non si leggerebbe piu'. Ed e' anche il vero: leggere i file e' un lavoro per
    cartella, cio' che viene dopo lavora su cio' che manca nel database, che di cartelle non
    sa niente.

    `cartelle` sono coppie `(folder_id, run_id)` con la ricevuta gia' aperta, nell'ordine in
    cui vanno lette. `on_folder(folder_id, run_id)` si chiama **prima** di ognuna: e' cosi'
    che chi guarda lo stato sa quale cartella e' sotto le mani adesso, e non la prima della
    fila per tutta la corsa."""
    if not cartelle:
        raise ValueError("nessuna cartella da leggere")

    def molte(conn):
        # Un `done` SOLO, in coda a tutte: il worker si ferma al primo che vede
        # (`worker/worker.py`), e passandogli quello della prima cartella la seconda non
        # partirebbe mai. Le ricevute per cartella le chiude `scan_folder`, ognuna con i suoi
        # numeri; questa e' la riga dello STADIO, e i suoi numeri sono la somma.
        conti = dict.fromkeys(COUNTS, 0)
        errori, esiti = [], []
        for folder_id, run_id in cartelle:
            if on_folder is not None:
                on_folder(folder_id, run_id)
            for evento in scan_folder(conn, folder_id, run_id=run_id):
                if not evento.get("done"):
                    yield evento
                    continue
                # Si sommano SOLO i conteggi, e i loro nomi li tiene `scan.COUNTS`: sommare
                # ogni intero prenderebbe anche `done`, che in Python e' un intero (`True`), e
                # la riga finale direbbe "done: 2" invece di "done: True".
                for chiave in COUNTS:
                    conti[chiave] += evento.get(chiave, 0)
                errori.extend(evento.get("errors_detail", []))
                esiti.append((evento.get("status"), evento.get("reason")))
        # **Lo stadio dice "tutto bene" solo se TUTTE sono andate bene.** Una cartella che
        # muore a meta' corsa -- il NAS che si spegne dopo il pre-controllo -- non finisce fra
        # le saltate (il controllo l'aveva passata) e la sua ricevuta si va a leggere in
        # Impostazioni / Le letture: se anche lo stadio tacesse, l'utente leggerebbe
        # "fatto" con una cartella non letta. Meglio un allarme che copre piu' del dovuto --
        # le altre cartelle sono entrate comunque, e ognuna ha la sua ricevuta -- che un
        # silenzio su un archivio incompleto.
        # (Uno Stop non passa di qui: interrompe il generatore, che non emette `done`.)
        storte = [e for e in esiti if e[0] != "ok"]
        stato, motivo = storte[0] if storte else ("ok", None)
        _detach_waiting(conn)
        yield receipt(stato, motivo, conti, errori)

    dopo = [s for s in ORDER if s != STAGE_SCAN]
    return [(STAGE_SCAN, _with_conn(db_path, molte)), *queue(db_path, dopo)]
