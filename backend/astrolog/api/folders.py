"""Le cartelle di FITS: elenco, registrazione, ritiro, "guarda senza registrare". La
scansione sta in `scan.py`.

Vincolo non ovvio: la registrazione e' permissiva (forma e unicita'): la cartella puo' non
rispondere adesso (NAS spento) e va bene. `frames` viene dal DB, mai dal disco; contare sul
disco e' un gesto esplicito del wizard (`probe`), mai un costo all'apertura di una pagina.
"""

import os
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..clock import now_iso
from ..db.transaction import transaction
from ..fits.walk import subfolders, walk_dir
from ..spine import typeless_answer
from ..spine.run import STAGE_IDENTIFY, STAGE_SOLVE
from ..spine.scan import root_readable
from ..spine.stages import count_pending, refresh_waiting
from . import work
from .deps import get_db
from .models import (
    BrowseOut,
    FolderCreate,
    FolderEntry,
    FolderList,
    FolderOut,
    PathInfo,
    PathProbe,
    ProbeOut,
    RetireOut,
)
from .paths import same_folder, validate_root

router = APIRouter(prefix="/api/v1", tags=["cartelle"])

# Quanto aspetta la conta di Aggiungi cartella prima di rispondere "piu' di": "10 seconds is
# about the limit for keeping the user's attention focused on the dialogue" (Nielsen, *Response
# Times: The 3 Important Limits*, 1993). Un archivio enorme o un NAS lento non tengono ferma la
# pagina. Il tetto si guarda fra una cartella e l'altra: una cartella lentissima da elencare lo
# sfora di quanto ci mette, e la risposta dice comunque che il conteggio non e' completo. Vale per
# la conta, non per cio' che viene prima: risolvere il percorso e chiedere se la cartella risponde
# aspettano quanto il sistema (in coda: *"Da misurare su un NAS vero"*).
PROBE_SECONDS = 10

_SELECT = (
    "SELECT f.id, f.name, f.root_path, f.created_at,"
    " (SELECT COUNT(*) FROM positions p WHERE p.folder_id = f.id AND p.status = 'present')"
    " AS frames FROM folders f"
)


def _out(row, **more):
    return FolderOut(**dict(row), reachable=root_readable(row["root_path"]), **more)


@router.get("/folders/path-info", response_model=PathInfo)
def path_info(request: Request):
    """Come sono fatti i percorsi su QUESTA macchina, e se c'e' una radice confinata."""
    return PathInfo(
        family="windows" if os.name == "nt" else "posix", data_root=request.app.state.data_root
    )


@router.post("/folders/probe", response_model=ProbeOut)
def probe(body: PathProbe, request: Request):
    """Guarda un percorso senza registrarlo: `fits_count` e' None se non si e' guardato. Conta
    anche i FITS solo online: ci sono, anche se non sul disco, e chi ha l'archivio sotto OneDrive
    non deve leggere "0" sulla cartella che ha appena scelto."""
    canonical = validate_root(body.root_path, request.app.state.data_root)
    if not root_readable(canonical):
        return ProbeOut(root_path=canonical, reachable=False, fits_count=None, complete=None)
    online, unvisited = [], []
    found = walk_dir(
        canonical,
        online_only=online,
        deadline=time.monotonic() + PROBE_SECONDS,
        unvisited=unvisited,
    )
    return ProbeOut(
        root_path=canonical,
        reachable=True,
        fits_count=len(found) + len(online),
        complete=not unvisited,
    )


@router.get("/folders/browse", response_model=BrowseOut)
def browse(request: Request, path: str | None = None):
    """Le sottocartelle da scegliere dentro la radice dei dati: sul NAS in Docker l'utente non
    sa quale percorso ha la cartella dentro il container, e la sceglie invece di scriverla. Senza
    radice (il desktop) non si elenca niente: 409 `no_data_root`. Senza pagine: sono le
    sottocartelle di una cartella sola, non l'archivio."""
    root = request.app.state.data_root
    if root is None:
        raise HTTPException(status_code=409, detail={"code": "no_data_root"})
    where = validate_root(path or root, root)
    try:
        names = subfolders(where)
    except OSError as err:
        raise HTTPException(
            status_code=409, detail={"code": "root_unreachable", "path": where}
        ) from err
    return BrowseOut(
        path=where,
        parent=None if same_folder(os.path.realpath(where), root) else os.path.dirname(where),
        folders=[FolderEntry(name=n, path=os.path.join(where, n)) for n in names],
    )


