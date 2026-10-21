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
from astrolog.db.connect import connect, create_database
from conftest import best_of

# Catturata all'import, PRIMA del recinto della suite: questo e' l'unico test che deve
# arrivare al catalogo vero, ed e' il motivo per cui esiste.
real_path = bundle.path

BASELINE = Path(__file__).with_name("perf_baseline.json")
TOLLERANZA = 3.0  # una CI e' piu' lenta di un portatile, ma non tre volte


@pytest.mark.lento
def test_catalog_load_seconds_does_not_regress(tmp_path):
    """Il catalogo vero, quello impacchettato: 22.080 voci, la migliore di tre corse, ognuna in un
    database nuovo (sullo stesso il catalogo c'e' gia' e non si ricarica)."""
    percorso = real_path()
    assert percorso, "il catalogo impacchettato non c'e'"
    giri = iter(range(3))

    def una_corsa():
        db = tmp_path / f"giro{next(giri)}.db"
        create_database(db)
        conn = connect(db)
        try:
            t0 = time.perf_counter()
            quante = load.load_catalog(conn, percorso)
            secondi = time.perf_counter() - t0
        finally:
            conn.close()
        assert quante > 20000, f"il catalogo ha solo {quante} voci"
        return secondi

    misura = round(best_of(3, una_corsa), 3)

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


def test_a_timing_skips_among_other_processes_and_keeps_its_best_run(monkeypatch):
    """Una misura di tempo con decine di processi addosso misura il carico, non il codice: sotto
    `-n auto` si salta. Da sola tiene la migliore di tre corse, come `timeit`."""
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")
    with pytest.raises(pytest.skip.Exception):
        best_of(3, lambda: 1.0)
    monkeypatch.delenv("PYTEST_XDIST_WORKER")
    corse = iter([0.9, 0.4, 0.7])
    assert best_of(3, lambda: next(corse)) == 0.4
