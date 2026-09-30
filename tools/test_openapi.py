"""Lo schema OpenAPI estratto senza server: e' la sorgente da cui il frontend genera i suoi tipi.

Se questo schema e' sbagliato non se ne accorge nessuno subito: si accorgono i tipi generati, cioe'
il frontend che non compila o -- peggio -- che compila contro nomi che non esistono piu'.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openapi  # noqa: E402


def test_the_schema_names_its_operations_readably():
    """I nomi delle operazioni sono quelli delle funzioni: da qui il generatore ricava le
    funzioni del client, e i nomi di fabbrica di FastAPI arrivano come `review_api_v1_review_get`.
    La stessa regola e' inchiodata anche dalla parte dell'app: qui si guarda cio' che **esce**."""
    paths = openapi.schema()["paths"]
    operazioni = [d["operationId"] for p in paths.values() for d in p.values()]
    assert "review" in operazioni
    assert not any("_api_v1_" in o for o in operazioni)


def test_the_page_is_not_in_the_schema():
    """La pagina non e' una rotta dell'API: se entrasse qui diventerebbe un tipo del frontend
    che non descrive niente."""
    assert "/" not in openapi.schema()["paths"]


def test_asking_for_the_schema_does_not_touch_the_real_data(tmp_path, monkeypatch):
    """**La promessa dell'intestazione**: lo schema si estrae su un database usa e getta.

    Senza questa prova basterebbe un `create_app()` senza percorso perche' lo strumento creasse
    il database **vero** dell'utente -- per stampare uno schema che i dati non li guarda nemmeno
    -- e nessuno se ne accorgerebbe, perche' lo schema uscirebbe giusto lo stesso."""
    monkeypatch.setenv("ASTROLOG_DATA_DIR", str(tmp_path))
    openapi.schema()
    assert not list(tmp_path.rglob("*.db")), "ha creato un database nella cartella dati"


def test_it_writes_the_schema_where_it_is_told(tmp_path):
    """Scritto su file, perche' e' cosi' che il generatore dei tipi lo consuma."""
    fuori = tmp_path / "openapi.json"
    assert openapi.main([str(fuori)]) == 0
    dati = json.loads(fuori.read_text(encoding="utf-8"))
    assert dati["info"]["title"] == "AstroLog API"
    assert "/api/v1/review" in dati["paths"]
