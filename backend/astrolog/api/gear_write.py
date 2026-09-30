"""I gesti sull'attrezzatura: un pezzo che nasce, e una scheda che si corregge dov'e' scritta.

Vincoli non ovvi:

* **Si passa da `instrument_answer`**, che fa anche l'unione di *Da confermare*, e da
  `review_write.answer_filter`, non da una seconda strada: una risposta che vale in una pagina e
  non nell'altra sarebbero due verita' sullo stesso pezzo.
* **Un lavoro alla volta**: col worker in corsa non si scrive, com'e' gia' per l'Applica -- meglio
  dirlo prima che lasciare l'archivio a meta'.
"""

from fastapi import APIRouter, Depends, Request

from ..clock import now_iso
from ..spine import gear, gear_create, gear_usage
from ..spine import rigs as corredi
from ..spine.run import STAGE_NORMALIZE
from . import instrument_answer as strumento
from . import review_write as write
from . import work
from .deps import get_db
from .models_gear import (
    FilterNew,
    GearWritten,
    InstrumentCorrection,
    InstrumentNew,
    RigMount,
    RigNaming,
    RigNew,
)
from .models_review_apply import FilterCorrection

router = APIRouter(prefix="/api/v1", tags=["attrezzatura"])


@router.post("/gear/instruments", response_model=GearWritten, status_code=201)
def add_instrument(body: InstrumentNew, request: Request, conn=Depends(get_db)):
    """Un pezzo che i tuoi file non nominano: una guida, un riduttore, una montatura.

    Nasce **dichiarato** e con la sua scheda gia' dentro. Un nome che gia' possiedi in quel genere
    non fa un secondo pezzo: e' un rifiuto, perche' un pezzo e' il suo nome dentro il suo genere e
    quello che scrivi a mano e' esattamente quello che la scansione riconoscera'."""
    work.busy(request.app.state)
    now = now_iso()
    with write.scrivendo(conn):
        new_id = gear_create.instrument(conn, body.kind, body.name, now, detected=False)
        scheda = strumento.of_the_kind(body.kind, body.model_dump(exclude_none=True))
        # La scheda, **senza genere e nome**: quelli li ha gia' la riga appena scritta, e
        # rimandarli a `declare_instrument` sarebbe una rinomina di se' -- che rimetterebbe
        # `detected` a mano e coprirebbe il fatto che un pezzo scritto da te nasce dichiarato.
        gear.declare_instrument(
            conn, new_id, {c: v for c, v in scheda.items() if c not in ("kind", "name")}, now
        )
        # quanto e' servito lo dice la pagina da subito -- zero, o "non si sa" per un genere che
        # nessuna posa nomina -- invece di aspettare il prossimo giro della spina
        gear_usage.add_piece(conn, new_id, body.kind)
    # Un pezzo appena nato non ha pose: non c'e' niente da rilavorare, e avviare il worker per
    # questo sarebbe una corsa che non cambia una riga.
    return GearWritten(id=new_id, requeued=0, run_started=False)


@router.patch("/gear/instruments/{instrument_id}", response_model=GearWritten)
def edit_instrument(
    instrument_id: int, body: InstrumentCorrection, request: Request, conn=Depends(get_db)
):
    """La scheda di un pezzo, corretta dalla pagina dove la si legge.

    Rinominare impara la grafia vecchia -- se no la scansione dopo ricrea il pezzo com'era -- e
    cambiare il colore di una camera rimette in coda le pose che non dicono il filtro: sono la
    stessa risposta di *Da confermare*, scritta dalla stessa mano."""
    work.busy(request.app.state)
    now = now_iso()
    with write.scrivendo(conn):
        requeued = strumento.answer(conn, instrument_id, body, now)
    return _scritto(request, instrument_id, requeued)


@router.patch("/gear/rigs/{rig_id}", response_model=GearWritten)
def name_rig(rig_id: int, body: RigNaming, request: Request, conn=Depends(get_db)):
    """Il nome di un corredo. Sta fra le dichiarazioni, non nella riga: torna quando la spina
    rifa' lo stesso corredo."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        corredi.declare_rig(conn, rig_id, body.name, now_iso())
    return GearWritten(id=rig_id, requeued=0, run_started=False)


@router.post("/gear/filters", response_model=GearWritten, status_code=201)
def add_filter(body: FilterNew, request: Request, conn=Depends(get_db)):
    """Un filtro che non hai ancora usato, o che i tuoi file chiamano in un modo che l'app non
    capisce. Un nome che possiedi gia' e' un rifiuto, non un secondo filtro."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        bande = [b.model_dump() for b in body.bands]
        nuovo = gear_create.filter_declared(
            conn, body.name, bande, now_iso(), brand=body.brand, model=body.model
        )
        gear_usage.add_new(conn, "filter", nuovo)
    return GearWritten(id=nuovo, requeued=0, run_started=False)


@router.post("/gear/rigs", response_model=GearWritten, status_code=201)
def add_rig(body: RigNew, request: Request, conn=Depends(get_db)):
    """Un corredo che non ha ancora ripreso: la sua impronta, quindi quello che la scansione
    trovera'. Uno che hai gia', focale entro il 5 %, e' un rifiuto."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        nuovo = corredi.create_declared(
            conn, body.optics_id, body.camera_id, body.focal_mm, now_iso()
        )
        gear_usage.add_new(conn, "rig", nuovo)
    return GearWritten(id=nuovo, requeued=0, run_started=False)


@router.put("/gear/rigs/{rig_id}/mount", response_model=GearWritten)
def mount_rig(rig_id: int, body: RigMount, request: Request, conn=Depends(get_db)):
    """La montatura di un corredo, dalla sua scheda. Sta fra le dichiarazioni come il nome, e le
    pose del corredo tornano a `normalize`, che la scrive su ognuna."""
    work.busy(request.app.state)
    with write.scrivendo(conn):
        requeued = corredi.declare_mount(conn, rig_id, body.mount_id, now_iso())
    return _scritto(request, rig_id, requeued)


@router.patch("/gear/filters/{filter_id}", response_model=GearWritten)
def edit_filter(filter_id: int, body: FilterCorrection, request: Request, conn=Depends(get_db)):
    """La scheda di un filtro, o l'unione con un altro: le stesse funzioni di *Da confermare*."""
    work.busy(request.app.state)
    now = now_iso()
    with write.scrivendo(conn):
        requeued, _ = write.answer_filter(conn, filter_id, body, now)
    return _scritto(request, filter_id, requeued)


def _scritto(request, row_id, requeued):
    """La ricevuta di un gesto: il lavoro riparte solo se c'e' qualche posa da rifare."""
    started = bool(requeued) and work.after(request.app.state, {STAGE_NORMALIZE})
    return GearWritten(id=row_id, requeued=len(requeued), run_started=started)
