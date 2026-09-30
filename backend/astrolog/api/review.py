"""Da confermare: cosa la scansione ha trovato, e le risposte dell'utente in un colpo solo.

Vincolo non ovvio: qui si legge la pagina e si prendono le due rotte; cosa una risposta scrive
sta in `review_write`, e le regole vere nella spina (`spine.declarations`, `spine.gear`). La
pagina rimanda il suo `seen` perche' l'Applica conferma gli oggetti che la pagina LETTA elencava,
non cio' che c'e' in tabella al momento del clic.
"""

from fastapi import APIRouter, Depends, Query, Request

from ..clock import now_iso
from ..spine import mosaic_proposals as mosaic_reader
from ..spine import rig_optics
from ..spine import rigless as rigless_reader
from ..spine import typeless as typeless_reader
from ..spine import unfiltered as unfiltered_reader
from ..spine import unnamed as unnamed_reader
from ..spine.run import STAGE_GROUP, STAGE_IDENTIFY, STAGE_NORMALIZE, STAGE_SOLVE
from ..vocab.filters import UNKNOWN
from . import lookalike, work
from . import review_page as page
from . import review_write as write
from .deps import get_db
from .models_page import page_of
from .models_review import BandOut, FilterOut, ReviewOut, ReviewSeen, SettledObjects
from .models_review_apply import ReviewApplied, ReviewApply
from .models_review_groups import (
    MosaicCandidate,
    OpticslessRig,
    RiglessGroup,
    TypelessFolder,
    UnfilteredCamera,
    UnnamedGroup,
)

router = APIRouter(prefix="/api/v1", tags=["da confermare"])


def unanswered(rows):
    """Quanti gruppi di una sezione aspettano ancora una risposta. Un gruppo risposto resta in
    pagina -- si deve poter cambiare idea -- ma non conta piu' fra le cose da confermare."""
    return sum(1 for r in rows if r["answer"] is None)


# Una copia riscritta non e' un'altra posa: ogni conteggio di questa pagina filtra
# `copy_of IS NULL`, scritto per esteso in ogni query perche' una query composta con le stringhe
# e' una presa di sicurezza in meno.
# Solo i filtri con la banda sconosciuta (`gear.band_unknown`, la stessa costante): contare le pose
# degli altri per poi scartarli legge le loro pose, e con l'archivio intero cresce il conto.
_FILTERS = """
SELECT fi.*, (SELECT COUNT(*) FROM frames f
              WHERE f.copy_of IS NULL AND f.filter_id = fi.id) AS frames
FROM filters fi WHERE fi.passband = ?
"""


