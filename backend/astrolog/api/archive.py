"""L'Archivio in lettura: cosa hai ripreso, con quanti frame, quante ore e con che filtri.

Vincolo non ovvio: qui non si calcola e non si filtra niente. La pagina la fa la spina in SQL
(`spine/archive.page`), perche' cercare fra le righe gia' scaricate troverebbe solo quelle -- e un
archivio di seicento oggetti direbbe "non trovato" mentendo. L'**ordine lo decide il backend**
anche quando lo scegli tu, o due viste dello stesso archivio si metterebbero d'accordo per caso.
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from ..spine import archive, filters_used, objects
from .deps import get_db
from .models_archive import ArchiveChoices, ArchiveFound, ArchiveList, ArchiveObject, ArchivePanel

router = APIRouter(prefix="/api/v1", tags=["archivio"])

# I tre ordini della barra, come chiavi: `Literal` li fa rifiutare a FastAPI **prima** che
# arrivino alla spina, e li scrive nell'OpenAPI, da cui il frontend genera i suoi tipi.
Sort = Literal["name", "hours", "frames"]


@router.get("/archive", response_model=ArchiveList)
def archive_page(  # noqa: PLR0913
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, max_length=200),
    catalog: str | None = Query(None, max_length=40),
    constellation: str | None = Query(None, max_length=8),
    filter_name: str | None = Query(None, alias="filter", max_length=120),
    mosaic: bool = False,
    sort: Sort = "name",
    conn=Depends(get_db),
):
    """Le righe dell'archivio -- oggetti e mosaici confermati -- in ordine di nome, coi filtri di
    ognuna.

    Il tetto di fabbrica e' alto (100) perche' questo elenco e' un **inventario**, non un flusso
    da scorrere: chi ha centomila frame ha comunque una manciata di oggetti, e chiederne venti per
    volta sarebbe cinque giri per vedere cio' che sta in uno."""
    criteri = {
        "q": q,
        "catalog": catalog,
        "constellation": constellation,
        "filter_name": filter_name,
        "mosaic": mosaic,
    }
    righe, quanti = archive.page(conn, limit=limit, offset=offset, sort=sort, **criteri)
    # I filtri in **una domanda per genere di riga** per tutta la pagina, non una per riga: sono la
    # stessa casa che li conta per una notte (`spine/filters_used.py`). La riga di un oggetto porta
    # solo le sue pose fuori dai mosaici, come le sue ore.
    oggetti = [r["id"] for r in righe if r["mosaic_key"] is None]
    filtri = filters_used.of(conn, "object", oggetti, alone=True)
    mosaici = [r["mosaic_key"] for r in righe if r["mosaic_key"]]
    filtri |= filters_used.of(conn, "mosaic", mosaici)
    pannelli = archive.panels(conn, mosaici)
    return ArchiveList(
        items=[
            ArchiveObject(
                # un mosaico si chiama con la chiave della sua risposta, che nessun oggetto porta
                key=r["mosaic_key"] or objects.stable_key(r),
                name=objects.display_name(r),
                slug=r["catalog_slug"],
                frames=r["frames"],
                integration_s=r["integration_s"],
                untimed=r["untimed"],
                constellation=r["constellation"],
                type_code=r["type_code"],
                filters=filtri.get(r["mosaic_key"] or r["id"], []),
                panels=r["panels"],
                panel_list=[ArchivePanel(**p) for p in pannelli.get(r["mosaic_key"], [])],
            )
            for r in righe
        ],
        total=quanti,
        found=ArchiveFound(**archive.found(conn, **criteri)),
        limit=limit,
        offset=offset,
        choices=ArchiveChoices(**archive.choices(conn)),
    )
