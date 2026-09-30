"""La forma di una risposta a pagine e' scritta una volta (`api/models_page.py`): un modello che
ricopiasse i suoi campi invece di ereditarli cade qui. I modelli si cercano in tutti i moduli
dell'API, non in un elenco scritto a mano."""

import importlib
import pkgutil

from pydantic import BaseModel

import astrolog.api
from astrolog.api.models_page import Page, page_of

CAMPI = set(Page.model_fields)


def _modelli_dell_api():
    for info in pkgutil.iter_modules(astrolog.api.__path__):
        modulo = importlib.import_module(f"astrolog.api.{info.name}")
        for valore in vars(modulo).values():
            if isinstance(valore, type) and issubclass(valore, BaseModel):
                yield valore


def test_every_paged_model_inherits_the_page():
    copie = {
        m.__name__
        for m in _modelli_dell_api()
        if set(m.model_fields) >= CAMPI and not issubclass(m, Page)
    }
    assert copie == set()


def test_the_page_cut_from_memory():
    righe = list(range(7))
    assert page_of(righe, 3, 5) == {"items": [5, 6], "total": 7, "limit": 3, "offset": 5}