@router.get("/review", response_model=ReviewOut)
def review(conn=Depends(get_db)):
    """Le domande aperte su cio' che la scansione ha trovato, e gli oggetti."""
    bands = {}
    for r in conn.execute("SELECT filter_id, band, width_nm FROM filter_bands ORDER BY band"):
        bands.setdefault(r["filter_id"], []).append(BandOut(band=r["band"], width_nm=r["width_nm"]))
    # Solo i filtri che l'app non riconosce (Marco, 25/9/2026): "che filtro e' H?". Uno che il
    # vocabolario riconosce non e' una domanda. I piu' usati in cima: l'ordine e' della pagina e
    # si legge qui.
    rows = conn.execute(_FILTERS, (UNKNOWN,)).fetchall()
    rows.sort(key=lambda r: (-r["frames"], r["name"]))
    filters = [
        FilterOut(
            id=r["id"],
            name=r["name"],
            brand=r["brand"],
            model=r["model"],
            catalog_id=r["catalog_id"],
            passband=r["passband"],
            is_none=bool(r["is_none"]),
            bands=bands.get(r["id"], []),
            frames=r["frames"],
        )
        for r in rows
    ]

    objects, certi = page.objects(conn)
    incerte = page.unclear_coordinates(conn)
    righe_camere = unfiltered_reader.by_camera(conn)
    da_chiedere = [UnfilteredCamera(**g) for g in righe_camere]
    righe_senza_camera = rigless_reader.by_group(conn)
    righe_senza_nome = unnamed_reader.by_group(conn)
    righe_senza_tipo = typeless_reader.by_folder(conn)
    senza_camera = [RiglessGroup(**g) for g in righe_senza_camera]
    righe_senza_ottica = rig_optics.by_rig(conn)
    righe_mosaici = mosaic_reader.candidates(conn)
    mosaici = [MosaicCandidate(**m) for m in righe_mosaici]
    coppie = lookalike.lookalikes(conn)
    # Fin dove questa pagina ha guardato: il numero di riga piu' alto fra quelli ELENCATI, non un
    # `SELECT MAX(id)` -- una riga scritta mentre la pagina si compone resta fuori dalla conferma.
    seen = ReviewSeen(objects=max((o.id for o in objects), default=0))
    # I posti su cui l'app non sa rispondere contano sempre: non sono voci "gia' viste una
    # volta", sono domande aperte, e restano tali finche' non si risponde.
    to_confirm = (
        sum(1 for o in objects if not o.confirmed)
        # un filtro che l'app non riconosce, e due grafie che sembrano un pezzo solo, sono domande
        # finche' non gli si risponde: vederle non e' rispondere
        + len(filters)
        + len(coppie)
        # un posto risposto resta in pagina per poterlo cambiare, ma non e' piu' una domanda
        + sum(1 for p in incerte if p.site is None)
        + unanswered(righe_camere)  # come i posti
        # Un gruppo di pose che non dicono la camera conta finche' nessuno ha risposto: senza
        # questa riga il conto tornerebbe a zero mentre quelle pose sono ancora senza corredo, ed e'
        # esattamente il buco per cui la domanda e' nata.
        + unanswered(righe_senza_camera)
        # e le pose che hanno la camera ma non l'ottica: senza, l'ASIAIR non chiederebbe mai niente
        + unanswered(righe_senza_ottica)
        # Lo stesso per le cartelle di pose senza nome e senza cielo: pose che non stanno su nessun
        # oggetto, e che senza questa riga lascerebbero il conto a zero.
        + unanswered(righe_senza_nome)
        # Un mosaico proposto conta finche' nessuno ha risposto: lo chiudono tutti e due, il si' e
        # il no, perche' anche il no e' una risposta -- altrimenti l'unico modo di far tacere una
        # proposta sbagliata sarebbe accettarla.
        + unanswered(righe_mosaici)
        # Una cartella i cui frame non dicono che file sono conta finche' nessuno ha risposto:
        # quei frame aspettano prima dell'oggetto, e senza questa riga il conto direbbe zero mentre
        # l'archivio non sa ancora che file sono.
        + unanswered(righe_senza_tipo)
    )
    return ReviewOut(
        lookalikes=coppie,
        filters=filters,
        # i filtri fra cui si sceglie una risposta: quelli con la banda nota, una volta sola
        filter_choices=page.filter_choices(conn),
        rig_choices=page.rig_choices(conn),
        objects=objects,
        settled_objects=len(certi),
        unnamed=[UnnamedGroup(**g) for g in righe_senza_nome],
        unclear=incerte,
        unfiltered=da_chiedere,
        rigless=senza_camera,
        opticsless=[OpticslessRig(**c) for c in righe_senza_ottica],
        optics_choices=page.optics_choices(conn),
        typeless=[TypelessFolder(**g) for g in righe_senza_tipo],
        mosaics=mosaici,
        to_confirm=to_confirm,
        seen=seen,
    )


@router.get("/review/objects/settled", response_model=SettledObjects)
def settled_objects(
    limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), conn=Depends(get_db)
):
    """Gli oggetti gia' visti, senza niente da scegliere, a pagine, nell'ordine della pagina."""
    _, certi = page.objects(conn)
    return SettledObjects(**page_of(certi, limit, offset))


@router.post("/review/apply", response_model=ReviewApplied)
def apply(body: ReviewApply, request: Request, conn=Depends(get_db)):
    """Le risposte diventano regole, e il lavoro riparte sulle pose che le riguardano."""
    state = request.app.state
    work.busy(state)
    now = now_iso()
    with write.scrivendo(conn):
        changed, requeued = write.apply_answers(conn, body, now)
        confirmed = write.confirm_seen(conn, body.seen, now)
    # senza pose da rilavorare non si occupa il worker per niente
    started = bool(requeued) and work.after(state, _stadi_toccati(body))
    return ReviewApplied(
        changed=changed, confirmed=confirmed, requeued=len(requeued), run_started=started
    )


def _stadi_toccati(body):
    """Quali stadi rifare, viste le risposte che sono arrivate.

    Una risposta sui soli oggetti non cambia niente a monte: rifare la normalizzazione sarebbe
    rileggere vocabolari che nessuno ha toccato. Ma a una risposta MISTA servono tutti e due, e in
    quest'ordine -- con la sola normalizzazione la risposta sugli oggetti restava ferma finche'
    qualcuno non cliccava Avvia."""
    voluti = set()
    if body.lookalikes or body.filters:
        voluti.add(STAGE_NORMALIZE)
    if body.unfiltered or body.rigless or body.opticsless:
        voluti.add(STAGE_NORMALIZE)  # cambiano il filtro o il corredo delle loro pose
    if body.typeless:
        # "E' una foto del cielo" rimette in coda il CIELO di quei frame: da li' il nome e la
        # notte vengono dietro da soli (`spine/stages.py`, il grafo).
        voluti.add(STAGE_SOLVE)
    if body.objects or body.unnamed:
        voluti.add(STAGE_IDENTIFY)
    elif body.unclear:
        # Una risposta sul luogo non cambia ne' i vocabolari ne' gli oggetti: cambia solo dove
        # stanno quelle pose, e a rimetterle a posto basta l'ultimo stadio.
        voluti.add(STAGE_GROUP)
    return voluti
