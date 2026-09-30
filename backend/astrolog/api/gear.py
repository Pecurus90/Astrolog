"""L'Attrezzatura in lettura: con cosa hai ripreso, e quanto.

Vincolo non ovvio: qui non si calcola niente. Le righe le fa la spina (`spine/inventory.py`), coi
conteggi che l'Archivio e le Notti usano gia'; e cio' che non si sa arriva **nullo**, non a zero.
La pagina scrive perche' manca.
"""

from fastapi import APIRouter, Depends

from ..spine import gear, inventory
from . import instrument_answer as strumento
from .deps import get_db
from .models_gear import GearList

router = APIRouter(prefix="/api/v1", tags=["attrezzatura"])


@router.get("/gear", response_model=GearList)
def gear_list(conn=Depends(get_db)):
    """I pezzi che possiedi, per genere, coi corredi e i filtri.

    Senza paginazione, e non per dimenticanza: l'attrezzatura di chiunque sta in una schermata --
    chi ha centomila frame ha comunque una manciata di telescopi -- e impaginarla vorrebbe dire
    un giro in piu' per vedere cio' che sta in uno."""
    pezzi = inventory.instruments(conn)
    for p in pezzi:
        # si offrono solo le unioni che la spina accetta: la stessa regola della risposta
        p["mergeable_into"] = [o["id"] for o in pezzi if gear.mergeable(p, o)]
    filtri = inventory.filters(conn)
    for f in filtri:
        # le unioni che la spina accetta: la stessa regola di chi unisce
        f["mergeable_into"] = [o["id"] for o in filtri if gear.filter_mergeable(f, o)]
    return GearList.model_validate(
        {
            "instruments": pezzi,
            "rigs": inventory.rigs(conn),
            "filters": filtri,
            # Quali campi chiede la scheda di un genere lo sa l'api, non la spina: e' la
            # stessa tabella con cui la risposta rifiuta un campo che quel genere non ha.
            "cards": strumento.CARD,
        }
    )