@router.get("/folders", response_model=FolderList)
def list_folders(
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), conn=Depends(get_db)
):
    """Le cartelle attive (le ritirate non compaiono)."""
    total = conn.execute("SELECT COUNT(*) FROM folders WHERE retired_at IS NULL").fetchone()[0]
    rows = conn.execute(
        _SELECT + " WHERE f.retired_at IS NULL ORDER BY f.id LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return FolderList(items=[_out(r) for r in rows], total=total, limit=limit, offset=offset)


@router.post("/folders", response_model=FolderOut, status_code=201)
def create_folder(body: FolderCreate, request: Request, conn=Depends(get_db)):
    """Registra una cartella; ri-registrare una ritirata la riattiva; 409 se gia' attiva."""
    canonical = validate_root(body.root_path, request.app.state.data_root)
    existing = conn.execute(
        "SELECT id, retired_at FROM folders WHERE root_path = ?", (canonical,)
    ).fetchone()
    if existing is not None:
        if existing["retired_at"] is None:
            raise HTTPException(
                status_code=409, detail={"code": "folder_exists", "folder_id": existing["id"]}
            )
        _move(conn, request.app.state, existing["id"], None)
        row = conn.execute(_SELECT + " WHERE f.id = ?", (existing["id"],)).fetchone()
        return _out(row, reactivated=True)
    folder_id = conn.execute(
        "INSERT INTO folders(root_path, name, created_at) VALUES(?, ?, ?)",
        (canonical, body.name, now_iso()),
    ).lastrowid
    return _out(conn.execute(_SELECT + " WHERE f.id = ?", (folder_id,)).fetchone())


@router.delete("/folders/{folder_id}", response_model=RetireOut)
def retire_folder(folder_id: int, request: Request, conn=Depends(get_db)):
    """Ritira: l'app smette di guardare li'. I frame restano. Idempotente; 404 se ignota."""
    row = conn.execute("SELECT id, retired_at FROM folders WHERE id = ?", (folder_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "folder_not_found"})
    kept = conn.execute(
        "SELECT COUNT(*) FROM positions WHERE folder_id = ?", (folder_id,)
    ).fetchone()[0]
    if row["retired_at"] is not None:
        return RetireOut(folder_id=folder_id, retired=False, kept_frames=kept)
    _move(conn, request.app.state, folder_id, now_iso())
    return RetireOut(folder_id=folder_id, retired=True, kept_frames=kept)


def _move(conn, state, folder_id, retired_at):
    """Toglie (`retired_at` e' l'istante) o rimette (`None`) una cartella. Cambia la cartella di un
    frame che sta anche altrove: il segno dell'attesa si riscrive **nella stessa transazione** del
    ritiro, perche' un ritiro scritto con i segni vecchi non si ripara ripetendolo -- torna prima,
    gia' ritirato. Chi torna ad aspettare si stacca (`typeless_answer.detach_waiting`), e la corsa
    da `identify` spazza gli oggetti e le sessioni rimasti vuoti; chi ha perso il cielo e sta in una
    cartella viva che non lo ferma torna in fila dal cielo, e la corsa che parte, se il worker e'
    libero, parte da li'. A differenza delle risposte non si rifiuta col worker occupato: rimettere
    una cartella passa da Aggiungi, che si usa mentre l'app scansiona, e toglierla si deve poter
    fare sempre. La corsa in volo non riattacca chi e' tornato ad aspettare, perche' `identify` e
    `group` ricontrollano ogni frame prima di lavorarlo (`stages.ready` con `frame_id`); se pero'
    ha gia' cominciato `identify`, l'oggetto rimasto vuoto lo spazza la corsa della scansione
    successiva."""
    with transaction(conn):
        conn.execute("UPDATE folders SET retired_at = ? WHERE id = ?", (retired_at, folder_id))
        refresh_waiting(conn)  # la cartella di un frame e' cambiata senza passare dalle posizioni
        detached, requeued = typeless_answer.detach_waiting(conn)
    # anche senza stacchi: rimessa la cartella, chi aspettava puo' tornare pronto
    if requeued:
        work.after(state, [STAGE_SOLVE])
    elif detached or count_pending(conn, STAGE_IDENTIFY):
        work.after(state, [STAGE_IDENTIFY])
