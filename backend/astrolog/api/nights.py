"""Le Notti in lettura: quando hai ripreso, da dove, e cosa hai fatto quella sera.

Vincolo non ovvio: qui non si calcola niente. Le righe le fa la spina in SQL
(`spine/nights.py`), e l'**ordine lo decide il backend** -- dalla notte piu' recente -- o due
schermi dello stesso archivio si metterebbero d'accordo per caso. Accanto all'elenco viaggiano
le due cose che spiegano un elenco corto: quante pose aspettano una risposta e quante la spina
ha ancora da leggere.
"""

from fastapi import APIRouter, Depends, Query

from ..spine import nights
from ..weather import history
from .deps import get_db
from .models_nights import NightList

router = APIRouter(prefix="/api/v1", tags=["notti"])


@router.get("/nights", response_model=NightList)
def night_list(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db),
):
    """Le notti dell'archivio, dalla piu' recente.

    Il tetto di fabbrica e' lo stesso dell'Archivio (100): sono molte piu' righe -- una per
    notte, non una per oggetto -- ma si guardano allo stesso modo, scorrendo indietro nel tempo,
    e chiederne venti per volta sarebbe cinque giri per vedere un anno."""
    # `model_validate` e non il costruttore: la spina manda gia' **la forma della pagina**, e
    # ricopiare qui campo per campo vorrebbe dire due elenchi di nomi da tenere d'accordo. Validare
    # non e' piu' permissivo: un campo che manca o che non e' del tipo giusto e' un errore qui,
    # non una riga storta a schermo.
    return NightList.model_validate(
        {
            "items": nights.page(conn, limit=limit, offset=offset, observed=history.KIND),
            "total": nights.how_many(conn),
            "limit": limit,
            "offset": offset,
            "totals": nights.archive_totals(conn),
            "waiting": nights.waiting(conn),
            "still_reading": nights.still_reading(conn),
        }
    )
