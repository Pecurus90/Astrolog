"""I vocabolari che l'app si porta dentro, come li legge la pagina.

Vincolo non ovvio: **non aprono il database**. Un vocabolario non e' un dato dell'utente -- e'
un elenco impacchettato col programma -- quindi si legge appena installati, a mani vuote, e una
dipendenza dal database qui sarebbe una promessa in piu' senza un difetto in meno.

L'**ordine** e' quello che il vocabolario dichiara (`filters.models()`: "l'ordine con cui si
cerca in tendina"): arriva intatto, e il frontend non riordina. Due case che ordinano sono due
ordini che prima o poi divergono.
"""

from fastapi import APIRouter

from ..vocab import filters
from .models_review import FilterModelList, FilterModelOut

router = APIRouter(prefix="/api/v1", tags=["vocabolari"])


@router.get("/vocab/filter-models", response_model=FilterModelList)
def filter_models():
    """I filtri in commercio da cui si dichiara un filtro nuovo: marca, nome e banda. Senza pagine:
    il vocabolario viene col programma e non cresce con l'archivio."""
    return FilterModelList(
        items=[
            FilterModelOut(id=m["id"], brand=m["brand"], name=m["name"], passband=m["passband"])
            for m in filters.models()
        ]
    )
