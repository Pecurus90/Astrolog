"""Quanto costa mettere il catalogo nel database, e quanto costa interrogarlo.

E' la misura che decide il disegno: se caricare ventiduemila voci costasse secondi, il
catalogo dovrebbe stare in un file letto a pezzi invece che in tabelle. Marcato `lento`: gira
a richiesta e in CI, mai nel cancello.
"""

import json
import time
from pathlib import Path

import pytest

from astrolog.catalog import bundle, load, lookup

# Catturata all'import, PRIMA del recinto della suite: questo e' l'unico test che deve
# arrivare al catalogo vero, ed e' il motivo per cui esiste.
real_path = bundle.path

BASELINE = Path(__file__).with_name("perf_baseline.json")
TOLLERANZA = 3.0  # una CI e' piu' lenta di un portatile, ma non tre volte


@pytest.mark.lento
def test_catalog_load_seconds_does_not_regress(conn):
    """Il catalogo vero, quello impacchettato: 22.080 voci."""
    percorso = real_path()
    assert percorso, "il catalogo impacchettato non c'e'"

    t0 = time.perf_counter()
    quante = load.load_catalog(conn, percorso)
    misura = round(time.perf_counter() - t0, 3)
    assert quante > 20000, f"il catalogo ha solo {quante} voci"

    dati = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    if "catalog_load_seconds" not in dati:
        dati["catalog_load_seconds"] = misura
        BASELINE.write_text(json.dumps(dati), encoding="utf-8")
        pytest.skip(f"prima misura: {misura} s scritti in perf_baseline.json")
    atteso = dati["catalog_load_seconds"]
    assert misura <= atteso * TOLLERANZA, f"{misura} s contro {atteso} committati"


@pytest.mark.lento
def test_the_cone_stays_fast_on_the_real_catalogue(conn):
    """La ricerca per cono la fara' `identify` una volta per posa: su diecimila pose, un
    decimo di secondo l'una sarebbe un'ora. Deve restare nell'ordine del millesimo, ed e'
    per questo che le voci portano il versore e l'indice."""
    load.load_catalog(conn, real_path())
    t0 = time.perf_counter()
    for _ in range(100):
        lookup.in_cone(conn, 10.6847, 41.269, 1.0)
    per_volta = (time.perf_counter() - t0) / 100
    assert per_volta < 0.05, f"{per_volta * 1000:.0f} ms a ricerca"
